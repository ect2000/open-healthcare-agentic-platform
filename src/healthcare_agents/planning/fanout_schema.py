"""Structured query fan-out schemas and models for multi-source healthcare retrieval."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field

IntentCategory = Literal[
    "provider_discovery",
    "clinical_research",
    "patient_education",
    "quality_metrics",
]

QueryStatus = Literal[
    "planned",
    "dispatched",
    "completed",
    "skipped",
    "failed",
]

HealthcareSource = Literal["NPPES", "PubMed", "MedlinePlus", "CMS"]


class PlannedQuery(BaseModel):
    """Structured search query targeted to an authoritative healthcare data source."""

    query_id: str
    parent_request_id: str
    source: HealthcareSource
    query_text: str
    search_params: dict[str, Any] = Field(default_factory=dict)
    intent_category: IntentCategory
    priority: int = 2  # 1: High, 2: Normal, 3: Optional/Enrichment
    status: QueryStatus = "planned"
    result_count: int = 0
    duration_ms: float = 0.0
    error_message: str | None = None
    dependency_ids: list[str] = Field(default_factory=list)

    def validate_parameters(self) -> bool:
        """Validate source-specific search parameters to prevent malformed API calls."""
        if self.source == "NPPES":
            # Must have either specialty, first/last name, city, or postal code
            has_spec = bool(self.search_params.get("specialty"))
            has_loc = bool(self.search_params.get("city") or self.search_params.get("state"))
            has_name = bool(
                self.search_params.get("first_name") or self.search_params.get("last_name")
            )
            return bool(has_spec or has_loc or has_name or self.query_text.strip())

        if self.source == "PubMed":
            # Must have non-empty search terms and no PHI patterns
            clean_text = self.query_text.strip()
            return len(clean_text) >= 2 and not bool(
                re.search(r"\b\d{3}-\d{2}-\d{4}\b", clean_text)
            )

        if self.source == "MedlinePlus":
            clean_text = self.query_text.strip()
            return len(clean_text) >= 2

        if self.source == "CMS":
            # CMS lookups require provider identifiers (e.g., NPIs) or facility names
            npis = self.search_params.get("npis", [])
            return bool(npis or self.search_params.get("entity_name") or self.query_text.strip())

        return True


class FanOutPlan(BaseModel):
    """Collection of planned queries decomposed from a single healthcare inquiry."""

    request_id: str
    original_query: str
    queries: list[PlannedQuery] = Field(default_factory=list)
    strategy_notes: str = ""
    max_fanout: int = 8

    def add_query(self, query: PlannedQuery) -> bool:
        """Add a query if within max_fanout and not semantically duplicate."""
        if len(self.queries) >= self.max_fanout:
            return False

        # Semantic deduplication check
        norm_text = query.query_text.lower().strip()
        for existing in self.queries:
            if existing.source == query.source and existing.query_text.lower().strip() == norm_text:
                return False

        if query.validate_parameters():
            self.queries.append(query)
            return True
        return False
