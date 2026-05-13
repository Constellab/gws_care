"""QR code generation utilities for Constellab Care.

Phase 4.1 — Patient QR codes (encode patient_number as base64 PNG data URI)
Phase 4.2 — Tube PDF grid for on-site operators
"""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gws_care.exam.exam_type_model import ExamTypeModel
    from gws_care.patient.patient import Patient


def generate_patient_qr_data_uri(patient_number: str) -> str:
    """Return a base64 PNG data URI encoding the patient_number.

    The data URI can be stored directly in Patient.qr_code and displayed
    via ``<img src="...">`` or ``rx.image(src=...)``.
    """
    import qrcode
    from qrcode.image.pil import PilImage  # type: ignore[attr-defined]

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(patient_number)
    qr.make(fit=True)

    img: PilImage = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def generate_tube_qr_data_uri(tube_code: str) -> str:
    """Generate a QR data URI for a tube QR code."""
    return generate_patient_qr_data_uri(tube_code)


# ── PDF tube grid ─────────────────────────────────────────────────────────────


class QrCodeService:
    """Service for QR code generation and PDF tube grids."""

    @classmethod
    def ensure_patient_qr(cls, patient: "Patient") -> str:
        """Return the patient's QR data URI, generating if missing.

        Persists to DB if generated on-the-fly.
        """
        if patient.qr_code:
            return patient.qr_code
        data_uri = generate_patient_qr_data_uri(patient.patient_number)
        patient.qr_code = data_uri
        patient.save()
        return data_uri

    @classmethod
    def generate_all_patient_qr_codes(cls) -> int:
        """Backfill QR codes for all patients that don't have one.

        Returns the number of patients updated.
        """
        from gws_care.patient.patient import Patient
        patients = list(Patient.select().where(Patient.qr_code.is_null(True)))
        for patient in patients:
            patient.qr_code = generate_patient_qr_data_uri(patient.patient_number)
            patient.save()
        return len(patients)

    @classmethod
    def generate_tube_qr_grid(cls, program_id: str) -> bytes:
        """Generate an A4 printable PDF grid of tube QR codes for a program.

        Grid layout (portrait A4):
          - Header: program name + account
          - One section per patient:
            - Patient name + DOB
            - One QR code box per exam type (encoded as TUBE-<patient_number>-<exam_code>)

        Returns PDF bytes.
        """
        import io as _io

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm, mm
        from reportlab.platypus import Image as RLImage
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        from gws_care.medical_program.medical_program_service import MedicalProgramService

        program = MedicalProgramService.get_program(program_id)
        patients = MedicalProgramService.get_patients(program_id)
        exam_types = MedicalProgramService.get_exam_types(program_id)

        buf = _io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "title",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=4 * mm,
        )
        subtitle_style = ParagraphStyle(
            "subtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.gray,
            spaceAfter=8 * mm,
        )
        patient_style = ParagraphStyle(
            "patient",
            parent=styles["Heading2"],
            fontSize=11,
            spaceBefore=6 * mm,
            spaceAfter=2 * mm,
        )
        label_style = ParagraphStyle(
            "label",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.darkgrey,
        )

        story = []

        # Title
        story.append(Paragraph(f"Grille QR Codes — {program.name}", title_style))
        story.append(Paragraph(
            f"Compte : {program.account.name if program.account_id else '—'}  "
            f"| Du {program.start_date} au {program.end_date}",
            subtitle_style,
        ))

        if not exam_types:
            story.append(Paragraph("Aucun type d'examen configuré pour cette campagne.", styles["Normal"]))
        elif not patients:
            story.append(Paragraph("Aucun patient inscrit dans cette campagne.", styles["Normal"]))
        else:
            qr_size = 2.2 * cm  # QR image side length

            for patient in patients:
                dob_str = str(patient.date_of_birth) if patient.date_of_birth else "—"
                story.append(Paragraph(
                    f"{patient.last_name} {patient.first_name} &nbsp;&nbsp;<font color='gray' size='9'>Né(e) le {dob_str} | {patient.patient_number}</font>",
                    patient_style,
                ))

                # Build a row of QR codes (one per exam type)
                table_data = [[], []]  # row 0 = QR images, row 1 = labels
                for et in exam_types:
                    tube_code = f"TUBE-{patient.patient_number}-{et.code}"
                    qr_uri = generate_tube_qr_data_uri(tube_code)
                    # Convert data URI to PIL image, then to RLImage
                    b64_data = qr_uri.split(",", 1)[1]
                    img_bytes = base64.b64decode(b64_data)
                    rl_img = RLImage(_io.BytesIO(img_bytes), width=qr_size, height=qr_size)
                    table_data[0].append(rl_img)
                    table_data[1].append(Paragraph(et.name[:20], label_style))

                col_width = qr_size + 4 * mm
                tbl = Table(
                    table_data,
                    colWidths=[col_width] * len(exam_types),
                    rowHeights=[qr_size + 2 * mm, 10 * mm],
                )
                tbl.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]))
                story.append(tbl)
                story.append(Spacer(1, 3 * mm))

        doc.build(story)
        return buf.getvalue()
