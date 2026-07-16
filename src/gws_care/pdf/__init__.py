"""Phase 8 — PDF generation service.

Three PDF generators:
  8.1 — Medical certificate (CertificateService.generate_pdf)
  8.2 — Campaign report    (CampaignService.generate_report)
  8.3 — CampaignVisit results      (CampaignVisitService.generate_results_pdf)

All methods return raw PDF bytes.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ── Shared colour palette ─────────────────────────────────────────────────────

_BLUE_DARK = (0.07, 0.27, 0.55)   # brand dark blue (RGB 0–1)
_BLUE_LIGHT = (0.88, 0.92, 0.98)  # light-blue background for table headers
_GREEN = (0.13, 0.55, 0.13)
_RED = (0.80, 0.10, 0.10)
_ORANGE = (0.85, 0.40, 0.00)
_GREY = (0.45, 0.45, 0.45)
_LIGHT_GREY = (0.95, 0.95, 0.95)

# ── Appreciation colours ──────────────────────────────────────────────────────

_APPRECIATION_COLORS = {
    "critical_low": _RED,
    "critical_high": _RED,
    "low": _ORANGE,
    "high": _ORANGE,
    "normal": _GREEN,
}

_APPRECIATION_LABELS = {
    "critical_low": "Critique bas ↓",
    "critical_high": "Critique haut ↑",
    "low": "Bas ↓",
    "high": "Haut ↑",
    "normal": "Normal",
}


# ── 8.1 — Certificate PDF ─────────────────────────────────────────────────────

def generate_certificate_pdf(certificate_id: str) -> bytes:
    """Generate a type-aware professional medical certificate PDF.

    Supports all 7 certificate types:
    - APTITUDE, WORK_STOPPAGE, PRE_EMPLOYMENT, PERIODIC,
      WORK_ACCIDENT, SIR, VACCINATION
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    from gws_care.certificate.medical_certificate import (
        CERTIFICATE_TYPES,
        MedicalCertificate,
    )
    from gws_care.patient.patient import Patient
    from gws_care.user.user import User

    cert: MedicalCertificate = MedicalCertificate.get_by_id(certificate_id)
    patient: Patient = Patient.get_by_id(str(cert.patient_id))
    cert_type = cert.certificate_type or "APTITUDE"
    type_label = CERTIFICATE_TYPES.get(cert_type, cert_type)

    issued_by_name = "—"
    if cert.issued_by_id:
        try:
            u: User = User.get_by_id(str(cert.issued_by_id))
            issued_by_name = f"Dr. {u.first_name} {u.last_name}"
        except Exception:
            pass

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    blue_color = colors.Color(*_BLUE_DARK)

    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=blue_color, fontSize=12, spaceBefore=6 * mm, spaceAfter=2 * mm)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=2 * mm)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor=colors.grey, leading=11)
    bold10 = ParagraphStyle("bold10", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold")
    center_big = ParagraphStyle("center_big", parent=styles["Normal"], fontSize=13, fontName="Helvetica-Bold",
                                textColor=blue_color, alignment=1, spaceBefore=8 * mm, spaceAfter=8 * mm)
    right_small = ParagraphStyle("right", parent=styles["Normal"], fontSize=9, textColor=colors.grey, alignment=2)

    def _fmt_date(d) -> str:
        if not d:
            return "—"
        if hasattr(d, "strftime"):
            return d.strftime("%d/%m/%Y")
        return str(d)

    def _info_table(rows: list[tuple[str, str]]) -> Table:
        tbl = Table([(r[0], r[1]) for r in rows], colWidths=[5.5 * cm, 11.5 * cm])
        tbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (0, 0), (0, -1), colors.Color(*_BLUE_LIGHT)),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ]))
        return tbl

    story: list = []

    # ── Letterhead ────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("<b>PS CONSULTING</b><br/><font size='9' color='grey'>Médecine du travail</font>", bold10),
        Paragraph(
            f"<font size='9' color='grey'>Généré par Constellab Care<br/>"
            f"Date d'émission : {_fmt_date(cert.issue_date)}</font>",
            right_small,
        ),
    ]]
    hdr_tbl = Table(header_data, colWidths=[9 * cm, 8 * cm])
    hdr_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    story.append(hdr_tbl)
    story.append(HRFlowable(width="100%", thickness=1.5, color=blue_color, spaceAfter=5 * mm))

    # ── Document title ────────────────────────────────────────────────────────
    story.append(Paragraph(type_label.upper(), center_big))

    # ── Patient identity ──────────────────────────────────────────────────────
    story.append(Paragraph("Identité du patient", h2))
    story.append(_info_table([
        ("Nom, Prénom", f"{patient.last_name} {patient.first_name}"),
        ("Date de naissance", _fmt_date(patient.date_of_birth)),
        ("Numéro patient", patient.patient_number or "—"),
    ]))

    # ── Type-specific fields ──────────────────────────────────────────────────
    if cert_type == "APTITUDE":
        story.append(Paragraph("Conclusion médicale", h2))
        story.append(Paragraph(cert.conclusion or "—", body))
        story.append(Paragraph("Décision d'aptitude", h2))
        _fitness = cert.effective_fitness
        fitness_text = "APTE" if _fitness == "FIT" else ("INAPTE DÉFINITIF" if _fitness == "PERMANENTLY_UNFIT" else "INAPTE")
        fitness_color = colors.Color(*_GREEN) if _fitness == "FIT" else colors.Color(*_RED)
        story.append(Paragraph(
            f"<b><font color='{fitness_color.hexval()}'>{fitness_text}</font></b>",
            ParagraphStyle("fitness", parent=styles["Normal"], fontSize=14, spaceAfter=3 * mm),
        ))
        if cert.restrictions:
            story.append(Paragraph("Restrictions / réserves", h2))
            story.append(Paragraph(cert.restrictions, body))

    elif cert_type == "WORK_STOPPAGE":
        story.append(Paragraph("Arrêt de travail", h2))
        story.append(_info_table([
            ("Date de début", _fmt_date(cert.start_date)),
            ("Date de fin prévue", _fmt_date(cert.end_date)),
            ("Date de reprise", _fmt_date(cert.return_date)),
        ]))
        story.append(Paragraph("Conclusion médicale", h2))
        story.append(Paragraph(cert.conclusion or "—", body))

    elif cert_type in ("PRE_EMPLOYMENT", "PERIODIC"):
        story.append(Paragraph("Type de visite", h2))
        subtype_label = cert.visit_subtype or ("Visite d'embauche" if cert_type == "PRE_EMPLOYMENT" else "Visite périodique")
        story.append(Paragraph(subtype_label, body))
        story.append(Paragraph("Conclusion médicale", h2))
        story.append(Paragraph(cert.conclusion or "—", body))
        story.append(Paragraph("Décision d'aptitude", h2))
        _fitness = cert.effective_fitness
        fitness_text = "APTE" if _fitness == "FIT" else ("INAPTE DÉFINITIF" if _fitness == "PERMANENTLY_UNFIT" else "INAPTE")
        fitness_color = colors.Color(*_GREEN) if _fitness == "FIT" else colors.Color(*_RED)
        story.append(Paragraph(
            f"<b><font color='{fitness_color.hexval()}'>{fitness_text}</font></b>",
            ParagraphStyle("fitness", parent=styles["Normal"], fontSize=14, spaceAfter=3 * mm),
        ))
        if cert.restrictions:
            story.append(Paragraph("Restrictions / réserves", h2))
            story.append(Paragraph(cert.restrictions, body))

    elif cert_type == "WORK_ACCIDENT":
        story.append(Paragraph("Accident du travail / Maladie professionnelle", h2))
        story.append(_info_table([
            ("Date de l'accident / déclaration", _fmt_date(cert.accident_date)),
            ("Zone corporelle atteinte", cert.body_part or "—"),
        ]))
        story.append(Paragraph("Conclusion médicale", h2))
        story.append(Paragraph(cert.conclusion or "—", body))

    elif cert_type == "SIR":
        story.append(Paragraph("Suivi Individuel Renforcé", h2))
        story.append(_info_table([
            ("Type d'exposition", cert.exposure_type or "—"),
        ]))
        story.append(Paragraph("Conclusion médicale", h2))
        story.append(Paragraph(cert.conclusion or "—", body))
        story.append(Paragraph("Décision d'aptitude", h2))
        _fitness = cert.effective_fitness
        fitness_text = "APTE" if _fitness == "FIT" else ("INAPTE DÉFINITIF" if _fitness == "PERMANENTLY_UNFIT" else "INAPTE")
        fitness_color = colors.Color(*_GREEN) if _fitness == "FIT" else colors.Color(*_RED)
        story.append(Paragraph(
            f"<b><font color='{fitness_color.hexval()}'>{fitness_text}</font></b>",
            ParagraphStyle("fitness", parent=styles["Normal"], fontSize=14, spaceAfter=3 * mm),
        ))

    elif cert_type == "VACCINATION":
        story.append(Paragraph("Vaccination", h2))
        story.append(_info_table([
            ("Vaccin", cert.vaccine_name or "—"),
            ("Numéro de lot", cert.vaccine_lot or "—"),
            ("Prochaine injection / rappel", _fmt_date(cert.next_booster)),
        ]))
        story.append(Paragraph("Conclusion médicale", h2))
        story.append(Paragraph(cert.conclusion or "—", body))

    else:
        story.append(Paragraph("Conclusion médicale", h2))
        story.append(Paragraph(cert.conclusion or "—", body))

    # ── Signature block ───────────────────────────────────────────────────────
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=5 * mm))
    sig_tbl = Table([[
        Paragraph(
            f"<b>{issued_by_name}</b><br/>"
            "<font size='9' color='grey'>Médecin du travail</font><br/><br/>"
            "<i>(Signature)</i>",
            ParagraphStyle("sig", parent=styles["Normal"], fontSize=10, alignment=2),
        )
    ]], colWidths=[17 * cm])
    sig_tbl.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "RIGHT")]))
    story.append(sig_tbl)

    # ── Confidentiality footer ────────────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        "Ce document est confidentiel. Il ne peut être communiqué qu'au salarié concerné "
        "et aux personnes habilitées. Document généré électroniquement par Constellab Care.",
        small,
    ))

    doc.build(story)
    return buf.getvalue()


# ── 8.2 — Campaign report PDF ─────────────────────────────────────────────────

def generate_campaign_report_pdf(program_id: str) -> bytes:
    """Generate an aggregated program presence/absence report.

    Contains NO individual medical data (RGPD-compliant for RH access).
    Content:
    - Campaign header (name, dates, account)
    - Presence statistics (present / absent / total)
    - Patient attendance table (name, status only)
    - Exam type coverage table (total done per type)
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    from gws_care.campaign.campaign_service import CampaignService
    from gws_care.visit.visit import Visit
    from gws_care.visit.campaign_visit_status import CampaignVisitStatus

    program = CampaignService.get_campaign(program_id)
    visits = list(Visit.select().where(Visit.campaign == program_id))
    patients = CampaignService.get_patients(program_id)
    exam_types = CampaignService.get_exam_types(program_id)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    blue_color = colors.Color(*_BLUE_DARK)
    blue_light = colors.Color(*_BLUE_LIGHT)

    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=blue_color, fontSize=15, spaceAfter=3 * mm)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=blue_color, fontSize=11, spaceBefore=6 * mm, spaceAfter=2 * mm)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    bold10 = ParagraphStyle("bold10", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold")

    story: list = []

    # ── Header ────────────────────────────────────────────────────────────────
    account_name = program.account.name if program.account_id else "—"
    story.append(Paragraph("<b>PS CONSULTING</b> — Rapport de campagne", bold10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=blue_color, spaceAfter=3 * mm))
    story.append(Paragraph(program.name, h1))

    info_data = [
        ["Account / Company", account_name],
        ["Période", f"du {program.start_date} au {program.end_date}"],
        ["Statut", program.status.get_label() if hasattr(program.status, "get_label") else str(program.status)],
        ["Généré le", __import__("datetime").date.today().strftime("%d/%m/%Y")],
    ]
    info_tbl = Table(info_data, colWidths=[5 * cm, 12 * cm])
    info_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (0, -1), blue_light),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
    ]))
    story.append(info_tbl)

    # ── Statistics ────────────────────────────────────────────────────────────
    story.append(Paragraph("Statistiques de présence", h2))
    total = len(patients)
    present = sum(
        1 for v in visits
        if v.campaign_visit_status not in (CampaignVisitStatus.PENDING, CampaignVisitStatus.CANCELLED)
    )
    absent = sum(1 for v in visits if v.campaign_visit_status == CampaignVisitStatus.CANCELLED)
    pct = round(present / total * 100) if total else 0

    stats_data = [
        ["Total convoqués", str(total)],
        ["Présents (on-site complété)", f"{present} ({pct} %)"],
        ["Absents", str(absent)],
        ["Types d'examens prévus", str(len(exam_types))],
    ]
    stats_tbl = Table(stats_data, colWidths=[9 * cm, 8 * cm])
    stats_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 0), (0, -1), blue_light),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
    ]))
    story.append(stats_tbl)

    # ── Attendance table ──────────────────────────────────────────────────────
    story.append(Paragraph("Liste de présence", h2))
    story.append(Paragraph(
        "⚠️ Ce tableau ne contient aucune donnée médicale (statut logistique uniquement).",
        ParagraphStyle("note", parent=styles["Normal"], fontSize=9, textColor=colors.orange, spaceAfter=3 * mm),
    ))

    visit_map = {str(v.patient_id): v for v in visits}

    attendance_header = [
        Paragraph("<b>N° Patient</b>", bold10),
        Paragraph("<b>Nom</b>", bold10),
        Paragraph("<b>Prénom</b>", bold10),
        Paragraph("<b>Statut présence</b>", bold10),
    ]
    attendance_rows = [attendance_header]
    for p in patients:
        visit = visit_map.get(str(p.id))
        if visit and visit.campaign_visit_status not in (CampaignVisitStatus.PENDING, CampaignVisitStatus.CANCELLED):
            status_cell = Paragraph("<font color='green'>✓ Présent</font>", body)
        elif visit and visit.campaign_visit_status == CampaignVisitStatus.CANCELLED:
            status_cell = Paragraph("<font color='red'>✗ Absent</font>", body)
        else:
            status_cell = Paragraph("<font color='gray'>— En attente</font>", body)
        attendance_rows.append([
            Paragraph(p.patient_number, body),
            Paragraph(p.last_name, body),
            Paragraph(p.first_name, body),
            status_cell,
        ])

    att_tbl = Table(attendance_rows, colWidths=[3.5 * cm, 4.5 * cm, 4.5 * cm, 4.5 * cm])
    att_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), blue_light),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(*_LIGHT_GREY)]),
    ]))
    story.append(att_tbl)

    # ── Exam types ────────────────────────────────────────────────────────────
    if exam_types:
        story.append(Paragraph("Types d'examens prévus", h2))
        et_header = [
            Paragraph("<b>Code</b>", bold10),
            Paragraph("<b>Nom</b>", bold10),
            Paragraph("<b>Catégorie</b>", bold10),
        ]
        et_rows = [et_header]
        for et in exam_types:
            et_rows.append([
                Paragraph(et.code, body),
                Paragraph(et.name, body),
                Paragraph(str(et.category.value) if et.category else "—", body),
            ])
        et_tbl = Table(et_rows, colWidths=[3 * cm, 9 * cm, 5 * cm])
        et_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), blue_light),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ]))
        story.append(et_tbl)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=3 * mm))
    story.append(Paragraph("Document généré par Constellab Care — PS CONSULTING. Confidentiel.", small))

    doc.build(story)
    return buf.getvalue()


# ── 8.3 — CampaignVisit results PDF ───────────────────────────────────────────────────

def generate_visit_results_pdf(visit_id: str) -> bytes:
    """Generate a patient-readable PDF of their visit results.

    Content:
    - Patient identity + visit info
    - Exam results table with appreciation colour coding
    - Doctor Clinic interpretation
    - Doctor Company interpretation + message
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    from gws_care.exam.exam import Exam
    from gws_care.exam.exam_result import ExamResult
    from gws_care.exam.exam_result_service import ExamResultService
    from gws_care.visit.visit import Visit
    from gws_care.visit.campaign_visit_service import CampaignVisitService

    visit: Visit = CampaignVisitService.get_visit(visit_id)
    patient = visit.patient
    program = visit.campaign

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    blue_color = colors.Color(*_BLUE_DARK)
    blue_light = colors.Color(*_BLUE_LIGHT)

    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=blue_color, fontSize=15, spaceAfter=3 * mm)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=blue_color, fontSize=11, spaceBefore=6 * mm, spaceAfter=2 * mm)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14)
    italic = ParagraphStyle("italic", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Oblique", leading=14, spaceAfter=2 * mm)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    bold10 = ParagraphStyle("bold10", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold")

    story: list = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("<b>PS CONSULTING</b> — Résultats médicaux", bold10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=blue_color, spaceAfter=3 * mm))
    story.append(Paragraph(f"Visite {visit.visit_number}", h1))

    # ── Patient info ──────────────────────────────────────────────────────────
    dob = str(patient.date_of_birth) if patient.date_of_birth else "—"
    patient_info = [
        ["Patient", patient.get_full_name()],
        ["Date de naissance", dob],
        ["N° patient", patient.patient_number],
        ["Campagne", program.name if program.id else "—"],
        ["Période", f"du {program.start_date} au {program.end_date}" if program.id else "—"],
    ]
    pt_tbl = Table(patient_info, colWidths=[5 * cm, 12 * cm])
    pt_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (0, -1), blue_light),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
    ]))
    story.append(pt_tbl)

    # ── Exam results table ────────────────────────────────────────────────────
    story.append(Paragraph("Résultats d'examens", h2))

    exams = list(Exam.select().where(Exam.visit_id == visit_id))
    if not exams:
        story.append(Paragraph("Aucun résultat d'examen enregistré pour cette visite.", body))
    else:
        results_header = [
            Paragraph("<b>Examen</b>", bold10),
            Paragraph("<b>Valeur</b>", bold10),
            Paragraph("<b>Unité</b>", bold10),
            Paragraph("<b>Appréciation</b>", bold10),
        ]
        results_rows = [results_header]

        for exam in exams:
            exam_type_name = str(exam.exam_type.value) if exam.exam_type else "—"
            unit = "—"

            # Try to get ExamTypeModel for unit
            try:
                from gws_care.exam.exam_type_service import ExamTypeService
                et_model = ExamTypeService.get_exam_type_model_for_exam(exam)
                if et_model:
                    exam_type_name = et_model.name
                    unit = et_model.unit or "—"
            except Exception:
                pass

            result = ExamResultService.get_result_for_exam(str(exam.id))
            appr_key = ""
            primary_val = "—"
            if result:
                appr_key = result.appreciation.value if result.appreciation else ""
                rd = result.result_data or {}
                if isinstance(rd, dict):
                    pv = rd.get("primary_value") or rd.get("value")
                    if pv is not None:
                        primary_val = str(pv)

            # Lab results (sub-rows from JSON)
            if exam.lab_results:
                for lr in exam.lab_results:
                    param = lr.get("parameter", exam_type_name)
                    val = str(lr.get("value", "—"))
                    lr_unit = lr.get("unit", unit)
                    lr_status = lr.get("status", appr_key)
                    lr_label = _APPRECIATION_LABELS.get(lr_status, lr_status or "—")
                    lr_color = colors.Color(*_APPRECIATION_COLORS.get(lr_status, _GREY))
                    results_rows.append([
                        Paragraph(param, body),
                        Paragraph(val, body),
                        Paragraph(lr_unit or "—", body),
                        Paragraph(f"<font color='{lr_color.hexval()}'><b>{lr_label}</b></font>", body),
                    ])
            else:
                appr_label = _APPRECIATION_LABELS.get(appr_key, appr_key or "—")
                appr_color = colors.Color(*_APPRECIATION_COLORS.get(appr_key, _GREY))
                results_rows.append([
                    Paragraph(exam_type_name, body),
                    Paragraph(primary_val, body),
                    Paragraph(unit, body),
                    Paragraph(f"<font color='{appr_color.hexval()}'><b>{appr_label}</b></font>", body),
                ])

        res_tbl = Table(results_rows, colWidths=[7 * cm, 3.5 * cm, 2.5 * cm, 4 * cm])
        res_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), blue_light),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(*_LIGHT_GREY)]),
        ]))
        story.append(res_tbl)

    # ── Clinic interpretation ─────────────────────────────────────────────────
    if visit.doctor_clinic_interpretation:
        story.append(Paragraph("Interprétation du Clinic Doctor", h2))
        story.append(Paragraph(visit.doctor_clinic_interpretation, italic))

    # ── Company interpretation ────────────────────────────────────────────────
    if visit.doctor_company_interpretation:
        story.append(Paragraph("Interprétation du Company Doctor", h2))
        story.append(Paragraph(visit.doctor_company_interpretation, italic))

    # ── Message to patient ────────────────────────────────────────────────────
    if visit.doctor_company_message:
        story.append(Paragraph("Message de votre médecin du travail", h2))
        story.append(Paragraph(visit.doctor_company_message, body))

    # ── Legend ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Légende des appréciations :", h2))
    legend_items = [
        ("Critique bas / haut", _RED, "Valeur en dehors des seuils critiques — consultation médicale recommandée"),
        ("Bas / Haut", _ORANGE, "Valeur légèrement anormale — à surveiller"),
        ("Normal", _GREEN, "Valeur dans les seuils normaux"),
    ]
    for label, col, desc in legend_items:
        c = colors.Color(*col)
        story.append(Paragraph(
            f"<font color='{c.hexval()}'><b>{label}</b></font> : {desc}",
            ParagraphStyle("legend", parent=styles["Normal"], fontSize=9, spaceAfter=1 * mm),
        ))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=3 * mm))
    story.append(Paragraph(
        "Ce document contient des données médicales personnelles et confidentielles. "
        "Document généré électroniquement par Constellab Care — PS CONSULTING.",
        small,
    ))

    doc.build(story)
    return buf.getvalue()


# ── 8.4 — Patient ID card PDF ─────────────────────────────────────────────────

def generate_patient_id_card_pdf(patient_id: str) -> bytes:
    """Generate a patient identity card PDF (A5 landscape, card-style layout).

    The card contains: name, date of birth, sex, social security number
    and the patient's QR code — laid out like a health/social-security card.
    Returns raw PDF bytes.
    """
    import base64

    from reportlab.lib.pagesizes import A5, landscape
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as pdfcanvas

    from gws_care.patient.patient import Patient

    p: Patient = Patient.get_by_id(patient_id)

    # ── Page setup ────────────────────────────────────────────────────────────
    page_w, page_h = landscape(A5)   # 210mm × 148mm
    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=(page_w, page_h))

    # ── Card dimensions (full bleed with small margins) ────────────────────────
    margin = 8 * mm
    card_x = margin
    card_y = margin
    card_w = page_w - 2 * margin
    card_h = page_h - 2 * margin
    radius = 4 * mm

    # ── Background (dark blue) ────────────────────────────────────────────────
    r, g, b = _BLUE_DARK
    c.setFillColorRGB(r, g, b)
    c.roundRect(card_x, card_y, card_w, card_h, radius=radius, fill=1, stroke=0)

    # ── Top accent band (light blue) ──────────────────────────────────────────
    band_h = 14 * mm
    rl, gl, bl = _BLUE_LIGHT
    c.setFillColorRGB(rl, gl, bl)
    # Rounded rect for top then cover bottom half of rounding with plain rect
    c.roundRect(card_x, card_y + card_h - band_h, card_w, band_h, radius=radius, fill=1, stroke=0)
    c.rect(card_x, card_y + card_h - band_h, card_w, band_h / 2, fill=1, stroke=0)

    # ── Header text (dark on light band) ─────────────────────────────────────
    c.setFillColorRGB(*_BLUE_DARK)
    c.setFont("Helvetica-Bold", 9)
    header_y = card_y + card_h - band_h + 4 * mm
    c.drawString(card_x + 5 * mm, header_y, "CONSTELLAB CARE — PS CONSULTING")

    pnum = getattr(p, "patient_number", "") or ""
    c.setFont("Helvetica", 7)
    c.drawRightString(card_x + card_w - 5 * mm, header_y, f"N° {pnum}")

    # ── Body layout: left text column | right QR code ─────────────────────────
    qr_size = 32 * mm
    qr_margin = 5 * mm
    qr_x = card_x + card_w - qr_size - qr_margin
    qr_y = card_y + (card_h - band_h - qr_size) / 2 + 2 * mm

    text_x = card_x + 5 * mm
    text_y_start = card_y + card_h - band_h - 10 * mm

    # ── Name ──────────────────────────────────────────────────────────────────
    c.setFillColorRGB(1, 1, 1)
    last = (getattr(p, "last_name", "") or "").upper()
    first = getattr(p, "first_name", "") or ""
    c.setFont("Helvetica-Bold", 14)
    c.drawString(text_x, text_y_start, f"{last}  {first}")

    # ── Info fields ────────────────────────────────────────────────────────────
    def _field(label: str, value: str, y: float) -> None:
        c.setFillColorRGB(0.65, 0.78, 0.92)
        c.setFont("Helvetica", 6)
        c.drawString(text_x, y + 3.5 * mm, label.upper())
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(text_x, y, value if value else "—")

    line_gap = 12 * mm
    y = text_y_start - line_gap

    dob_str = p.date_of_birth.strftime("%d / %m / %Y") if p.date_of_birth else "—"
    _field("Date de naissance", dob_str, y)
    y -= line_gap

    sex_map = {"M": "Masculin", "F": "Féminin", "Autre": "Autre"}
    sex_val = sex_map.get(getattr(p, "sex", None) or "", "—")
    _field("Sexe", sex_val, y)
    y -= line_gap

    ssn = getattr(p, "social_security_number", None) or "—"
    _field("N° Sécurité Sociale (NIR)", ssn, y)

    # ── QR code ───────────────────────────────────────────────────────────────
    qr_data = getattr(p, "qr_code", None)
    if qr_data:
        try:
            if "base64," in qr_data:
                b64_str = qr_data.split("base64,")[1]
            else:
                b64_str = qr_data
            img_bytes = base64.b64decode(b64_str)
            qr_img = ImageReader(io.BytesIO(img_bytes))
            pad = 1.5 * mm
            c.setFillColorRGB(1, 1, 1)
            c.roundRect(qr_x - pad, qr_y - pad, qr_size + 2 * pad, qr_size + 2 * pad,
                        radius=2 * mm, fill=1, stroke=0)
            c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)
        except Exception:
            pass  # QR code unavailable — skip silently

    # ── Footer strip ──────────────────────────────────────────────────────────
    footer_h = 5 * mm
    c.setFillColorRGB(0.04, 0.17, 0.38)
    c.rect(card_x, card_y, card_w, footer_h, fill=1, stroke=0)
    c.setFillColorRGB(0.6, 0.7, 0.85)
    c.setFont("Helvetica", 5)
    c.drawCentredString(
        card_x + card_w / 2,
        card_y + 1.5 * mm,
        "Document confidentiel — Données médicales personnelles — Constellab Care",
    )

    c.save()
    return buf.getvalue()


# ── 8.4 — Prescription PDF ───────────────────────────────────────────────────

def generate_prescription_pdf(prescription_id: str) -> bytes:
    """Generate a professional medical prescription PDF.

    Content:
    - Organization letterhead
    - Patient identity block
    - Diagnosis
    - Drug table (name, dosage, frequency, duration)
    - General instructions
    - Doctor signature block
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    from gws_care.prescription.prescription import Prescription

    presc: Prescription = Prescription.get_by_id(prescription_id)
    detail = presc.to_detail_dto()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    blue_color = colors.Color(*_BLUE_DARK)
    blue_light = colors.Color(*_BLUE_LIGHT)

    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=blue_color,
                         fontSize=11, spaceBefore=5 * mm, spaceAfter=2 * mm)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=2 * mm)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor=colors.grey, leading=11)
    bold10 = ParagraphStyle("bold10", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold")
    center_big = ParagraphStyle("center_big", parent=styles["Normal"], fontSize=14,
                                 fontName="Helvetica-Bold", textColor=blue_color,
                                 alignment=1, spaceBefore=6 * mm, spaceAfter=6 * mm)

    # Format date dd/mm/yyyy
    try:
        from datetime import date as _date
        d = _date.fromisoformat(detail.prescription_date)
        date_display = d.strftime("%d/%m/%Y")
    except Exception:
        date_display = detail.prescription_date

    story: list = []

    # ── Header ────────────────────────────────────────────────────────────────
    header_data = [
        [
            Paragraph("<b>PS CONSULTING</b><br/><font size='9' color='grey'>Médecine du travail</font>", bold10),
            Paragraph(
                f"<font size='9' color='grey'>Généré par Constellab Care<br/>Date : {date_display}</font>",
                ParagraphStyle("right", parent=styles["Normal"], fontSize=9, textColor=colors.grey, alignment=2),
            ),
        ]
    ]
    header_tbl = Table(header_data, colWidths=[9 * cm, 8 * cm])
    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(header_tbl)
    story.append(HRFlowable(width="100%", thickness=1.5, color=blue_color, spaceAfter=4 * mm))

    # ── Title ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("ORDONNANCE MÉDICALE", center_big))

    # ── Patient block ─────────────────────────────────────────────────────────
    story.append(Paragraph("Patient", h2))
    patient_info = [
        ["Nom, Prénom", detail.patient_name],
        ["Date de naissance", detail.patient_date_of_birth],
        ["N° patient", detail.patient_number],
    ]
    pt_tbl = Table(patient_info, colWidths=[5 * cm, 12 * cm])
    pt_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (0, -1), blue_light),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
    ]))
    story.append(pt_tbl)

    # ── Diagnosis ─────────────────────────────────────────────────────────────
    if detail.diagnosis:
        story.append(Paragraph("Diagnostic / Motif", h2))
        story.append(Paragraph(detail.diagnosis, body))

    # ── Drug table ────────────────────────────────────────────────────────────
    story.append(Paragraph("Médicaments prescrits", h2))
    if detail.drugs:
        drug_header = [
            Paragraph("<b>Médicament</b>", bold10),
            Paragraph("<b>Posologie</b>", bold10),
            Paragraph("<b>Fréquence</b>", bold10),
            Paragraph("<b>Durée</b>", bold10),
        ]
        drug_rows = [drug_header]
        for drug in detail.drugs:
            drug_rows.append([
                Paragraph(drug.name or "—", body),
                Paragraph(drug.dosage or "—", body),
                Paragraph(drug.frequency or "—", body),
                Paragraph(drug.duration or "—", body),
            ])
        drug_tbl = Table(drug_rows, colWidths=[5.5 * cm, 4 * cm, 4 * cm, 3.5 * cm])
        drug_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), blue_light),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(*_LIGHT_GREY)]),
        ]))
        story.append(drug_tbl)
    else:
        story.append(Paragraph("Aucun médicament listé.", body))

    # ── Instructions ──────────────────────────────────────────────────────────
    if detail.instructions:
        story.append(Paragraph("Instructions générales", h2))
        story.append(Paragraph(detail.instructions, body))

    # ── Signature ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 12 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=5 * mm))
    sig_data = [
        [
            Paragraph(
                f"<b>{detail.prescribed_by_name}</b><br/>"
                "<font size='9' color='grey'>Médecin prescripteur</font><br/><br/>"
                "<i>(Signature)</i>",
                ParagraphStyle("sig", parent=styles["Normal"], fontSize=10, alignment=2),
            )
        ]
    ]
    sig_tbl = Table(sig_data, colWidths=[17 * cm])
    sig_tbl.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "RIGHT")]))
    story.append(sig_tbl)

    # ── Confidentiality footer ─────────────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        "Ordonnance confidentielle — à remettre uniquement au patient concerné. "
        "Document généré électroniquement par Constellab Care — PS CONSULTING.",
        small,
    ))

    doc.build(story)
    return buf.getvalue()
