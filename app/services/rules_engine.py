from typing import List

from app.schemas import ExtractionResult, RuleAlert, MedicationChange


# Helper drug groups
ANTICOAGULANTS = [
    "apixaban", "rivaroxaban", "edoxaban", "dabigatran", "warfarin",
]

ACE_ARB_ARNI = [
    "ramipril", "lisinopril", "perindopril", "enalapril",
    "losartan", "candesartan", "valsartan",
    "sacubitril",  # sacubitril/valsartan (Entresto)
]

BETA_BLOCKERS = [
    "bisoprolol", "carvedilol", "metoprolol", "nebivolol",
]

STATINS = [
    "atorvastatin", "rosuvastatin", "simvastatin", "pravastatin",
]


def _lower_meds(meds: List[MedicationChange]) -> List[MedicationChange]:
    """normalize medication names for safer comparison"""
    for m in meds:
        m.name = m.name.lower()
    return meds


def run_rules(extraction: ExtractionResult) -> List[RuleAlert]:
    alerts: List[RuleAlert] = []

    diagnoses_text = " ".join(extraction.diagnoses).lower()
    procedures_text = " ".join(extraction.procedures).lower()
    meds = _lower_meds(extraction.medication_changes)

    # ------------------------------------------
    # Rule 1 — AF + anticoagulant stopped (critical)
    # ------------------------------------------
    if "atrial fibrillation" in diagnoses_text or "af" in diagnoses_text:
        stopped_thinner = [
            m for m in meds
            if m.action == "stop" and any(drug in m.name for drug in ANTICOAGULANTS)
        ]
        if stopped_thinner:
            alerts.append(
                RuleAlert(
                    code="AF_AC_STOPPED",
                    severity="critical",
                    message=(
                        "Anticoagulant appears to have been stopped in a patient with "
                        "atrial fibrillation. This may increase stroke risk and should "
                        "be reviewed urgently."
                    ),
                    suggested_question=(
                        "My blood thinner seems to have been stopped even though I have "
                        "atrial fibrillation. Is this safe?"
                    ),
                )
            )

    # ------------------------------------------
    # Rule 2 — MI/ACS + no cardiology follow-up (warning)
    # ------------------------------------------
    if any(term in diagnoses_text for term in ["mi", "myocardial infarction", "acs"]):
        has_fu = any("cardio" in fu.type.lower() for fu in extraction.follow_up)

        if not has_fu:
            alerts.append(
                RuleAlert(
                    code="MI_NO_CARDIO_FU",
                    severity="warning",
                    message=(
                        "A heart attack / ACS is documented but no cardiology clinic "
                        "follow-up was found."
                    ),
                    suggested_question=(
                        "Should I have a follow-up appointment with a cardiologist?"
                    ),
                )
            )

        # ------------------------------------------
        # Rule 3 — MI + no statin
        # ------------------------------------------
        has_statin = any(
            any(statin in m.name for statin in STATINS)
            for m in meds
        )
        if not has_statin:
            alerts.append(
                RuleAlert(
                    code="MI_NO_STATIN",
                    severity="warning",
                    message=(
                        "A heart attack / ACS is documented but no statin medication "
                        "was identified."
                    ),
                    suggested_question=(
                        "Should I be on a statin to reduce my risk after a heart attack?"
                    ),
                )
            )

    # ------------------------------------------
    # Rule 4 — HF + incomplete therapy (ACE/ARB/ARNI + BB)
    # ------------------------------------------
    if "heart failure" in diagnoses_text or "hf" in diagnoses_text:
        has_ace_arb_arni = any(
            any(drug in m.name for drug in ACE_ARB_ARNI)
            for m in meds
        )
        has_beta_blocker = any(
            any(bb in m.name for bb in BETA_BLOCKERS)
            for m in meds
        )

        if not (has_ace_arb_arni and has_beta_blocker):
            alerts.append(
                RuleAlert(
                    code="HF_INCOMPLETE_THERAPY",
                    severity="warning",
                    message=(
                        "Heart failure is documented but guideline-standard medications "
                        "(ACEi/ARB/ARNI and beta-blocker) are not clearly present."
                    ),
                    suggested_question=(
                        "Are my heart failure medications complete?"
                    ),
                )
            )

    # ------------------------------------------
    # Rule 5 — Acute diagnosis but no red-flag advice (info)
    # ------------------------------------------
    acute_terms = ["mi", "myocardial infarction", "hf", "heart failure",
                   "pneumonia", "pulmonary embolism", "stroke", "tia"]

    if any(term in diagnoses_text for term in acute_terms) and not extraction.red_flags:
        alerts.append(
            RuleAlert(
                code="NO_REDFLAG_ADVICE",
                severity="info",
                message=(
                    "An acute illness is documented but no red-flag safety advice "
                    "was identified."
                ),
                suggested_question="What symptoms mean I should seek urgent help?",
            )
        )

    # ------------------------------------------
    # Rule 6 — PCI but no DAPT/wound follow-up (info)
    # ------------------------------------------
    if any(term in procedures_text for term in ["pci", "angioplasty"]):
        has_dapt_or_wound_fu = any(
            any(keyword in fu.type.lower() for keyword in
                ["wound", "stent", "site", "dapt", "dual antiplatelet"])
            for fu in extraction.follow_up
        )

        if not has_dapt_or_wound_fu:
            alerts.append(
                RuleAlert(
                    code="PCI_NO_DAPT_PLAN",
                    severity="info",
                    message=(
                        "PCI / angioplasty is documented but no plan for DAPT duration "
                        "or wound review was found."
                    ),
                    suggested_question=(
                        "How long should I stay on both blood thinners after my stent?"
                    ),
                )
            )

    return alerts