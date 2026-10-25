"""FastAPI application factory for the Open Healthcare Agentic Platform."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from healthcare_agents import __version__
from healthcare_agents.api.routes import router as api_router
from healthcare_agents.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    settings = get_settings()
    logger.info(
        "Starting Healthcare Agents API v%s (env=%s, retrieval_mode=%s)",
        __version__,
        settings.environment,
        settings.retrieval_mode,
    )
    yield
    logger.info("Shutting down Healthcare Agents API.")
    from healthcare_agents.observability import shutdown_metrics, shutdown_tracing

    shutdown_tracing()
    shutdown_metrics()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="Open Healthcare Agentic Platform API",
        description=(
            "Vendor-neutral, open-source, evidence-grounded healthcare search "
            "and agentic AI platform. Coordinates multi-agent retrieval over "
            "CMS NPPES, NCBI PubMed, CMS Provider Data, and NLM MedlinePlus."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    from healthcare_agents.observability import instrument_fastapi

    instrument_fastapi(app)

    return app


app = create_app()
