from pydantic import BaseModel
from typing import List, Optional, Literal


class ImagingResult(BaseModel):
    type: str
    findings: List[str]
    explanation: Optional[str] = None


class HelpSeeking(BaseModel):
    call_999: List[str] = []
    contact_gp: List[str] = []
    contact_team: Optional[str] = None


class MedicationChange(BaseModel):
    name: str
    action: Literal["start", "stop", "increase", "decrease", "continue"]
    dose: Optional[str] = None
    explanation: Optional[str] = None
    reason_for_change: Optional[str] = None
    side_effects: Optional[str] = None
    importance: Optional[str] = None


class FollowUpItem(BaseModel):
    type: str
    when: str
    location: Optional[str] = None
    explanation: Optional[str] = None


class ExtractionResult(BaseModel):
    diagnoses: List[str]
    procedures: List[str]
    medication_changes: List[MedicationChange]
    follow_up: List[FollowUpItem]
    imaging_results: List[ImagingResult] = []
    pending_tests: List[str]
    red_flags: List[str]
    help_seeking: Optional[HelpSeeking] = None
    narrative_summary: Optional[str] = None
    diagnoses_explanation: Optional[str] = None
    procedures_explanation: Optional[str] = None
    imaging_results_explanation: Optional[str] = None
    pending_tests_explanation: Optional[str] = None
    red_flags_explanation: Optional[str] = None
    patient_instructions: Optional[str] = None
    ef_percent: Optional[int] = None
    raw_text: Optional[str] = None
    access_site: Optional[str] = None
    pci_context: Optional[str] = None
    stent_placed: bool = False
    staged_procedure: bool = False


class RuleAlert(BaseModel):
    code: str
    severity: Literal["info", "warning", "critical"]
    message: str
    suggested_question: Optional[str] = None