from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional

from app.schemas import ExtractionResult, RuleAlert
from app.services.extractor import extract_structured
from app.services.rules_engine import run_rules
from app.services.deid import deidentify_pdf, DeidentificationError


app = FastAPI(
    title="CardioCoach API",
    description="Backend for structured NHS discharge extraction + clinical rules",
    version="1.0.0",
)

# Serve static CSS + assets
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


# ----------------------------------------------------------
# FRONTEND: Patient UI
# ----------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the patient-facing UI."""
    return templates.TemplateResponse("index.html", {"request": request})


# ----------------------------------------------------------
# API MODELS
# ----------------------------------------------------------
class ProcessRequest(BaseModel):
    text: str


class ProcessResponse(BaseModel):
    extraction: ExtractionResult
    alerts: List[RuleAlert]
    explanation: Optional[str] = None
    gp_questions: Optional[List[str]] = None


# ----------------------------------------------------------
# HEALTHCHECK
# ----------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}


# ----------------------------------------------------------
# MAIN PROCESSING ROUTES
# ----------------------------------------------------------
@app.post("/process", response_model=ProcessResponse)
async def process_discharge_letter(payload: ProcessRequest):
    """
    Process a plain-text discharge letter pasted into the UI.
    """
    extraction = extract_structured(payload.text)
    alerts = run_rules(extraction)

    return ProcessResponse(
        extraction=extraction,
        alerts=alerts,
        explanation=extraction.narrative_summary,
        gp_questions=None,
    )


@app.post("/process-pdf", response_model=ProcessResponse)
async def process_discharge_pdf(file: UploadFile = File(...)):
    """
    Accept a PDF discharge letter, de-identify it, then run
    the same extraction + rules pipeline as /process.
    """
    raw_bytes = await file.read()

    try:
        clean_text = deidentify_pdf(raw_bytes)
    except DeidentificationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")

    extraction = extract_structured(clean_text)
    alerts = run_rules(extraction)

    return ProcessResponse(
        extraction=extraction,
        alerts=alerts,
        explanation=extraction.narrative_summary,
        gp_questions=None,
    )