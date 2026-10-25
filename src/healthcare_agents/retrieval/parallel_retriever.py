"""Concurrent healthcare retrieval execution orchestrating parallel multi-source requests."""

from __future__ import annotations

import concurrent.futures
import time
from datetime import UTC, datetime
from typing import Any

from healthcare_agents.planning.fanout_schema import FanOutPlan, PlannedQuery, QueryStatus
from healthcare_agents.retrieval.base import (
    BaseEvidenceRetriever,
    BasePatientEducationRetriever,
    BaseProviderRetriever,
    BaseQualityRetriever,
    ClinicalEvidenceRecord,
    CMSQualityRecord,
    ProviderRecord,
)


def execute_parallel_retrieval(
    fanout_plan: FanOutPlan,
    provider_retriever: BaseProviderRetriever,
    evidence_retriever: BaseEvidenceRetriever,
    patient_education_retriever: BasePatientEducationRetriever,
    quality_retriever: BaseQualityRetriever,
    max_workers: int = 4,
    timeout_seconds: float = 15.0,
) -> dict[str, Any]:
    """Execute independent healthcare retrieval queries concurrently using a bounded thread pool.

    Maintains strict dependency ordering:
    - Independent queries (NPPES, PubMed, MedlinePlus) are dispatched in parallel.
    - Dependent queries (CMS Quality enrichment) wait for candidate NPIs.
    - Records start/end timestamps, monotonic duration, status, and error types per query.
    """
    request_id = fanout_plan.request_id
    execution_events: list[dict[str, Any]] = []
    errors: list[str] = []

    candidates: list[ProviderRecord] = []
    clinical_evidence: list[ClinicalEvidenceRecord] = []
    patient_education: list[ClinicalEvidenceRecord] = []
    cms_quality: list[CMSQualityRecord] = []
    unmatched_cms: list[CMSQualityRecord] = []

    # Separate independent vs dependent queries
    independent_queries = [
        q for q in fanout_plan.queries if not q.dependency_ids and q.source != "CMS"
    ]
    cms_queries = [q for q in fanout_plan.queries if q.source == "CMS" or q.dependency_ids]

    def run_nppes_query(
        query: PlannedQuery,
    ) -> tuple[PlannedQuery, list[ProviderRecord], dict[str, Any]]:
        t0 = time.perf_counter()
        t_start = datetime.now(UTC).isoformat()
        status: QueryStatus = "completed"
        err_type = None
        records: list[ProviderRecord] = []
        try:
            params = query.search_params
            records = list(
                provider_retriever.search_providers(
                    specialty=params.get("specialty"),
                    city=params.get("city"),
                    state=params.get("state"),
                    limit=params.get("limit", 5),
                )
            )
            if (
                not records
                and params.get("specialty")
                and (params.get("city") or params.get("state"))
            ):
                records = list(
                    provider_retriever.search_providers(
                        specialty=params.get("specialty"),
                        limit=params.get("limit", 5),
                    )
                )
        except Exception as exc:
            status = "failed"
            err_type = type(exc).__name__
            errors.append(f"NPPES retrieval error for '{query.query_text}': {exc}")
        finally:
            t1 = time.perf_counter()
            duration_ms = round((t1 - t0) * 1000.0, 2)
            query.status = status
            query.result_count = len(records)
            query.duration_ms = duration_ms
            query.error_message = err_type

            event = {
                "request_id": request_id,
                "query_id": query.query_id,
                "dependency_ids": query.dependency_ids,
                "stage": "NPPES Retrieval",
                "tool_name": type(provider_retriever).__name__,
                "status": status,
                "start_time": t_start,
                "end_time": datetime.now(UTC).isoformat(),
                "duration_ms": duration_ms,
                "query_summary": query.query_text,
                "result_count": len(records),
                "error_type": err_type,
                "output_summary": f"Retrieved {len(records)} provider records",
            }
        return query, records, event

    def run_pubmed_query(
        query: PlannedQuery,
    ) -> tuple[PlannedQuery, list[ClinicalEvidenceRecord], dict[str, Any]]:
        t0 = time.perf_counter()
        t_start = datetime.now(UTC).isoformat()
        status: QueryStatus = "completed"
        err_type = None
        records: list[ClinicalEvidenceRecord] = []
        try:
            params = query.search_params
            topic = params.get("topic") or query.query_text
            limit = params.get("limit", 5)
            records = list(evidence_retriever.search_evidence(topic=topic, limit=limit))
        except Exception as exc:
            status = "failed"
            err_type = type(exc).__name__
            errors.append(f"PubMed retrieval error for '{query.query_text}': {exc}")
        finally:
            t1 = time.perf_counter()
            duration_ms = round((t1 - t0) * 1000.0, 2)
            query.status = status
            query.result_count = len(records)
            query.duration_ms = duration_ms
            query.error_message = err_type

            event = {
                "request_id": request_id,
                "query_id": query.query_id,
                "dependency_ids": query.dependency_ids,
                "stage": "PubMed Retrieval",
                "tool_name": type(evidence_retriever).__name__,
                "status": status,
                "start_time": t_start,
                "end_time": datetime.now(UTC).isoformat(),
                "duration_ms": duration_ms,
                "query_summary": query.query_text,
                "result_count": len(records),
                "error_type": err_type,
                "output_summary": f"Retrieved {len(records)} PubMed research articles",
            }
        return query, records, event

    def run_medline_query(
        query: PlannedQuery,
    ) -> tuple[PlannedQuery, list[ClinicalEvidenceRecord], dict[str, Any]]:
        t0 = time.perf_counter()
        t_start = datetime.now(UTC).isoformat()
        status: QueryStatus = "completed"
        err_type = None
        records: list[ClinicalEvidenceRecord] = []
        try:
            params = query.search_params
            raw_topics = params.get("topics")
            lang = params.get("language", "en")
            limit = params.get("limit", 3)

            candidates_found: list[ClinicalEvidenceRecord] = []
            if isinstance(raw_topics, list) and raw_topics:
                for t in raw_topics:
                    recs = list(
                        patient_education_retriever.search_topics(
                            keyword=str(t), language=lang, limit=limit
                        )
                    )
                    for r in recs:
                        if not any(x.official_url == r.official_url for x in candidates_found):
                            candidates_found.append(r)
            else:
                kw = str(params.get("keyword") or query.query_text)
                candidates_found = list(
                    patient_education_retriever.search_topics(
                        keyword=kw, language=lang, limit=limit
                    )
                )
                # If compound query returned 0, try splitting on 'and'
                if not candidates_found and " and " in kw:
                    for sub_kw in kw.split(" and "):
                        recs = list(
                            patient_education_retriever.search_topics(
                                keyword=sub_kw.strip(), language=lang, limit=limit
                            )
                        )
                        for r in recs:
                            if not any(x.official_url == r.official_url for x in candidates_found):
                                candidates_found.append(r)

            records = candidates_found[:limit]
        except Exception as exc:
            status = "failed"
            err_type = type(exc).__name__
            errors.append(f"MedlinePlus retrieval error for '{query.query_text}': {exc}")
        finally:
            t1 = time.perf_counter()
            duration_ms = round((t1 - t0) * 1000.0, 2)
            query.status = status
            query.result_count = len(records)
            query.duration_ms = duration_ms
            query.error_message = err_type

            event = {
                "request_id": request_id,
                "query_id": query.query_id,
                "dependency_ids": query.dependency_ids,
                "stage": "MedlinePlus Retrieval",
                "tool_name": type(patient_education_retriever).__name__,
                "status": status,
                "start_time": t_start,
                "end_time": datetime.now(UTC).isoformat(),
                "duration_ms": duration_ms,
                "query_summary": query.query_text,
                "result_count": len(records),
                "error_type": err_type,
                "output_summary": f"Retrieved {len(records)} patient education topics",
            }
        return query, records, event

    # Phase 1: Parallel dispatch of independent retrieval queries
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures: list[
            concurrent.futures.Future[tuple[PlannedQuery, list[Any], dict[str, Any]]]
        ] = []
        for q in independent_queries:
            q.status = "dispatched"
            if q.source == "NPPES":
                futures.append(executor.submit(run_nppes_query, q))
            elif q.source == "PubMed":
                futures.append(executor.submit(run_pubmed_query, q))
            elif q.source == "MedlinePlus":
                futures.append(executor.submit(run_medline_query, q))

        # Collect results as they complete
        for fut in concurrent.futures.as_completed(futures):
            q_res, recs, ev = fut.result()
            execution_events.append(ev)
            if q_res.source == "NPPES":
                candidates.extend(recs)
            elif q_res.source == "PubMed":
                clinical_evidence.extend(recs)
            elif q_res.source == "MedlinePlus":
                patient_education.extend(recs)

    # Phase 2: Dependent execution of CMS queries
    # CMS lookups depend strictly on candidate provider NPIs discovered in Phase 1
    npis_queried = [p.npi for p in candidates if p.npi and p.npi.isdigit() and len(p.npi) == 10]
    for q_cms in cms_queries:
        q_cms.status = "dispatched"
        t0_cms = time.perf_counter()
        t_start_cms = datetime.now(UTC).isoformat()
        status_cms: QueryStatus = "completed"
        err_cms = None
        cms_records_count = 0

        if not npis_queried:
            # Explicitly mark as completed with 0 results due to lack of candidate NPIs
            t1_cms = time.perf_counter()
            duration_ms = round((t1_cms - t0_cms) * 1000.0, 2)
            q_cms.status = "completed"
            q_cms.result_count = 0
            q_cms.duration_ms = duration_ms

            execution_events.append(
                {
                    "request_id": request_id,
                    "query_id": q_cms.query_id,
                    "dependency_ids": q_cms.dependency_ids,
                    "stage": "CMS Retrieval",
                    "tool_name": type(quality_retriever).__name__,
                    "status": "completed",
                    "start_time": t_start_cms,
                    "end_time": datetime.now(UTC).isoformat(),
                    "duration_ms": duration_ms,
                    "query_summary": "No candidate NPIs available for CMS quality lookup",
                    "result_count": 0,
                    "error_type": None,
                    "output_summary": "Discovered 0 candidate NPIs from NPPES; skipped CMS lookups",
                }
            )
            continue

        try:
            for npi_val in npis_queried:
                try:
                    records = quality_retriever.get_provider_quality(npi=npi_val)
                    for q_rec in records:
                        if q_rec.npi == npi_val:
                            cms_quality.append(q_rec)
                        else:
                            unmatched_cms.append(q_rec)
                except Exception as q_exc:
                    err_cms = type(q_exc).__name__
                    errors.append(f"CMS retrieval error for NPI {npi_val}: {q_exc}")
            cms_records_count = len(cms_quality)
        except Exception as exc:
            status_cms = "failed"
            err_cms = type(exc).__name__
            errors.append(f"CMS batch error: {exc}")
        finally:
            t1_cms = time.perf_counter()
            duration_ms = round((t1_cms - t0_cms) * 1000.0, 2)
            q_cms.status = status_cms
            q_cms.result_count = cms_records_count
            q_cms.duration_ms = duration_ms
            q_cms.error_message = err_cms

            execution_events.append(
                {
                    "request_id": request_id,
                    "query_id": q_cms.query_id,
                    "dependency_ids": q_cms.dependency_ids,
                    "stage": "CMS Retrieval",
                    "tool_name": type(quality_retriever).__name__,
                    "status": status_cms,
                    "start_time": t_start_cms,
                    "end_time": datetime.now(UTC).isoformat(),
                    "duration_ms": duration_ms,
                    "query_summary": f"NPIs: {npis_queried[:3]} ({len(npis_queried)} total)",
                    "result_count": cms_records_count,
                    "error_type": err_cms,
                    "output_summary": f"Retrieved {cms_records_count} CMS quality metric records",
                }
            )

    return {
        "provider_candidates": candidates,
        "clinical_evidence": clinical_evidence,
        "patient_education_evidence": patient_education,
        "cms_quality": cms_quality,
        "unmatched_cms_records": unmatched_cms,
        "execution_events": execution_events,
        "errors": errors,
        "fanout_plan": fanout_plan.model_dump(),
    }
