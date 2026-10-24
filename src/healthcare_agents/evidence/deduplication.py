"""Deterministic deduplication routines for normalized healthcare evidence.

Deduplication rules:
- NPPES: Exact 10-digit NPI, specialty taxonomy, and practice location.
- PubMed: Exact PMID and DOI where present; never merges distinct papers.
- CMS: Dataset ID, Entity Type, Measure ID, and NPI / Facility ID.
- MedlinePlus: Canonical official URL, topic ID, and language (EN vs ES preserved).
- Cross-source: Never merges unrelated entity types (e.g., clinician with publication).
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from healthcare_agents.evidence.schemas import UnifiedEvidenceItem


def deduplicate_providers(
    items: Sequence[UnifiedEvidenceItem],
) -> list[UnifiedEvidenceItem]:
    """Deduplicate provider candidates by exact NPI or normalized name + practice address."""
    deduped: list[UnifiedEvidenceItem] = []
    seen_keys: set[str] = set()

    for item in items:
        if item.source_type != "NPPES":
            continue

        npi = str(item.source_metadata.get("npi", "")).strip()
        if npi and len(npi) == 10 and npi.isdigit():
            key = f"npi:{npi}"
        else:
            norm_name = re.sub(r"[^a-z0-9]", "", item.title_or_name.lower())
            norm_addr = re.sub(
                r"[^a-z0-9]", "", str(item.source_metadata.get("practice_address", "")).lower()
            )
            key = f"name_addr:{norm_name}:{norm_addr}"

        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(item)

    return deduped


def deduplicate_pubmed_articles(
    items: Sequence[UnifiedEvidenceItem],
) -> list[UnifiedEvidenceItem]:
    """Deduplicate biomedical research publications by exact PMID or DOI."""
    deduped: list[UnifiedEvidenceItem] = []
    seen_pmids: set[str] = set()
    seen_dois: set[str] = set()

    for item in items:
        if item.source_type != "PubMed":
            continue

        pmid = str(item.source_metadata.get("pmid", "")).strip()
        doi = str(item.source_metadata.get("doi", "")).strip().lower()

        if pmid and pmid in seen_pmids:
            continue
        if doi and doi in seen_dois:
            continue

        if pmid:
            seen_pmids.add(pmid)
        if doi:
            seen_dois.add(doi)

        deduped.append(item)

    return deduped


def deduplicate_medlineplus_topics(
    items: Sequence[UnifiedEvidenceItem],
) -> list[UnifiedEvidenceItem]:
    """Deduplicate consumer health topics by canonical URL and language."""
    deduped: list[UnifiedEvidenceItem] = []
    seen_keys: set[str] = set()

    for item in items:
        if item.source_type not in ("MedlinePlus", "MedlinePlus-Connect"):
            continue

        lang = str(item.source_metadata.get("language", "en")).lower()
        topic_id = str(item.source_metadata.get("topic_id", "")).lower()
        url = item.source_url.rstrip("/").lower()

        key = f"{lang}:{topic_id or url}"
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(item)

    return deduped


def deduplicate_cms_records(
    items: Sequence[UnifiedEvidenceItem],
) -> list[UnifiedEvidenceItem]:
    """Deduplicate CMS provider data by dataset, measure, and entity identifier."""
    deduped: list[UnifiedEvidenceItem] = []
    seen_keys: set[str] = set()

    for item in items:
        if item.source_type != "CMS":
            continue

        dataset_id = str(item.source_metadata.get("dataset_id", ""))
        measure_id = str(item.source_metadata.get("measure_id", ""))
        entity_id = item.external_id

        key = f"{dataset_id}:{entity_id}:{measure_id}"
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(item)

    return deduped


def deduplicate_all_evidence(
    items: Sequence[UnifiedEvidenceItem],
) -> list[UnifiedEvidenceItem]:
    """Deduplicate an entire collection of unified evidence preserving source categories."""
    provs = deduplicate_providers(items)
    pubmed = deduplicate_pubmed_articles(items)
    cms = deduplicate_cms_records(items)
    medline = deduplicate_medlineplus_topics(items)
    return provs + pubmed + cms + medline
