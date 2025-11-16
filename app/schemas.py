from pydantic import BaseModel
from typing import List, Optional, Literal


class MedicationChange(BaseModel):
    name: str
    action: Literal["start", "stop", "increase", "decrease", "continue"]
    dose: Optional[str] = None


class FollowUpItem(BaseModel):
    type: str
    when: str
    location: Optional[str] = None


class ExtractionResult(BaseModel):
    diagnoses: List[str]
    procedures: List[str]
    medication_changes: List[MedicationChange]
    follow_up: List[FollowUpItem]
    pending_tests: List[str]
    red_flags: List[str]


class RuleAlert(BaseModel):
    code: str
    severity: Literal["info", "warning", "critical"]
    message: str
    suggested_question: Optional[str] = None