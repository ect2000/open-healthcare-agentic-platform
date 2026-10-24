"""Live NPPES (National Plan and Provider Enumeration System) HTTP Registry Client.

Interacts with the CMS NPPES NPI Registry API version 2.1:
https://npiregistry.cms.hhs.gov/api/

In accordance with platform governance and healthcare standards:
- An NPI is a standard administrative identification number issued by CMS.
- An NPI is NOT proof of state medical licensure, board certification, clinical
  competence, malpractice history, or provider quality.
- No ratings, clinical quality scores, or unestablished credentials are ever invented.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from healthcare_agents.retrieval.base import BaseProviderRetriever, ProviderRecord

logger = logging.getLogger(__name__)

DEFAULT_NPPES_API_URL = "https://npiregistry.cms.hhs.gov/api/"
DEFAULT_USER_AGENT = "open-healthcare-agentic-platform/0.4.0 (NPPES Client)"


class NPPESClientError(Exception):
    """Base exception for NPPES client issues."""


class NPPESConnectionError(NPPESClientError):
    """Raised when connection to NPPES fails or times out."""


class NPPESResponseError(NPPESClientError):
    """Raised when NPPES responds with HTTP error or malformed payload."""


class NPPESProviderRetriever(BaseProviderRetriever):
    """Live HTTP retriever connecting to the public CMS NPPES Registry API v2.1."""

    def __init__(
        self,
        base_url: str = DEFAULT_NPPES_API_URL,
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.user_agent = user_agent

    def search_providers(
        self,
        specialty: str | None = None,
        city: str | None = None,
        state: str | None = None,
        npi: str | None = None,
        limit: int = 5,
    ) -> Sequence[ProviderRecord]:
        """Execute query against NPPES API 2.1 and return normalized ProviderRecords.

        Bounded pagination limit is capped at 100 per CMS API specification.
        """
        # Clamp limit
        clamped_limit = max(1, min(limit, 100))

        params: dict[str, str] = {
            "version": "2.1",
            "limit": str(clamped_limit),
        }

        if npi:
            # Direct NPI lookup
            cleaned_npi = npi.strip()
            params["number"] = cleaned_npi
        else:
            if city:
                params["city"] = city.strip()
            if state:
                # State should be 2-letter postal abbreviation if possible
                params["state"] = state.strip().upper()[:2]
            if specialty:
                params["taxonomy_description"] = specialty.strip()

        # Build full request URL
        query_string = urllib.parse.urlencode(params)
        full_url = f"{self.base_url}?{query_string}"

        raw_data = self._execute_request(full_url)
        return self._normalize_response(raw_data, source_url=full_url)

    def _execute_request(self, url: str) -> dict[str, Any]:
        """Execute HTTP GET with bounded retries and exponential backoff."""
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            },
        )

        attempts = 0
        backoff = 0.5
        last_error: Exception | None = None

        while attempts <= self.max_retries:
            attempts += 1
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    status_code = resp.status
                    if status_code != 200:
                        raise NPPESResponseError(
                            f"NPPES API responded with status code {status_code}"
                        )
                    body_bytes = resp.read()
                    try:
                        data = json.loads(body_bytes.decode("utf-8"))
                        if not isinstance(data, dict):
                            raise NPPESResponseError(
                                "Malformed NPPES response: expected JSON object"
                            )
                        return data
                    except (json.JSONDecodeError, UnicodeDecodeError) as decode_err:
                        raise NPPESResponseError(
                            f"Malformed NPPES JSON payload: {decode_err}"
                        ) from decode_err
            except (
                urllib.error.HTTPError,
                urllib.error.URLError,
                TimeoutError,
                OSError,
            ) as net_err:
                last_error = net_err
                if attempts <= self.max_retries:
                    time.sleep(backoff)
                    backoff *= 2.0
                else:
                    break

        raise NPPESConnectionError(
            f"Failed to query NPPES after {attempts} attempts: {last_error}"
        ) from last_error

    def _normalize_response(self, data: dict[str, Any], source_url: str) -> list[ProviderRecord]:
        """Parse raw NPPES results into strictly typed ProviderRecord instances."""
        retrieval_timestamp = datetime.now(UTC).isoformat()
        results = data.get("results", [])
        if not isinstance(results, list):
            return []

        normalized: list[ProviderRecord] = []

        for item in results:
            if not isinstance(item, dict):
                continue

            npi = str(item.get("number", "")).strip()
            if not npi:
                continue

            enum_type = item.get("enumeration_type", "")
            is_organization = enum_type == "NPI-2"
            entity_type = "Organization" if is_organization else "Individual"

            basic = item.get("basic", {}) if isinstance(item.get("basic"), dict) else {}

            if is_organization:
                org_name = basic.get("organization_name", "").strip()
                name = org_name or "Unknown Organization"
                facility_name = org_name
            else:
                first = basic.get("first_name", "").strip()
                last = basic.get("last_name", "").strip()
                middle = basic.get("middle_name", "").strip()
                cred = basic.get("credential", "").strip()
                prefix = basic.get("name_prefix", "").strip()

                name_parts = [prefix, first, middle, last]
                full_name = " ".join(p for p in name_parts if p).strip()
                if cred:
                    full_name = f"{full_name}, {cred}" if full_name else cred
                name = full_name or "Unknown Practitioner"
                facility_name = "Independent Practice"

            # Parse taxonomies (specialties)
            taxonomies = item.get("taxonomies", [])
            primary_specialty = "General Practice"
            primary_taxonomy_code = ""

            if isinstance(taxonomies, list) and taxonomies:
                # Find primary or first taxonomy
                primary_tax = next(
                    (t for t in taxonomies if isinstance(t, dict) and t.get("primary") is True),
                    taxonomies[0] if isinstance(taxonomies[0], dict) else {},
                )
                if isinstance(primary_tax, dict):
                    primary_specialty = primary_tax.get("desc") or primary_specialty
                    primary_taxonomy_code = primary_tax.get("code") or ""

            # Parse Addresses: differentiate practice (LOCATION) vs mailing (MAILING)
            addresses = item.get("addresses", [])
            practice_addr_str = ""
            mailing_addr_str = ""
            city = ""
            state = ""
            telephone = ""

            if isinstance(addresses, list):
                for addr in addresses:
                    if not isinstance(addr, dict):
                        continue
                    purpose = addr.get("address_purpose", "").upper()
                    line1 = addr.get("address_1", "").strip()
                    line2 = addr.get("address_2", "").strip()
                    addr_city = addr.get("city", "").strip()
                    addr_state = addr.get("state", "").strip()
                    postal = addr.get("postal_code", "").strip()
                    phone = addr.get("telephone_number", "").strip()

                    addr_summary = ", ".join(
                        p for p in [line1, line2, f"{addr_city} {addr_state} {postal}".strip()] if p
                    )

                    if purpose == "LOCATION":
                        practice_addr_str = addr_summary
                        city = addr_city
                        state = addr_state
                        if phone:
                            telephone = phone
                    elif purpose == "MAILING":
                        mailing_addr_str = addr_summary
                        if not city:
                            city = addr_city
                        if not state:
                            state = addr_state
                        if not telephone and phone:
                            telephone = phone

            metadata: dict[str, str] = {
                "enumeration_type": enum_type,
                "status": basic.get("status", "Unknown"),
            }
            if basic.get("enumeration_date"):
                metadata["enumeration_date"] = str(basic["enumeration_date"])
            if basic.get("last_updated"):
                metadata["last_updated"] = str(basic["last_updated"])

            record = ProviderRecord(
                provider_id=f"NPPES-{npi}",
                npi=npi,
                name=name,
                specialty=primary_specialty,
                facility_name=facility_name,
                city=city or "Unknown",
                state=state or "Unknown",
                source="CMS-NPPES-Live",
                is_synthetic=False,
                entity_type=entity_type,
                taxonomy_code=primary_taxonomy_code,
                practice_address=practice_addr_str,
                mailing_address=mailing_addr_str,
                telephone=telephone,
                retrieval_timestamp=retrieval_timestamp,
                source_url=source_url,
                metadata=metadata,
            )
            normalized.append(record)

        return normalized
