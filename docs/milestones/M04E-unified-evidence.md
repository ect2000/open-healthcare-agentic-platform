# Milestone M4E: Unified Evidence Normalization, Ranking, Deduplication & Provenance

> **Target Release Tag:** `v0.4.4-m04e`  
> **Branch:** `main`  
> **Status:** Verified & Released  

---

## Executive Summary

Milestone M4E completes the evidence-processing foundation of the **Open Healthcare Agentic Platform** by introducing a unified, typed normalization, deduplication, explainable relevance/ranking, and provenance layer over all four live public healthcare data sources:

1. **CMS NPPES Registry API v2.1** — Live clinician NPI, taxonomy, and practice location discovery.
2. **NCBI PubMed E-Utilities** — Live biomedical research literature and scientific evidence.
3. **CMS Provider Data Catalog** — Official hospital and facility quality metrics.
4. **NLM MedlinePlus Web Services & Connect API** — Authoritative patient health education.

Prior to M4E, retrieved records were handled through ad-hoc agent state structures. M4E establishes deterministic pipelines that normalize records without semantic flattening, deduplicate strictly on authoritative external keys, enforce explainable source-specific relevance (including regression guards against unrelated research), and verify provenance domains and citation boundaries.

---

## Architecture

![M4E Unified Evidence Workflow](../images/m4e_workflow.png)

### Key Architectural Tenets

1. **Preservation of Distinct Record Types**:
   A hospital quality metric, a registered clinician, a peer-reviewed PubMed paper, and a MedlinePlus consumer topic are fundamentally different entities. M4E wraps each record in a `UnifiedEvidenceItem` while preserving the full typed underlying object (`original_provider`, `original_record`, `original_cms`).

2. **Deterministic Deduplication**:
   - **NPPES**: Exact 10-digit NPI + location string.
   - **PubMed**: Exact numeric PMID + lowercase DOI.
   - **CMS**: `dataset_id:entity_type:external_id:reporting_period`.
   - **MedlinePlus**: Canonical official URL + topic ID + language (EN vs ES).

3. **Explainable Ranking without Invented Quality Scores**:
   Healthcare AI must not invent arbitrary 1-to-5 star ratings or clinician quality scores from administrative registry data. Provider discovery ranks purely on verified specialty alignment, location matching, and profile completeness.

4. **Biomedical Relevance Guard**:
   PubMed queries for pediatric dental anxiety explicitly reject unrelated clinical studies (such as PMID `39046104`, a genome-wide association study on vascular dementia).

5. **Source Provenance & Boundary Enforcement**:
   All citations are validated against authorized federal domains (`nih.gov`, `cms.gov`, `hhs.gov`). Claims cannot cross evidence boundaries:
   - An NPI does not attest to clinical quality or competence.
   - PubMed papers do not attest to an individual doctor's skills.
   - CMS hospital metrics do not apply to individual outpatient dentists.
   - MedlinePlus is for consumer literacy, not primary medical diagnosis.

---

## Deliverables & Modules

- `src/healthcare_agents/evidence/`:
  - `schemas.py`: `UnifiedEvidenceItem`, `ProvenanceRecord`, `RelevanceAssessment`, `StructuredDiscoveryResult`.
  - `normalization.py`: Source-specific normalizers.
  - `deduplication.py`: Deterministic entity deduplicators.
  - `relevance.py`: Explainable scoring and topical rejection guards.
  - `ranking.py`: Explainable source-specific rankers.
  - `provenance.py`: Provenance registry, domain validation, and citation integrity checks.
- `src/healthcare_agents/agents/evidence_processor.py`: LangGraph workflow node.
- `tests/test_evidence_pipeline.py`: Comprehensive test suite with 18 tests.
- `docs/images/m4e_workflow.svg` & `docs/images/m4e_workflow.png`: Architecture diagram.

---

## Quality Gate Summary

- **Unit & Integration Tests**: 114 passed, 15 skipped (live opt-in), 0 failed.
- **Code Coverage**: 91.68% (exceeds $\ge 90.0\%$ threshold).
- **Linter (Ruff)**: 0 errors.
- **Formatter (Ruff)**: 0 errors (92 files formatted).
- **Type Checker (Mypy)**: 0 issues across 51 source files.
- **Wheel Build & Clean Install**: Verified in clean virtual environment.
- **Live Search Verification**: Verified against live NPPES, PubMed, CMS, and MedlinePlus APIs.
