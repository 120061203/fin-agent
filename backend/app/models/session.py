from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class SessionStatus(str, Enum):
    active = "active"
    expired = "expired"
    cleaned = "cleaned"


@dataclass
class Session:
    session_id: str
    created_at: datetime
    last_active_at: datetime
    upload_dir: str
    status: SessionStatus = SessionStatus.active

    @property
    def expires_at(self) -> datetime:
        return self.last_active_at + timedelta(minutes=30)

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
