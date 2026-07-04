"""FFmpeg frame sampler.

Reads a camera's stream from MediaMTX (internal RTSP) at the configured sample
FPS, resizes to 640x640, and pushes JPEG frames onto the shared Redis frames
stream. Runs in a background thread with automatic reconnect.
"""

from __future__ import annotations

import subprocess
import threading
import time

import redis
import structlog

from src.config import get_settings
from src.redis_streams import FRAMES_STREAM

logger = structlog.get_logger("sampler")

_SOI = b"\xff\xd8"  # JPEG start-of-image
_EOI = b"\xff\xd9"  # JPEG end-of-image


class FrameSampler:
    def __init__(self, camera_id: str, sample_fps: int, client: redis.Redis) -> None:
        self.camera_id = camera_id
        self.sample_fps = sample_fps
        self._client = client
        self._settings = get_settings()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._proc: subprocess.Popen | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name=f"sampler-{self.camera_id}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    def _ffmpeg_command(self) -> list[str]:
        source = f"{self._settings.mediamtx_rtsp_url.rstrip('/')}/{self.camera_id}"
        imgsz = self._settings.model_imgsz
        return [
            "ffmpeg", "-rtsp_transport", "tcp", "-i", source,
            "-vf", f"fps={self.sample_fps},scale={imgsz}:{imgsz}",
            "-f", "image2pipe", "-vcodec", "mjpeg", "-q:v", "5", "pipe:1",
        ]

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self._proc = subprocess.Popen(  # noqa: S603
                    self._ffmpeg_command(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                self._read_frames(self._proc.stdout)
            except FileNotFoundError:
                logger.error("ffmpeg_not_found")
                return
            except Exception as exc:  # noqa: BLE001 - keep the sampler alive
                logger.warning("sampler_error", camera_id=self.camera_id, error=str(exc))
            if not self._stop.is_set():
                time.sleep(2)  # backoff before reconnect

    def _read_frames(self, stdout) -> None:
        buffer = bytearray()
        while not self._stop.is_set():
            chunk = stdout.read(4096)
            if not chunk:
                return  # process ended; caller reconnects
            buffer.extend(chunk)
            # Extract every complete JPEG in the buffer.
            while True:
                start = buffer.find(_SOI)
                end = buffer.find(_EOI, start + 2)
                if start == -1 or end == -1:
                    break
                frame = bytes(buffer[start : end + 2])
                del buffer[: end + 2]
                self._publish(frame)

    def _publish(self, frame: bytes) -> None:
        try:
            self._client.xadd(
                FRAMES_STREAM,
                {"camera_id": self.camera_id, "ts": str(time.time()), "frame": frame},
                maxlen=self._settings.frames_stream_maxlen,
                approximate=True,
            )
        except redis.RedisError as exc:
            logger.warning("frame_publish_failed", camera_id=self.camera_id, error=str(exc))
