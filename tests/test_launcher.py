"""Tests for healthcare-agents launcher and preflight checks."""

from unittest.mock import MagicMock, patch

import pytest

from healthcare_agents.launcher import (
    check_command_available,
    check_ollama,
    get_runtime_status,
    is_port_in_use,
    run_prerequisite_checks,
    stop_native_services,
    wait_for_endpoint,
)


def test_is_port_in_use_false() -> None:
    """Verify is_port_in_use returns False when port is free."""
    with patch("socket.socket") as mock_sock:
        instance = mock_sock.return_value.__enter__.return_value
        instance.connect_ex.return_value = 1  # non-zero = port closed
        assert not is_port_in_use(59999)


def test_is_port_in_use_true() -> None:
    """Verify is_port_in_use returns True when port is occupied."""
    with patch("socket.socket") as mock_sock:
        instance = mock_sock.return_value.__enter__.return_value
        instance.connect_ex.return_value = 0  # 0 = connection succeeded (open)
        assert is_port_in_use(8000)


def test_check_command_available() -> None:
    """Verify command availability check."""
    with patch("shutil.which", return_value="/usr/local/bin/docker"):
        assert check_command_available("docker")
    with patch("shutil.which", return_value=None):
        assert not check_command_available("nonexistent_binary_xyz")


def test_check_ollama_success() -> None:
    """Verify check_ollama when daemon is reachable and model is present."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b'{"models": [{"name": "gemma4:e2b"}]}'
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        ok, msg, models = check_ollama("http://localhost:11434", "gemma4:e2b")
        assert ok
        assert "Model available" in msg
        assert "gemma4:e2b" in models


def test_check_ollama_failure() -> None:
    """Verify check_ollama handles connection error gracefully."""
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        ok, msg, models = check_ollama("http://localhost:11434", "gemma4:e2b")
        assert not ok
        assert "unreachable" in msg
        assert models == []


def test_run_prerequisite_checks() -> None:
    """Verify prerequisite checks collection."""
    with (
        patch("healthcare_agents.launcher.is_port_in_use", return_value=False),
        patch("healthcare_agents.launcher.check_ollama", return_value=(True, "OK", ["gemma4:e2b"])),
    ):
        results = run_prerequisite_checks(api_port=9000, ui_port=9501)
        assert len(results) >= 5
        names = [r.name for r in results]
        assert "Python Version" in names
        assert "Port 9000 (FastAPI)" in names
        assert "Port 9501 (Streamlit)" in names
        assert "Inference Endpoint (Ollama)" in names


def test_wait_for_endpoint_success() -> None:
    """Verify wait_for_endpoint returns True on 200."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert wait_for_endpoint("http://localhost:8000/health", timeout_seconds=1.0)


def test_wait_for_endpoint_timeout() -> None:
    """Verify wait_for_endpoint returns False on repeated failures."""
    with patch("urllib.request.urlopen", side_effect=Exception("refused")):
        assert not wait_for_endpoint("http://localhost:8000/health", timeout_seconds=0.5)


def test_stop_native_services(tmp_path: pytest.TempPathFactory) -> None:
    """Verify stop_native_services terminates recorded PIDs."""
    import pathlib

    fake_pid_dir = tmp_path if isinstance(tmp_path, pathlib.Path) else tmp_path.mktemp("runtime")
    fake_pid_file = fake_pid_dir / "runtime_pids.json"
    fake_pid_file.write_text('{"api_pid": 999999, "ui_pid": 999998}')

    with (
        patch("healthcare_agents.launcher.get_pid_file", return_value=fake_pid_file),
        patch("os.kill") as mock_kill,
    ):
        code = stop_native_services()
        assert code == 0
        assert mock_kill.call_count == 2
        assert not fake_pid_file.exists()


def test_get_runtime_status() -> None:
    """Verify get_runtime_status reports port statuses."""
    with patch("healthcare_agents.launcher.is_port_in_use", side_effect=[True, False]):
        status = get_runtime_status(api_port=8000, ui_port=8501)
        assert "running (port 8000)" in status["api"]
        assert status["ui"] == "stopped"


def test_start_native_services_success(tmp_path: pytest.TempPathFactory) -> None:
    """Verify start_native_services launches processes, tracks pids, and shuts down."""
    import pathlib

    fake_dir = tmp_path if isinstance(tmp_path, pathlib.Path) else tmp_path.mktemp("rt")
    fake_pid_file = fake_dir / "pids.json"

    mock_proc1 = MagicMock()
    mock_proc1.pid = 11111
    mock_proc1.poll.return_value = None

    mock_proc2 = MagicMock()
    mock_proc2.pid = 22222
    mock_proc2.poll.return_value = None

    with (
        patch("healthcare_agents.launcher.get_pid_file", return_value=fake_pid_file),
        patch("subprocess.Popen", side_effect=[mock_proc1, mock_proc2]),
        patch("healthcare_agents.launcher.wait_for_endpoint", return_value=True),
        patch("healthcare_agents.launcher.stop_native_services") as mock_stop,
        patch("webbrowser.open"),
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        from healthcare_agents.launcher import start_native_services

        code = start_native_services(open_browser=False)
        assert code == 0
        assert mock_stop.called


def test_start_native_services_failure(tmp_path: pytest.TempPathFactory) -> None:
    """Verify start_native_services cleans up if health check fails."""
    import pathlib

    fake_dir = tmp_path if isinstance(tmp_path, pathlib.Path) else tmp_path.mktemp("rt")
    fake_pid_file = fake_dir / "pids.json"

    mock_proc1 = MagicMock()
    mock_proc1.pid = 11111
    mock_proc1.poll.return_value = None

    mock_proc2 = MagicMock()
    mock_proc2.pid = 22222
    mock_proc2.poll.return_value = None

    with (
        patch("healthcare_agents.launcher.get_pid_file", return_value=fake_pid_file),
        patch("subprocess.Popen", side_effect=[mock_proc1, mock_proc2]),
        patch("healthcare_agents.launcher.wait_for_endpoint", return_value=False),
        patch("healthcare_agents.launcher.stop_native_services") as mock_stop,
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        from healthcare_agents.launcher import start_native_services

        code = start_native_services(open_browser=False)
        assert code == 0
        assert mock_stop.called
