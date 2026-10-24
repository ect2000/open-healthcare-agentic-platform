# Milestone M4E Implementation: Unified Evidence Normalization, Ranking, Deduplication & Provenance

## Architectural Overview

Milestone M4E introduces a unified evidence-processing layer spanning all four live public healthcare data sources:
1. **CMS NPPES Provider Registry API v2.1** (Provider credentials and practice locations)
2. **NCBI PubMed E-Utilities** (Biomedical research studies, PMIDs, abstracts)
3. **CMS Provider Data Catalog** (Hospital & facility quality metrics, isolated from individual clinicians)
4. **NLM MedlinePlus Web Services & Connect API** (Authoritative patient literacy education)

Instead of flattening heterogeneous healthcare entities into interchangeable rows, M4E maintains strong typed distinctions and preserves raw source dataclass instances while introducing structured wrappers for deduplication, relevance scoring, ranking, provenance auditing, and deterministic validation.

```
+---------------------------------------------------------------------------------------------------+
|                                  Milestone M4E Pipeline Architecture                               |
+---------------------------------------------------------------------------------------------------+
|  1. Planner Agent (Gemma 4)                                                                       |
|     Extracts specialty, location (city/state), PubMed clinical queries, and education topics       |
|                                                                                                   |
|  2. Four-Source Retrieval                                                                         |
|     • NPPES Provider Registry Client (NPI-level provider discovery)                                |
|     • PubMed NCBI E-Utilities (Topical biomedical literature)                                     |
|     • CMS Provider Data Catalog (Facility/clinician quality datasets)                             |
|     • MedlinePlus XML Web Service & Connect API (Patient health topics)                           |
|                                                                                                   |
|  3. Unified Evidence Layer (`healthcare_agents.evidence`)                                         |
|     • Normalization: Builds `UnifiedEvidenceItem` preserving `original_provider`/`original_record` |
|     • Deterministic Deduplication:                                                                |
|         - NPPES: Exact 10-digit NPI + location key                                                |
|         - PubMed: Exact numeric PMID + canonical DOI                                              |
|         - CMS: `dataset_id:entity_type:external_id:reporting_period`                              |
|         - MedlinePlus: Canonical official URL + topic ID + language (EN vs ES preserved)          |
|     • Explainable Relevance & Ranking:                                                            |
|         - Provider: Specialty exact/partial match + location proximity + record completeness       |
|         - PubMed: Intent-topic token overlap + explicit rejection of unrelated dementia studies   |
|         - MedlinePlus: Consumer literacy alignment + English/Spanish isolation                    |
|         - CMS: Metric reporting period + facility boundary isolation                              |
|         - NO fake universal clinician quality scores; explainable per-source ranks only           |
|     • Source Provenance: Verified domains (`nih.gov`, `cms.gov`, `hhs.gov`), cross-boundary guard |
|                                                                                                   |
|  4. Deterministic Validator                                                                       |
|     Verifies NPI Luhn/format, uniqueness, provenance authenticity, and citation boundaries         |
|                                                                                                   |
|  5. Answer Agent (Gemma 4)                                                                        |
|     Generates grounded narrative citing only validated items, produces `StructuredDiscoveryResult`|
+---------------------------------------------------------------------------------------------------+
```

## Key Files Created and Modified

### Created Modules
- `src/healthcare_agents/evidence/schemas.py`: Typed schemas (`EvidenceSourceType`, `EvidenceStatus`, `ProvenanceRecord`, `RelevanceAssessment`, `UnifiedEvidenceItem`, `StructuredDiscoveryResult`).
- `src/healthcare_agents/evidence/normalization.py`: Normalizers for NPPES providers, PubMed clinical literature, MedlinePlus patient education topics, and CMS quality records.
- `src/healthcare_agents/evidence/deduplication.py`: Deterministic deduplication functions for each source preventing collision and entity contamination.
- `src/healthcare_agents/evidence/relevance.py`: Explainable relevance filters; contains the explicit regression rule rejecting unrelated biomedical studies (such as PMID `39046104` vascular dementia GWAS) from dental anxiety contexts.
- `src/healthcare_agents/evidence/ranking.py`: Explainable source-specific ranking routines based on verified metadata, match completeness, and publication recency without uncalibrated universal scores.
- `src/healthcare_agents/evidence/provenance.py`: Provenance audit ledger, official URL domain validator, citation integrity checker, and cross-boundary claim validation.
- `src/healthcare_agents/evidence/__init__.py`: Public package exports.
- `src/healthcare_agents/agents/evidence_processor.py`: LangGraph node coordinating normalization, deduplication, relevance scoring, and ranking.
- `tests/test_evidence_pipeline.py`: Comprehensive test suite containing 18 unit and adversarial tests.
- `docs/images/m4e_workflow.svg`: Scalable vector architecture diagram matching the visual design of M4A.
- `docs/images/m4e_workflow.png`: High-resolution PNG diagram rendered via headless Chrome.
- `docs/milestones/M04E-unified-evidence.md`: Standalone milestone report.

### Modified Modules
- `src/healthcare_agents/workflows/state.py`: Added `unified_evidence`, `excluded_evidence`, `provenance_records`, and `structured_discovery_result` to workflow state.
- `src/healthcare_agents/workflows/healthcare_graph.py`: Wired `evidence_processor` node between retrieval stages and `validator`.
- `src/healthcare_agents/agents/validator.py`: Integrated `verify_citation_integrity` into deterministic validation rules.
- `src/healthcare_agents/agents/answer.py`: Cites structured evidence and generates `StructuredDiscoveryResult`.
- `src/healthcare_agents/cli.py`: Verbose mode reports normalization counts, deduplication stats, exclusion reasons, and provenance records.
- `pyproject.toml`, `src/healthcare_agents/__init__.py`, `tests/test_cli.py`, `tests/test_package.py`: Bumped version to `0.4.4`.

## Exact Deduplication Keys

| Source | Primary Deduplication Key | Secondary / Collision Safeguard | Notes |
| :--- | :--- | :--- | :--- |
| **NPPES** | `record.npi` (10-digit NPI string) | Practice street address & ZIP5 | Never merges distinct clinicians |
| **PubMed** | `record.pmid` (numeric string) | `record.doi` (lowercase trimmed) | Preserves distinct clinical studies |
| **CMS** | `dataset_id:entity_type:external_id` | `reporting_period:measure_id` | Facility metrics remain isolated |
| **MedlinePlus** | `canonical_url` (trimmed, lowercase) | `record.language:topic_id` | Preserves distinct EN and ES topics |

## Boundary Enforcement & Anti-Hallucination Rules

1. **NPPES Administrative Boundary**: An NPI is purely an administrative identifier. It does not certify competence, quality, malpractice history, or active board certification.
2. **PubMed Credential Boundary**: Peer-reviewed biomedical literature establishes general clinical science; it does not attest to an individual doctor's skills or practice.
3. **CMS Facility Boundary**: Hospital and institutional quality scores (HCAHPS, readmissions) apply strictly to organizations and cannot be ascribed to individual outpatient clinicians or dentists.
4. **MedlinePlus Consumer Literacy Boundary**: MedlinePlus provides general consumer health literacy and is not primary research or clinical guidance.
