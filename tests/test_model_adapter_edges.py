"""Additional unit tests to verify edge cases and streaming exceptions in OllamaAdapter."""

import io
import json
import socket
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from healthcare_agents.models import (
    Message,
    ModelInferenceError,
    ModelNotFoundError,
    ModelTimeoutError,
    ModelUnavailableError,
    OllamaAdapter,
)


def test_ollama_adapter_generate_generic_http_error() -> None:
    """Verify HTTP error other than 404 raises ModelInferenceError."""
    adapter = OllamaAdapter(base_url="http://localhost:11434")
    err = urllib.error.HTTPError(
        url="http://localhost:11434/api/chat",
        code=500,
        msg="Internal Server Error",
        hdrs=MagicMock(),
        fp=io.BytesIO(b'{"error":"internal crash"}'),
    )
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(ModelInferenceError, match="HTTP error 500"):
            adapter.generate(prompt="hello")


def test_ollama_adapter_generate_stream_errors() -> None:
    """Verify stream generation handles HTTP 404, generic HTTP, and timeouts."""
    adapter = OllamaAdapter(base_url="http://localhost:11434", timeout_seconds=2.0)

    # 404 on stream
    err_404 = urllib.error.HTTPError(
        url="http://localhost:11434/api/chat",
        code=404,
        msg="Not Found",
        hdrs=MagicMock(),
        fp=io.BytesIO(b"not found"),
    )
    with patch("urllib.request.urlopen", side_effect=err_404):
        with pytest.raises(ModelNotFoundError):
            list(adapter.generate_stream(prompt="hi"))

    # Generic HTTP error on stream
    err_500 = urllib.error.HTTPError(
        url="http://localhost:11434/api/chat",
        code=500,
        msg="Server Error",
        hdrs=MagicMock(),
        fp=io.BytesIO(b"server error"),
    )
    with patch("urllib.request.urlopen", side_effect=err_500):
        with pytest.raises(ModelInferenceError):
            list(adapter.generate_stream(prompt="hi"))

    # Timeout on stream
    with patch("urllib.request.urlopen", side_effect=socket.timeout):
        with pytest.raises(ModelTimeoutError):
            list(adapter.generate_stream(prompt="hi"))

    # Connection refused on stream
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        with pytest.raises(ModelUnavailableError):
            list(adapter.generate_stream(prompt="hi"))


def test_ollama_adapter_generate_stream_malformed_chunk() -> None:
    """Verify malformed JSON line inside stream raises ModelInferenceError."""
    adapter = OllamaAdapter(base_url="http://localhost:11434")
    mock_resp = MagicMock()
    mock_resp.__iter__.return_value = iter([b"bad json\n"])
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(ModelInferenceError, match="Malformed streaming chunk"):
            list(adapter.generate_stream(prompt="hi"))


def test_ollama_adapter_messages_input() -> None:
    """Verify generate handles explicit messages sequence."""
    adapter = OllamaAdapter(base_url="http://localhost:11434")
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(
        {
            "message": {"content": "ok"},
            "model": "gemma4:e2b",
        }
    ).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = adapter.generate(
            prompt="",
            messages=[
                Message(role="user", content="msg 1"),
                Message(role="assistant", content="resp 1"),
            ],
        )
        assert res.content == "ok"
