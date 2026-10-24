"""Offline unit and integration tests for CMS Provider Data Catalog HTTP client."""

from unittest.mock import patch

import pytest

from healthcare_agents.retrieval.cms_client import (
    CMS_DATASET_CLINICIAN_MIPS,
    CMS_DATASET_FACILITY_AFFILIATION,
    CMSConnectionError,
    CMSDatasetNotFoundError,
    CMSProviderDataRetriever,
    CMSResponseError,
)

SAMPLE_METASTORE_ITEMS = b"""[
  {
    "identifier": "a174-a962",
    "title": "PY 2024 Clinician Public Reporting: Overall MIPS Performance",
    "description": "Final MIPS performance scores for individual clinicians.",
    "theme": ["Doctors and clinicians"]
  },
  {
    "identifier": "xubh-q36u",
    "title": "Hospital General Information",
    "description": "General information and overall rating for Medicare certified hospitals.",
    "theme": ["Hospitals"]
  },
  {
    "identifier": "27ea-46a8",
    "title": "Facility Affiliation Data",
    "description": "Facility affiliation data for clinicians.",
    "theme": ["Doctors and clinicians"]
  }
]"""

SAMPLE_MIPS_QUERY_RESPONSE = b"""{
  "count": 1,
  "results": [
    {
      "npi": "1003809641",
      "org_pac_id": "",
      "provider_last_name": "DAVIDSON",
      "provider_first_name": "ROBERT",
      "source": "individual",
      "facilitybased_scoring_certification_number": "",
      "facility_name": "",
      "quality_category_score": "85.8708",
      "pi_category_score": "",
      "ia_category_score": "40",
      "cost_category_score": "76.4128",
      "final_mips_score_without_cpb": "87.2722",
      "final_mips_score": "87.2722"
    }
  ]
}"""

SAMPLE_AFFILIATION_QUERY_RESPONSE = b"""{
  "count": 1,
  "results": [
    {
      "npi": "1003809641",
      "ind_pac_id": "7517003643",
      "provider_last_name": "DAVIDSON",
      "provider_first_name": "ROBERT",
      "provider_middle_name": "",
      "suff": "",
      "facility_type": "Hospital",
      "facility_affiliations_certification_number": "450001",
      "facility_type_certification_number": ""
    }
  ]
}"""

SAMPLE_HOSPITAL_QUERY_RESPONSE = b"""{
  "count": 1,
  "results": [
    {
      "facility_id": "450001",
      "facility_name": "TEXAS CHILDREN'S HOSPITAL",
      "address": "6621 FANNIN ST",
      "citytown": "HOUSTON",
      "state": "TX",
      "zip_code": "77030",
      "countyparish": "HARRIS",
      "telephone_number": "8328241000",
      "hospital_type": "Childrens",
      "hospital_ownership": "Voluntary non-profit - Private",
      "emergency_services": "Yes",
      "hospital_overall_rating": "5",
      "hospital_overall_rating_footnote": ""
    }
  ]
}"""


def test_cms_discover_datasets() -> None:
    """Verify dataset discovery and keyword filtering from metastore."""
    retriever = CMSProviderDataRetriever()

    with patch.object(retriever, "_execute_request", return_value=SAMPLE_METASTORE_ITEMS):
        all_ds = retriever.discover_datasets()
        assert len(all_ds) == 3

        hosp_ds = retriever.discover_datasets(keyword="Hospital")
        assert len(hosp_ds) == 1
        assert hosp_ds[0]["identifier"] == "xubh-q36u"

        doc_ds = retriever.discover_datasets(keyword="clinician")
        assert len(doc_ds) == 2


def test_cms_get_dataset_metadata() -> None:
    """Verify dataset metadata lookup for a single dataset."""
    retriever = CMSProviderDataRetriever()
    sample_meta = b'{"identifier": "a174-a962", "title": "PY 2024 Clinician MIPS"}'

    with patch.object(retriever, "_execute_request", return_value=sample_meta):
        meta = retriever.get_dataset_metadata("a174-a962")
        assert meta["identifier"] == "a174-a962"
        assert meta["title"] == "PY 2024 Clinician MIPS"


def test_cms_query_dataset_pagination_and_conditions() -> None:
    """Verify datastore query construction with conditions and limit/offset."""
    retriever = CMSProviderDataRetriever()

    with patch.object(
        retriever, "_execute_request", return_value=SAMPLE_MIPS_QUERY_RESPONSE
    ) as mock_exec:
        data = retriever.query_dataset(
            dataset_id=CMS_DATASET_CLINICIAN_MIPS,
            conditions=[{"property": "npi", "value": "1003809641"}],
            limit=5,
            offset=10,
        )
        assert data["count"] == 1
        assert len(data["results"]) == 1
        called_url = mock_exec.call_args[0][0]
        assert "conditions%5B0%5D%5Bproperty%5D=npi" in called_url
        assert "conditions%5B0%5D%5Bvalue%5D=1003809641" in called_url
        assert "limit=5" in called_url
        assert "offset=10" in called_url


def test_cms_get_provider_quality_mips_and_affiliations() -> None:
    """Verify provider quality retrieval for MIPS score and affiliations."""
    retriever = CMSProviderDataRetriever()

    from typing import Any

    def mock_query(
        dataset_id: str,
        conditions: Any = None,
        limit: int = 5,
        offset: int = 0,
    ) -> dict[str, Any]:
        if dataset_id == CMS_DATASET_CLINICIAN_MIPS:
            return {
                "count": 1,
                "results": [
                    {
                        "npi": "1003809641",
                        "provider_last_name": "DAVIDSON",
                        "provider_first_name": "ROBERT",
                        "final_mips_score": "87.2722",
                        "quality_category_score": "85.8708",
                        "cost_category_score": "76.4128",
                        "source": "individual",
                    }
                ],
            }
        elif dataset_id == CMS_DATASET_FACILITY_AFFILIATION:
            return {
                "count": 1,
                "results": [
                    {
                        "npi": "1003809641",
                        "provider_last_name": "DAVIDSON",
                        "provider_first_name": "ROBERT",
                        "facility_type": "Hospital",
                        "facility_affiliations_certification_number": "450001",
                    }
                ],
            }
        return {"count": 0, "results": []}

    with patch.object(retriever, "query_dataset", side_effect=mock_query):
        records = retriever.get_provider_quality("1003809641")
        assert len(records) == 2

        mips_rec = next(r for r in records if r.measure_id == "FINAL_MIPS_SCORE")
        assert mips_rec.score == "87.2722"
        assert mips_rec.entity_name == "ROBERT DAVIDSON"
        assert mips_rec.npi == "1003809641"
        assert not mips_rec.is_synthetic

        affil_rec = next(r for r in records if r.measure_id == "FACILITY_AFFILIATION")
        assert affil_rec.facility_id == "450001"
        assert affil_rec.facility_type == "Hospital"


def test_cms_get_provider_quality_invalid_npi_returns_empty() -> None:
    """Verify invalid NPI returns empty list without calling API."""
    retriever = CMSProviderDataRetriever()
    assert retriever.get_provider_quality("") == []
    assert retriever.get_provider_quality("12345") == []  # Not 10 digits
    assert retriever.get_provider_quality("abcdefghij") == []


def test_cms_search_facility_quality() -> None:
    """Verify hospital quality search by city, state, and facility name."""
    retriever = CMSProviderDataRetriever()

    with patch.object(retriever, "_execute_request", return_value=SAMPLE_HOSPITAL_QUERY_RESPONSE):
        facilities = retriever.search_facility_quality(
            facility_name="Texas Children",
            city="Houston",
            state="TX",
            limit=5,
        )
        assert len(facilities) == 1
        fac = facilities[0]
        assert fac.entity_type == "Facility"
        assert fac.facility_name == "TEXAS CHILDREN'S HOSPITAL"
        assert fac.score == "5"
        assert fac.star_rating == "5"
        assert fac.city == "HOUSTON"
        assert fac.state == "TX"


def test_cms_http_error_handling_and_retries() -> None:
    """Verify HTTP errors, timeouts, and 404 resource errors."""
    retriever = CMSProviderDataRetriever(max_retries=1, timeout_seconds=0.1)

    # 404 Not Found
    import email.message
    import urllib.error

    msg = email.message.Message()
    http_404 = urllib.error.HTTPError(
        url="https://test", code=404, msg="Not Found", hdrs=msg, fp=None
    )
    with patch("urllib.request.urlopen", side_effect=http_404):
        with pytest.raises(CMSDatasetNotFoundError):
            retriever._execute_request("https://data.cms.gov/provider-data/api/1/test")

    # 500 with retry
    http_500 = urllib.error.HTTPError(
        url="https://test", code=500, msg="Server Error", hdrs=msg, fp=None
    )
    with patch("urllib.request.urlopen", side_effect=http_500):
        with pytest.raises(CMSResponseError) as exc:
            retriever._execute_request("https://data.cms.gov/provider-data/api/1/test")
        assert "HTTP error 500" in str(exc.value)

    # Timeout error
    with patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
        with patch("time.sleep"):
            with pytest.raises(CMSConnectionError):
                retriever._execute_request("https://data.cms.gov/provider-data/api/1/test")


def test_cms_malformed_json_response() -> None:
    """Verify malformed JSON triggers CMSResponseError."""
    retriever = CMSProviderDataRetriever()
    with patch.object(retriever, "_execute_request", return_value=b"not valid json"):
        with pytest.raises(CMSResponseError):
            retriever.query_dataset("a174-a962")

        with pytest.raises(CMSResponseError):
            retriever.discover_datasets()

        with pytest.raises(CMSResponseError):
            retriever.get_dataset_metadata("a174-a962")
