"""Offline unit and integration tests for MedlinePlus Web Service HTTP client."""

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from healthcare_agents.retrieval.fixtures import (
    FixturePatientEducationRetriever,
)
from healthcare_agents.retrieval.medlineplus_client import (
    MedlinePlusConnectionError,
    MedlinePlusPatientEducationRetriever,
    MedlinePlusResponseError,
    strip_html_tags,
)

SAMPLE_XML_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<nlmSearchResult version="1.2">
  <term>pediatric dental anxiety</term>
  <count>2</count>
  <list>
    <document url="https://medlineplus.gov/childdentalhealth.html" id="1">
      <content name="title">&lt;span class="qt0"&gt;Child&lt;/span&gt; Dental Health</content>
      <content name="FullSummary">Dental care for children includes brushing and visits.</content>
      <content name="snippet">Tips to keep your child's teeth clean.</content>
    </document>
    <document url="https://medlineplus.gov/phobias.html" id="2">
      <content name="title">Phobias and Anxiety Disorders</content>
      <content name="snippet">A phobia is an intense fear of something.</content>
    </document>
  </list>
</nlmSearchResult>
"""

SAMPLE_SPANISH_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<nlmSearchResult version="1.2">
  <term>salud dental infantil</term>
  <count>1</count>
  <list>
    <document url="https://medlineplus.gov/spanish/childdentalhealth.html" id="1">
      <content name="title">Salud dental infantil</content>
      <content name="FullSummary">Cuidado dental para ninos y caries.</content>
    </document>
  </list>
</nlmSearchResult>
"""

SAMPLE_EMPTY_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<nlmSearchResult version="1.2">
  <term>xyznonexistentquery123</term>
  <count>0</count>
  <list>
  </list>
</nlmSearchResult>
"""

SAMPLE_CONNECT_JSON = b"""{
  "feed": {
    "entry": [
      {
        "title": {
          "_value": "Dental Caries (Tooth Decay)"
        },
        "link": [
          {
            "href": "https://medlineplus.gov/toothdecay.html"
          }
        ],
        "summary": {
          "_value": "Information on tooth decay and cavities."
        }
      }
    ]
  }
}
"""


def test_strip_html_tags() -> None:
    assert strip_html_tags(None) == ""
    assert strip_html_tags("") == ""
    assert strip_html_tags('<span class="qt0">Dental</span> &amp; Care') == "Dental & Care"
    assert strip_html_tags("<p>Hello <b>World</b></p>") == "Hello World"


def test_medlineplus_search_topics_success() -> None:
    retriever = MedlinePlusPatientEducationRetriever(cache_ttl_seconds=60)
    mock_resp = MagicMock()
    mock_resp.read.return_value = SAMPLE_XML_RESPONSE
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        records = retriever.search_topics(keyword="pediatric dental anxiety", limit=5)

    assert len(records) == 2
    r1 = records[0]
    assert r1.title == "Child Dental Health"
    assert "Dental care for children" in r1.summary
    assert r1.official_url == "https://medlineplus.gov/childdentalhealth.html"
    assert r1.topic_id == "childdentalhealth"
    assert r1.evidence_type == "patient_education"
    assert r1.source == "MedlinePlus-Live"
    assert not r1.is_synthetic
    assert r1.language == "en"

    r2 = records[1]
    assert r2.title == "Phobias and Anxiety Disorders"
    assert r2.topic_id == "phobias"


def test_medlineplus_spanish_query() -> None:
    retriever = MedlinePlusPatientEducationRetriever()
    mock_resp = MagicMock()
    mock_resp.read.return_value = SAMPLE_SPANISH_XML
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        records = retriever.search_topics(keyword="salud dental infantil", language="es", limit=5)

    assert len(records) == 1
    assert records[0].title == "Salud dental infantil"
    assert records[0].language == "es"
    req = mock_urlopen.call_args[0][0]
    assert "db=healthTopicsSpanish" in req.full_url


def test_medlineplus_empty_and_whitespace_query() -> None:
    retriever = MedlinePlusPatientEducationRetriever()
    assert retriever.search_topics(keyword="   ") == []

    mock_resp = MagicMock()
    mock_resp.read.return_value = SAMPLE_EMPTY_XML
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        records = retriever.search_topics(keyword="xyznonexistentquery123")
    assert records == []


def test_medlineplus_cache_behavior() -> None:
    retriever = MedlinePlusPatientEducationRetriever(cache_ttl_seconds=3600)
    mock_resp = MagicMock()
    mock_resp.read.return_value = SAMPLE_XML_RESPONSE
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        res1 = retriever.search_topics(keyword="dental", limit=2)
        res2 = retriever.search_topics(keyword="dental", limit=2)

    assert len(res1) == 2
    assert len(res2) == 2
    # Only one HTTP request should be made due to cache
    assert mock_urlopen.call_count == 1


def test_medlineplus_malformed_xml() -> None:
    retriever = MedlinePlusPatientEducationRetriever()
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"<not-valid-xml"
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(MedlinePlusResponseError) as exc_info:
            retriever.search_topics(keyword="malformed")
    assert "Malformed XML" in str(exc_info.value)


def test_medlineplus_http_error_retry_and_exhaustion() -> None:
    retriever = MedlinePlusPatientEducationRetriever(max_retries=1)

    http_503 = urllib.error.HTTPError(
        url="https://wsearch.nlm.nih.gov",
        code=503,
        msg="Service Unavailable",
        hdrs=None,  # type: ignore
        fp=None,
    )

    with patch("urllib.request.urlopen", side_effect=http_503), patch("time.sleep"):
        with pytest.raises(MedlinePlusResponseError) as exc_info:
            retriever.search_topics(keyword="retry")
    assert "HTTP error 503" in str(exc_info.value)


def test_medlineplus_connection_error() -> None:
    retriever = MedlinePlusPatientEducationRetriever(max_retries=0)

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("DNS failure")):
        with pytest.raises(MedlinePlusConnectionError) as exc_info:
            retriever.search_topics(keyword="connection-fail")
    assert "Failed to connect" in str(exc_info.value)


def test_medlineplus_connect_code_lookup() -> None:
    retriever = MedlinePlusPatientEducationRetriever()
    mock_resp = MagicMock()
    mock_resp.read.return_value = SAMPLE_CONNECT_JSON
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        records = retriever.lookup_code(code="K02.9")

    assert len(records) == 1
    r = records[0]
    assert r.title == "Dental Caries (Tooth Decay)"
    assert r.source == "MedlinePlus-Connect"
    assert r.official_url == "https://medlineplus.gov/toothdecay.html"

    # Empty code
    assert retriever.lookup_code("") == []


def test_medlineplus_connect_error_returns_empty() -> None:
    retriever = MedlinePlusPatientEducationRetriever()
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Network down")):
        records = retriever.lookup_code("K02.9")
    assert records == []


def test_fixture_patient_education_retriever() -> None:
    retriever = FixturePatientEducationRetriever()
    results = retriever.search_topics(keyword="anxiety")
    assert len(results) > 0
    assert all(r.evidence_type == "patient_education" for r in results)

    # Fallback when no match
    results_nomatch = retriever.search_topics(keyword="zzznomatch")
    assert len(results_nomatch) > 0
