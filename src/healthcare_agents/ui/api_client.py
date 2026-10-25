"""HTTP client communicating with the Healthcare Agents FastAPI service."""

from __future__ import annotations

import logging
from typing import Literal

import httpx

from healthcare_agents.api.schemas import (
    HealthResponse,
    ReadinessResponse,
    SearchRequest,
    SearchResponse,
    SystemStatusResponse,
)

logger = logging.getLogger(__name__)


class HealthcareApiClient:
    """Synchronous / Async capable client for the Healthcare Agents backend API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_health(self) -> HealthResponse | None:
        """Call GET /health."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/health")
                if resp.status_code == 200:
                    return HealthResponse.model_validate(resp.json())
        except Exception as exc:
            logger.debug("API check_health failed: %s", exc)
        return None

    def check_readiness(self) -> ReadinessResponse | None:
        """Call GET /ready."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/ready")
                if resp.status_code == 200:
                    return ReadinessResponse.model_validate(resp.json())
        except Exception as exc:
            logger.debug("API check_readiness failed: %s", exc)
        return None

    def get_system_status(self) -> SystemStatusResponse | None:
        """Call GET /api/v1/status."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/api/v1/status")
                if resp.status_code == 200:
                    return SystemStatusResponse.model_validate(resp.json())
        except Exception as exc:
            logger.debug("API get_system_status failed: %s", exc)
        return None

    def search(
        self,
        query: str,
        retrieval_mode: str | None = None,
        result_limit: int = 10,
        request_id: str | None = None,
    ) -> SearchResponse:
        """Call POST /api/v1/search."""
        mode_val: Literal["fixtures", "live"] | None = (
            "fixtures"
            if retrieval_mode == "fixtures"
            else ("live" if retrieval_mode == "live" else None)
        )
        req_payload = SearchRequest(
            query=query,
            request_id=request_id,
            retrieval_mode=mode_val,
            result_limit=result_limit,
        )

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url}/api/v1/search",
                json=req_payload.model_dump(exclude_none=True),
            )
            resp.raise_for_status()
            return SearchResponse.model_validate(resp.json())
