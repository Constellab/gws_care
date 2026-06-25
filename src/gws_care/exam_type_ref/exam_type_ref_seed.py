"""Seed data — pre-configured exam types with parameters and reference limits.

Usage (run once, idempotent — skips exams that already exist by name):

    from gws_care.exam_type_ref.exam_type_ref_seed import seed_exam_types
    seed_exam_types()
"""

from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
from gws_care.exam_type_ref.exam_parameter import ExamParameter
from gws_care.exam_type_ref.exam_type_ref_dto import SaveExamTypeRefDTO, SaveExamParameterDTO
from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService

# Each entry: (SaveExamTypeRefDTO, list[SaveExamParameterDTO with name, ...])
_SEED: list[tuple[SaveExamTypeRefDTO, list[SaveExamParameterDTO]]] = [

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
            SaveExamParameterDTO(name="ASAT",              unit="UI/L",   value_type="NUMERIC", ref_high=37.0,  critical_high=200.0, is_required=True,  display_order=1),
            SaveExamParameterDTO(name="ALAT",              unit="UI/L",   value_type="NUMERIC", ref_high=41.0,  critical_high=200.0, is_required=True,  display_order=2),
            SaveExamParameterDTO(name="GGT",               unit="UI/L",   value_type="NUMERIC", ref_high=55.0,  critical_high=300.0, is_required=True,  display_order=3),
            SaveExamParameterDTO(name="Bilirubine totale", unit="µmol/L", value_type="NUMERIC", ref_low=0.0,  ref_high=17.0, critical_high=60.0, is_required=True, display_order=4),
            SaveExamParameterDTO(name="Albumine",          unit="g/L",    value_type="NUMERIC", ref_low=35.0, ref_high=50.0, critical_low=20.0,  is_required=True,  display_order=5),
            SaveExamParameterDTO(name="TP (Taux prothrombine)", unit="%", value_type="NUMERIC", ref_low=70.0, ref_high=100.0, critical_low=40.0, is_required=True,  display_order=6),
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
            SaveExamParameterDTO(name="LDL",              unit="mmol/L", value_type="NUMERIC", ref_high=3.4,  critical_high=6.0,  is_required=True,  display_order=1),
            SaveExamParameterDTO(name="HDL",              unit="mmol/L", value_type="NUMERIC", ref_low=1.0,   critical_low=0.5,   is_required=True,  display_order=2),
            SaveExamParameterDTO(name="Cholestérol total",unit="mmol/L", value_type="NUMERIC", ref_high=5.2,  critical_high=8.0,  is_required=True,  display_order=3),
            SaveExamParameterDTO(name="Triglycérides",    unit="mmol/L", value_type="NUMERIC", ref_high=1.7,  critical_high=5.0,  is_required=True,  display_order=4),
            SaveExamParameterDTO(name="Glycémie à jeun",  unit="mmol/L", value_type="NUMERIC", ref_low=3.9, ref_high=6.1, critical_low=2.5, critical_high=25.0, is_required=True, display_order=5),
            SaveExamParameterDTO(name="HbA1c",            unit="%",      value_type="NUMERIC", ref_high=5.7,  critical_high=14.0, is_required=False, display_order=6),
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
            SaveExamParameterDTO(name="Globules rouges (GR)", unit="T/L",  value_type="NUMERIC", ref_low=4.5,  ref_high=5.9,  critical_low=3.0,  critical_high=7.0,  is_required=True, display_order=1),
            SaveExamParameterDTO(name="Hémoglobine",          unit="g/dL", value_type="NUMERIC", ref_low=13.5, ref_high=17.5, critical_low=7.0,  critical_high=20.0, is_required=True, display_order=2),
            SaveExamParameterDTO(name="Hématocrite",          unit="%",    value_type="NUMERIC", ref_low=40.0, ref_high=52.0, critical_low=20.0, critical_high=60.0, is_required=True, display_order=3),
            SaveExamParameterDTO(name="Globules blancs (GB)", unit="G/L",  value_type="NUMERIC", ref_low=4.0,  ref_high=10.0, critical_low=2.0,  critical_high=30.0, is_required=True, display_order=4),
            SaveExamParameterDTO(name="Plaquettes",           unit="G/L",  value_type="NUMERIC", ref_low=150.0,ref_high=400.0,critical_low=50.0, critical_high=800.0,is_required=True, display_order=5),
            SaveExamParameterDTO(name="VGM",                  unit="fL",   value_type="NUMERIC", ref_low=80.0, ref_high=100.0,                                       is_required=False,display_order=6),
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
            SaveExamParameterDTO(name="Perte auditive moyenne", unit="dB HL", value_type="NUMERIC", ref_high=25.0, critical_high=70.0, is_required=True, display_order=1),
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
            SaveExamParameterDTO(name="VEMS (FEV1)",        unit="%",  value_type="NUMERIC", ref_low=80.0, critical_low=50.0, is_required=True,  display_order=1),
            SaveExamParameterDTO(name="CVF",                 unit="%",  value_type="NUMERIC", ref_low=80.0, critical_low=50.0, is_required=True,  display_order=2),
            SaveExamParameterDTO(name="Rapport VEMS/CVF",   unit="%",  value_type="NUMERIC", ref_low=70.0, critical_low=50.0, is_required=True,  display_order=3),
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
            SaveExamParameterDTO(name="Cannabis (THC)",       unit=None, value_type="BOOLEAN", is_required=True,  display_order=1),
            SaveExamParameterDTO(name="Cocaïne",              unit=None, value_type="BOOLEAN", is_required=True,  display_order=2),
            SaveExamParameterDTO(name="Opiacés",              unit=None, value_type="BOOLEAN", is_required=True,  display_order=3),
            SaveExamParameterDTO(name="Amphétamines",         unit=None, value_type="BOOLEAN", is_required=True,  display_order=4),
            SaveExamParameterDTO(name="Benzodiazépines",      unit=None, value_type="BOOLEAN", is_required=False, display_order=5),
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
            SaveExamParameterDTO(name="Créatinine",        unit="µmol/L", value_type="NUMERIC", ref_low=62.0,  ref_high=106.0, critical_high=500.0, is_required=True,  display_order=1),
            SaveExamParameterDTO(name="Urée",              unit="mmol/L", value_type="NUMERIC", ref_low=2.5,   ref_high=7.5,   critical_high=30.0,  is_required=True,  display_order=2),
            SaveExamParameterDTO(name="Acide urique",      unit="µmol/L", value_type="NUMERIC", ref_low=200.0, ref_high=420.0, critical_high=700.0, is_required=False, display_order=3),
            SaveExamParameterDTO(name="DFG (CKD-EPI)",    unit="mL/min/1.73m²", value_type="NUMERIC", ref_low=60.0, critical_low=15.0, is_required=True, display_order=4),
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
