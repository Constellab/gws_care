"""Seed data — pre-configured exam types with parameters.

Thresholds (ref values, critical values, interpretation labels) are NOT seeded here.
They are defined per age/sex range through the Age Range manager inside the parameter form.

Usage (run once, idempotent — skips exams that already exist by name):

    from gws_care.exam_type_ref.exam_type_ref_seed import seed_exam_types
    seed_exam_types()
"""

from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
from gws_care.exam_type_ref.exam_parameter import ExamParameter
from gws_care.exam_type_ref.exam_param_age_range import ExamParameterAgeRange
from gws_care.exam_type_ref.exam_type_ref_dto import SaveExamTypeRefDTO, SaveExamParameterDTO
from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService

# Each entry: (SaveExamTypeRefDTO, list[SaveExamParameterDTO])
# NOTE: no ref_low/ref_high/critical/label fields — define those per age/sex range
_SEED: list[tuple[SaveExamTypeRefDTO, list[SaveExamParameterDTO]]] = [

    # ── Constantes vitales ────────────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="Constantes vitales",
            category="CLINICAL",
            department="Médecine du travail",
            description="Mesures anthropométriques et signes vitaux de base.",
            allows_attachment=False,
            requires_attachment=False,
        ),
        [
            SaveExamParameterDTO(name="Taille",              code="taille", unit="cm",    value_type="NUMERIC", is_required=True,  display_order=1),
            SaveExamParameterDTO(name="Poids",               code="poids",  unit="kg",    value_type="NUMERIC", is_required=True,  display_order=2),
            SaveExamParameterDTO(
                name="IMC", code="imc", unit="kg/m²", value_type="NUMERIC",
                is_computed=True, formula="poids / (taille / 100) ** 2",
                is_required=False, display_order=3,
            ),
            SaveExamParameterDTO(name="Fréquence cardiaque", code="fc",    unit="bpm",   value_type="NUMERIC", is_required=True,  display_order=4),
            SaveExamParameterDTO(name="Tension systolique",  code="pas",   unit="mmHg",  value_type="NUMERIC", is_required=True,  display_order=5),
            SaveExamParameterDTO(name="Tension diastolique", code="pad",   unit="mmHg",  value_type="NUMERIC", is_required=True,  display_order=6),
            SaveExamParameterDTO(name="Température",         code="temp",  unit="°C",    value_type="NUMERIC", is_required=False, display_order=7),
            SaveExamParameterDTO(name="SpO2",                code="spo2",  unit="%",     value_type="NUMERIC", is_required=False, display_order=8),
        ],
    ),

    # ── Bilan hépatique ────────────────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="Bilan hépatique",
            category="BIOLOGY",
            department="Biologie",
            description="Évaluation de la fonction hépatique.",
            allows_attachment=True,
            requires_attachment=False,
            required_sample_type="Sang total (EDTA)",
        ),
        [
            SaveExamParameterDTO(name="ASAT",                   unit="UI/L",    value_type="NUMERIC", is_required=True,  display_order=1),
            SaveExamParameterDTO(name="ALAT",                   unit="UI/L",    value_type="NUMERIC", is_required=True,  display_order=2),
            SaveExamParameterDTO(name="GGT",                    unit="UI/L",    value_type="NUMERIC", is_required=True,  display_order=3),
            SaveExamParameterDTO(name="Bilirubine totale",      unit="µmol/L",  value_type="NUMERIC", is_required=True,  display_order=4),
            SaveExamParameterDTO(name="Albumine",               unit="g/L",     value_type="NUMERIC", is_required=True,  display_order=5),
            SaveExamParameterDTO(name="TP (Taux prothrombine)", unit="%",       value_type="NUMERIC", is_required=True,  display_order=6),
        ],
    ),

    # ── Bilan cardio-métabolique ───────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="Bilan cardio-métabolique",
            category="BIOLOGY",
            department="Biologie",
            description="Bilan lipidique et glycémique pour le risque cardiovasculaire.",
            allows_attachment=True,
            requires_attachment=False,
            required_sample_type="Sang total (EDTA)",
        ),
        [
            SaveExamParameterDTO(name="LDL",               unit="mmol/L", value_type="NUMERIC", is_required=True,  display_order=1),
            SaveExamParameterDTO(name="HDL",               unit="mmol/L", value_type="NUMERIC", is_required=True,  display_order=2),
            SaveExamParameterDTO(name="Cholestérol total", unit="mmol/L", value_type="NUMERIC", is_required=True,  display_order=3),
            SaveExamParameterDTO(name="Triglycérides",     unit="mmol/L", value_type="NUMERIC", is_required=True,  display_order=4),
            SaveExamParameterDTO(name="Glycémie à jeun",   unit="mmol/L", value_type="NUMERIC", is_required=True,  display_order=5),
            SaveExamParameterDTO(name="HbA1c",             unit="%",      value_type="NUMERIC", is_required=False, display_order=6),
        ],
    ),

    # ── NFS Hémogramme ────────────────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="NFS Hémogramme",
            category="BIOLOGY",
            department="Biologie",
            description="Numération formule sanguine complète.",
            allows_attachment=True,
            requires_attachment=False,
            required_sample_type="Sang total (EDTA)",
        ),
        [
            SaveExamParameterDTO(name="Globules rouges (GR)", unit="T/L",  value_type="NUMERIC", is_required=True,  display_order=1),
            SaveExamParameterDTO(name="Hémoglobine",          unit="g/dL", value_type="NUMERIC", is_required=True,  display_order=2),
            SaveExamParameterDTO(name="Hématocrite",          unit="%",    value_type="NUMERIC", is_required=True,  display_order=3),
            SaveExamParameterDTO(name="Globules blancs (GB)", unit="G/L",  value_type="NUMERIC", is_required=True,  display_order=4),
            SaveExamParameterDTO(name="Plaquettes",           unit="G/L",  value_type="NUMERIC", is_required=True,  display_order=5),
            SaveExamParameterDTO(name="VGM",                  unit="fL",   value_type="NUMERIC", is_required=False, display_order=6),
        ],
    ),

    # ── ECG 12 dérivations ────────────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="ECG 12 dérivations",
            category="ECG",
            department="Cardiologie",
            description="Électrocardiogramme 12 dérivations au repos.",
            allows_attachment=True,
            requires_attachment=True,
        ),
        [],
    ),

    # ── Radiographie thoracique ───────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="Radiographie thoracique",
            category="IMAGING",
            department="Radiologie",
            description="Radiographie du thorax face et profil.",
            allows_attachment=True,
            requires_attachment=True,
        ),
        [],
    ),

    # ── Audiométrie tonale ────────────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="Audiométrie tonale",
            category="ORL",
            department="ORL",
            description="Mesure des seuils auditifs par fréquences.",
            allows_attachment=True,
            requires_attachment=False,
        ),
        [
            SaveExamParameterDTO(name="Perte auditive moyenne", unit="dB HL", value_type="NUMERIC", is_required=True, display_order=1),
        ],
    ),

    # ── Spirométrie ───────────────────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="Spirométrie",
            category="CLINICAL",
            department="Pneumologie",
            description="Exploration fonctionnelle respiratoire (EFR).",
            allows_attachment=True,
            requires_attachment=False,
        ),
        [
            SaveExamParameterDTO(name="VEMS (FEV1)",       unit="%", value_type="NUMERIC", is_required=True,  display_order=1),
            SaveExamParameterDTO(name="CVF",                unit="%", value_type="NUMERIC", is_required=True,  display_order=2),
            SaveExamParameterDTO(name="Rapport VEMS/CVF",  unit="%", value_type="NUMERIC", is_required=True,  display_order=3),
        ],
    ),

    # ── Test toxicologique drogues ────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="Test toxicologique drogues",
            category="URINE",
            department="Toxicologie",
            description="Dépistage multi-drogues urinaire (cannabis, cocaïne, opiacés, amphétamines, benzodiazépines).",
            allows_attachment=True,
            requires_attachment=False,
            required_sample_type="Urine (flacon stérile)",
        ),
        [
            SaveExamParameterDTO(name="Cannabis (THC)",  unit=None, value_type="BOOLEAN", is_required=True,  display_order=1),
            SaveExamParameterDTO(name="Cocaïne",         unit=None, value_type="BOOLEAN", is_required=True,  display_order=2),
            SaveExamParameterDTO(name="Opiacés",         unit=None, value_type="BOOLEAN", is_required=True,  display_order=3),
            SaveExamParameterDTO(name="Amphétamines",    unit=None, value_type="BOOLEAN", is_required=True,  display_order=4),
            SaveExamParameterDTO(name="Benzodiazépines", unit=None, value_type="BOOLEAN", is_required=False, display_order=5),
        ],
    ),

    # ── Bilan rénal ───────────────────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="Bilan rénal",
            category="BIOLOGY",
            department="Biologie",
            description="Évaluation de la fonction rénale.",
            allows_attachment=True,
            requires_attachment=False,
            required_sample_type="Sang total (EDTA)",
        ),
        [
            SaveExamParameterDTO(name="Créatinine",      unit="µmol/L",          value_type="NUMERIC", is_required=True,  display_order=1),
            SaveExamParameterDTO(name="Urée",            unit="mmol/L",          value_type="NUMERIC", is_required=True,  display_order=2),
            SaveExamParameterDTO(name="Acide urique",    unit="µmol/L",          value_type="NUMERIC", is_required=False, display_order=3),
            SaveExamParameterDTO(name="DFG (CKD-EPI)",  unit="mL/min/1.73m²",   value_type="NUMERIC", is_required=True,  display_order=4),
        ],
    ),

    # ── Bilan ophtalmologique ─────────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="Bilan ophtalmologique",
            category="CLINICAL",
            department="Ophtalmologie",
            description="Examen de la vision : acuité, champ visuel, vision des couleurs.",
            allows_attachment=True,
            requires_attachment=False,
        ),
        [
            SaveExamParameterDTO(name="Acuité visuelle OD (sans correction)", unit=None,   value_type="TEXT",    is_required=True,  display_order=1),
            SaveExamParameterDTO(name="Acuité visuelle OG (sans correction)", unit=None,   value_type="TEXT",    is_required=True,  display_order=2),
            SaveExamParameterDTO(name="Acuité visuelle OD (avec correction)", unit=None,   value_type="TEXT",    is_required=False, display_order=3),
            SaveExamParameterDTO(name="Acuité visuelle OG (avec correction)", unit=None,   value_type="TEXT",    is_required=False, display_order=4),
            SaveExamParameterDTO(name="Vision des couleurs",                  unit=None,   value_type="TEXT",    is_required=False, display_order=5),
            SaveExamParameterDTO(name="Champ visuel",                         unit=None,   value_type="TEXT",    is_required=False, display_order=6),
            SaveExamParameterDTO(name="Tension oculaire OD",                  unit="mmHg", value_type="NUMERIC", is_required=False, display_order=7),
            SaveExamParameterDTO(name="Tension oculaire OG",                  unit="mmHg", value_type="NUMERIC", is_required=False, display_order=8),
        ],
    ),

    # ── Sérologies infectieuses ───────────────────────────────────────────
    (
        SaveExamTypeRefDTO(
            name="Sérologies infectieuses",
            category="BIOLOGY",
            department="Biologie",
            description="Dépistage sérologique : hépatites B et C, VIH, syphilis.",
            allows_attachment=True,
            requires_attachment=False,
            required_sample_type="Sang total (EDTA)",
        ),
        [
            SaveExamParameterDTO(name="AgHBs (Hépatite B — antigène surface)", unit=None, value_type="BOOLEAN", is_required=True,  display_order=1),
            SaveExamParameterDTO(name="Ac anti-HBs (Hépatite B — anticorps)",  unit=None, value_type="BOOLEAN", is_required=True,  display_order=2),
            SaveExamParameterDTO(name="Ac anti-HBc (Hépatite B — core)",       unit=None, value_type="BOOLEAN", is_required=False, display_order=3),
            SaveExamParameterDTO(name="Ac anti-VHC (Hépatite C)",              unit=None, value_type="BOOLEAN", is_required=True,  display_order=4),
            SaveExamParameterDTO(name="Sérologie VIH (Ag/Ac combinés)",        unit=None, value_type="BOOLEAN", is_required=False, display_order=5),
            SaveExamParameterDTO(name="TPHA (Syphilis)",                        unit=None, value_type="BOOLEAN", is_required=False, display_order=6),
            SaveExamParameterDTO(name="VDRL (Syphilis — activité)",             unit=None, value_type="BOOLEAN", is_required=False, display_order=7),
        ],
    ),
]


def seed_exam_types() -> dict:
    """Create all seed exam types if they don't exist yet. Returns a summary."""
    created = []
    skipped = []
    for exam_dto, params in _SEED:
        existing = ExamTypeRef.get_or_none(ExamTypeRef.name == exam_dto.name)
        if existing:
            skipped.append(exam_dto.name)
            continue
        ref = ExamTypeRefService.create(exam_dto)
        for p in params:
            ExamTypeRefService.add_parameter(ref.id, p)
        created.append(exam_dto.name)
    return {"created": created, "skipped": skipped}


def clear_exam_types() -> int:
    """Delete ALL exam type refs and cascade-delete their parameters and age ranges."""
    deleted = ExamTypeRef.delete().execute()
    return deleted


def clear_and_reseed() -> dict:
    """Delete all existing exam types then re-seed from scratch."""
    clear_exam_types()
    return seed_exam_types()
