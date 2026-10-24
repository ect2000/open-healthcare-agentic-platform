"""Offline unit and integration tests for NCBI Entrez PubMed HTTP client."""

from unittest.mock import MagicMock, patch

import pytest

from healthcare_agents.retrieval.pubmed_client import (
    PubMedConnectionError,
    PubMedEvidenceRetriever,
    PubMedResponseError,
)

SAMPLE_ESEARCH_JSON = b"""{
  "header": {"type": "esearch", "version": "0.3"},
  "esearchresult": {
    "count": "2",
    "retmax": "2",
    "retstart": "0",
    "idlist": ["39342194", "36152953"]
  }
}"""

SAMPLE_EFETCH_XML = b"""<?xml version="1.0" ?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2025//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_250101.dtd">
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation Status="MEDLINE" Owner="NLM">
      <PMID Version="1">39342194</PMID>
      <Article PubModel="Electronic">
        <Journal>
          <JournalIssue CitedMedium="Internet">
            <PubDate><Year>2024</Year><Month>Sep</Month><Day>28</Day></PubDate>
          </JournalIssue>
          <Title>BMC oral health</Title>
        </Journal>
        <ArticleTitle>Non-pharmacological interventions for dental anxiety.</ArticleTitle>
        <ELocationID EIdType="doi" ValidYN="Y">10.1186/s12903-024-04919-x</ELocationID>
        <Abstract>
          <AbstractText Label="BACKGROUND">Child dental anxiety is a prevalent issue.</AbstractText>
          <AbstractText Label="CONCLUSION">Music therapy reduced anxiety.</AbstractText>
        </Abstract>
        <AuthorList CompleteYN="Y">
          <Author ValidYN="Y">
            <LastName>Kong</LastName>
            <ForeName>Xiang</ForeName>
          </Author>
          <Author ValidYN="Y">
            <LastName>Song</LastName>
            <ForeName>Nan</ForeName>
          </Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation Status="MEDLINE" Owner="NLM">
      <PMID Version="1">36152953</PMID>
      <Article PubModel="Print-Electronic">
        <Journal>
          <JournalIssue CitedMedium="Internet">
            <PubDate><MedlineDate>2022 Nov-Dec</MedlineDate></PubDate>
          </JournalIssue>
          <Title>Journal of dentistry</Title>
        </Journal>
        <ArticleTitle>Basic behavioral management techniques in pediatric dentistry.</ArticleTitle>
        <ELocationID EIdType="doi" ValidYN="Y">10.1016/j.jdent.2022.104303</ELocationID>
        <AuthorList CompleteYN="Y">
          <Author ValidYN="Y">
            <LastName>Gizani</LastName>
            <ForeName>Sotiria</ForeName>
          </Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""


def test_pubmed_client_query_construction_and_rate_limit() -> None:
    """Verify ESearch and EFetch parameter construction, headers, and rate limit settings."""
    retriever = PubMedEvidenceRetriever(
        api_key="mock_secret_key",
        email="test@example.com",
        tool="test-suite",
    )
    assert retriever._min_interval == 0.11

    params = retriever._build_common_params()
    assert params["api_key"] == "mock_secret_key"
    assert params["email"] == "test@example.com"
    assert params["tool"] == "test-suite"

    retriever_no_key = PubMedEvidenceRetriever()
    assert retriever_no_key._min_interval == 0.35
    no_key_params = retriever_no_key._build_common_params()
    assert "api_key" not in no_key_params


def test_pubmed_esearch_parsing() -> None:
    """Verify ESearch parses valid JSON into PMIDs."""
    retriever = PubMedEvidenceRetriever()
    with patch.object(retriever, "_execute_request", return_value=SAMPLE_ESEARCH_JSON):
        pmids = retriever._esearch(term="pediatric dentistry anxiety", retmax=5)
        assert pmids == ["39342194", "36152953"]


def test_pubmed_efetch_xml_normalization() -> None:
    """Verify EFetch normalizes XML with title, authors, DOI, abstract, and PubMed URL."""
    retriever = PubMedEvidenceRetriever()
    with patch.object(retriever, "_execute_request", return_value=SAMPLE_EFETCH_XML):
        records = retriever._efetch(pmids=["39342194", "36152953"])
        assert len(records) == 2

        # Record 1 (structured abstract and authors)
        rec1 = records[0]
        assert rec1.pmid == "39342194"
        assert rec1.record_id == "PUBMED-39342194"
        assert "Non-pharmacological interventions" in rec1.title
        assert rec1.journal == "BMC oral health"
        assert rec1.year == 2024
        assert rec1.doi == "10.1186/s12903-024-04919-x"
        assert rec1.pubmed_url == "https://pubmed.ncbi.nlm.nih.gov/39342194/"
        assert "BACKGROUND: Child dental anxiety" in rec1.summary
        assert "CONCLUSION: Music therapy" in rec1.summary
        assert rec1.evidence_status == "available"
        assert rec1.is_synthetic is False
        assert rec1.source == "PubMed-Live"
        assert rec1.authors == ("Kong Xiang", "Song Nan")

        # Record 2 (missing abstract handled gracefully, MedlineDate parsed)
        rec2 = records[1]
        assert rec2.pmid == "36152953"
        assert rec2.year == 2022
        assert rec2.evidence_status == "no_abstract"
        assert "No abstract available" in rec2.summary
        assert rec2.authors == ("Gizani Sotiria",)
        assert rec2.doi == "10.1016/j.jdent.2022.104303"


def test_pubmed_search_evidence_end_to_end_mocked() -> None:
    """Verify search_evidence coordinates ESearch and EFetch."""
    retriever = PubMedEvidenceRetriever()

    def mock_exec(url: str) -> bytes:
        if "esearch.fcgi" in url:
            return SAMPLE_ESEARCH_JSON
        return SAMPLE_EFETCH_XML

    with patch.object(retriever, "_execute_request", side_effect=mock_exec):
        results = retriever.search_evidence("pediatric dentistry anxiety", limit=2)
        assert len(results) == 2
        assert results[0].pmid == "39342194"
        assert results[1].pmid == "36152953"


def test_pubmed_empty_query_and_empty_results() -> None:
    """Verify empty query returns [] and empty idlist returns []."""
    retriever = PubMedEvidenceRetriever()
    assert retriever.search_evidence("") == []
    assert retriever.search_evidence("   ") == []

    empty_json = b'{"esearchresult": {"count": "0", "idlist": []}}'
    with patch.object(retriever, "_execute_request", return_value=empty_json):
        assert retriever.search_evidence("nonexistent term 1234567") == []


def test_pubmed_http_errors_and_retries() -> None:
    """Verify bounded HTTP retry with backoff and error wrapping."""
    retriever = PubMedEvidenceRetriever(max_retries=1, timeout_seconds=0.1)

    with patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
        with patch("time.sleep") as mock_sleep:
            with pytest.raises(PubMedConnectionError) as exc_info:
                retriever.search_evidence("pediatric dentistry")
            assert "Failed to connect to PubMed API" in str(exc_info.value)
            sleep_args = [call_args[0][0] for call_args in mock_sleep.call_args_list]
            assert 0.5 in sleep_args

    # HTTP 500
    mock_resp = MagicMock()
    mock_resp.status = 500
    mock_resp.code = 500
    mock_resp.reason = "Internal Server Error"
    import email.message
    import urllib.error

    msg = email.message.Message()
    http_err = urllib.error.HTTPError(
        url="https://test", code=500, msg="Internal Server Error", hdrs=msg, fp=None
    )
    with patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(PubMedResponseError) as exc_info2:
            retriever.search_evidence("pediatric dentistry")
        assert "HTTP error 500" in str(exc_info2.value)


def test_pubmed_malformed_xml_and_json() -> None:
    """Verify malformed XML and JSON trigger PubMedResponseError."""
    retriever = PubMedEvidenceRetriever()

    with patch.object(retriever, "_execute_request", return_value=b"{not valid json"):
        with pytest.raises(PubMedResponseError) as exc_info:
            retriever._esearch("test")
        assert "Malformed JSON" in str(exc_info.value)

    with patch.object(retriever, "_execute_request", return_value=b"<not valid xml"):
        with pytest.raises(PubMedResponseError) as exc_info2:
            retriever._efetch(["12345"])
        assert "Malformed XML" in str(exc_info2.value)


def test_pubmed_query_refinement_and_relevance_exclusion() -> None:
    """Verify deterministic query refinement and title/abstract relevance safeguards."""
    retriever = PubMedEvidenceRetriever()

    # 1. Query refinement syntax
    refined = retriever._build_search_query("dental anxiety, pediatric dentistry")
    assert '("dental anxiety"[Title/Abstract] OR "dental anxiety"[MeSH Terms])' in refined
    assert '("pediatric dentistry"[Title/Abstract] OR "pediatric dentistry"[MeSH Terms])' in refined
    assert " AND " in refined

    # 2. Relevance checking
    from healthcare_agents.retrieval.base import ClinicalEvidenceRecord

    relevant_record = ClinicalEvidenceRecord(
        record_id="PUBMED-1",
        title="Reducing Dental Anxiety in Pediatric Patients",
        source="PubMed-Live",
        summary="A study evaluating music interventions for children experiencing dental anxiety.",
        evidence_type="research_study",
        year=2024,
        is_synthetic=False,
    )
    assert retriever._is_topically_relevant(relevant_record, "dental anxiety, pediatric dentistry")

    # 3. Irrelevant study with only affiliation mention (e.g., dementia study)
    irrelevant_record = ClinicalEvidenceRecord(
        record_id="PUBMED-39046104",
        title="A genome-wide association meta-analysis of all-cause and vascular dementia",
        source="PubMed-Live",
        summary=(
            "GWAS meta-analysis identifying genetic risk variants for Alzheimer and dementia."
        ),
        evidence_type="research_study",
        year=2024,
        is_synthetic=False,
    )
    assert not retriever._is_topically_relevant(
        irrelevant_record, "dental anxiety, pediatric dentistry"
    )
