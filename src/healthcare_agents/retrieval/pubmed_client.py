"""Live PubMed (NCBI Entrez E-utilities) HTTP Biomedical Literature Client.

Interacts with the official NCBI Entrez E-utilities API:
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/

In accordance with platform governance and healthcare standards:
- PubMed citations establish that a publication exists in the biomedical literature;
  they do not prove that conclusions are universally valid or directly applicable to an individual.
- Publication titles, authors, PMIDs, DOIs, and abstracts are NEVER fabricated.
- Empty search results or API errors are surfaced transparently.
- NCBI rate-limits (3 requests/second without API key, 10/second with key) are respected.
- Optional NCBI_API_KEY, NCBI_EMAIL, and NCBI_TOOL parameters are supported.
- API keys are never logged.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from datetime import UTC, datetime

from healthcare_agents.retrieval.base import (
    BaseEvidenceRetriever,
    ClinicalEvidenceRecord,
)

logger = logging.getLogger(__name__)

DEFAULT_PUBMED_API_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
DEFAULT_USER_AGENT = "open-healthcare-agentic-platform/0.4.1 (PubMed Client)"
PUBMED_BASE_ARTICLE_URL = "https://pubmed.ncbi.nlm.nih.gov/"


class PubMedClientError(Exception):
    """Base exception for PubMed client issues."""


class PubMedConnectionError(PubMedClientError):
    """Raised when connection to PubMed fails or times out."""


class PubMedResponseError(PubMedClientError):
    """Raised when PubMed responds with HTTP error or malformed XML/JSON."""


class PubMedEvidenceRetriever(BaseEvidenceRetriever):
    """Live HTTP retriever connecting to official NCBI Entrez E-utilities for PubMed literature."""

    def __init__(
        self,
        base_url: str = DEFAULT_PUBMED_API_URL,
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        api_key: str | None = None,
        email: str | None = None,
        tool: str = "open-healthcare-agentic-platform",
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.api_key = api_key.strip() if api_key and api_key.strip() else None
        self.email = email.strip() if email and email.strip() else None
        self.tool = tool.strip() or "open-healthcare-agentic-platform"
        self.user_agent = user_agent
        self._min_interval = 0.11 if self.api_key else 0.35  # Respect 10 req/s or 3 req/s
        self._last_request_time = 0.0

    def search_evidence(
        self,
        topic: str,
        evidence_type: str | None = None,
        limit: int = 5,
    ) -> Sequence[ClinicalEvidenceRecord]:
        """Search PubMed via ESearch and fetch article metadata via EFetch.

        Args:
            topic: Biomedical query or search string.
            evidence_type: Optional filter (e.g., 'research_study', 'clinical_guideline').
            limit: Maximum number of articles to retrieve (bounded 1 to 50).
        """
        cleaned_topic = topic.strip()
        if not cleaned_topic:
            return []

        clamped_limit = max(1, min(limit, 50))
        pmids = self._esearch(term=cleaned_topic, retmax=clamped_limit)
        if not pmids:
            return []

        return self._efetch(pmids=pmids)

    def _apply_rate_limit(self) -> None:
        """Enforce rate limits between consecutive NCBI requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _build_common_params(self) -> dict[str, str]:
        """Build standard NCBI Entrez query parameters without exposing secrets in logs."""
        params: dict[str, str] = {
            "tool": self.tool,
        }
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def _execute_request(self, full_url: str) -> bytes:
        """Execute HTTP GET with bounded retries and exponential backoff."""
        headers = {"User-Agent": self.user_agent}
        # Safe URL for logging that masks api_key if present
        log_url = full_url
        if "api_key=" in log_url:
            log_url = urllib.parse.urlsplit(full_url)._replace(query="<masked_api_key>").geturl()

        for attempt in range(self.max_retries + 1):
            self._apply_rate_limit()
            req = urllib.request.Request(full_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    raw_content: bytes = resp.read()
                    return raw_content
            except urllib.error.HTTPError as http_err:
                code = http_err.code
                if code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    backoff = (2**attempt) * 0.5
                    logger.warning(
                        "PubMed API HTTP %d at %s. Retrying in %.2fs (attempt %d/%d)...",
                        code,
                        log_url,
                        backoff,
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(backoff)
                    continue
                raise PubMedResponseError(
                    f"PubMed API returned HTTP error {code}: {http_err.reason}"
                ) from http_err
            except (urllib.error.URLError, TimeoutError, OSError) as conn_err:
                if attempt < self.max_retries:
                    backoff = (2**attempt) * 0.5
                    logger.warning(
                        "Connection error to PubMed API: %s. Retrying in %.2fs (attempt %d/%d)...",
                        conn_err,
                        backoff,
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(backoff)
                    continue
                raise PubMedConnectionError(
                    f"Failed to connect to PubMed API at {log_url}: {conn_err}"
                ) from conn_err

        raise PubMedConnectionError(
            f"Exhausted retries ({self.max_retries}) connecting to PubMed API."
        )

    def _esearch(self, term: str, retmax: int = 5, sort: str = "relevance") -> list[str]:
        """Execute ESearch against PubMed database and return list of PMIDs."""
        params = self._build_common_params()
        params.update(
            {
                "db": "pubmed",
                "term": term,
                "retmode": "json",
                "retmax": str(retmax),
                "sort": sort,
            }
        )
        url = f"{self.base_url}esearch.fcgi?{urllib.parse.urlencode(params)}"
        raw_bytes = self._execute_request(url)

        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as json_err:
            raise PubMedResponseError(
                f"Malformed JSON returned by PubMed ESearch: {json_err}"
            ) from json_err

        if not isinstance(data, dict):
            raise PubMedResponseError("Expected JSON object from PubMed ESearch.")

        search_result = data.get("esearchresult", {})
        if not isinstance(search_result, dict):
            return []

        id_list = search_result.get("idlist", [])
        if isinstance(id_list, list):
            # Clean and preserve valid numeric PMIDs
            return [str(pmid).strip() for pmid in id_list if str(pmid).strip().isdigit()]
        return []

    def _efetch(self, pmids: Sequence[str]) -> list[ClinicalEvidenceRecord]:
        """Execute EFetch to retrieve article abstracts and metadata for PMIDs."""
        if not pmids:
            return []

        params = self._build_common_params()
        params.update(
            {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
            }
        )
        url = f"{self.base_url}efetch.fcgi?{urllib.parse.urlencode(params)}"
        raw_bytes = self._execute_request(url)

        try:
            root = ET.fromstring(raw_bytes.decode("utf-8", errors="replace"))
        except ET.ParseError as xml_err:
            raise PubMedResponseError(
                f"Malformed XML returned by PubMed EFetch: {xml_err}"
            ) from xml_err

        retrieval_timestamp = datetime.now(UTC).isoformat()
        records: list[ClinicalEvidenceRecord] = []

        for article in root.findall(".//PubmedArticle"):
            pmid_elem = article.find(".//MedlineCitation/PMID")
            pmid = pmid_elem.text.strip() if pmid_elem is not None and pmid_elem.text else ""
            if not pmid:
                continue

            # Title
            title_elem = article.find(".//MedlineCitation/Article/ArticleTitle")
            title = (
                "".join(title_elem.itertext()).strip()
                if title_elem is not None
                else "Untitled Publication"
            )

            # Journal
            journal_elem = article.find(".//MedlineCitation/Article/Journal/Title")
            journal = (
                journal_elem.text.strip()
                if journal_elem is not None and journal_elem.text
                else "Unknown Journal"
            )

            # Publication Year
            year = datetime.now(UTC).year
            pubdate_elem = article.find(".//MedlineCitation/Article/Journal/JournalIssue/PubDate")
            if pubdate_elem is not None:
                year_elem = pubdate_elem.find("Year")
                if year_elem is not None and year_elem.text and year_elem.text.strip().isdigit():
                    year = int(year_elem.text.strip())
                else:
                    medline_date = pubdate_elem.find("MedlineDate")
                    if medline_date is not None and medline_date.text:
                        raw_date = medline_date.text.strip()
                        # Extract first 4-digit year if present
                        digits = [d for d in raw_date.split() if d.isdigit() and len(d) == 4]
                        if digits:
                            year = int(digits[0])

            # Authors
            authors_list: list[str] = []
            for author in article.findall(".//MedlineCitation/Article/AuthorList/Author"):
                last = author.find("LastName")
                fore = author.find("ForeName")
                if fore is None:
                    fore = author.find("Initials")
                if last is not None and last.text:
                    fore_str = f" {fore.text.strip()}" if fore is not None and fore.text else ""
                    authors_list.append(f"{last.text.strip()}{fore_str}")
                else:
                    collab = author.find("CollectiveName")
                    if collab is not None and collab.text:
                        authors_list.append(collab.text.strip())

            # Abstract
            abstract_parts: list[str] = []
            for abs_text in article.findall(".//MedlineCitation/Article/Abstract/AbstractText"):
                label = abs_text.get("Label")
                text = "".join(abs_text.itertext()).strip()
                if label:
                    abstract_parts.append(f"{label}: {text}")
                elif text:
                    abstract_parts.append(text)

            abstract = "\n".join(abstract_parts).strip()
            summary = (
                abstract
                if abstract
                else "No abstract available in the official MEDLINE/PubMed record."
            )
            evidence_status = "available" if abstract else "no_abstract"

            # DOI
            doi = ""
            for eloc in article.findall(".//MedlineCitation/Article/ELocationID"):
                if (
                    eloc.get("EIdType") == "doi"
                    and eloc.text
                    and eloc.attrib.get("ValidYN", "Y") == "Y"
                ):
                    doi = eloc.text.strip()
            if not doi:
                for aid in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
                    if aid.get("IdType") == "doi" and aid.text:
                        doi = aid.text.strip()

            pubmed_url = f"{PUBMED_BASE_ARTICLE_URL}{pmid}/"

            record = ClinicalEvidenceRecord(
                record_id=f"PUBMED-{pmid}",
                title=title,
                source="PubMed-Live",
                summary=summary,
                evidence_type="research_study",
                year=year,
                is_synthetic=False,
                citation_ref=f"PMID:{pmid}",
                pmid=pmid,
                authors=tuple(authors_list),
                journal=journal,
                doi=doi,
                pubmed_url=pubmed_url,
                retrieval_timestamp=retrieval_timestamp,
                source_type="PubMed",
                evidence_status=evidence_status,
            )
            records.append(record)

        return records
