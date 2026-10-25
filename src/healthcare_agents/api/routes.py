"""FastAPI HTTP routes for health, readiness, status, and multi-agent discovery."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from healthcare_agents.api.schemas import (
    HealthResponse,
    ReadinessResponse,
    SearchRequest,
    SearchResponse,
    SystemStatusResponse,
)
from healthcare_agents.api.service import HealthcareSearchService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_search_service() -> HealthcareSearchService:
    """Dependency provider for search service."""
    return HealthcareSearchService()


@router.get("/health", response_model=HealthResponse, tags=["Operations"])
def health_check(
    service: Annotated[HealthcareSearchService, Depends(get_search_service)],
) -> HealthResponse:
    """Basic liveness probe checking FastAPI service process health."""
    return service.get_health()


@router.get("/ready", response_model=ReadinessResponse, tags=["Operations"])
def readiness_check(
    service: Annotated[HealthcareSearchService, Depends(get_search_service)],
) -> ReadinessResponse:
    """Readiness probe checking availability of local Ollama runtime and data configurations."""
    res = service.get_readiness()
    if not res.ready:
        logger.info(
            "Readiness probe indicates degraded status: model_installed=%s",
            res.model_installed,
        )
    return res


@router.get("/api/v1/status", response_model=SystemStatusResponse, tags=["System"])
def system_status(
    service: Annotated[HealthcareSearchService, Depends(get_search_service)],
) -> SystemStatusResponse:
    """System information, supported public sources, and clinical/administrative disclaimers."""
    return service.get_system_status()


@router.post(
    "/api/v1/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    tags=["Discovery"],
    summary="Multi-source evidence-grounded healthcare discovery",
)
def search_healthcare(
    request: SearchRequest,
    service: Annotated[HealthcareSearchService, Depends(get_search_service)],
) -> SearchResponse:
    """Execute LangGraph multi-agent discovery across NPPES, PubMed, CMS, and MedlinePlus."""
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query must not be empty.",
        )
    try:
        return service.execute_search(request)
    except TimeoutError as exc:
        logger.error("Workflow execution timed out: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Healthcare workflow execution timed out: {exc}",
        ) from exc
    except Exception as exc:
        logger.error("Unhandled search execution error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during multi-agent execution: {exc}",
        ) from exc
