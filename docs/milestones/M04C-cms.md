# Milestone M4C: CMS Provider Data Integration

> **Target Version:** `0.4.2` (`v0.4.2-m04c`)  
> **Status:** Released  
> **Date:** October 2026  

---

## Overview

Milestone M4C integrates authoritative clinician quality performance metrics and hospital quality star ratings from the official **CMS Provider Data Catalog** into the Open Healthcare Agentic Platform.

### Key Capabilities Delivered

1. **Official CMS Provider Data Client** (`src/healthcare_agents/retrieval/cms_client.py`):
   - Metastore discovery endpoint querying 237 published CMS datasets.
   - Structured datastore queries with conditions, pagination, and retry logic.
   - Support for Clinician MIPS scores (`a174-a962`), Hospital General Information & Star Ratings (`xubh-q36u`), and Facility Affiliations (`27ea-46a8`).
2. **Reliable Exact NPI Joining & Safe Isolation**:
   - Exact 10-digit NPI matching joins clinician records to candidate providers.
   - Unmatched records are kept isolated in `state["unmatched_cms_records"]` without geographic or name-based guesswork.
   - Facility star ratings are maintained at facility scope.
3. **Research Relevance Safeguards**:
   - Resolved M4B issue where PMID `39046104` (dementia study) was retrieved in pediatric dental queries due to author department affiliation.
   - Constructed bounded field queries using `[Title/Abstract]` and `[MeSH Terms]`.
   - Implemented deterministic post-fetch title and abstract relevance checks.
4. **Clinical Independence & Reporting Scope Guardrails**:
   - Validated that absence of CMS measures (standard in dentistry) indicates lack of public Medicare program reporting, not poor clinical quality.
   - Ensured general research articles are never cited as proof of an individual doctor's skills or outcomes.
5. **Quality Gates & Release**:
   - 82 passing offline tests, 91.48% coverage.
   - Opt-in live tests validating live CMS queries and end-to-end multi-agent LangGraph execution with Gemma 4.
