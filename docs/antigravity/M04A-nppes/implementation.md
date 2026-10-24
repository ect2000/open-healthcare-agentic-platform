# Milestone M04A: Implementation Details

## 1. Architectural Overview & Objectives

Milestone M04A replaces synthetic provider retrieval within the LangGraph Provider Agent with **real, live provider discovery** using the public Centers for Medicare & Medicaid Services (CMS) **NPPES NPI Registry API version 2.1**.

### Core Governance & Verification Principles:
- **No API Key Required**: NPPES API v2.1 is an open public federal service.
- **Strict Data Grounding**: Never invent ratings, patient reviews, accepted insurance networks, state licensing status, or board certifications.
- **Administrative Scope Boundary**: An NPI is purely an administrative standard identifier established by HIPAA; it is **NOT** proof of state medical licensure, clinical competence, credentialing status, or service quality.
- **Configurable Mode**: `RETRIEVAL_MODE=live` (default) vs `RETRIEVAL_MODE=fixture` for deterministic offline testing.
- **No Silent Fallback**: If live NPPES fails, the platform records a provider retrieval error rather than silently substituting synthetic providers.

---

## 2. Package & Module Architecture

### New and Updated Modules
```
src/healthcare_agents/
    config.py                     # Added RETRIEVAL_MODE, NPPES_API_URL, NPPES_TIMEOUT_SECONDS, NPPES_MAX_RETRIES
    retrieval/
        base.py                   # Extended ProviderRecord with entity_type, taxonomy_code, addresses, telephone
        nppes_client.py           # Real HTTP NPPES client with bounded retries, backoff, and typed normalization
        fixtures.py               # Maintained synthetic fixtures for offline testing
    agents/
        provider.py               # Updated to support live NPPES retriever and record citations & errors
        validator.py              # Added 10-digit NPI numeric format check and provenance validation
        answer.py                 # Grounded synthesis distinguishing live vs simulated records
    workflows/
        healthcare_graph.py       # Configurable default retriever resolver based on RETRIEVAL_MODE
    cli.py                        # Enhanced search CLI displaying live provider records, practice address, phone
```

---

## 3. NPPES API Client Implementation (`retrieval/nppes_client.py`)

- **Target Endpoint**: `https://npiregistry.cms.hhs.gov/api/?version=2.1`
- **Supported Query Criteria**:
  - Direct 10-digit NPI lookup (`number=...`)
  - Specialty / taxonomy search (`taxonomy_description=...`)
  - Geographic filtering (`city=...`, `state=...`)
  - Bounded pagination limits (`limit=...`, capped at 100 per CMS limits)
- **Robust Network Protocol**:
  - Configurable timeouts (`NPPES_TIMEOUT_SECONDS`, default 10.0s).
  - Bounded exponential backoff retries (`NPPES_MAX_RETRIES`, default 2).
  - Explicit error hierarchy: `NPPESClientError`, `NPPESConnectionError`, `NPPESResponseError`.
- **Normalization Layer**:
  - Differentiates **Individual (NPI-1)** and **Organization (NPI-2)** enumeration types.
  - Normalizes practice location (`address_purpose == "LOCATION"`) separately from mailing address (`address_purpose == "MAILING"`).
  - Extracts primary healthcare taxonomy description and code.
  - Captures telephone number and ISO-8601 UTC retrieval timestamps.

---

## 4. LangGraph Multi-Agent Flow & State Transitions

1. **User Query**: Natural language input (e.g. `"Find pediatric dentists in Houston"`).
2. **Planner Agent**: Gemma 4 extracts structured JSON plan (`specialty="Pediatric Dentistry"`, `city="Houston"`, `state="TX"`).
3. **Provider Agent**: Queries live CMS NPPES API v2.1 via `NPPESProviderRetriever`, normalizing 5 real practitioner records.
4. **Evidence Agent**: Queries biomedical research and patient education (retaining simulated fixtures for M4A).
5. **Deterministic Validator**: Validates 10-digit NPI formats, source provenance, and removes duplicate records.
6. **Answer Synthesis Agent**: Synthesizes a grounded clinical discovery summary strictly referencing retrieved records with full source citations.

---

## 5. Non-Clinical Disclaimer
An NPI (National Provider Identifier) is an administrative identifier issued by the Centers for Medicare & Medicaid Services. It does not establish clinical competency, credentialing, state medical board standing, or quality ratings.
