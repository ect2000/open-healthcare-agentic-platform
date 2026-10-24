"""Comprehensive offline unit and error-handling tests for NPPESProviderRetriever."""

from unittest.mock import MagicMock, patch

import pytest

from healthcare_agents.retrieval.nppes_client import (
    NPPESConnectionError,
    NPPESProviderRetriever,
    NPPESResponseError,
)

SAMPLE_NPPES_API_RESPONSE = {
    "result_count": 2,
    "results": [
        {
            "number": "1134345234",
            "enumeration_type": "NPI-1",
            "basic": {
                "first_name": "BHAVINI",
                "last_name": "ACHARYA",
                "middle_name": "S",
                "credential": "BDS, MPH",
                "name_prefix": "Dr.",
                "status": "A",
                "enumeration_date": "2007-04-17",
                "last_updated": "2022-10-28",
            },
            "addresses": [
                {
                    "address_purpose": "LOCATION",
                    "address_1": "7500 CAMBRIDGE ST STE 3410",
                    "address_2": "",
                    "city": "HOUSTON",
                    "state": "TX",
                    "postal_code": "770542032",
                    "telephone_number": "713-500-8220",
                },
                {
                    "address_purpose": "MAILING",
                    "address_1": "4310 DUNLAVY ST APT 457",
                    "city": "HOUSTON",
                    "state": "TX",
                    "postal_code": "770065315",
                    "telephone_number": "713-865-0462",
                },
            ],
            "taxonomies": [
                {
                    "code": "1223P0221X",
                    "desc": "Dentist, Pediatric Dentistry",
                    "primary": True,
                    "state": "TX",
                    "license": "24153",
                }
            ],
        },
        {
            "number": "1982736450",
            "enumeration_type": "NPI-2",
            "basic": {
                "organization_name": "HOUSTON PEDIATRIC SMILES LLC",
                "status": "A",
                "enumeration_date": "2015-01-10",
            },
            "addresses": [
                {
                    "address_purpose": "LOCATION",
                    "address_1": "100 MEDICAL CENTER BLVD",
                    "city": "HOUSTON",
                    "state": "TX",
                    "postal_code": "77030",
                    "telephone_number": "713-555-0199",
                }
            ],
            "taxonomies": [
                {
                    "code": "261QD0000X",
                    "desc": "Dental Clinic, Pediatric Dentistry",
                    "primary": True,
                }
            ],
        },
    ],
}


def test_nppes_normalization_individual_and_organization() -> None:
    """Verify NPPES normalization correctly handles both NPI-1 and NPI-2."""
    retriever = NPPESProviderRetriever()
    records = retriever._normalize_response(
        SAMPLE_NPPES_API_RESPONSE,
        source_url="https://npiregistry.cms.hhs.gov/api/?mock=1",
    )

    assert len(records) == 2

    # Individual (NPI-1)
    ind = records[0]
    assert ind.npi == "1134345234"
    assert "BHAVINI" in ind.name
    assert "ACHARYA" in ind.name
    assert "BDS, MPH" in ind.name
    assert ind.entity_type == "Individual"
    assert ind.specialty == "Dentist, Pediatric Dentistry"
    assert ind.taxonomy_code == "1223P0221X"
    assert ind.city == "HOUSTON"
    assert ind.state == "TX"
    assert "7500 CAMBRIDGE ST" in ind.practice_address
    assert "4310 DUNLAVY ST" in ind.mailing_address
    assert ind.telephone == "713-500-8220"
    assert ind.is_synthetic is False
    assert ind.source == "CMS-NPPES-Live"
    assert ind.metadata["enumeration_type"] == "NPI-1"

    # Organization (NPI-2)
    org = records[1]
    assert org.npi == "1982736450"
    assert org.name == "HOUSTON PEDIATRIC SMILES LLC"
    assert org.facility_name == "HOUSTON PEDIATRIC SMILES LLC"
    assert org.entity_type == "Organization"
    assert "Dental Clinic" in org.specialty
    assert org.is_synthetic is False


def test_nppes_query_parameters_building() -> None:
    """Verify search_providers builds query string with city, state, specialty, and npi."""
    retriever = NPPESProviderRetriever(base_url="https://test.nppes/api/")

    with patch.object(retriever, "_execute_request") as mock_exec:
        mock_exec.return_value = {"result_count": 0, "results": []}

        # Search by criteria
        retriever.search_providers(
            specialty="Pediatric Dentistry",
            city="Houston",
            state="TX",
            limit=10,
        )
        called_url = mock_exec.call_args[0][0]
        assert "city=Houston" in called_url
        assert "state=TX" in called_url
        assert "taxonomy_description=Pediatric+Dentistry" in called_url
        assert "limit=10" in called_url
        assert "version=2.1" in called_url

        # Search by direct NPI
        retriever.search_providers(npi="1134345234")
        npi_url = mock_exec.call_args[0][0]
        assert "number=1134345234" in npi_url


def test_nppes_empty_and_malformed_responses() -> None:
    """Verify empty results and malformed data handling."""
    retriever = NPPESProviderRetriever()

    # Empty results
    assert retriever._normalize_response({"results": []}, "url") == []
    assert retriever._normalize_response({}, "url") == []

    # Non-dict items or missing number
    bad_items = {"results": ["string", {"basic": {}}]}
    assert retriever._normalize_response(bad_items, "url") == []


def test_nppes_http_retries_and_connection_error() -> None:
    """Verify bounded retry with backoff and eventual NPPESConnectionError."""
    retriever = NPPESProviderRetriever(max_retries=1, timeout_seconds=0.1)

    with patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
        with patch("time.sleep") as mock_sleep:
            with pytest.raises(NPPESConnectionError) as exc_info:
                retriever.search_providers(city="Houston")
            assert "Failed to query NPPES after 2 attempts" in str(exc_info.value)
            mock_sleep.assert_called_once()


def test_nppes_http_non_200_and_bad_json() -> None:
    """Verify handling of non-200 responses and corrupt JSON bodies."""
    retriever = NPPESProviderRetriever(max_retries=0)

    # HTTP 500 error
    mock_resp_500 = MagicMock()
    mock_resp_500.status = 500
    mock_resp_500.__enter__.return_value = mock_resp_500

    with patch("urllib.request.urlopen", return_value=mock_resp_500):
        with pytest.raises(NPPESResponseError) as exc_info:
            retriever.search_providers(city="Houston")
        assert "NPPES API responded with status code 500" in str(exc_info.value)

    # Corrupt JSON body
    mock_resp_bad_json = MagicMock()
    mock_resp_bad_json.status = 200
    mock_resp_bad_json.read.return_value = b"{corrupt json"
    mock_resp_bad_json.__enter__.return_value = mock_resp_bad_json

    with patch("urllib.request.urlopen", return_value=mock_resp_bad_json):
        with pytest.raises(NPPESResponseError) as exc_info:
            retriever.search_providers(city="Houston")
        assert "Malformed NPPES JSON payload" in str(exc_info.value)


def test_nppes_provider_retriever_offline_mocked_search() -> None:
    """Verify search_providers returns ProviderRecords end-to-end with mocked execute."""
    retriever = NPPESProviderRetriever()
    with patch.object(retriever, "_execute_request", return_value=SAMPLE_NPPES_API_RESPONSE):
        results = retriever.search_providers(city="Houston", specialty="Pediatric Dentistry")
        assert len(results) == 2
        assert results[0].npi == "1134345234"
        assert results[1].npi == "1982736450"


def test_nppes_practice_location_and_taxonomy_regression_filtering() -> None:
    """M4A Correction: Exclude candidates outside requested practice city or taxonomy."""
    retriever = NPPESProviderRetriever()

    mixed_response = {
        "result_count": 3,
        "results": [
            # Candidate 1: In Houston practice location, Pediatric Dentistry -> KEEP
            {
                "number": "1111111111",
                "enumeration_type": "NPI-1",
                "basic": {"first_name": "Alice", "last_name": "Dentist"},
                "addresses": [
                    {
                        "address_purpose": "LOCATION",
                        "city": "Houston",
                        "state": "TX",
                        "address_1": "123 Main St",
                    },
                    {
                        "address_purpose": "MAILING",
                        "city": "Dallas",
                        "state": "TX",
                        "address_1": "PO Box 99",
                    },
                ],
                "taxonomies": [
                    {"code": "1223P0221X", "desc": "Dentist, Pediatric Dentistry", "primary": True}
                ],
            },
            # Candidate 2: Columbus OH practice location, only mailing in Houston -> EXCLUDE
            {
                "number": "2222222222",
                "enumeration_type": "NPI-1",
                "basic": {"first_name": "Bob", "last_name": "Outofarea"},
                "addresses": [
                    {
                        "address_purpose": "LOCATION",
                        "city": "Columbus",
                        "state": "OH",
                        "address_1": "456 North St",
                    },
                    {
                        "address_purpose": "MAILING",
                        "city": "Houston",
                        "state": "TX",
                        "address_1": "PO Box 1",
                    },
                ],
                "taxonomies": [
                    {"code": "1223P0221X", "desc": "Dentist, Pediatric Dentistry", "primary": True}
                ],
            },
            # Candidate 3: In Houston practice location, but taxonomy is Dermatology -> EXCLUDE
            {
                "number": "3333333333",
                "enumeration_type": "NPI-1",
                "basic": {"first_name": "Carol", "last_name": "Skin"},
                "addresses": [
                    {
                        "address_purpose": "LOCATION",
                        "city": "Houston",
                        "state": "TX",
                        "address_1": "789 Elm St",
                    }
                ],
                "taxonomies": [{"code": "207N00000X", "desc": "Dermatology", "primary": True}],
            },
        ],
    }

    with patch.object(retriever, "_execute_request", return_value=mixed_response):
        filtered = retriever.search_providers(
            city="Houston",
            state="TX",
            specialty="Pediatric Dentistry",
        )
        assert len(filtered) == 1
        assert filtered[0].npi == "1111111111"
        assert filtered[0].name == "Alice Dentist"
        assert filtered[0].city == "Houston"
        assert filtered[0].specialty == "Dentist, Pediatric Dentistry"
