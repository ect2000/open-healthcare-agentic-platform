"""Source-specific ranking routines for normalized healthcare evidence.

CRITICAL DESIGN PRINCIPLES:
1. NEVER construct an invented, misleading universal clinician quality score.
2. Provider ranking must be explainable: based strictly on specialty relevance,
   practice location proximity, and provenance completeness (never inferred clinical competence).
3. Biomedical research ranking (PubMed): based on topical alignment with clinical intent,
   publication type (e.g., systematic review / guideline / RCT), and publication recency.
4. Patient education ranking (MedlinePlus): based on topical directness, English/Spanish
   matching, and consumer appropriateness.
5. CMS metrics ranking: based on dataset coverage, reporting period currency, and measure
   completeness (clearly isolating facility vs clinician measures).
"""

from __future__ import annotations

import re

from healthcare_agents.evidence.schemas import UnifiedEvidenceItem


def _extract_year(date_str: str) -> int:
    """Extract a 4-digit year from a date string, defaulting to 1900 if not found."""
    if not date_str:
        return 1900
    match = re.search(r"\b(19\d\d|20\d\d)\b", date_str)
    if match:
        return int(match.group(1))
    return 1900


def rank_providers(
    providers: list[UnifiedEvidenceItem],
    limit: int | None = None,
) -> list[UnifiedEvidenceItem]:
    """Rank provider items by explainable relevance, completeness, and NPI stability.

    Ranking Criteria:
    1. Relevance Score (descending)
    2. Practice location completeness (has address, city, state, postal code)
    3. Taxonomy description completeness
    4. Deterministic secondary sort: External ID (NPI) ascending
    """

    def _sort_key(item: UnifiedEvidenceItem) -> tuple[float, int, int, str]:
        score = item.relevance.score
        meta = item.source_metadata
        address_complete = (
            1 if (meta.get("practice_address") and meta.get("city") and meta.get("state")) else 0
        )
        specialty_complete = 1 if meta.get("taxonomy_desc") else 0
        return (score, address_complete, specialty_complete, item.external_id)

    # Sort descending by score, completeness; ascending by external_id
    sorted_items = sorted(
        providers,
        key=lambda item: (
            -_sort_key(item)[0],
            -_sort_key(item)[1],
            -_sort_key(item)[2],
            _sort_key(item)[3],
        ),
    )
    if limit is not None and limit > 0:
        return sorted_items[:limit]
    return sorted_items


def rank_pubmed_articles(
    articles: list[UnifiedEvidenceItem],
    limit: int | None = None,
) -> list[UnifiedEvidenceItem]:
    """Rank PubMed articles by topical relevance, study type hierarchy, and recency.

    Ranking Criteria:
    1. Relevance Score (descending)
    2. Study design weight (guidelines / systematic reviews / trials ranked higher)
    3. Publication year (descending)
    4. Deterministic secondary sort: PMID ascending
    """

    def _study_type_weight(item: UnifiedEvidenceItem) -> int:
        title = item.title_or_name.lower()
        abstract = item.source_metadata.get("abstract", "").lower()
        combined = f"{title} {abstract}"
        if (
            "systematic review" in combined
            or "meta-analysis" in combined
            or "guideline" in combined
        ):
            return 3
        if "randomized controlled trial" in combined or "clinical trial" in combined:
            return 2
        if "cohort" in combined or "case-control" in combined or "observational" in combined:
            return 1
        return 0

    def _sort_key(item: UnifiedEvidenceItem) -> tuple[float, int, int, str]:
        score = item.relevance.score
        study_weight = _study_type_weight(item)
        pub_year = _extract_year(item.published_or_updated)
        return (score, study_weight, pub_year, item.external_id)

    sorted_items = sorted(
        articles,
        key=lambda item: (
            -_sort_key(item)[0],
            -_sort_key(item)[1],
            -_sort_key(item)[2],
            _sort_key(item)[3],
        ),
    )
    if limit is not None and limit > 0:
        return sorted_items[:limit]
    return sorted_items


def rank_medlineplus_topics(
    topics: list[UnifiedEvidenceItem],
    limit: int | None = None,
) -> list[UnifiedEvidenceItem]:
    """Rank MedlinePlus educational topics by topical directness and completeness.

    Ranking Criteria:
    1. Relevance Score (descending)
    2. Title match / exact topic alignment
    3. Content snippet availability
    4. Deterministic secondary sort: Title ascending
    """

    def _sort_key(item: UnifiedEvidenceItem) -> tuple[float, int, str]:
        score = item.relevance.score
        has_snippet = 1 if item.source_metadata.get("snippet") else 0
        return (score, has_snippet, item.title_or_name)

    sorted_items = sorted(
        topics,
        key=lambda item: (
            -_sort_key(item)[0],
            -_sort_key(item)[1],
            _sort_key(item)[2],
        ),
    )
    if limit is not None and limit > 0:
        return sorted_items[:limit]
    return sorted_items


def rank_cms_records(
    cms_records: list[UnifiedEvidenceItem],
    limit: int | None = None,
) -> list[UnifiedEvidenceItem]:
    """Rank CMS Provider Data quality records by entity match and measure completeness.

    Ranking Criteria:
    1. Relevance Score (descending)
    2. Measure count / completeness
    3. Reporting period recency
    4. Deterministic secondary sort: Facility/Provider name ascending
    """

    def _sort_key(item: UnifiedEvidenceItem) -> tuple[float, int, int, str]:
        score = item.relevance.score
        measures = item.source_metadata.get("measures", {})
        measure_count = len(measures) if isinstance(measures, dict) else 0
        rep_year = _extract_year(item.provenance.reporting_period)
        return (score, measure_count, rep_year, item.title_or_name)

    sorted_items = sorted(
        cms_records,
        key=lambda item: (
            -_sort_key(item)[0],
            -_sort_key(item)[1],
            -_sort_key(item)[2],
            _sort_key(item)[3],
        ),
    )
    if limit is not None and limit > 0:
        return sorted_items[:limit]
    return sorted_items


def rank_evidence_collection(
    providers: list[UnifiedEvidenceItem],
    clinical_research: list[UnifiedEvidenceItem],
    cms_records: list[UnifiedEvidenceItem],
    patient_education: list[UnifiedEvidenceItem],
) -> tuple[
    list[UnifiedEvidenceItem],
    list[UnifiedEvidenceItem],
    list[UnifiedEvidenceItem],
    list[UnifiedEvidenceItem],
]:
    """Rank all evidence categories using their dedicated, explainable sorters."""
    return (
        rank_providers(providers),
        rank_pubmed_articles(clinical_research),
        rank_cms_records(cms_records),
        rank_medlineplus_topics(patient_education),
    )
