"""Unit tests for RTSP URL helpers + error classification."""

from app.core.rtsp import (
    ProbeStatus,
    _classify_error,
    build_authenticated_url,
    is_valid_rtsp_url,
)


def test_valid_rtsp_urls() -> None:
    assert is_valid_rtsp_url("rtsp://192.168.1.10:554/stream1")
    assert is_valid_rtsp_url("rtsps://cam.example.com/live")


def test_invalid_rtsp_urls() -> None:
    assert not is_valid_rtsp_url("http://192.168.1.10/stream")
    assert not is_valid_rtsp_url("not a url")
    assert not is_valid_rtsp_url("rtsp://")


def test_build_authenticated_url_injects_credentials() -> None:
    url = build_authenticated_url("rtsp://host:554/s", "admin", "pass")
    assert url == "rtsp://admin:pass@host:554/s"


def test_build_authenticated_url_keeps_existing_userinfo() -> None:
    url = "rtsp://a:b@host:554/s"
    assert build_authenticated_url(url, "admin", "pass") == url


def test_classify_error() -> None:
    assert _classify_error("401 Unauthorized") is ProbeStatus.AUTH_FAILED
    assert _classify_error("Connection refused") is ProbeStatus.UNREACHABLE
    assert _classify_error("Operation timed out") is ProbeStatus.TIMEOUT
    assert _classify_error("some other failure") is ProbeStatus.ERROR
