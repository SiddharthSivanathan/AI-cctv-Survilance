"""Live stream schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class LiveStreamResponse(BaseModel):
    """Everything the frontend needs to open a WebRTC (WHEP) stream."""

    camera_id: uuid.UUID
    whep_url: str
    token: str
    expires_in: int
    expires_at: datetime
