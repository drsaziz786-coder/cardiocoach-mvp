# CardioCoach — Investigation Knowledge Cards
# File: app/services/investigation_cards.py
#
# Pre-approved plain-English explanation templates for common cardiology
# investigations and monitoring tests. Built to mirror the structure of
# medication_cards.py and integrated in the same way via the extractor prompt.
#
# Usage: reference in EXTRACTOR_SYSTEM_PROMPT as approved scaffolding.
# The LLM personalises from these cards — it does not generate from scratch.
# Cards are versioned with the prompt layer and git-tagged at prototype lock.
#
# Version: 1.0-pre-lock | April 2026

"""
investigation_cards.py
CardioCoach — Investigation Knowledge Cards
Mirrors the structure of medication_cards.py.
Each card is a flat dict consumed by the extractor system prompt
and checked by the rules engine.
"""

# ── CORONARY ANGIOGRAM ─────────────────────────────────────────────────────

INVESTIGATION_CARDS = {

    "coronary_angiogram": {
        "procedure_name": "Coronary angiogram",
        "lay_name": "X-ray of the heart arteries",
        "what_it_shows": (
            "A coronary angiogram is an X-ray of the arteries that supply blood "
            "to your heart. Dye is injected so the arteries show up clearly, "
            "allowing the doctor to see whether there are any narrowings or "
            "blockages in the blood supply to your heart muscle."
        ),
        "findings_language": {
            "normal": (
                "Your coronary angiogram showed no significant narrowings. "
                "There is good blood flow down the main arteries to your heart muscle. "
                "This is reassuring news."
            ),
            "mild": "a mild narrowing",
            "moderate": "a moderate narrowing",
            "severe": "a severe narrowing",
            "near_total": "a very severe narrowing — nearly, but not completely, blocked",
            "total": "a complete blockage",
            "medical_management": (
                "The angiogram showed narrowings that are not causing a major restriction "
                "in blood supply to your heart muscle at this stage. Your cardiologist has "
                "decided that the best treatment is medication and lifestyle changes rather "
                "than a procedure. This is an active, planned decision."
            ),
        },
        "top_warning": (
            "Call 999 immediately if you develop chest pain similar to your admission "
            "symptoms that does not settle within 10 minutes, sudden severe shortness "
            "of breath, or loss of consciousness."
        ),
        "access_site": {
            "radial": (
                "Your procedure was performed through a small artery at your wrist. "
                "You may notice bruising or tenderness — this is normal and will settle."
            ),
            "femoral": (
                "Your procedure was performed through an artery in your groin. If you "
                "develop a persistent tender lump, spreading bruising, or any bleeding "
                "at the site, seek medical attention promptly — you may need an ultrasound "
                "to exclude a pseudoaneurysm."
            ),
        },
        "must_preserve": [
            "access site instructions (radial vs femoral)",
            "warning symptoms requiring 999",
            "vessel names must match source letter",
            "severity language must use mild/moderate/severe not raw percentages "
            "except near-total or total occlusion",
        ],
    },

    # ── PCI / CORONARY ANGIOPLASTY ─────────────────────────────────────────

    "pci": {
        "procedure_name": "Coronary angioplasty (PCI)",
        "lay_name": "Procedure to open blocked heart arteries",
        "context_language": {
            "emergency": (
                "You were having a heart attack caused by a sudden complete blockage "
                "in one of the arteries supplying your heart. The procedure — called "
                "primary PCI — was performed as an emergency to open that blocked artery "
                "and restore blood flow. This was a life-saving procedure."
            ),
            "urgent": (
                "During your admission, investigations showed that one of your heart "
                "arteries was critically narrowed and causing your symptoms. The procedure "
                "was carried out before you went home to open that narrowing and stabilise "
                "your condition."
            ),
            "elective": (
                "This procedure was planned in advance to treat a narrowing in one of "
                "your heart arteries that was causing your symptoms — most likely chest "
                "pain or breathlessness on exertion."
            ),
        },
        "stent_explanation": (
            "A stent is a small, thin metal mesh tube that is used to hold a narrowed "
            "artery open. A high-pressure balloon opened the narrowing and the stent was "
            "pushed into place against the artery wall. The balloon was removed, leaving "
            "the stent permanently in place as a scaffold. The artery wall gradually heals "
            "around the stent over the following months."
        ),
        "des_addition": (
            "Your stent is coated with a small amount of medication that is released "
            "slowly to prevent scar tissue from re-forming inside the stent. This is why "
            "your blood-thinning tablets are non-negotiable — they work together with the "
            "stent coating to keep the artery open."
        ),
        "staged_explanation": (
            "Your angiogram showed narrowings in more than one artery. The most important "
            "narrowing was treated today. Treating everything in one session would mean "
            "more X-ray time and more dye, which places extra strain on the body. You will "
            "be brought back to treat the remaining narrowings when your heart has rested. "
            "This staged approach is planned and deliberate."
        ),
        "failed_pci": (
            "During your procedure, your cardiologist attempted to open a blockage. On "
            "this occasion, the blockage was too hardened for the wire to cross safely. "
            "Your cardiologist will focus on protecting your heart with medication and may "
            "consider further options in the future. This outcome has been anticipated and "
            "your treatment plan takes it into account."
        ),
        "driving": {
            "group1_elective": (
                "You must not drive for at least 1 week after your procedure. You may "
                "return to driving when you feel well and are free from symptoms."
            ),
            "group1_post_mi": (
                "You must not drive for at least 4 weeks after your heart attack."
            ),
            "group2": (
                "If you hold a Group 2 licence (lorry, bus, or heavy goods vehicle), "
                "you must stop driving immediately and notify the DVLA. You will need a "
                "satisfactory exercise test before applying to return to Group 2 driving. "
                "Please contact your cardiologist's secretary for guidance."
            ),
        },
        "not_a_cure": (
            "A stent repairs a blockage in one part of one artery — it is not a cure "
            "for heart disease. The underlying condition that caused the blockage is still "
            "present. Without ongoing medication and lifestyle changes, new narrowings can "
            "develop elsewhere. Your medications and lifestyle changes are just as important "
            "as the stent itself."
        ),
        "top_warning": (
            "Call 999 immediately if you develop chest pain similar to your admission "
            "symptoms not settling within 10 minutes, sudden severe shortness of breath, "
            "or collapse. Do not drive yourself — call 999."
        ),
        "must_preserve": [
            "antiplatelet drug names and duration — both drugs must be named explicitly",
            "do-not-stop antiplatelet warning",
            "driving restriction — Group 1 duration must match clinical context "
            "(1 week elective / 4 weeks post-MI)",
            "Group 2 DVLA notification if Group 2 licence documented",
            "not-a-cure closing statement — mandatory in every PCI output",
            "staged procedure explanation if not all vessels treated",
            "cardiac rehabilitation attendance encouraged if referred",
        ],
    },

    # ── ECHOCARDIOGRAM ─────────────────────────────────────────────────────

    "echocardiogram": {
        "procedure_name": "Echocardiogram (echo)",
        "lay_name": "Ultrasound scan of the heart",
        "what_it_shows": (
            "An echocardiogram is a specialised ultrasound scan that uses sound waves "
            "to create a live moving picture of your heart. It shows the pumping machinery "
            "and physical structure — the muscle, the chambers, and the valves. This is "
            "different from an ECG, which looks at the heart's electrical signals."
        ),
        "ef_ranges": {
            "normal":   ("55% or above",  "Your heart pumping function is normal. This is reassuring."),
            "mild":     ("45–54%",         "Your heart pumping function is mildly reduced. It is working reasonably well but not at full strength. Your medications and follow-up are important to keep it stable."),
            "moderate": ("36–44%",         "Your heart pumping function is moderately reduced. Your heart is working harder than it should. Your medications play an important role in protecting your heart."),
            "severe":   ("35% or below",   "Your heart pumping function is significantly reduced. Your medications are essential — they are not just for blood pressure or fluid control, they actively protect your heart muscle and help prevent it from weakening further. It is very important that you take them every day as prescribed."),
        },
        "diastolic_dysfunction": (
            "Your echo showed that your heart muscle is stiff and has some difficulty "
            "relaxing fully between beats to refill with blood. Your heart's squeeze may "
            "be preserved, but the relaxation and refilling phase is less efficient. "
            "This can explain breathlessness even when pumping function appears normal."
        ),
        "wall_motion": (
            "Your echo showed that one area of your heart muscle is not squeezing as "
            "strongly as the rest. This usually means that part of the heart muscle has "
            "been affected by a previous heart attack or reduced blood supply. Your "
            "cardiologist is aware and it has been taken into account in your treatment."
        ),
        "lvh": (
            "Your echo showed that the walls of your heart are thicker than normal. "
            "This is called left ventricular hypertrophy and is usually caused by "
            "long-term high blood pressure, making the heart muscle grow thick and bulky. "
            "This is a reason to keep your blood pressure well controlled."
        ),
        "valves": {
            "trivial_trace": (
                "This is a normal finding — almost everyone has a tiny amount of valve "
                "leakiness that does not affect health."
            ),
            "aortic_stenosis": {
                "mild":     "Your echo showed mild narrowing of the aortic valve. This does not need treatment now and will be monitored with repeat scans.",
                "moderate": "Your echo showed moderate narrowing of the aortic valve. Your heart is working harder to push blood through. Regular monitoring is needed and your cardiologist will advise on timing of any future treatment.",
                "severe":   "Your echo showed severe narrowing of the aortic valve. This is an important finding. Your cardiologist will discuss with you whether a procedure to replace or repair the valve is appropriate and when this should happen.",
            },
            "mitral_regurgitation": {
                "mild":             "Your echo showed mild leakiness of the mitral valve. This is being monitored but does not currently need treatment.",
                "moderate_severe":  "Your echo showed significant leakiness of the mitral valve. Your heart is doing extra work to compensate. A specialist review is needed to decide on the right timing for any intervention.",
            },
        },
        "pericardial_effusion": {
            "small":    "A small amount of fluid around the heart. This is common after procedures or inflammation and usually clears on its own. Your clinical team is aware.",
            "moderate": "A moderate amount of fluid around the heart. This needs close monitoring as it can put pressure on the heart if it increases. Your cardiologist will advise on further action.",
            "large":    "A significant amount of fluid around the heart. This is an important finding that requires close monitoring and may need treatment.",
        },
        "top_warning": (
            "Contact your GP or seek urgent attention if you notice new or worsening "
            "fainting or lightheadedness, sudden severe shortness of breath especially "
            "when lying flat, or chest pain during minimal exertion. Call 999 immediately "
            "for sudden severe chest pain or collapse."
        ),
        "repeat_echo": (
            "Your cardiologist has recommended a repeat echocardiogram in [timeframe]. "
            "Heart function can change, and repeat scans allow your team to see whether "
            "your heart is responding to treatment. If you do not receive an appointment "
            "within the expected timeframe, contact your GP or cardiologist's secretary."
        ),
        "must_preserve": [
            "EF value or qualitative description must be included when documented",
            "EF ≤35% must include essential medication warning",
            "severe aortic stenosis must include specialist review message",
            "moderate or severe MR must include specialist review message",
            "moderate or large pericardial effusion must not be minimised",
            "warning symptoms section mandatory for EF ≤44%, severe AS, moderate/severe MR",
            "repeat echo instructions must include action if appointment not received",
            "trivial/trace valve findings must use reassurance language only",
        ],
    },
}


# ── PROMPT SECTION ─────────────────────────────────────────────────────────
# Injected into EXTRACTOR_SYSTEM_PROMPT in extractor.py
# (mirror of MEDICATION_CARDS_PROMPT_SECTION pattern)

INVESTIGATION_CARDS_PROMPT_SECTION = """
INVESTIGATION KNOWLEDGE CARDS — apply these rules when the discharge letter documents any of the following procedures or investigations:

CORONARY ANGIOGRAM (if documented):
- Extract: procedure type (diagnostic only vs combined with PCI), access site (radial/femoral), vessels examined, findings per vessel (normal/mild/moderate/severe narrowing or percentage stenosis), any treatment performed, overall result
- Severity language: use mild/moderate/severe. Only use percentage for near-total (90–99%) or total occlusion (100%)
- If normal: state no significant narrowings and good flow — reassuring result
- If disease found but not treated: explain medical management decision explicitly — do not leave unexplained
- Access site: always include radial or femoral instructions
- Always include: warning symptoms requiring 999

CORONARY ANGIOPLASTY / PCI (if documented):
- Extract: clinical context (emergency/urgent/elective), vessel(s) treated, stent type (DES/BMS/balloon only), number of stents, special techniques (Rotablation/bifurcation/IVUS/OCT), procedural result, completeness of revascularisation, antiplatelet regime (both drugs + duration), driving instructions, cardiac rehab referral
- MANDATORY: antiplatelet section with both drug names and duration
- MANDATORY: do-not-stop antiplatelet warning
- MANDATORY: driving restrictions — Group 1 (1 week elective / 4 weeks post-MI); Group 2 DVLA notification if applicable
- MANDATORY: not-a-cure closing statement in every PCI output
- If staged procedure: explain why not everything treated at once
- If failed PCI / CTO: explain without causing alarm

ECHOCARDIOGRAM (if documented):
- Extract: echo type (TTE/TOE/stress), EF value or qualitative description, diastolic function, wall motion, LV size and hypertrophy, aortic valve (normal/AS severity/AR severity), mitral valve (normal/MR severity/MS), tricuspid valve, RV function, pulmonary pressure, pericardial effusion, any recommendation for repeat imaging
- EF ranges: normal ≥55%, mildly impaired 45–54%, moderately impaired 36–44%, severely impaired ≤35%
- MANDATORY for EF ≤35%: essential medication warning — medications protect the heart muscle
- MANDATORY for severe AS: specialist review / valve replacement discussion
- MANDATORY for moderate or severe MR: specialist review message
- Trivial/trace valve findings: always use reassurance language
- Always include: warning symptoms; repeat echo instructions if recommended
"""
