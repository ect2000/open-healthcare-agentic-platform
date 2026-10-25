"""Intelligent query fan-out generator decomposing patient questions into source-specific plans."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from healthcare_agents.models.base import BaseModelAdapter
from healthcare_agents.planning.fanout_schema import FanOutPlan, PlannedQuery
from healthcare_agents.workflows.state import SearchPlan

FANOUT_SYSTEM_PROMPT = """You are a healthcare retrieval query decomposition planner.
Analyze the user's healthcare inquiry and formulate targeted, source-specific retrieval queries.

Authoritative Healthcare Sources:
1. "NPPES" (National Plan and Provider Enumeration System):
   - Focus: Provider discovery (clinicians, dentists, physicians, clinics).
   - Parameters: "specialty", "city", "state", "first_name", "last_name".
2. "PubMed" (Biomedical Research Literature):
   - Focus: Clinical trials, systematic reviews, interventions, mechanisms.
   - Text: Scientific terminology, biomedical keywords.
3. "MedlinePlus" (Authoritative Consumer Health Education):
   - Focus: Patient guidance, health literacy, overview topics, condition management.
   - Text: Concise consumer health terms (e.g., "child dental health", "tooth decay").
   - DO NOT formulate long conversational sentences or multi-clause academic phrases.
4. "CMS" (CMS Provider Data Catalog):
   - Focus: Facility or clinician quality measures. Dependent on candidate provider discovery.

CRITICAL RULES:
1. ONLY formulate queries reflecting the user's genuine intent.
2. DO NOT invent unsupported medical specialties, locations, or clinical assertions.
3. DO NOT include patient identifiers, dates of birth, or PHI.
4. Return ONLY a valid JSON object matching this structure:
{
  "strategy_notes": "Decomposition strategy summary",
  "queries": [
    {
      "source": "NPPES",
      "query_text": "Pediatric dentistry in Houston, TX",
      "intent_category": "provider_discovery",
      "priority": 1,
      "search_params": {"specialty": "Pediatric Dentistry", "city": "Houston", "state": "TX"}
    },
    {
      "source": "PubMed",
      "query_text": "pediatric dental anxiety management interventions",
      "intent_category": "clinical_research",
      "priority": 1,
      "search_params": {"limit": 5}
    },
    {
      "source": "MedlinePlus",
      "query_text": "child dental health",
      "intent_category": "patient_education",
      "priority": 2,
      "search_params": {"language": "en"}
    }
  ]
}
"""


def extract_json(text: str) -> dict[str, Any]:
    """Extract and parse JSON from model output safely."""
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {}


def build_deterministic_fanout(
    request_id: str,
    original_query: str,
    search_plan: SearchPlan,
    max_fanout: int = 8,
) -> FanOutPlan:
    """Generate a reliable, deterministic query fan-out plan without requiring LLM inference."""
    plan = FanOutPlan(
        request_id=request_id,
        original_query=original_query,
        strategy_notes="Deterministic multi-source healthcare query fan-out.",
        max_fanout=max_fanout,
    )

    specialty = search_plan.get("specialty") or ""
    city = search_plan.get("city") or ""
    state = search_plan.get("state") or ""
    evidence_topics = search_plan.get("evidence_topics") or []
    lower_q = original_query.lower()

    # 1. Provider Discovery (NPPES)
    if specialty or city or "doctor" in lower_q or "dentist" in lower_q or "physician" in lower_q:
        q_text = (
            f"{specialty} in {city}, {state}".strip(" ,") if specialty or city else original_query
        )
        plan.add_query(
            PlannedQuery(
                query_id=f"q-nppes-{uuid.uuid4().hex[:6]}",
                parent_request_id=request_id,
                source="NPPES",
                query_text=q_text or "Healthcare provider registry search",
                search_params={"specialty": specialty, "city": city, "state": state, "limit": 5},
                intent_category="provider_discovery",
                priority=1,
            )
        )

    # 2. Clinical Research (PubMed)
    # Fan out into primary clinical topic + systematic reviews/interventions if research indicated
    primary_topic = " ".join(evidence_topics) if evidence_topics else original_query
    if "anxiety" in lower_q and ("pediatric" in lower_q or "child" in lower_q or "dent" in lower_q):
        plan.add_query(
            PlannedQuery(
                query_id=f"q-pubmed-{uuid.uuid4().hex[:6]}",
                parent_request_id=request_id,
                source="PubMed",
                query_text="pediatric dental anxiety management",
                search_params={"topic": "pediatric dental anxiety management", "limit": 5},
                intent_category="clinical_research",
                priority=1,
            )
        )
        plan.add_query(
            PlannedQuery(
                query_id=f"q-pubmed-{uuid.uuid4().hex[:6]}",
                parent_request_id=request_id,
                source="PubMed",
                query_text="dental anxiety interventions in children",
                search_params={"topic": "dental anxiety interventions in children", "limit": 5},
                intent_category="clinical_research",
                priority=2,
            )
        )
    elif evidence_topics:
        for topic in evidence_topics[:2]:
            plan.add_query(
                PlannedQuery(
                    query_id=f"q-pubmed-{uuid.uuid4().hex[:6]}",
                    parent_request_id=request_id,
                    source="PubMed",
                    query_text=topic,
                    search_params={"topic": topic, "limit": 5},
                    intent_category="clinical_research",
                    priority=1,
                )
            )
    else:
        plan.add_query(
            PlannedQuery(
                query_id=f"q-pubmed-{uuid.uuid4().hex[:6]}",
                parent_request_id=request_id,
                source="PubMed",
                query_text=primary_topic,
                search_params={"topic": primary_topic, "limit": 5},
                intent_category="clinical_research",
                priority=1,
            )
        )

    # 3. Patient Education (MedlinePlus)
    # Granular consumer health queries
    if "dental anxiety" in lower_q or ("anxiety" in lower_q and "dent" in lower_q):
        plan.add_query(
            PlannedQuery(
                query_id=f"q-medline-{uuid.uuid4().hex[:6]}",
                parent_request_id=request_id,
                source="MedlinePlus",
                query_text="child dental health",
                search_params={"keyword": "child dental health", "limit": 3},
                intent_category="patient_education",
                priority=1,
            )
        )
        plan.add_query(
            PlannedQuery(
                query_id=f"q-medline-{uuid.uuid4().hex[:6]}",
                parent_request_id=request_id,
                source="MedlinePlus",
                query_text="dental anxiety",
                search_params={"keyword": "dental anxiety", "limit": 3},
                intent_category="patient_education",
                priority=2,
            )
        )
    elif "cavity" in lower_q or "tooth decay" in lower_q or "caries" in lower_q:
        plan.add_query(
            PlannedQuery(
                query_id=f"q-medline-{uuid.uuid4().hex[:6]}",
                parent_request_id=request_id,
                source="MedlinePlus",
                query_text="tooth decay",
                search_params={"keyword": "tooth decay", "limit": 3},
                intent_category="patient_education",
                priority=1,
            )
        )
    elif "child" in lower_q and "dent" in lower_q:
        plan.add_query(
            PlannedQuery(
                query_id=f"q-medline-{uuid.uuid4().hex[:6]}",
                parent_request_id=request_id,
                source="MedlinePlus",
                query_text="child dental health",
                search_params={"keyword": "child dental health", "limit": 3},
                intent_category="patient_education",
                priority=1,
            )
        )
    else:
        # Use first extracted topic or clean query keywords
        edu_term = evidence_topics[0] if evidence_topics else (specialty or "health")
        plan.add_query(
            PlannedQuery(
                query_id=f"q-medline-{uuid.uuid4().hex[:6]}",
                parent_request_id=request_id,
                source="MedlinePlus",
                query_text=edu_term,
                search_params={"keyword": edu_term, "limit": 3},
                intent_category="patient_education",
                priority=2,
            )
        )

    # 4. CMS Quality Enrichment (Dependent Query)
    nppes_queries = [q for q in plan.queries if q.source == "NPPES"]
    dep_ids = [q.query_id for q in nppes_queries]
    plan.add_query(
        PlannedQuery(
            query_id=f"q-cms-{uuid.uuid4().hex[:6]}",
            parent_request_id=request_id,
            source="CMS",
            query_text=f"CMS Provider Quality Measures for {specialty or 'Discovered Clinicians'}",
            search_params={"specialty": specialty, "dependent_on": "candidate_npis"},
            intent_category="quality_metrics",
            priority=3,
            dependency_ids=dep_ids,
        )
    )

    return plan


def generate_fanout_plan(
    request_id: str,
    original_query: str,
    search_plan: SearchPlan,
    model_adapter: BaseModelAdapter | None = None,
    max_fanout: int = 8,
) -> FanOutPlan:
    """Generate query fan-out plan with LLM planning and robust deterministic fallback."""
    if model_adapter is not None:
        try:
            prompt = (
                f"Healthcare inquiry: {original_query}\n"
                f"Extracted parameters: {json.dumps(dict(search_plan))}\n"
                f"Decompose into targeted retrieval queries for NPPES, PubMed, MedlinePlus, "
                f"and CMS."
            )
            response = model_adapter.generate(
                prompt=prompt,
                system_instruction=FANOUT_SYSTEM_PROMPT,
                temperature=0.0,
            )
            parsed = extract_json(response.content)
            raw_queries = parsed.get("queries", [])
            if isinstance(raw_queries, list) and raw_queries:
                plan = FanOutPlan(
                    request_id=request_id,
                    original_query=original_query,
                    strategy_notes=str(
                        parsed.get("strategy_notes", "LLM-synthesized query fan-out.")
                    ),
                    max_fanout=max_fanout,
                )
                for q_dict in raw_queries:
                    if not isinstance(q_dict, dict):
                        continue
                    src = q_dict.get("source")
                    if src not in ("NPPES", "PubMed", "MedlinePlus", "CMS"):
                        continue
                    cat = q_dict.get("intent_category", "provider_discovery")
                    q_obj = PlannedQuery(
                        query_id=f"q-{src.lower()}-{uuid.uuid4().hex[:6]}",
                        parent_request_id=request_id,
                        source=src,
                        query_text=str(q_dict.get("query_text", "")).strip(),
                        search_params=q_dict.get("search_params", {}),
                        intent_category=cat,
                        priority=int(q_dict.get("priority", 2)),
                    )
                    plan.add_query(q_obj)

                if plan.queries:
                    return plan
        except Exception:
            pass  # Fall through to deterministic fanout

    return build_deterministic_fanout(
        request_id=request_id,
        original_query=original_query,
        search_plan=search_plan,
        max_fanout=max_fanout,
    )
