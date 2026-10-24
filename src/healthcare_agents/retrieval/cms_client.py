"""CMS Provider Data Catalog Client: Fetches official CMS dataset records, quality scores,
and facility affiliations.

Integrates with the official CMS Provider Data Catalog APIs (https://data.cms.gov/provider-data/)
supporting:
- Dataset discovery and metadata lookup (/api/1/metastore/schemas/dataset/items)
- Datastore querying with conditions and pagination (/api/1/datastore/query/{dataset_id}/0)
- MIPS clinician performance measures (Dataset: a174-a962)
- Hospital general information & quality ratings (Dataset: xubh-q36u)
- Clinician hospital and facility affiliations (Dataset: 27ea-46a8)
- Timeouts, bounded retries with backoff, and graceful error handling
- Source provenance and retrieval timestamps
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from healthcare_agents.retrieval.base import BaseQualityRetriever, CMSQualityRecord

logger = logging.getLogger(__name__)

# Standard CMS Provider Data Catalog Datasets
CMS_DATASET_CLINICIAN_MIPS = "a174-a962"
CMS_DATASET_CLINICIAN_MIPS_TITLE = "PY 2024 Clinician Public Reporting: Overall MIPS Performance"

CMS_DATASET_HOSPITAL_GENERAL = "xubh-q36u"
CMS_DATASET_HOSPITAL_GENERAL_TITLE = "Hospital General Information"

CMS_DATASET_FACILITY_AFFILIATION = "27ea-46a8"
CMS_DATASET_FACILITY_AFFILIATION_TITLE = "Facility Affiliation Data"

DEFAULT_CMS_API_URL = "https://data.cms.gov/provider-data/api/1/"
DEFAULT_USER_AGENT = (
    "open-healthcare-agentic-platform/0.4.2 "
    "(https://github.com/hastimal/open-healthcare-agentic-platform; contact: research@example.com)"
)


class CMSClientError(Exception):
    """Base exception for CMS Provider Data client errors."""


class CMSConnectionError(CMSClientError):
    """Network connection or timeout error accessing CMS Provider Data Catalog API."""


class CMSResponseError(CMSClientError):
    """Malformed or unexpected HTTP response from CMS Provider Data Catalog API."""


class CMSDatasetNotFoundError(CMSClientError):
    """Requested dataset ID does not exist in the CMS Provider Data Catalog."""


class CMSProviderDataRetriever(BaseQualityRetriever):
    """Official client for CMS Provider Data Catalog datasets."""

    def __init__(
        self,
        base_url: str = DEFAULT_CMS_API_URL,
        timeout_seconds: float = 15.0,
        max_retries: int = 3,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.user_agent = user_agent

    def _execute_request(self, full_url: str) -> bytes:
        """Execute HTTP GET with bounded retries and exponential backoff."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        for attempt in range(self.max_retries + 1):
            req = urllib.request.Request(full_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    raw_content: bytes = resp.read()
                    return raw_content
            except urllib.error.HTTPError as http_err:
                code = http_err.code
                if code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    backoff = (2**attempt) * 0.5
                    logger.warning(
                        "CMS API HTTP %d at %s. Retrying in %.2fs (attempt %d/%d)...",
                        code,
                        full_url,
                        backoff,
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(backoff)
                    continue
                if code == 404:
                    raise CMSDatasetNotFoundError(
                        f"CMS Provider Data resource not found: {full_url}"
                    ) from http_err
                raise CMSResponseError(
                    f"CMS Provider Data API returned HTTP error {code}: {http_err.reason}"
                ) from http_err
            except (urllib.error.URLError, TimeoutError, OSError) as conn_err:
                if attempt < self.max_retries:
                    backoff = (2**attempt) * 0.5
                    logger.warning(
                        "Connection error to CMS API: %s. Retrying in %.2fs (attempt %d/%d)...",
                        conn_err,
                        backoff,
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(backoff)
                    continue
                raise CMSConnectionError(
                    f"Failed to connect to CMS API at {full_url}: {conn_err}"
                ) from conn_err

        raise CMSConnectionError(f"Exhausted retries ({self.max_retries}) connecting to CMS API.")

    def query_dataset(
        self,
        dataset_id: str,
        conditions: Sequence[Mapping[str, str]] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Query datastore rows for a dataset with structured conditions.

        Args:
            dataset_id: CMS dataset identifier (e.g., 'a174-a962', 'xubh-q36u').
            conditions: Optional sequence of dicts with 'property' and 'value'.
            limit: Maximum rows to return (bounded 1 to 500).
            offset: Starting row offset for pagination.

        Returns:
            Dictionary with 'count' and 'results' rows.
        """
        clamped_limit = max(1, min(limit, 500))
        params: list[tuple[str, str]] = [
            ("limit", str(clamped_limit)),
            ("offset", str(max(0, offset))),
        ]

        if conditions:
            for idx, cond in enumerate(conditions):
                prop = cond.get("property", "").strip()
                val = cond.get("value", "").strip()
                if prop and val:
                    params.append((f"conditions[{idx}][property]", prop))
                    params.append((f"conditions[{idx}][value]", val))

        query_string = urllib.parse.urlencode(params)
        endpoint = f"{self.base_url}datastore/query/{dataset_id}/0?{query_string}"
        raw_bytes = self._execute_request(endpoint)

        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as json_err:
            raise CMSResponseError(
                f"Malformed JSON returned by CMS datastore query: {json_err}"
            ) from json_err

        if not isinstance(data, dict):
            raise CMSResponseError("Expected JSON object from CMS datastore query.")

        return data

    def get_dataset_metadata(self, dataset_id: str) -> dict[str, Any]:
        """Fetch metadata and schema description for a dataset from the metastore."""
        endpoint = f"{self.base_url}metastore/schemas/dataset/items/{dataset_id}"
        raw_bytes = self._execute_request(endpoint)
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as json_err:
            raise CMSResponseError(
                f"Malformed JSON returned by CMS metastore: {json_err}"
            ) from json_err

        if not isinstance(data, dict):
            raise CMSResponseError("Expected JSON object from CMS metastore.")
        return data

    def discover_datasets(self, keyword: str | None = None) -> list[dict[str, Any]]:
        """List available datasets from metastore, optionally filtered by keyword."""
        endpoint = f"{self.base_url}metastore/schemas/dataset/items"
        raw_bytes = self._execute_request(endpoint)
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as json_err:
            raise CMSResponseError(
                f"Malformed JSON returned by CMS metastore items: {json_err}"
            ) from json_err

        if not isinstance(data, list):
            raise CMSResponseError("Expected JSON list from CMS metastore items.")

        if not keyword:
            return data

        kw_lower = keyword.lower().strip()
        filtered: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            title = item.get("title", "").lower()
            desc = item.get("description", "").lower()
            theme = str(item.get("theme", [])).lower()
            if kw_lower in title or kw_lower in desc or kw_lower in theme:
                filtered.append(item)
        return filtered

    def get_provider_quality(self, npi: str) -> Sequence[CMSQualityRecord]:
        """Retrieve MIPS performance and facility affiliations for an individual NPI."""
        clean_npi = npi.strip()
        if not (clean_npi.isdigit() and len(clean_npi) == 10):
            return []

        retrieval_timestamp = datetime.now(UTC).isoformat()
        records: list[CMSQualityRecord] = []

        # 1. Query Clinician MIPS Quality Measures (dataset: a174-a962)
        try:
            data_mips = self.query_dataset(
                dataset_id=CMS_DATASET_CLINICIAN_MIPS,
                conditions=[{"property": "npi", "value": clean_npi}],
                limit=5,
            )
            for row in data_mips.get("results", []):
                if not isinstance(row, dict):
                    continue
                row_npi = str(row.get("npi", "")).strip()
                if row_npi != clean_npi:
                    continue

                provider_last = row.get("provider_last_name", "").strip()
                provider_first = row.get("provider_first_name", "").strip()
                name = f"{provider_first} {provider_last}".strip() or f"NPI {clean_npi}"

                score = str(row.get("final_mips_score", "")).strip()
                quality_score = str(row.get("quality_category_score", "")).strip()
                cost_score = str(row.get("cost_category_score", "")).strip()
                source_type = row.get("source", "individual")

                records.append(
                    CMSQualityRecord(
                        record_id=f"CMS-MIPS-{clean_npi}",
                        npi=clean_npi,
                        entity_name=name,
                        dataset_id=CMS_DATASET_CLINICIAN_MIPS,
                        dataset_name=CMS_DATASET_CLINICIAN_MIPS_TITLE,
                        source="CMS-Provider-Data",
                        is_synthetic=False,
                        entity_type="Individual",
                        measure_id="FINAL_MIPS_SCORE",
                        measure_name="MIPS Final Performance Score",
                        score=score,
                        performance_rate=quality_score,
                        retrieval_timestamp=retrieval_timestamp,
                        source_url=f"https://data.cms.gov/provider-data/dataset/{CMS_DATASET_CLINICIAN_MIPS}",
                        metadata={
                            "mips_source": source_type,
                            "quality_category_score": quality_score,
                            "cost_category_score": cost_score,
                        },
                    )
                )
        except Exception as e:
            logger.warning("Failed querying CMS MIPS for NPI %s: %s", clean_npi, e)

        # 2. Query Facility Affiliations (dataset: 27ea-46a8)
        try:
            data_affil = self.query_dataset(
                dataset_id=CMS_DATASET_FACILITY_AFFILIATION,
                conditions=[{"property": "npi", "value": clean_npi}],
                limit=5,
            )
            for row in data_affil.get("results", []):
                if not isinstance(row, dict):
                    continue
                row_npi = str(row.get("npi", "")).strip()
                if row_npi != clean_npi:
                    continue

                ccn = str(row.get("facility_affiliations_certification_number", "")).strip()
                facility_type = str(row.get("facility_type", "")).strip()
                provider_last = row.get("provider_last_name", "").strip()
                provider_first = row.get("provider_first_name", "").strip()
                name = f"{provider_first} {provider_last}".strip() or f"NPI {clean_npi}"

                records.append(
                    CMSQualityRecord(
                        record_id=f"CMS-AFFIL-{clean_npi}-{ccn}",
                        npi=clean_npi,
                        entity_name=name,
                        dataset_id=CMS_DATASET_FACILITY_AFFILIATION,
                        dataset_name=CMS_DATASET_FACILITY_AFFILIATION_TITLE,
                        source="CMS-Provider-Data",
                        is_synthetic=False,
                        entity_type="Individual",
                        facility_id=ccn,
                        facility_type=facility_type,
                        measure_id="FACILITY_AFFILIATION",
                        measure_name="Affiliated Facility CCN",
                        score=ccn,
                        retrieval_timestamp=retrieval_timestamp,
                        source_url=f"https://data.cms.gov/provider-data/dataset/{CMS_DATASET_FACILITY_AFFILIATION}",
                        metadata={
                            "facility_ccn": ccn,
                            "facility_type": facility_type,
                        },
                    )
                )
        except Exception as e:
            logger.warning("Failed querying CMS affiliations for NPI %s: %s", clean_npi, e)

        return records

    def search_facility_quality(
        self,
        facility_name: str | None = None,
        city: str | None = None,
        state: str | None = None,
        limit: int = 5,
    ) -> Sequence[CMSQualityRecord]:
        """Search hospital general information and quality star ratings (dataset: xubh-q36u)."""
        conditions: list[dict[str, str]] = []
        if city:
            conditions.append({"property": "citytown", "value": city.strip().upper()})
        if state:
            conditions.append({"property": "state", "value": state.strip().upper()})

        retrieval_timestamp = datetime.now(UTC).isoformat()
        records: list[CMSQualityRecord] = []

        try:
            data = self.query_dataset(
                dataset_id=CMS_DATASET_HOSPITAL_GENERAL,
                conditions=conditions,
                limit=limit * 2 if facility_name else limit,
            )
            for row in data.get("results", []):
                if not isinstance(row, dict):
                    continue

                fac_name = row.get("facility_name", "").strip()
                if facility_name and facility_name.lower() not in fac_name.lower():
                    continue

                fac_id = str(row.get("facility_id", "")).strip()
                row_city = row.get("citytown", "").strip()
                row_state = row.get("state", "").strip()
                rating = str(row.get("hospital_overall_rating", "")).strip()
                hosp_type = row.get("hospital_type", "").strip()
                emerg = row.get("emergency_services", "").strip()

                record = CMSQualityRecord(
                    record_id=f"CMS-HOSP-{fac_id}",
                    npi="",
                    entity_name=fac_name,
                    dataset_id=CMS_DATASET_HOSPITAL_GENERAL,
                    dataset_name=CMS_DATASET_HOSPITAL_GENERAL_TITLE,
                    source="CMS-Provider-Data",
                    is_synthetic=False,
                    entity_type="Facility",
                    facility_id=fac_id,
                    facility_name=fac_name,
                    facility_type=hosp_type,
                    measure_id="HOSPITAL_OVERALL_RATING",
                    measure_name="Hospital Overall Star Rating",
                    score=rating if rating and rating != "Not Available" else "Not Available",
                    star_rating=rating if rating and rating.isdigit() else "",
                    city=row_city,
                    state=row_state,
                    retrieval_timestamp=retrieval_timestamp,
                    source_url=f"https://data.cms.gov/provider-data/dataset/{CMS_DATASET_HOSPITAL_GENERAL}",
                    metadata={
                        "emergency_services": emerg,
                        "hospital_ownership": row.get("hospital_ownership", "").strip(),
                        "rating_footnote": row.get("hospital_overall_rating_footnote", "").strip(),
                    },
                )
                records.append(record)
                if len(records) >= limit:
                    break
        except Exception as e:
            logger.warning("Failed querying CMS hospital quality: %s", e)

        return records
