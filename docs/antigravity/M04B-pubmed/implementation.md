# Milestone M04B: Implementation Details

## 1. Overview & Objectives

Milestone M04B implements real, public biomedical research retrieval from NCBI PubMed using official NCBI Entrez E-utilities. It connects biomedical research to the existing LangGraph multi-agent orchestration architecture alongside live CMS NPPES provider discovery from M4A.

---

## 2. Package Architecture & Changes

### A. New Modules
- `src/healthcare_agents/retrieval/pubmed_client.py`:
  - `PubMedEvidenceRetriever`: Implements `BaseEvidenceRetriever`.
  - `_esearch`: Discovers article identifiers (PMIDs) matching clinical query terms.
  - `_efetch`: Retrieves structured article metadata, authors, abstracts, DOIs, and canonical links.
  - Rate limiting: 0.35s delay for standard usage (respecting NCBI 3 requests/second policy) and 0.11s when `NCBI_API_KEY` is present.
  - Bounded exponential backoff retries for transient HTTP errors (429, 500, 502, 503, 504) and timeouts.
  - Masks `api_key` in all log messages.

### B. Normalized Research Schema (`src/healthcare_agents/retrieval/base.py`)
- Extended `ClinicalEvidenceRecord` dataclass:
  - `pmid`: str (e.g. `"39342194"`)
  - `authors`: tuple[str, ...] (e.g. `("Kong Xiang", "Song Nan")`)
  - `journal`: str (e.g. `"BMC oral health"`)
  - `doi`: str (e.g. `"10.1186/s12903-024-04919-x"`)
  - `pubmed_url`: str (e.g. `"https://pubmed.ncbi.nlm.nih.gov/39342194/"`)
  - `retrieval_timestamp`: ISO 8601 UTC timestamp
  - `source_type`: `"PubMed"`
  - `evidence_status`: `"available"`, `"no_abstract"`, `"empty_results"`, or `"error"`

### C. M4A Provider Data Quality Corrections (`src/healthcare_agents/retrieval/nppes_client.py`)
- **Practice Address Location Validation**: Evaluates normalized practice address (`address_purpose == "LOCATION"`) against the requested city and state. Candidates with mailing addresses in the requested city but actual physical practices outside the jurisdiction (e.g., Columbus, OH) are excluded.
- **Taxonomy Validation**: Evaluates primary and secondary taxonomies to ensure the clinician or facility matches the requested specialty tokens (e.g., pediatric dentistry).

### D. LangGraph Evidence Agent (`src/healthcare_agents/agents/evidence.py`)
- Resolves default evidence retriever to `PubMedEvidenceRetriever` in live mode and `FixtureEvidenceRetriever` in fixture mode.
- Queries PubMed for clinical evidence while continuing to surface simulated demonstration fixtures for MedlinePlus patient education (to be transitioned in M4D).

### E. Deterministic Validator (`src/healthcare_agents/agents/validator.py`)
- Verifies numeric PMID format.
- Verifies HTTPS format for PubMed URLs (`https://pubmed.ncbi.nlm.nih.gov/<PMID>/`).
- Detects duplicate articles.
- Injects Literature Independence Guardrail: general biomedical publications establish scientific literature context only and must never be asserted as direct qualifications or outcomes for individual practitioners.

### F. Gemma 4 Answer Synthesis & CLI (`src/healthcare_agents/agents/answer.py`, `src/healthcare_agents/cli.py`)
- Formats live PubMed literature with titles, publication years, authors, abstracts, PMIDs, and URLs.
- Clear disclaimers stating that provider records are live from CMS NPPES, research is live from NCBI PubMed, and patient education remains simulated fixtures for M4B.
