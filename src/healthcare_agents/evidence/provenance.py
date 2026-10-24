"""Provenance validation and citation integrity verification layer.

CRITICAL DESIGN PRINCIPLES:
1. Every supported factual claim must have a traceable, retrieved source record.
2. Source URL must be consistent with the known source domain (e.g., nlm.nih.gov, cms.gov, hhs.gov).
3. Citation IDs must be unique across retrieved evidence items.
4. Claims must NOT cross inappropriate evidence boundaries:
   - NPPES cannot establish clinical competence or licensure sanctions.
   - PubMed biomedical research cannot establish an individual provider's credentials or licensing.
   - CMS facility ratings are NOT individual clinician/dentist ratings.
   - MedlinePlus consumer education is NOT primary clinical trial research.
5. Models must NEVER invent citation IDs, publication titles, or external sources.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from healthcare_agents.evidence.schemas import ProvenanceRecord, UnifiedEvidenceItem

# Known legitimate source domains
EXPECTED_DOMAINS: dict[str, tuple[str, ...]] = {
    "NPPES": ("npiregistry.cms.hhs.gov", "cms.hhs.gov", "hhs.gov"),
    "PubMed": ("ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov", "nih.gov"),
    "CMS": ("data.cms.gov", "cms.gov", "medicare.gov"),
    "MedlinePlus": ("medlineplus.gov", "nlm.nih.gov"),
    "MedlinePlus-Connect": ("medlineplus.gov", "nlm.nih.gov"),
}


@dataclass(frozen=True)
class CitationCheckResult:
    """Outcome of validating citations against retrieved evidence provenance."""

    is_valid: bool
    cited_ids: list[str]
    valid_citations: list[str]
    unresolved_citations: list[str]
    boundary_violations: list[str]
    url_mismatches: list[str]
    duplicate_citation_ids: list[str]
    validation_notes: list[str]


def build_provenance_registry(
    items: list[UnifiedEvidenceItem],
) -> dict[str, ProvenanceRecord]:
    """Index provenance records by their stable citation identifier."""
    registry: dict[str, ProvenanceRecord] = {}
    for item in items:
        cid = item.citation_id
        if cid:
            registry[cid] = item.provenance
    return registry


def extract_citation_references(text: str) -> list[str]:
    """Extract citations in standard bracketed format, e.g. [NPPES-123] or [PMID-345]."""
    if not text:
        return []
    citations = re.findall(r"\[([A-Za-z0-9_.:-]+)\]", text)
    valid = []
    prefixes = (
        "NPPES-",
        "NPPES:",
        "PMID-",
        "PMID:",
        "CMS-",
        "CMS:",
        "MEDLINEPLUS-",
        "MEDLINEPLUS:",
        "MLP-",
        "MLP:",
        "SYNTH-",
        "SOURCE-",
    )
    for c in citations:
        upper = c.upper()
        if any(upper.startswith(p) for p in prefixes) or upper.startswith("CITE:"):
            valid.append(c)
    return valid


def validate_source_url(source_type: str, url: str) -> bool:
    """Verify source URL matches expected official governmental/institutional domain."""
    if not url:
        return False
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    expected = EXPECTED_DOMAINS.get(source_type, ())
    return any(domain == exp or domain.endswith("." + exp) for exp in expected)


def check_boundary_crossings(
    citation_id: str,
    source_type: str,
    claim_sentence: str,
) -> str | None:
    """Detect if a claim attributes semantics outside the authorized boundary of the source."""
    sentence_lower = claim_sentence.lower()

    if source_type == "NPPES":
        forbidden = [
            "highest quality",
            "top rated",
            "award winning",
            "board certified",
            "malpractice free",
            "best outcome",
        ]
        for phrase in forbidden:
            if phrase in sentence_lower:
                return (
                    f"NPPES citation [{citation_id}] used to claim "
                    f"clinical competence/quality: '{phrase}'"
                )

    elif source_type == "PubMed":
        if (
            "practices at" in sentence_lower
            or "located at" in sentence_lower
            or "contact phone" in sentence_lower
        ):
            return f"PubMed citation [{citation_id}] used to verify provider practice location"

    elif source_type == "CMS":
        if (
            "individual dentist quality" in sentence_lower
            or "pediatric dentist star rating" in sentence_lower
        ):
            return f"CMS citation [{citation_id}] applied as individual clinician rating"

    elif source_type in ("MedlinePlus", "MedlinePlus-Connect"):
        if (
            "primary clinical trial conducted by" in sentence_lower
            or "randomized trial cohort" in sentence_lower
        ):
            return f"MedlinePlus citation [{citation_id}] cited as primary clinical trial data"

    return None


def verify_citation_integrity(
    text: str,
    evidence_items: list[UnifiedEvidenceItem],
) -> CitationCheckResult:
    """Verify that all citations in the narrative exist in retrieved evidence."""
    registry = build_provenance_registry(evidence_items)

    seen_cids: set[str] = set()
    duplicates: list[str] = []
    for item in evidence_items:
        cid = item.citation_id
        if cid in seen_cids:
            duplicates.append(cid)
        seen_cids.add(cid)

    url_mismatches: list[str] = []
    for item in evidence_items:
        if not item.is_synthetic and item.source_url:
            if not validate_source_url(item.source_type, item.source_url):
                url_mismatches.append(
                    f"{item.citation_id}: {item.source_url} does not match "
                    f"expected {item.source_type} domains"
                )

    cited_ids = extract_citation_references(text)
    valid_citations: list[str] = []
    unresolved: list[str] = []
    boundary_violations: list[str] = []
    notes: list[str] = []

    cid_to_item = {item.citation_id: item for item in evidence_items}
    sentences = re.split(r"(?<=[.!?])\s+", text)

    for cid in cited_ids:
        if cid in registry:
            valid_citations.append(cid)
            item = cid_to_item[cid]
            for sentence in sentences:
                if f"[{cid}]" in sentence:
                    violation = check_boundary_crossings(cid, item.source_type, sentence)
                    if violation and violation not in boundary_violations:
                        boundary_violations.append(violation)
        else:
            unresolved.append(cid)

    is_valid = (
        len(unresolved) == 0
        and len(boundary_violations) == 0
        and len(duplicates) == 0
        and len(url_mismatches) == 0
    )

    if not is_valid:
        if unresolved:
            notes.append(f"Unresolved citations not present in retrieved evidence: {unresolved}")
        if boundary_violations:
            notes.append(f"Boundary violations detected: {boundary_violations}")
        if duplicates:
            notes.append(f"Duplicate citation IDs in evidence: {duplicates}")
        if url_mismatches:
            notes.append(f"URL domain mismatches: {url_mismatches}")
    else:
        notes.append(f"All {len(valid_citations)} citations verified against provenance registry.")

    return CitationCheckResult(
        is_valid=is_valid,
        cited_ids=cited_ids,
        valid_citations=valid_citations,
        unresolved_citations=unresolved,
        boundary_violations=boundary_violations,
        url_mismatches=url_mismatches,
        duplicate_citation_ids=duplicates,
        validation_notes=notes,
    )
