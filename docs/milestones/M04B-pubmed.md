# Milestone M4B: Live PubMed Biomedical Research Literature Discovery

> **Tag:** `v0.4.1-m04b`  
> **Target Branch:** `main`  
> **Status:** Complete & Verified  

---

## 1. Overview & Objectives

Milestone M4B integrates real, public biomedical research literature from **NCBI PubMed** into the LangGraph multi-agent discovery workflow using official NCBI Entrez E-utilities (ESearch and EFetch).

Building upon the live CMS NPPES provider registry integration from M4A:
- **Planner Agent** generates structured biomedical search topics alongside provider criteria.
- **Provider Agent** retrieves real healthcare clinicians from CMS NPPES API v2.1 with strict practice location matching and relevant provider taxonomy filtering.
- **Evidence Agent** queries NCBI ESearch for relevant PubMed IDs and EFetch for structured XML article metadata, authors, abstracts, DOIs, and official publication links.
- **Validator** deterministically validates 10-digit NPIs, practice locations, numeric PMIDs, PubMed URLs, duplicate articles, and enforces the scientific independence guardrail.
- **Answer Agent** synthesizes grounded summaries with local Gemma 4 (`gemma4:e2b`), citing real NPI numbers and valid PMIDs.
- **Patient Education (MedlinePlus)** remains clearly labeled demonstration fixtures.

---

## 2. Implemented Capabilities

### A. Official NCBI E-utilities Client (`src/healthcare_agents/retrieval/pubmed_client.py`)
- **ESearch Integration**: JSON-based discovery querying `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` by relevance.
- **EFetch Integration**: XML-based metadata retrieval from `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi`, extracting article titles, journals, publication years, author rosters, abstracts, DOIs, and canonical URLs (`https://pubmed.ncbi.nlm.nih.gov/<PMID>/`).
- **Rate-Limit Awareness**: Enforces a minimum interval between requests (0.35s for unauthenticated requests respecting the 3 req/s policy; 0.11s when `NCBI_API_KEY` is supplied).
- **Exponential Backoff**: Bounded retry mechanism on HTTP 429, 500, 502, 503, 504, or network timeouts.
- **Security**: Masks `api_key` values from logs; never outputs credentials in stdout or stderr.

### B. M4A Data Quality Correction (Practice Address & Taxonomy Matching)
- **Practice Location Filter**: Explicitly validates requested city and state against normalized `LOCATION` addresses, excluding providers whose practice address is outside the queried jurisdiction.
- **Taxonomy Validation**: Evaluates provider taxonomy codes and descriptions against requested specialty tokens, filtering out unrelated specialties.

### C. Deterministic Validation & Clinical Guardrails (`src/healthcare_agents/agents/validator.py`)
- Validates numeric PMID structure and canonical PubMed HTTPS URLs.
- Deduplicates article records.
- **Literature Independence Guardrail**: Flags that biomedical research articles establish literature context only and must never be asserted as direct evidence of an individual clinician's qualifications, experience, or quality.

---

## 3. Verification & Quality Gates

- **Ruff Linting**: All checks passed across all source files.
- **Ruff Formatting**: 62 files formatted and verified.
- **Mypy Static Typing**: Strict type checks passed (`Success: no issues found in 36 source files`).
- **Test Suite**: 72 offline unit tests passing; 81 total passing including opt-in live tests.
- **Code Coverage**: **93.07%** offline coverage (exceeds required 90.0% threshold).
