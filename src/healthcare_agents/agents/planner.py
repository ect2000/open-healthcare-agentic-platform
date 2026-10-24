"""Planner Agent: Interprets healthcare inquiries and produces structured search plans."""

from __future__ import annotations

import json
import re
from typing import Any

from healthcare_agents.models.base import BaseModelAdapter
from healthcare_agents.workflows.state import HealthcareWorkflowState, SearchPlan

PLANNER_SYSTEM_PROMPT = """You are a healthcare discovery planner.
Analyze the user's healthcare query and extract the search parameters.
Return ONLY a valid JSON object with the following fields:
- "specialty": string (medical or dental specialty, or empty string if not found)
- "city": string (city name, or empty string if not found)
- "state": string (two-letter state abbreviation if available, or full state name, or empty string)
- "evidence_topics": array of strings (relevant medical/health topics for clinical evidence review)
- "intent_description": string (short summary of the user's intent)

Do not include any explanation or extra text outside the JSON object.
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


def plan_query(
    state: HealthcareWorkflowState,
    model_adapter: BaseModelAdapter | None = None,
) -> dict[str, Any]:
    """Execute the planner step on the current workflow state."""
    query = state.get("original_query", "")
    metadata = dict(state.get("execution_metadata", {}))
    errors = list(state.get("errors", []))

    plan: SearchPlan = {
        "specialty": "",
        "city": "",
        "state": "",
        "evidence_topics": [],
        "intent_description": f"Healthcare inquiry: {query}",
    }

    if model_adapter is not None:
        try:
            response = model_adapter.generate(
                prompt=f"Healthcare query: {query}",
                system_instruction=PLANNER_SYSTEM_PROMPT,
                temperature=0.0,
            )
            parsed = extract_json(response.content)
            if parsed:
                plan["specialty"] = str(parsed.get("specialty", "")).strip()
                plan["city"] = str(parsed.get("city", "")).strip()
                plan["state"] = str(parsed.get("state", "")).strip()
                raw_topics = parsed.get("evidence_topics", [])
                if isinstance(raw_topics, list):
                    plan["evidence_topics"] = [str(t) for t in raw_topics if str(t).strip()]
                plan["intent_description"] = str(
                    parsed.get("intent_description", plan["intent_description"])
                )
                metadata["planner_tokens"] = response.usage.total_tokens if response.usage else None
        except Exception as err:
            errors.append(f"Planner model invocation warning: {err}")

    # Deterministic fallback heuristics if model extraction was empty or model absent
    lower_q = query.lower()
    if not plan["specialty"]:
        if "pediatric dentist" in lower_q or "pediatric dentistry" in lower_q:
            plan["specialty"] = "Pediatric Dentistry"
        elif "dentist" in lower_q:
            plan["specialty"] = "Dentistry"
        elif "cardio" in lower_q or "heart" in lower_q:
            plan["specialty"] = "Cardiology"
        elif "pediatric" in lower_q or "children" in lower_q:
            plan["specialty"] = "Pediatrics"

    if not plan["city"]:
        if "houston" in lower_q:
            plan["city"] = "Houston"
            plan["state"] = plan["state"] or "TX"
        elif "austin" in lower_q:
            plan["city"] = "Austin"
            plan["state"] = plan["state"] or "TX"

    if not plan["evidence_topics"]:
        if plan["specialty"]:
            plan["evidence_topics"].append(plan["specialty"])
        plan["evidence_topics"].append(query)

    metadata["planner_completed"] = True
    return {
        "search_plan": plan,
        "execution_metadata": metadata,
        "errors": errors,
    }
