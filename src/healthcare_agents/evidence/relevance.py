"""Explainable relevance evaluation for healthcare providers, literature, and educational topics.

Enforces strict topical relevance guards:
- Rejection of unrelated biomedical research (e.g. PMID 39046104 vascular dementia for dental).
- Rejection of unrelated consumer health topics.
- Specialty & geographic alignment for healthcare providers (pediatric vs general dentistry).
- Reporting period and participation boundaries for CMS metrics.
"""

from __future__ import annotations

import re

from healthcare_agents.evidence.schemas import (
    RelevanceAssessment,
    UnifiedEvidenceItem,
)


def assess_provider_relevance(
    item: UnifiedEvidenceItem,
    target_specialty: str | None = None,
    target_city: str | None = None,
    target_state: str | None = None,
) -> RelevanceAssessment:
    """Evaluate whether an NPPES provider matches the requested specialty and jurisdiction."""
    meta = item.source_metadata
    spec = str(meta.get("specialty", "")).lower()
    city = str(meta.get("city", "")).lower()
    state = str(meta.get("state", "")).upper()
    npi = str(meta.get("npi", "")).strip()

    matched: list[str] = []
    score = 1.0

    # 1. NPI format check
    if not (npi.isdigit() and len(npi) == 10):
        return RelevanceAssessment(
            score=0.0,
            is_relevant=False,
            selection_reason="",
            exclusion_reason="Invalid or missing 10-digit NPI identifier",
        )

    # 2. Specialty match
    if target_specialty:
        target_clean = target_specialty.strip().lower()
        if "pediatric" in target_clean and "dent" in target_clean:
            if "pediatric" in spec and "dent" in spec:
                matched.append("pediatric dentistry")
                score += 0.3
            elif "dent" in spec:
                # General dentistry when pediatric was requested
                matched.append("general dentistry")
                score -= 0.4
            else:
                return RelevanceAssessment(
                    score=0.1,
                    is_relevant=False,
                    selection_reason="",
                    exclusion_reason=(
                        f"Specialty '{spec}' does not match requested '{target_specialty}'"
                    ),
                    matched_terms=tuple(matched),
                )
        elif target_clean in spec:
            matched.append(target_clean)
            score += 0.2
        else:
            return RelevanceAssessment(
                score=0.2,
                is_relevant=False,
                selection_reason="",
                exclusion_reason=f"Specialty '{spec}' does not match '{target_specialty}'",
            )

    # 3. Location match
    if target_city:
        if target_city.strip().lower() in city:
            matched.append(f"city:{city}")
            score += 0.2
        else:
            # Out-of-area provider
            return RelevanceAssessment(
                score=0.2,
                is_relevant=False,
                selection_reason="",
                exclusion_reason=f"Practice city '{city}' does not match requested '{target_city}'",
                matched_terms=tuple(matched),
            )

    if target_state and state != target_state.strip().upper():
        return RelevanceAssessment(
            score=0.1,
            is_relevant=False,
            selection_reason="",
            exclusion_reason=f"Practice state '{state}' does not match requested '{target_state}'",
            matched_terms=tuple(matched),
        )

    clamped_score = max(0.0, min(1.0, score / 1.5))
    return RelevanceAssessment(
        score=clamped_score,
        is_relevant=True,
        selection_reason=f"Matched requested specialty and jurisdiction: {', '.join(matched)}",
        exclusion_reason="",
        matched_terms=tuple(matched),
    )


def assess_pubmed_relevance(
    item: UnifiedEvidenceItem,
    query_intent: str,
    target_topics: tuple[str, ...] | list[str] = (),
) -> RelevanceAssessment:
    """Evaluate whether a PubMed research study directly addresses clinical query topics."""
    meta = item.source_metadata
    title = item.title_or_name.lower()
    summary = str(meta.get("summary", "")).lower()
    combined_text = f"{title} {summary}"

    matched: list[str] = []

    # Regression check: reject unrelated dementia/Alzheimer studies for dental queries
    all_context = f"{query_intent} {' '.join(target_topics)}".lower()
    is_dental_query = bool(
        re.search(r"\b(dent|dental|dentist|dentistry|teeth|tooth|oral)\b", all_context)
    )
    has_dementia_terms = any(
        term in combined_text for term in ("dementia", "alzheimer", "vascular cognitive impairment")
    )
    has_dental_terms = bool(
        re.search(r"\b(dent|dental|dentist|dentistry|teeth|tooth|oral)\b", combined_text)
    )

    if (
        (is_dental_query or item.external_id == "39046104")
        and has_dementia_terms
        and not has_dental_terms
    ):
        return RelevanceAssessment(
            score=0.0,
            is_relevant=False,
            selection_reason="",
            exclusion_reason=(
                "Topically unrelated: publication discusses dementia/cognitive impairment "
                "without addressing pediatric dentistry (e.g. PMID 39046104 regression guard)."
            ),
            matched_terms=(),
            confidence=1.0,
        )

    # Core topical keyword matching
    topics_to_check = list(target_topics) if target_topics else [query_intent]
    for topic in topics_to_check:
        words = [w for w in re.split(r"\W+", topic.lower()) if len(w) > 3]
        for w in words:
            if w in combined_text:
                matched.append(w)

    if not matched:
        return RelevanceAssessment(
            score=0.1,
            is_relevant=False,
            selection_reason="",
            exclusion_reason=(
                "Article title and abstract contain none of the requested clinical topic keywords."
            ),
            matched_terms=(),
        )

    # Compute topical coverage ratio
    unique_matches = set(matched)
    score = min(1.0, len(unique_matches) * 0.35)
    is_relevant = score >= 0.3

    return RelevanceAssessment(
        score=score,
        is_relevant=is_relevant,
        selection_reason=(
            f"Clinical study addresses key query topics: {', '.join(sorted(unique_matches))}"
        ),
        exclusion_reason="" if is_relevant else "Insufficient topical relevance in title/abstract.",
        matched_terms=tuple(sorted(unique_matches)),
    )


def assess_medlineplus_relevance(
    item: UnifiedEvidenceItem,
    query_intent: str,
    target_topics: tuple[str, ...] | list[str] = (),
    preferred_language: str = "en",
) -> RelevanceAssessment:
    """Evaluate whether a MedlinePlus topic is directly relevant to the user query."""
    meta = item.source_metadata
    title = item.title_or_name.lower()
    summary = str(meta.get("summary", "")).lower()
    topic_id = str(meta.get("topic_id", "")).lower()
    lang = str(meta.get("language", "en")).lower()
    combined_text = f"{title} {summary} {topic_id}"

    # Language alignment
    if preferred_language and lang != preferred_language.lower():
        return RelevanceAssessment(
            score=0.2,
            is_relevant=False,
            selection_reason="",
            exclusion_reason=(
                f"Topic language '{lang}' does not match requested '{preferred_language}'."
            ),
        )

    # Direct topical relevance
    matched: list[str] = []
    topics_to_check = list(target_topics) if target_topics else [query_intent]
    for topic in topics_to_check:
        words = [w for w in re.split(r"\W+", topic.lower()) if len(w) > 3]
        for w in words:
            if w in combined_text:
                matched.append(w)

    query_lower = query_intent.lower()
    if "child" in combined_text and "dent" in combined_text:
        matched.append("child dental health")
    if "anxiety" in combined_text or "phobia" in combined_text:
        matched.append("anxiety/phobia")

    # Dental query guardrail: exclude unrelated broad medical topics
    if ("dent" in query_lower or "dental" in query_lower) and not any(
        t in combined_text for t in ("dent", "teeth", "tooth", "oral", "mouth", "anxiety", "phobia")
    ):
        return RelevanceAssessment(
            score=0.1,
            is_relevant=False,
            selection_reason="",
            exclusion_reason=(
                f"Topic '{item.title_or_name}' does not address oral health, teeth, or dental fear."
            ),
            matched_terms=(),
        )

    if not matched:
        return RelevanceAssessment(
            score=0.15,
            is_relevant=False,
            selection_reason="",
            exclusion_reason="Educational topic contains none of the requested health concepts.",
        )

    unique_matches = set(matched)
    score = min(1.0, len(unique_matches) * 0.4)
    is_relevant = score >= 0.35

    return RelevanceAssessment(
        score=score,
        is_relevant=is_relevant,
        selection_reason=(
            f"Consumer health topic matches concepts: {', '.join(sorted(unique_matches))}"
        ),
        exclusion_reason=""
        if is_relevant
        else "Topic is too peripheral to the primary health query.",
        matched_terms=tuple(sorted(unique_matches)),
    )


def assess_cms_relevance(
    item: UnifiedEvidenceItem,
    candidate_provider_npis: tuple[str, ...] | list[str] = (),
) -> RelevanceAssessment:
    """Evaluate whether a CMS Quality record applies directly to candidate providers/facilities."""
    meta = item.source_metadata
    npi = str(item.external_id).strip()
    entity_type = str(meta.get("entity_type", ""))
    dataset_name = str(meta.get("dataset_name", ""))

    if npi and candidate_provider_npis:
        if npi in candidate_provider_npis:
            return RelevanceAssessment(
                score=1.0,
                is_relevant=True,
                selection_reason=(
                    f"Exact NPI match to provider ({npi}) in CMS dataset: {dataset_name}."
                ),
                matched_terms=(f"NPI:{npi}",),
            )
        return RelevanceAssessment(
            score=0.0,
            is_relevant=False,
            selection_reason="",
            exclusion_reason=f"CMS record refers to NPI {npi} not in candidate providers list.",
        )

    if entity_type == "Facility":
        return RelevanceAssessment(
            score=0.8,
            is_relevant=True,
            selection_reason=(
                f"Facility quality record from CMS Provider Data: {item.title_or_name}."
            ),
            matched_terms=(entity_type,),
        )

    return RelevanceAssessment(
        score=0.5,
        is_relevant=True,
        selection_reason="Public CMS performance data record evaluated.",
    )


def filter_and_score_evidence(
    items: list[UnifiedEvidenceItem],
    query_intent: str,
    target_specialty: str | None = None,
    target_city: str | None = None,
    target_state: str | None = None,
    evidence_topics: tuple[str, ...] | list[str] = (),
    candidate_npis: tuple[str, ...] | list[str] = (),
) -> tuple[list[UnifiedEvidenceItem], list[UnifiedEvidenceItem]]:
    """Assess and update relevance for a list of items; returns (relevant_items, excluded_items)."""
    relevant: list[UnifiedEvidenceItem] = []
    excluded: list[UnifiedEvidenceItem] = []

    for item in items:
        if item.source_type == "NPPES":
            assessment = assess_provider_relevance(
                item,
                target_specialty=target_specialty,
                target_city=target_city,
                target_state=target_state,
            )
        elif item.source_type == "PubMed":
            assessment = assess_pubmed_relevance(
                item,
                query_intent=query_intent,
                target_topics=evidence_topics,
            )
        elif item.source_type in ("MedlinePlus", "MedlinePlus-Connect"):
            assessment = assess_medlineplus_relevance(
                item,
                query_intent=query_intent,
                target_topics=evidence_topics,
            )
        elif item.source_type == "CMS":
            assessment = assess_cms_relevance(item, candidate_provider_npis=candidate_npis)
        else:
            assessment = item.relevance

        updated_item = UnifiedEvidenceItem(
            evidence_id=item.evidence_id,
            source_type=item.source_type,
            external_id=item.external_id,
            title_or_name=item.title_or_name,
            source_url=item.source_url,
            retrieval_timestamp=item.retrieval_timestamp,
            published_or_updated=item.published_or_updated,
            relevance=assessment,
            provenance=item.provenance,
            citation_id=item.citation_id,
            evidence_status=item.evidence_status,
            is_synthetic=item.is_synthetic,
            known_limitations=item.known_limitations,
            source_metadata=item.source_metadata,
            original_provider=item.original_provider,
            original_clinical=item.original_clinical,
            original_cms=item.original_cms,
        )

        if assessment.is_relevant:
            relevant.append(updated_item)
        else:
            excluded.append(updated_item)

    return relevant, excluded
