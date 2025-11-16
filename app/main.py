
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from app.schemas import ExtractionResult, RuleAlert
from app.services.extractor import extract_structured
from app.services.rules_engine import run_rules


# ----------------------------------------------------------
# FASTAPI APP
# ----------------------------------------------------------
app = FastAPI(
    title="CardioCoach API",
    description="Backend for structured NHS discharge extraction + clinical rules",
    version="1.0.0"
)


# ----------------------------------------------------------
# REQUEST / RESPONSE MODELS
# ----------------------------------------------------------
class ProcessRequest(BaseModel):
    text: str   # raw discharge summary text


class ProcessResponse(BaseModel):
    extraction: ExtractionResult
    alerts: List[RuleAlert]
    explanation: Optional[str] = None
    gp_questions: Optional[List[str]] = None


# ----------------------------------------------------------
# HEALTH CHECK
# ----------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}


# ----------------------------------------------------------
# MAIN PIPELINE ENDPOINT
# ----------------------------------------------------------
@app.post("/process", response_model=ProcessResponse)
async def process_discharge_letter(payload: ProcessRequest):
    """
    The main backend pipeline:
    1. Structured extraction
    2. Rules engine (safety + quality checks)
    3. Explanation + GP questions will be added later
    """

    # Step 1 — Run structured extractor
    extraction = extract_structured(payload.text)

    # Step 2 — Apply cardiology safety rules
    alerts = run_rules(extraction)

    # Step 3 — Return API response
    return ProcessResponse(
        extraction=extraction,
        alerts=alerts,
        explanation=None,
        gp_questions=None,
    )