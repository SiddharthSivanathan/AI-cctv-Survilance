"""RTSP connection validation via ffmpeg/ffprobe.

Validates an RTSP URL, attempts an (optionally authenticated) connection,
captures a single frame, and detects resolution / fps / codec. Returns a
typed result the API and health worker map to camera status.

This module shells out to the system ``ffmpeg`` and ``ffprobe`` binaries
(installed in the API image). It never logs credentials.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse, urlunparse


class ProbeStatus(str, Enum):
    CONNECTED = "connected"
    AUTH_FAILED = "auth_failed"
    UNREACHABLE = "unreachable"
    INVALID_URL = "invalid_url"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class ProbeResult:
    status: ProbeStatus
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    codec: str | None = None
    frame_jpeg: bytes | None = None
    message: str | None = None

    @property
    def resolution(self) -> str | None:
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return None


def is_valid_rtsp_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in {"rtsp", "rtsps"} and bool(parsed.hostname)


def build_authenticated_url(url: str, username: str | None, password: str | None) -> str:
    """Inject credentials into the URL netloc if provided and not already present."""
    parsed = urlparse(url)
    if username and "@" not in parsed.netloc:
        host = parsed.netloc
        cred = username if not password else f"{username}:{password}"
        parsed = parsed._replace(netloc=f"{cred}@{host}")
    return urlunparse(parsed)


def _classify_error(stderr: str) -> ProbeStatus:
    lowered = stderr.lower()
    if "401" in lowered or "unauthorized" in lowered or "authentication" in lowered:
        return ProbeStatus.AUTH_FAILED
    if any(s in lowered for s in ("connection refused", "no route to host", "network is unreachable")):
        return ProbeStatus.UNREACHABLE
    if "timed out" in lowered or "timeout" in lowered:
        return ProbeStatus.TIMEOUT
    return ProbeStatus.ERROR


async def _run(cmd: list[str], timeout: float, *, capture: bool) -> tuple[int, bytes, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE if capture else asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise
    return proc.returncode or 0, stdout or b"", (stderr or b"").decode(errors="ignore")


async def probe_rtsp(
    url: str,
    *,
    username: str | None = None,
    password: str | None = None,
    timeout: float = 12.0,
    capture_frame: bool = True,
) -> ProbeResult:
    """Validate and probe an RTSP stream. Never raises for connection issues."""
    if not is_valid_rtsp_url(url):
        return ProbeResult(ProbeStatus.INVALID_URL, message="Invalid RTSP URL")

    auth_url = build_authenticated_url(url, username, password)

    # 1) ffprobe for stream metadata (resolution / fps / codec).
    probe_cmd = [
        "ffprobe", "-v", "error", "-rtsp_transport", "tcp",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name,avg_frame_rate",
        "-of", "json", "-timeout", str(int(timeout * 1_000_000)), auth_url,
    ]
    try:
        code, out, err = await _run(probe_cmd, timeout, capture=True)
    except asyncio.TimeoutError:
        return ProbeResult(ProbeStatus.TIMEOUT, message="Connection timed out")
    except FileNotFoundError:
        return ProbeResult(ProbeStatus.ERROR, message="ffprobe not available")

    if code != 0:
        return ProbeResult(_classify_error(err), message="Could not read stream")

    width = height = None
    fps = None
    codec = None
    try:
        streams = json.loads(out).get("streams", [])
        if streams:
            s = streams[0]
            width, height = s.get("width"), s.get("height")
            codec = s.get("codec_name")
            rate = s.get("avg_frame_rate", "0/0")
            num, _, den = rate.partition("/")
            fps = round(int(num) / int(den), 2) if den and int(den) else None
    except (ValueError, ZeroDivisionError):
        pass

    frame: bytes | None = None
    if capture_frame:
        frame_cmd = [
            "ffmpeg", "-rtsp_transport", "tcp", "-i", auth_url,
            "-frames:v", "1", "-q:v", "3", "-f", "image2", "-y", "pipe:1",
        ]
        try:
            fcode, fout, _ = await _run(frame_cmd, timeout, capture=True)
            if fcode == 0 and fout:
                frame = fout
        except (asyncio.TimeoutError, FileNotFoundError):
            frame = None

    return ProbeResult(
        ProbeStatus.CONNECTED,
        width=width,
        height=height,
        fps=fps,
        codec=codec,
        frame_jpeg=frame,
        message="Connected",
    )
