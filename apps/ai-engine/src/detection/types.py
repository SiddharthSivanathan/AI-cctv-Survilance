"""Detection value objects shared across the detection pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Detection:
    """A single object detection (optionally with a tracking id)."""

    class_id: int
    class_name: str
    confidence: float
    # Pixel coordinates in the (resized) frame: x1, y1, x2, y2.
    bbox: tuple[float, float, float, float]
    track_id: int | None = None

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "bbox": [round(v, 2) for v in self.bbox],
            "track_id": self.track_id,
        }

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
