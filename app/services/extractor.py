import os
import json
import re
from typing import Any, Dict

from openai import OpenAI
from app.schemas import ExtractionResult

# Create OpenAI client (uses OPENAI_API_KEY from environment)
client = OpenAI()


def deidentify_text(text: str) -> str:
    """
    Very simple PHI scrubbing. You can extend with better regex later.
    This is run BEFORE the text is sent to OpenAI.
    """
    # Name line
    text = re.sub(r"(?i)name:\s*.*", "Name: <<PATIENT_NAME>>", text)

    # DOB
    text = re.sub(r"(?i)dob:\s*.*", "DOB: <<DOB>>", text)

    # NHS number (rough match)
    text = re.sub(r"\b\d{3}\s?\d{3}\s?\d{4}\b", "<<NHS_NUMBER>>", text)

    # Postcodes
    text = re.sub(r"\b[A-Z]{1,2}\d[A-Z0-9]?\s*\d[A-Z]{2}\b", "<<POSTCODE>>", text)

    # Phone numbers
    text = re.sub(r"\b0\d{9,10}\b", "<<PHONE_NUMBER>>", text)

    return text


EXTRACTOR_SYSTEM_PROMPT = """
You are CardioCoach, an NHS-trained medical text extraction engine.
Your job is to convert messy, unstructured discharge summaries into precise, structured medical data.

You MUST:
- Extract only what is explicitly stated.
- NOT hallucinate, guess, or invent missing information.
- If data is not present, leave the relevant list empty.

Use the following JSON schema exactly (do not add fields):

{
  "diagnoses": [string],
  "procedures": [string],
  "medication_changes": [
    {
      "name": string,
      "action": "start" | "stop" | "increase" | "decrease" | "continue",
      "dose": string | null
    }
  ],
  "follow_up": [
    {
      "type": string,
      "when": string,
      "location": string | null
    }
  ],
  "pending_tests": [string],
  "red_flags": [string]
}

Interpret common NHS abbreviations correctly using this glossary:
- TTO = To Take Out (discharge medications)
- DNACPR = Do Not Attempt CPR
- PCI = Percutaneous Coronary Intervention
- CCU = Coronary Care Unit
- ACS = Acute Coronary Syndrome
- OOH = Out of hours
- ECHO = Transthoracic echocardiogram
- CR = Cardiac rehabilitation

If the summary mentions Coronary Angiography or Angioplasty / PCI, list the procedure in "procedures".
"""


def extract_structured(raw_text: str) -> ExtractionResult:
    """
    Main extractor entrypoint:
    - de-identifies text
    - calls OpenAI
    - parses JSON into ExtractionResult
    """

    deid = deidentify_text(raw_text)

    user_prompt = f"""
    Discharge summary (de-identified):

    \"\"\"{deid}\"\"\"

    Return ONLY a single valid JSON object matching the schema.
    Do not include any extra text before or after the JSON.
    """

    # Use the new OpenAI client API
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )

    content = response.choices[0].message.content.strip()

    # Strip ```json ... ``` wrappers if present
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:].strip()

    try:
        data: Dict[str, Any] = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse extractor JSON: {e}\nRaw content: {content}"
        )

    for key in [
        "diagnoses",
        "procedures",
        "medication_changes",
        "follow_up",
        "pending_tests",
        "red_flags",
    ]:
        data.setdefault(key, [])

    return ExtractionResult(**data)