from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class ComparisonStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    error = "error"


class StepType(str, Enum):
    info = "info"
    thinking = "thinking"
    result = "result"


@dataclass
class ReasoningStep:
    step_id: int
    job_id: str
    type: StepType
    content: str
    timestamp: datetime


@dataclass
class ComparisonJob:
    job_id: str
    session_id: str
    pdf_id_a: str
    pdf_id_b: str
    created_at: datetime
    status: ComparisonStatus = ComparisonStatus.queued
    completed_at: Optional[datetime] = None
    report_markdown: Optional[str] = None
    error_message: Optional[str] = None
    steps: List[ReasoningStep] = field(default_factory=list)
