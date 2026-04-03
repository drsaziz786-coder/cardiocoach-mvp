import re
from datetime import date
from typing import List

from app.schemas import ExtractionResult, RuleAlert, MedicationChange


# Helper drug groups
ANTICOAGULANTS = [
    "apixaban", "rivaroxaban", "edoxaban", "dabigatran", "warfarin",
]

DAPT_AGENTS = [
    "clopidogrel", "ticagrelor", "prasugrel",
]

ANTIPLATELETS = [
    "clopidogrel", "ticagrelor", "prasugrel", "aspirin",
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

ECHO_SEVERE_AS_TERMS = ["severe aortic stenosis", "severe as", "critical as"]
ECHO_MODERATE_SEVERE_MR_TERMS = ["moderate mr", "severe mr", "moderate mitral regurgitation", "severe mitral regurgitation"]
PCI_TERMS = ["pci", "angioplasty", "percutaneous coronary intervention", "stent"]
ECHO_TERMS = ["echocardiogram", "echo", "tte", "toe", "transthoracic"]
ANGIO_TERMS = ["coronary angiogram", "angiography", "coronary angiography"]


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
        cardio_keywords = ["cardio", "cardiac", "pci", "post-pci", "heart", "coronary", "angio"]
        has_fu = any(
            any(kw in fu.type.lower() for kw in cardio_keywords)
            for fu in extraction.follow_up
        )

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

    # ------------------------------------------
    # Rule 7 — Stale follow-up date (warning)
    # ------------------------------------------
    today = date.today()
    date_patterns = [
        r"\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b",   # DD/MM/YYYY or DD-MM-YYYY
        r"\b(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})\b",   # YYYY-MM-DD
    ]
    for fu in extraction.follow_up:
        when_str = fu.when or ""
        parsed = None
        for pat in date_patterns:
            m = re.search(pat, when_str)
            if m:
                try:
                    g = m.groups()
                    if len(g[0]) == 4:  # YYYY-MM-DD
                        parsed = date(int(g[0]), int(g[1]), int(g[2]))
                    else:               # DD/MM/YYYY
                        parsed = date(int(g[2]), int(g[1]), int(g[0]))
                except ValueError:
                    pass
                break
        if parsed and parsed < today:
            alerts.append(
                RuleAlert(
                    code="FU_DATE_IN_PAST",
                    severity="warning",
                    message=(
                        f"A follow-up appointment ({fu.type}) appears to have a date "
                        f"that has already passed ({fu.when}). Please check with your "
                        "GP or hospital team that this is still the correct plan."
                    ),
                    suggested_question=(
                        "My follow-up appointment date looks like it has already passed "
                        "— can you check whether I still need to book this?"
                    ),
                )
            )

    # ------------------------------------------
    # Rule 8 — Dual antithrombotic (anticoagulant + DAPT agent) (critical)
    # ------------------------------------------
    active_meds = [m for m in meds if m.action != "stop"]
    has_anticoagulant = any(
        any(drug in m.name for drug in ANTICOAGULANTS) for m in active_meds
    )
    has_dapt = any(
        any(drug in m.name for drug in DAPT_AGENTS) for m in active_meds
    )
    if has_anticoagulant and has_dapt:
        alerts.append(
            RuleAlert(
                code="DUAL_ANTITHROMBOTIC",
                severity="critical",
                message=(
                    "Both a blood-thinning tablet (anticoagulant) and a DAPT agent "
                    "(e.g. clopidogrel or ticagrelor) appear to be prescribed together. "
                    "This combination significantly increases bleeding risk and requires "
                    "close monitoring."
                ),
                suggested_question=(
                    "I am on both a blood thinner and a clopidogrel-type medicine — "
                    "who should I contact if I notice unusual bruising or bleeding?"
                ),
            )
        )

    # ------------------------------------------
    # Rule 9 — Triple therapy: anticoagulant + 2 antiplatelets (critical)
    # Defence-in-depth: catches cases where Layer 1 prompt did not flag this
    # ------------------------------------------
    active_antiplatelet_count = sum(
        1 for m in active_meds
        if any(drug in m.name for drug in ANTIPLATELETS)
    )
    if has_anticoagulant and active_antiplatelet_count >= 2:
        alerts.append(
            RuleAlert(
                code="TRIPLE_THERAPY",
                severity="critical",
                message=(
                    "You appear to be on triple therapy: a blood-thinning tablet "
                    "(anticoagulant) plus two antiplatelet medicines. This combination "
                    "carries a high risk of serious bleeding and requires close monitoring "
                    "by your cardiac team."
                ),
                suggested_question=(
                    "I am on a blood thinner and two antiplatelet medicines at the same "
                    "time — how long should I stay on all three, and what bleeding signs "
                    "should I watch for?"
                ),
            )
        )

    # ------------------------------------------
    # Rule 10 (was 9) — Polypharmacy (≥6 active medicines) (info)
    # ------------------------------------------
    active_count = len(active_meds)
    if active_count >= 6:
        alerts.append(
            RuleAlert(
                code="POLYPHARMACY",
                severity="info",
                message=(
                    f"{active_count} medicines have been identified on your discharge "
                    "letter. Having many medicines increases the chance of interactions "
                    "or side effects. Ask your GP or pharmacist for a medicines review."
                ),
                suggested_question=(
                    "I have been discharged on many medicines — can I have a medicines "
                    "review with my GP or pharmacist?"
                ),
            )
        )

    # ------------------------------------------
    # Rule 11 (was 10) — Amiodarone started without monitoring plan (warning)
    # ------------------------------------------
    amiodarone_started = any(
        "amiodarone" in m.name and m.action in ("start", "continue")
        for m in active_meds
    )
    if amiodarone_started:
        monitoring_kws = ["thyroid", "liver", "tfts", "lft", "chest", "cxr", "amiodarone", "monitor"]
        has_monitoring_fu = any(
            any(kw in fu.type.lower() for kw in monitoring_kws)
            for fu in extraction.follow_up
        )
        has_monitoring_pending = any(
            any(kw in t.lower() for kw in monitoring_kws)
            for t in extraction.pending_tests
        )
        if not has_monitoring_fu and not has_monitoring_pending:
            alerts.append(
                RuleAlert(
                    code="AMIODARONE_NO_MONITORING",
                    severity="warning",
                    message=(
                        "Amiodarone is prescribed but no monitoring plan (thyroid function, "
                        "liver tests, or chest X-ray) was identified in the follow-up. "
                        "Long-term amiodarone requires regular blood and imaging checks."
                    ),
                    suggested_question=(
                        "I have been started on amiodarone — what monitoring blood tests "
                        "and checks do I need, and how often?"
                    ),
                )
            )

    # ------------------------------------------
    # Rule 12 — PCI documented but no driving advice (critical)
    # ------------------------------------------
    if any(term in procedures_text for term in PCI_TERMS):
        driving_mentioned = any(
            word in (extraction.patient_instructions or "").lower()
            for word in ["drive", "driving", "dvla", "licence", "license"]
        )
        if not driving_mentioned:
            alerts.append(RuleAlert(
                code="R12_PCI_NO_DRIVING_ADVICE",
                severity="critical",
                message=(
                    "PCI documented but no driving instructions found. "
                    "Group 1: 1 week elective / 4 weeks post-MI. "
                    "Group 2: DVLA notification required."
                ),
                suggested_question=(
                    "What are the driving restrictions after my heart procedure, "
                    "and do I need to contact the DVLA?"
                ),
            ))

    # ------------------------------------------
    # Rule 13 — PCI documented but not-a-cure statement absent (critical)
    # ------------------------------------------
    if any(term in procedures_text for term in PCI_TERMS):
        cure_mentioned = any(
            phrase in (extraction.narrative_summary or "").lower()
            for phrase in ["not a cure", "patch, not a cure", "new blockages", "lifestyle changes"]
        )
        if not cure_mentioned:
            alerts.append(RuleAlert(
                code="R13_PCI_NO_CURE_STATEMENT",
                severity="critical",
                message=(
                    "PCI documented but 'stent is not a cure' statement absent. "
                    "Mandatory closing statement for all PCI outputs."
                ),
                suggested_question=(
                    "Does having a stent mean my heart disease is cured, "
                    "or do I still need to take my medications?"
                ),
            ))

    # ------------------------------------------
    # Rule 14 — Echo EF ≤35% but no medication warning (critical)
    # ------------------------------------------
    if extraction.ef_percent is not None and extraction.ef_percent <= 35:
        medication_warning = any(
            phrase in (extraction.narrative_summary or "").lower()
            for phrase in ["essential", "life-support", "protect your heart muscle",
                           "every day", "do not stop"]
        )
        if not medication_warning:
            alerts.append(RuleAlert(
                code="R14_LOW_EF_NO_MED_WARNING",
                severity="critical",
                message=(
                    f"Echo EF ≤35% ({extraction.ef_percent}%) documented but essential "
                    "medication warning absent."
                ),
                suggested_question=(
                    "Why are my heart medications so important given my heart "
                    "pumping function result?"
                ),
            ))

    # ------------------------------------------
    # Rule 15 — Severe AS but no specialist review message (critical)
    # ------------------------------------------
    imaging_text = " ".join(
        " ".join(ir.findings) for ir in extraction.imaging_results
    ).lower()
    if any(term in imaging_text for term in ECHO_SEVERE_AS_TERMS):
        specialist_mentioned = any(
            phrase in (extraction.narrative_summary or "").lower()
            for phrase in ["specialist", "valve replacement", "valve repair",
                           "discuss", "tavi", "avr"]
        )
        if not specialist_mentioned:
            alerts.append(RuleAlert(
                code="R15_SEVERE_AS_NO_SPECIALIST",
                severity="critical",
                message=(
                    "Severe aortic stenosis documented but no specialist review "
                    "or valve intervention discussion present."
                ),
                suggested_question=(
                    "My echo showed a severely narrowed heart valve — what does "
                    "this mean and will I need an operation?"
                ),
            ))

    # ------------------------------------------
    # Rule 16 — Moderate or severe MR but no follow-up message (warning)
    # ------------------------------------------
    if any(term in imaging_text for term in ECHO_MODERATE_SEVERE_MR_TERMS):
        fu_mentioned = any(
            phrase in (extraction.narrative_summary or "").lower()
            for phrase in ["specialist", "review", "monitor", "repair",
                           "surgery", "intervention", "extra work"]
        )
        if not fu_mentioned:
            alerts.append(RuleAlert(
                code="R16_SIGNIFICANT_MR_NO_FU",
                severity="warning",
                message=(
                    "Moderate or severe mitral regurgitation documented but no "
                    "specialist review or monitoring message present."
                ),
                suggested_question=(
                    "My echo showed a leaky heart valve — what does this mean "
                    "for my long-term care?"
                ),
            ))

    # ------------------------------------------
    # Rule 17 — PCI + cardiac rehab in letter but missing from output (warning)
    # ------------------------------------------
    if any(term in procedures_text for term in PCI_TERMS):
        rehab_in_letter = any(
            phrase in (extraction.raw_text or "").lower()
            for phrase in ["cardiac rehab", "cardiac rehabilitation", "rehab referral"]
        )
        rehab_in_output = any(
            phrase in (extraction.narrative_summary or "").lower()
            for phrase in ["rehab", "rehabilitation", "maintenance programme"]
        )
        if rehab_in_letter and not rehab_in_output:
            alerts.append(RuleAlert(
                code="R17_PCI_REHAB_NOT_MENTIONED",
                severity="warning",
                message=(
                    "Cardiac rehabilitation referral in discharge letter "
                    "but not included in CardioCoach output."
                ),
                suggested_question=(
                    "I was referred to cardiac rehabilitation — what is it "
                    "and should I attend?"
                ),
            ))

    # ------------------------------------------
    # Rule 18 — Echo documented but EF not extracted (info)
    # ------------------------------------------
    if any(term in imaging_text for term in ECHO_TERMS):
        if extraction.ef_percent is None:
            alerts.append(RuleAlert(
                code="R18_ECHO_NO_EF",
                severity="info",
                message=(
                    "Echocardiogram documented but ejection fraction not extracted. "
                    "Check source letter — EF may be present and was missed."
                ),
                suggested_question=(
                    "What did my heart scan show about how well my heart is pumping?"
                ),
            ))

    # ------------------------------------------
    # Rule 19 — Femoral access documented but no groin site instructions (warning)
    # ------------------------------------------
    if any(term in procedures_text for term in ANGIO_TERMS):
        femoral = "femoral" in procedures_text
        site_advice = any(
            phrase in (extraction.patient_instructions or "").lower()
            for phrase in ["groin", "femoral", "pseudoaneurysm", "lump", "tender"]
        )
        if femoral and not site_advice:
            alerts.append(RuleAlert(
                code="R19_FEMORAL_NO_SITE_ADVICE",
                severity="warning",
                message=(
                    "Femoral access documented but no groin site instructions "
                    "or pseudoaneurysm warning present."
                ),
                suggested_question=(
                    "What should I watch for at the site where the procedure "
                    "was performed in my groin?"
                ),
            ))

    return alerts