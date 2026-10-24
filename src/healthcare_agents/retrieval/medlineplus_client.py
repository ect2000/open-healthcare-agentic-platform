"""MedlinePlus Web Service Client: Fetches authoritative consumer health topics from NLM.

Integrates with the official MedlinePlus Web Service (https://medlineplus.gov/about/developers/webservices/)
supporting:
- Keyword-based search against English (healthTopics) and Spanish (healthTopicsSpanish) databases
- XML response parsing extracting topic titles, official URLs, snippets, and FullSummary text
- HTML tag stripping (<span class="qt0">...</span> highlights)
- Source attribution and ISO-8601 UTC retrieval timestamps
- Rate limit awareness (strictly respecting the 85 req/min threshold via client-side throttling)
- In-memory thread-safe TTL caching (default 12 hours) for non-personalized educational content
- Timeout handling and bounded exponential backoff retries
- Optional MedlinePlus Connect service adapter for code-based lookups
  (ICD-10-CM / RxCUI / SNOMED CT)
"""

from __future__ import annotations

import html
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from datetime import UTC, datetime

from healthcare_agents.retrieval.base import (
    BasePatientEducationRetriever,
    ClinicalEvidenceRecord,
)

logger = logging.getLogger(__name__)

DEFAULT_MEDLINEPLUS_URL = "https://wsearch.nlm.nih.gov/ws/query"
DEFAULT_CONNECT_URL = "https://connect.medlineplus.gov/service"
DEFAULT_USER_AGENT = (
    "open-healthcare-agentic-platform/0.4.3 "
    "(https://github.com/hastimal/open-healthcare-agentic-platform; contact: research@example.com)"
)
# MedlinePlus policy: maximum 85 requests per minute per IP address (~0.71s between requests)
MIN_REQUEST_INTERVAL_SECONDS = 0.72


class MedlinePlusClientError(Exception):
    """Base exception for MedlinePlus client errors."""


class MedlinePlusConnectionError(MedlinePlusClientError):
    """Network connection or timeout error accessing MedlinePlus Web Service."""


class MedlinePlusResponseError(MedlinePlusClientError):
    """Malformed XML or unexpected response from MedlinePlus Web Service."""


def strip_html_tags(raw_text: str | None) -> str:
    """Remove HTML highlight tags (like <span class='qt0'>) and unescape entities."""
    if not raw_text:
        return ""
    clean = re.sub(r"<[^>]+>", "", raw_text)
    return html.unescape(clean).strip()


class MedlinePlusPatientEducationRetriever(BasePatientEducationRetriever):
    """Official client for the NLM MedlinePlus Web Service."""

    def __init__(
        self,
        base_url: str = DEFAULT_MEDLINEPLUS_URL,
        connect_url: str = DEFAULT_CONNECT_URL,
        timeout_seconds: float = 12.0,
        max_retries: int = 3,
        user_agent: str = DEFAULT_USER_AGENT,
        cache_ttl_seconds: float = 43200.0,  # 12 hours
    ) -> None:
        self.base_url = base_url
        self.connect_url = connect_url
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.cache_ttl_seconds = cache_ttl_seconds
        self._min_interval = MIN_REQUEST_INTERVAL_SECONDS
        self._last_request_time = 0.0
        self._lock = threading.Lock()
        self._cache: dict[str, tuple[float, list[ClinicalEvidenceRecord]]] = {}

    def _apply_rate_limit(self) -> None:
        """Enforce strict client-side rate limit (<85 requests/min)."""
        with self._lock:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request_time = time.time()

    def _execute_request(self, full_url: str) -> bytes:
        """Execute HTTP GET with rate limiting, timeouts, and bounded retries."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/xml, text/xml, */*",
        }

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
                    backoff = (2**attempt) * 0.75
                    logger.warning(
                        "MedlinePlus API HTTP %d at %s. Retrying in %.2fs (attempt %d/%d)...",
                        code,
                        full_url,
                        backoff,
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(backoff)
                    continue
                raise MedlinePlusResponseError(
                    f"MedlinePlus API returned HTTP error {code}: {http_err.reason}"
                ) from http_err
            except (urllib.error.URLError, TimeoutError, OSError) as conn_err:
                if attempt < self.max_retries:
                    backoff = (2**attempt) * 0.75
                    logger.warning(
                        "Connection error to MedlinePlus API: %s. "
                        "Retrying in %.2fs (attempt %d/%d)...",
                        conn_err,
                        backoff,
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(backoff)
                    continue
                raise MedlinePlusConnectionError(
                    f"Failed to connect to MedlinePlus API at {full_url}: {conn_err}"
                ) from conn_err

        raise MedlinePlusConnectionError(
            f"Exhausted retries ({self.max_retries}) connecting to MedlinePlus API."
        )

    def search_topics(
        self,
        keyword: str,
        language: str = "en",
        limit: int = 5,
    ) -> Sequence[ClinicalEvidenceRecord]:
        """Search authoritative MedlinePlus consumer health topics.

        Args:
            keyword: Free-text health topic query.
            language: 'en' for English (healthTopics) or 'es' for Spanish (healthTopicsSpanish).
            limit: Maximum topics to return (bounded 1 to 20).

        Returns:
            Sequence of normalized ClinicalEvidenceRecord entries labeled as patient_education.
        """
        clean_kw = keyword.strip()
        if not clean_kw:
            return []

        lang_code = language.strip().lower()
        db_name = "healthTopicsSpanish" if lang_code in ("es", "spanish") else "healthTopics"
        cache_key = f"{db_name}:{clean_kw.lower()}"

        # Check cache
        with self._lock:
            cached_entry = self._cache.get(cache_key)
            if cached_entry:
                timestamp, cached_records = cached_entry
                if time.time() - timestamp < self.cache_ttl_seconds:
                    return cached_records[:limit]

        clamped_limit = max(1, min(limit, 20))
        params = {
            "db": db_name,
            "term": clean_kw,
            "rettype": "all",
        }
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
        raw_bytes = self._execute_request(url)

        try:
            root = ET.fromstring(raw_bytes.decode("utf-8", errors="replace"))
        except ET.ParseError as xml_err:
            raise MedlinePlusResponseError(
                f"Malformed XML returned by MedlinePlus Web Service: {xml_err}"
            ) from xml_err

        retrieval_timestamp = datetime.now(UTC).isoformat()
        current_year = datetime.now(UTC).year
        records: list[ClinicalEvidenceRecord] = []

        for doc in root.findall(".//document"):
            url_attr = doc.attrib.get("url", "").strip()
            # Title
            title_elem = doc.find('.//content[@name="title"]')
            raw_title = title_elem.text if title_elem is not None else ""
            clean_title = strip_html_tags(raw_title) or "MedlinePlus Health Topic"

            # Summary / Snippet
            full_summary_elem = doc.find('.//content[@name="FullSummary"]')
            snippet_elem = doc.find('.//content[@name="snippet"]')

            raw_summary = ""
            if full_summary_elem is not None and full_summary_elem.text:
                raw_summary = full_summary_elem.text
            elif snippet_elem is not None and snippet_elem.text:
                raw_summary = snippet_elem.text

            clean_summary = strip_html_tags(raw_summary)
            if not clean_summary:
                clean_summary = (
                    f"Authoritative patient education topic from MedlinePlus on {clean_title}."
                )

            # Topic ID
            topic_id = ""
            if url_attr:
                match = re.search(r"/([^/]+)\.html$", url_attr)
                if match:
                    topic_id = match.group(1)

            record = ClinicalEvidenceRecord(
                record_id=f"MEDLINE-{topic_id.upper() or len(records) + 1}",
                title=clean_title,
                source="MedlinePlus-Live",
                summary=clean_summary,
                evidence_type="patient_education",
                year=current_year,
                is_synthetic=False,
                citation_ref=f"MedlinePlus:{topic_id or 'topic'}",
                pubmed_url="",
                retrieval_timestamp=retrieval_timestamp,
                source_type="MedlinePlus",
                evidence_status="available",
                official_url=url_attr,
                topic_id=topic_id,
                language=lang_code,
            )
            records.append(record)
            if len(records) >= clamped_limit:
                break

        # Store in cache
        with self._lock:
            self._cache[cache_key] = (time.time(), records)

        return records

    def lookup_code(
        self,
        code: str,
        code_system_oid: str = "2.16.840.1.113883.6.90",  # ICD-10-CM
        language: str = "en",
    ) -> list[ClinicalEvidenceRecord]:
        """Optional adapter querying MedlinePlus Connect with standardized codes."""
        clean_code = code.strip()
        if not clean_code:
            return []

        params = {
            "mainSearchCriteria.v.cs": code_system_oid,
            "mainSearchCriteria.v.c": clean_code,
            "knowledgeResponseType": "application/json",
        }
        url = f"{self.connect_url}?{urllib.parse.urlencode(params)}"
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}

        self._apply_rate_limit()
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.warning("MedlinePlus Connect code lookup failed for %s: %s", clean_code, e)
            return []

        records: list[ClinicalEvidenceRecord] = []
        feed = data.get("feed", {})
        entries = feed.get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]

        retrieval_timestamp = datetime.now(UTC).isoformat()
        current_year = datetime.now(UTC).year

        for entry in entries:
            title_obj = entry.get("title", {})
            title_text = (
                title_obj.get("_value", "") if isinstance(title_obj, dict) else str(title_obj)
            )
            link_obj = entry.get("link", [{}])
            link_url = ""
            if isinstance(link_obj, list) and link_obj:
                link_url = link_obj[0].get("href", "")
            elif isinstance(link_obj, dict):
                link_url = link_obj.get("href", "")

            summary_obj = entry.get("summary", {})
            summary_text = (
                summary_obj.get("_value", "") if isinstance(summary_obj, dict) else str(summary_obj)
            )

            record = ClinicalEvidenceRecord(
                record_id=f"CONNECT-{clean_code}",
                title=strip_html_tags(title_text) or f"Condition Code {clean_code}",
                source="MedlinePlus-Connect",
                summary=(
                    strip_html_tags(summary_text) or f"Patient education for code {clean_code}."
                ),
                evidence_type="patient_education",
                year=current_year,
                is_synthetic=False,
                citation_ref=f"MedlinePlus-Connect:{clean_code}",
                pubmed_url="",
                retrieval_timestamp=retrieval_timestamp,
                source_type="MedlinePlus-Connect",
                evidence_status="available",
                official_url=link_url,
                topic_id=clean_code,
                language=language,
            )
            records.append(record)

        return records
