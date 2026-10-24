"""Retrieval package exposing provider and evidence search abstractions."""

from healthcare_agents.retrieval.base import (
    BaseEvidenceRetriever,
    BaseProviderRetriever,
    ClinicalEvidenceRecord,
    ProviderRecord,
)
from healthcare_agents.retrieval.fixtures import (
    SYNTHETIC_EVIDENCE,
    SYNTHETIC_PROVIDERS,
    FixtureEvidenceRetriever,
    FixtureProviderRetriever,
)
from healthcare_agents.retrieval.nppes_client import (
    NPPESClientError,
    NPPESConnectionError,
    NPPESProviderRetriever,
    NPPESResponseError,
)
from healthcare_agents.retrieval.pubmed_client import (
    PubMedClientError,
    PubMedConnectionError,
    PubMedEvidenceRetriever,
    PubMedResponseError,
)

__all__ = [
    "SYNTHETIC_EVIDENCE",
    "SYNTHETIC_PROVIDERS",
    "BaseEvidenceRetriever",
    "BaseProviderRetriever",
    "ClinicalEvidenceRecord",
    "FixtureEvidenceRetriever",
    "FixtureProviderRetriever",
    "NPPESClientError",
    "NPPESConnectionError",
    "NPPESProviderRetriever",
    "NPPESResponseError",
    "ProviderRecord",
    "PubMedClientError",
    "PubMedConnectionError",
    "PubMedEvidenceRetriever",
    "PubMedResponseError",
]
