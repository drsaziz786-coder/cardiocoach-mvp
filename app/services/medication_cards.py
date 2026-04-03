# CardioCoach — Medication Knowledge Cards
# File: app/services/medication_cards.py
#
# Pre-approved plain-English explanation templates for common cardiology
# discharge medicines. Built from BNF, NHS medicines A-Z, and cardiology
# discharge practice at North Bristol NHS Trust.
#
# Usage: reference in EXTRACTOR_SYSTEM_PROMPT as approved scaffolding.
# The LLM personalises from these cards — it does not generate from scratch.
# Cards are versioned with the prompt layer and git-tagged at prototype lock.
#
# Version: 1.0-pre-lock | March 2026

MEDICATION_CARDS = {

    # ── ANTIPLATELETS ─────────────────────────────────────────────────────────

    "aspirin": {
        "class": "Antiplatelet",
        "purpose": "Helps prevent blood clots forming in your heart arteries.",
        "duration_logic": "This medicine is usually lifelong after a heart attack or stent.",
        "top_warning": (
            "Do not stop this medicine without speaking to your cardiologist first. "
            "Stopping suddenly after a stent can be life-threatening."
        ),
        "side_effects": "Can irritate the stomach. Take with or after food.",
        "missed_dose": "If you miss a dose, take it as soon as you remember. "
                       "Do not double up.",
        "must_preserve": ["lifelong", "do not stop", "stent context if applicable"],
    },

    "clopidogrel": {
        "class": "Antiplatelet",
        "purpose": (
            "Works with aspirin to prevent blood clots, especially important "
            "after a stent procedure."
        ),
        "duration_logic": (
            "Usually taken for 12 months after a stent, or as directed by "
            "your cardiologist. Your letter should state how long."
        ),
        "top_warning": (
            "Do not stop this medicine without speaking to your cardiologist "
            "first — stopping suddenly after a stent can be life-threatening."
        ),
        "side_effects": "May cause easy bruising or bleeding. Tell your doctor "
                        "before any procedure, dental work, or operation.",
        "missed_dose": "Take as soon as you remember, unless it is nearly time "
                       "for your next dose.",
        "must_preserve": [
            "do not stop", "duration if stated", "stent context", "DAPT context"
        ],
    },

    "ticagrelor": {
        "class": "Antiplatelet",
        "purpose": (
            "Prevents blood clots forming in your heart arteries. "
            "Often used alongside aspirin after a heart attack or stent."
        ),
        "duration_logic": "Usually taken for 12 months after a heart attack or stent.",
        "top_warning": (
            "Do not stop without speaking to your cardiologist first — "
            "stopping suddenly after a stent can be life-threatening. "
            "Do not take more than 100mg of aspirin daily while on ticagrelor."
        ),
        "side_effects": (
            "Some people notice shortness of breath, especially at rest early on — "
            "this usually settles. May cause easy bruising or bleeding."
        ),
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": [
            "do not stop", "aspirin dose limit 100mg", "duration if stated"
        ],
    },

    "prasugrel": {
        "class": "Antiplatelet",
        "purpose": "Prevents blood clots, used after a stent procedure.",
        "duration_logic": "Usually taken for 12 months after a stent.",
        "top_warning": (
            "Do not stop without speaking to your cardiologist first. "
            "Higher bleeding risk than other antiplatelets — tell any doctor, "
            "dentist, or nurse before any procedure."
        ),
        "side_effects": "May cause easy bruising or bleeding.",
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": ["do not stop", "duration if stated", "bleeding risk"],
    },

    # ── ANTICOAGULANTS ────────────────────────────────────────────────────────

    "apixaban": {
        "class": "Anticoagulant (blood thinner)",
        "purpose": (
            "Reduces your risk of stroke. This is important because your heart "
            "rhythm (atrial fibrillation) increases stroke risk."
        ),
        "duration_logic": "Usually taken long-term for AF.",
        "top_warning": (
            "Tell any doctor, dentist, or nurse that you are taking this before "
            "any procedure or operation. Do not stop without medical advice."
        ),
        "side_effects": (
            "May cause bruising or bleeding more easily. "
            "Seek urgent help if you notice unusual bleeding that will not stop, "
            "blood in your urine, or vomiting blood."
        ),
        "missed_dose": (
            "Take as soon as you remember on the same day. "
            "Do not take two doses in one day."
        ),
        "must_preserve": [
            "tell before procedures", "indication (AF or other)", "do not stop"
        ],
    },

    "rivaroxaban": {
        "class": "Anticoagulant (blood thinner)",
        "purpose": "Reduces your risk of stroke or blood clots.",
        "duration_logic": "Usually long-term for AF. Take with food.",
        "top_warning": (
            "Tell any doctor, dentist, or nurse before any procedure. "
            "Do not stop without medical advice."
        ),
        "side_effects": "May cause bruising or bleeding. Seek help for unusual bleeding.",
        "missed_dose": "Take as soon as you remember on the same day.",
        "must_preserve": ["tell before procedures", "take with food", "indication"],
    },

    "edoxaban": {
        "class": "Anticoagulant (blood thinner)",
        "purpose": "Reduces your risk of stroke in atrial fibrillation.",
        "duration_logic": "Usually long-term.",
        "top_warning": (
            "Tell any doctor, dentist, or nurse before any procedure. "
            "Do not stop without medical advice."
        ),
        "side_effects": "May cause easier bruising or bleeding.",
        "missed_dose": "Take as soon as you remember on the same day.",
        "must_preserve": ["tell before procedures", "indication"],
    },

    "warfarin": {
        "class": "Anticoagulant (blood thinner)",
        "purpose": "Reduces your risk of stroke or blood clots.",
        "duration_logic": "Usually long-term. Dose adjusted by regular blood tests (INR).",
        "top_warning": (
            "You need regular blood tests to check your dose is correct. "
            "Many medicines and foods can affect warfarin — always tell any "
            "prescriber you are taking it. Do not stop without medical advice."
        ),
        "side_effects": "May cause easier bruising. Seek help for unusual bleeding.",
        "missed_dose": "Contact your anticoagulation clinic if you miss a dose.",
        "must_preserve": ["INR monitoring", "tell before procedures", "interactions"],
    },

    # ── RATE/RHYTHM ───────────────────────────────────────────────────────────

    "bisoprolol": {
        "class": "Beta-blocker",
        "purpose": (
            "Controls your heart rate and protects your heart muscle. "
            "NOT primarily for blood pressure."
        ),
        "duration_logic": "Usually long-term.",
        "top_warning": (
            "Do not stop suddenly — this can cause your heart rate to increase "
            "rapidly. Always reduce gradually with your doctor's guidance."
        ),
        "side_effects": (
            "May cause tiredness or cold hands and feet, especially at first. "
            "Tell your doctor if you develop wheeze or breathing problems."
        ),
        "missed_dose": "Take as soon as you remember, unless nearly time for next dose.",
        "must_preserve": ["do not stop suddenly", "heart rate not blood pressure"],
    },

    "amiodarone": {
        "class": "Antiarrhythmic",
        "purpose": "Helps control your heart rhythm.",
        "duration_logic": (
            "May be started at a higher dose (loading) then reduced. "
            "Your letter should state the current dose and plan."
        ),
        "top_warning": (
            "This medicine can affect your thyroid gland, lungs, liver, and eyes "
            "if taken long-term. You will need regular blood tests and check-ups "
            "to monitor this. Tell any doctor you are taking amiodarone before "
            "any new medicine is prescribed — it interacts with many drugs."
        ),
        "side_effects": (
            "Skin may become more sensitive to sunlight — use sunscreen. "
            "May cause nausea, especially at higher doses."
        ),
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": [
            "monitoring plan", "loading dose context if applicable", "interactions"
        ],
    },

    # ── HEART FAILURE QUADRUPLE THERAPY ───────────────────────────────────────

    "ramipril": {
        "class": "ACE inhibitor",
        "purpose": (
            "Protects your heart muscle and helps it pump more efficiently. "
            "Also reduces the risk of further heart attacks."
        ),
        "duration_logic": "Usually long-term.",
        "top_warning": (
            "Do not take anti-inflammatory painkillers (like ibuprofen or "
            "naproxen) without speaking to your doctor. "
            "Stop and seek advice if you develop facial swelling or a persistent cough."
        ),
        "side_effects": (
            "A dry cough is common. If troublesome, tell your doctor — "
            "there are alternatives."
        ),
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": ["heart protection not just BP", "cough side effect"],
    },

    "sacubitril_valsartan": {
        "class": "ARNI (angiotensin receptor-neprilysin inhibitor)",
        "purpose": (
            "Helps your heart pump more effectively and reduces your risk of "
            "being admitted to hospital with heart failure."
        ),
        "duration_logic": "Long-term.",
        "top_warning": (
            "Do NOT take with an ACE inhibitor (such as ramipril or lisinopril) "
            "— this combination is dangerous. Leave at least 36 hours between "
            "stopping an ACE inhibitor and starting this medicine. "
            "Tell any doctor you are taking it before any new prescription."
        ),
        "side_effects": "May cause dizziness, especially when standing up quickly.",
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": ["no ACE inhibitor", "36-hour washout", "replaces ACEi"],
    },

    "dapagliflozin": {
        "class": "SGLT2 inhibitor",
        "purpose": (
            "Reduces the strain on your heart and lowers your risk of being "
            "admitted to hospital with heart failure. Also protects your kidneys. "
            "Take every day even if you feel well."
        ),
        "duration_logic": "Long-term.",
        "top_warning": (
            "Stop this medicine and seek urgent advice if you become unwell, "
            "are vomiting, or are not eating — particularly if you have diabetes. "
            "Do not describe as a diabetes medicine unless diabetes is confirmed "
            "in the letter."
        ),
        "side_effects": (
            "May increase the risk of genital yeast infections. "
            "Drink plenty of fluids."
        ),
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": [
            "heart and kidney protection", "not just diabetes", "take every day"
        ],
    },

    "empagliflozin": {
        "class": "SGLT2 inhibitor",
        "purpose": (
            "Reduces the strain on your heart and protects your kidneys. "
            "Take every day even if you feel well."
        ),
        "duration_logic": "Long-term.",
        "top_warning": (
            "Stop if you become unwell or are not eating. "
            "Not primarily a diabetes medicine in this context unless stated."
        ),
        "side_effects": "May increase risk of genital infections.",
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": ["heart and kidney", "take every day"],
    },

    "eplerenone": {
        "class": "Mineralocorticoid receptor antagonist (MRA)",
        "purpose": (
            "Helps your heart work more efficiently and reduces fluid build-up. "
            "Protects the heart muscle."
        ),
        "duration_logic": "Long-term.",
        "top_warning": (
            "Your kidney function and potassium levels need to be checked "
            "regularly while you take this medicine. "
            "Avoid potassium supplements or salt substitutes unless advised."
        ),
        "side_effects": "May cause raised potassium — this is why blood tests are needed.",
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": ["potassium monitoring", "link to U+E blood test if present"],
    },

    "spironolactone": {
        "class": "Mineralocorticoid receptor antagonist (MRA)",
        "purpose": "Helps your heart and reduces fluid build-up.",
        "duration_logic": "Long-term.",
        "top_warning": (
            "Kidney function and potassium levels need regular monitoring. "
            "Can cause breast tenderness in men."
        ),
        "side_effects": "May cause raised potassium and breast tenderness.",
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": ["potassium monitoring"],
    },

    # ── DIURETICS ─────────────────────────────────────────────────────────────

    "furosemide": {
        "class": "Loop diuretic (water tablet)",
        "purpose": "Removes excess fluid from your body.",
        "duration_logic": "May be short-term or long-term depending on your condition.",
        "top_warning": (
            "Weigh yourself every morning before eating or drinking. "
            "If your weight goes up by more than 2kg in 2 days, "
            "contact your GP or heart failure team — fluid may be building up again."
        ),
        "side_effects": (
            "You will pass more urine, especially in the first few hours after taking it. "
            "Take in the morning to avoid being up at night."
        ),
        "missed_dose": "Take as soon as you remember, but not late in the day.",
        "must_preserve": ["weight monitoring", "morning dosing advice"],
    },

    "bumetanide": {
        "class": "Loop diuretic (water tablet)",
        "purpose": "Removes excess fluid from your body.",
        "duration_logic": "As directed.",
        "top_warning": (
            "Weigh yourself every morning. If weight increases by more than "
            "2kg in 2 days, contact your GP or heart failure team."
        ),
        "side_effects": "Increased urine, especially after taking it.",
        "missed_dose": "Take as soon as you remember, not late in the day.",
        "must_preserve": ["weight monitoring"],
    },

    # ── STATINS ───────────────────────────────────────────────────────────────

    "atorvastatin": {
        "class": "Statin",
        "purpose": (
            "Protects your heart and reduces your risk of another heart attack. "
            "Also lowers your cholesterol."
        ),
        "duration_logic": "Lifelong after a heart attack or stent.",
        "top_warning": (
            "Tell your doctor immediately if you develop unexplained muscle pain, "
            "weakness, or dark urine — rare but important side effect."
        ),
        "side_effects": "Most people tolerate this well. Muscle aches are uncommon but worth reporting.",
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": [
            "heart protection not just cholesterol", "post-ACS context", "lifelong"
        ],
    },

    "rosuvastatin": {
        "class": "Statin",
        "purpose": "Protects your heart and lowers cholesterol.",
        "duration_logic": "Usually lifelong.",
        "top_warning": "Report unexplained muscle pain or weakness to your doctor.",
        "side_effects": "Generally well tolerated.",
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": ["heart protection", "post-ACS if applicable"],
    },

    # ── NITRATES / SYMPTOMATIC ────────────────────────────────────────────────

    "gtn_spray": {
        "class": "Nitrate (GTN spray)",
        "purpose": "Relieves chest pain quickly.",
        "duration_logic": "Use when needed. Not a regular daily medicine.",
        "top_warning": (
            "If your chest pain is not relieved after two sprays two minutes apart, "
            "call 999 immediately — do not wait."
        ),
        "side_effects": "May cause headache or dizziness — sit down after using.",
        "missed_dose": "Not applicable — use when needed.",
        "must_preserve": ["999 if two sprays fail", "sit down after use"],
    },

    "isosorbide_mononitrate": {
        "class": "Nitrate",
        "purpose": "Helps prevent chest pain (angina) by widening blood vessels.",
        "duration_logic": "Take as directed. Leave a nitrate-free period each day if on twice-daily dosing.",
        "top_warning": (
            "May cause headaches, especially at first. "
            "Do not take with medicines for erectile dysfunction (sildenafil, tadalafil) "
            "— this combination can cause a dangerous drop in blood pressure."
        ),
        "side_effects": "Headache (usually settles), flushing, dizziness.",
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": ["no PDE5 inhibitors", "nitrate-free period if bd"],
    },

    # ── GASTROPROTECTION ──────────────────────────────────────────────────────

    "lansoprazole": {
        "class": "Proton pump inhibitor (PPI)",
        "purpose": "Protects your stomach, especially while taking blood-thinning medicines.",
        "duration_logic": "Usually continued as long as you are on antiplatelets or anticoagulants.",
        "top_warning": None,
        "side_effects": "Generally well tolerated.",
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": ["link to antiplatelet/anticoagulant context"],
    },

    "omeprazole": {
        "class": "Proton pump inhibitor (PPI)",
        "purpose": "Protects your stomach lining.",
        "duration_logic": "Continue as directed.",
        "top_warning": (
            "Note: if taking clopidogrel, omeprazole may reduce its effectiveness. "
            "Lansoprazole or pantoprazole are preferred alternatives — flag for review."
        ),
        "side_effects": "Generally well tolerated.",
        "missed_dose": "Take as soon as you remember.",
        "must_preserve": ["clopidogrel interaction flag"],
    },

}

# ── PROMPT INTEGRATION ────────────────────────────────────────────────────────
# Add this to EXTRACTOR_SYSTEM_PROMPT after MEDICATION EXPLANATION RULES:

MEDICATION_CARDS_PROMPT_SECTION = """
MEDICATION KNOWLEDGE CARDS — use these as approved scaffolding:

For each medicine change in the discharge letter, check whether a pre-approved
knowledge card exists. If it does, personalise from the card rather than generating
from scratch. The card provides the approved purpose, key warning, and must-preserve
items. You add the patient-specific context (why this patient needs it, what changed,
the specific dose, and any letter-specific instructions).

Key cards available: aspirin, clopidogrel, ticagrelor, prasugrel, apixaban,
rivaroxaban, edoxaban, warfarin, bisoprolol, amiodarone, ramipril,
sacubitril/valsartan (Entresto), dapagliflozin, empagliflozin, eplerenone,
spironolactone, furosemide, bumetanide, atorvastatin, rosuvastatin,
GTN spray, isosorbide mononitrate, lansoprazole, omeprazole.

For any medicine NOT in this list: generate from BNF-consistent principles —
state purpose, key warning, and any monitoring requirement. Do not guess.

MEDICATION EXPLANATION FORMAT (use for every new or changed medicine):
- What it is for (one sentence, patient-specific where possible)
- What changed: STARTED / STOPPED / DOSE CHANGED / CONTINUING
- How to take it (dose, frequency, timing — from the letter)
- How long (if time-limited — state this explicitly)
- Most important warning (from card or BNF-consistent)
- What to watch for / when to seek help (if relevant)
"""
