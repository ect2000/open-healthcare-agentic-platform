# Milestone M4D Implementation Record: Live MedlinePlus Patient Education

## 1. Overview & Architectural Goals

Milestone M4D connects the open healthcare agentic platform to the official, authoritative consumer health Web Service operated by the U.S. National Library of Medicine (NLM): **MedlinePlus**.

Prior to M4D, patient education records were simulated using synthetic demonstration fixtures (`MedlinePlus-Demo-Fixture`). In M4D, the platform coordinates all **four** major live public healthcare evidence categories simultaneously:
1. **CMS NPPES Registry v2.1**: Live clinician credentials, taxonomies, and practice addresses.
2. **NCBI Entrez PubMed E-utilities**: Live biomedical literature, systematic reviews, and clinical trials.
3. **CMS Provider Data Catalog**: Live clinician MIPS quality scores and hospital star ratings.
4. **NLM MedlinePlus Web Service & Connect**: Live, patient-friendly health topics, authoritative summaries, official URLs, and standardized code-based consumer education.

---

## 2. Official MedlinePlus Service Architecture

MedlinePlus provides two primary APIs:
1. **MedlinePlus Web Service (Keyword-Based)**:
   - Endpoint: `https://wsearch.nlm.nih.gov/ws/query`
   - Data Format: XML (no JSON endpoint exists for keyword search)
   - Databases:
     - `db=healthTopics`: English health topics
     - `db=healthTopicsSpanish`: Spanish health topics
   - Key Document Fields:
     - `url`: Official topic URL (e.g., `https://medlineplus.gov/childdentalhealth.html`)
     - `title`: Health topic title with embedded highlight markup (e.g., `<span class="qt0">...</span>`)
     - `FullSummary` or `snippet`: Plain-language medical overview for consumers.
2. **MedlinePlus Connect (Code-Based)**:
   - Endpoint: `https://connect.medlineplus.gov/service`
   - Data Format: JSON (`knowledgeResponseType=application/json`) or XML
   - Standard Code Systems: ICD-10-CM (`2.16.840.1.113883.6.90`), SNOMED CT, RxCUI, LOINC.
   - Purpose: Direct EHR / clinical code lookups without free-text keyword ambiguity.

---

## 3. Acceptable Use Policy & Client Protection

The U.S. NLM acceptable use policy stipulates:
- **Maximum 85 requests per minute per IP address** (~0.71 seconds between requests).
- Clients exceeding this rate are blocked or throttled by NLM servers.

### Client-Side Throttling & Thread-Safe Caching
In `src/healthcare_agents/retrieval/medlineplus_client.py`:
- `MIN_REQUEST_INTERVAL_SECONDS = 0.72`: Imposes an atomic, thread-safe sleep interval ensuring requests never exceed 83.3 req/min.
- Thread-safe TTL cache: In-memory cache keyed by database and query (e.g., `healthTopics:child dental health`) with a default TTL of 12 hours (43,200 seconds) configurable via `MEDLINEPLUS_CACHE_TTL_SECONDS`.
- Cache Isolation: Caches only public, non-personalized educational health topic records; never stores PHI, user identifiers, or private queries.
- Bounded Exponential Backoff: Retries on 429/5xx status codes up to 3 times with exponential backoff ($0.75 \times 2^{\text{attempt}}$ seconds).

---

## 4. Key Files Created and Modified

| File | Status | Description |
|:---|:---|:---|
| `src/healthcare_agents/retrieval/medlineplus_client.py` | Created | Official client for MedlinePlus XML Web Service and Connect JSON endpoint with rate limiting, caching, HTML unescaping, and typed record extraction. |
| `src/healthcare_agents/retrieval/base.py` | Modified | Added `official_url`, `topic_id`, and `language` to `ClinicalEvidenceRecord`; created `BasePatientEducationRetriever` abstract interface. |
| `src/healthcare_agents/retrieval/fixtures.py` | Modified | Created `FixturePatientEducationRetriever` providing deterministic offline test fixtures. |
| `src/healthcare_agents/retrieval/__init__.py` | Modified | Exported `MedlinePlusPatientEducationRetriever`, `MedlinePlusClientError`, `MedlinePlusConnectionError`, `MedlinePlusResponseError`, and `FixturePatientEducationRetriever`. |
| `src/healthcare_agents/config.py` | Modified | Added settings for MedlinePlus URL, Connect URL, timeouts, cache TTL, and retries. |
| `.env.example` | Modified | Added documentation for MedlinePlus configuration variables. |
| `src/healthcare_agents/agents/evidence.py` | Modified | Updated Evidence Agent to query `patient_education_retriever` alongside PubMed literature, deduplicating topic queries. |
| `src/healthcare_agents/workflows/healthcare_graph.py` | Modified | Added `get_default_patient_education_retriever()` and wired `patient_education_retriever` into compiled graph. |
| `src/healthcare_agents/agents/validator.py` | Modified | Added official URL verification (`https://medlineplus.gov/`), topic deduplication, and consumer health guardrails. |
| `src/healthcare_agents/agents/answer.py` | Modified | Updated answer synthesis to format live MedlinePlus resources and distinguish consumer education from primary research. |
| `src/healthcare_agents/cli.py` | Modified | Updated CLI verbose stage reporting and notice banner for live MedlinePlus retrieval. |
| `tests/test_medlineplus_client.py` | Created | Comprehensive offline unit tests covering XML parsing, Spanish queries, empty queries, caching, retries, and errors. |
| `tests/test_live_medlineplus.py` | Created | Opt-in live tests for English/Spanish keyword search and full 4-source LangGraph workflow. |
| `docs/images/m4d_workflow.svg` | Created | Editable vector diagram showing all 4 live retrieval sources, validator guardrails, and Answer Agent synthesis. |
| `docs/images/m4d_workflow.png` | Created | Rendered high-resolution PNG diagram (1960x810) rasterized via headless Chrome. |

---

## 5. Healthcare Guardrails & Provenance Integrity

1. **Consumer Health Separation**: Patient education summaries from MedlinePlus provide consumer health context; they are not primary biomedical research publications or clinician credentials.
2. **Official URL Grounding**: The validator checks that all MedlinePlus links point strictly to official domains (`https://medlineplus.gov/` or `https://medlineplus.gov/spanish/`).
3. **Clinical Independence**:
   - Provider qualifications require provider registry evidence (NPPES).
   - Research citations require PubMed literature evidence.
   - CMS quality scores require exact NPI matches in CMS Provider Data.
   - Absence of CMS data denotes reporting program scope, not low quality.
   - NPI existence denotes administrative registration, not proof of clinical licensure or competence.
