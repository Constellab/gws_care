"""State for the certificate detail page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class CertificateDetailDTO(BaseModel):
    id: str
    issue_date: str
    certificate_type: str = "APTITUDE"
    certificate_type_label: str = ""
    conclusion: str = ""
    is_fit_for_work: bool = True
    restrictions: str = ""
    issued_by_name: str = ""
    patient_id: str = ""
    patient_name: str = ""
    patient_number: str = ""
    patient_date_of_birth: str = ""
    # Extended fields
    start_date: str = ""
    end_date: str = ""
    return_date: str = ""
    exposure_type: str = ""
    vaccine_name: str = ""
    vaccine_lot: str = ""
    next_booster: str = ""
    accident_date: str = ""
    body_part: str = ""
    visit_subtype: str = ""
    is_archived: bool = False


class CertificateDetailState(ReflexMainState):
    """State for the certificate detail page."""

    certificate: CertificateDetailDTO | None = None
    is_loading: bool = False
    error_message: str = ""
    is_archiving: bool = False
    is_sending_email: bool = False

    @rx.event
    async def on_load(self):
        await self._load_certificate()

    async def _load_certificate(self):
        certificate_id = self.certificate_id_param
        if not certificate_id:
            self.error_message = "No certificate ID in URL"
            return
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.certificate.medical_certificate import (
                    CERTIFICATE_TYPES,
                    MedicalCertificateService,
                )
                from gws_care.patient.patient import Patient
                from gws_care.user.user import User
                c = MedicalCertificateService.get(certificate_id)
                patient = Patient.get_by_id(str(c.patient_id))
                issued_by = ""
                if c.issued_by_id:
                    try:
                        u = User.get_by_id(str(c.issued_by_id))
                        issued_by = f"Dr. {u.first_name} {u.last_name}".strip()
                    except Exception:
                        pass
                self.certificate = CertificateDetailDTO(
                    id=str(c.id),
                    issue_date=c.issue_date.isoformat() if c.issue_date else "",
                    certificate_type=c.certificate_type or "APTITUDE",
                    certificate_type_label=CERTIFICATE_TYPES.get(c.certificate_type or "APTITUDE", c.certificate_type or ""),
                    conclusion=c.conclusion or "",
                    is_fit_for_work=bool(c.is_fit_for_work),
                    restrictions=c.restrictions or "",
                    issued_by_name=issued_by,
                    patient_id=str(patient.id),
                    patient_name=f"{patient.first_name} {patient.last_name}".strip(),
                    patient_number=patient.patient_number,
                    patient_date_of_birth=patient.date_of_birth.isoformat() if patient.date_of_birth else "",
                    start_date=c.start_date.isoformat() if c.start_date else "",
                    end_date=c.end_date.isoformat() if c.end_date else "",
                    return_date=c.return_date.isoformat() if c.return_date else "",
                    exposure_type=c.exposure_type or "",
                    vaccine_name=c.vaccine_name or "",
                    vaccine_lot=c.vaccine_lot or "",
                    next_booster=c.next_booster.isoformat() if c.next_booster else "",
                    accident_date=c.accident_date.isoformat() if c.accident_date else "",
                    body_part=c.body_part or "",
                    visit_subtype=c.visit_subtype or "",
                    is_archived=bool(c.is_archived),
                )
        except Exception as e:
            self.error_message = f"Erreur : {e}"
        finally:
            self.is_loading = False

    @rx.event
    def go_to_patient(self):
        """Navigate to the patient detail page."""
        if self.certificate and self.certificate.patient_id:
            return rx.redirect(f"/patient/{self.certificate.patient_id}")
        return rx.redirect("/")

    @rx.event
    async def send_pdf_email(self):
        """Send the certificate PDF to the patient by email."""
        if not self.certificate:
            return
        self.error_message = ""
        self.is_sending_email = True
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.notification.notification_service import NotificationService
                from gws_care.pdf import generate_certificate_pdf
                from gws_care.user.user import User
                pdf_bytes = generate_certificate_pdf(self.certificate_id_param)
                doctor = User.get_by_id(str(auth_user.id))
                NotificationService.send_pdf_to_patient(
                    patient_id=self.certificate.patient_id,
                    subject=f"Certificat médical du {self.certificate.issue_date}",
                    body=(
                        f"Cher(e) {self.certificate.patient_name},\n\n"
                        f"Veuillez trouver ci-joint votre certificat médical "
                        f"du {self.certificate.issue_date}.\n\n"
                        f"Cordialement,\nConstellab Care"
                    ),
                    pdf_bytes=pdf_bytes,
                    filename=f"certificat_{self.certificate_id_param[:8]}.pdf",
                    sent_by=doctor,
                )
        except Exception as e:
            self.error_message = f"Erreur envoi email : {e}"
        finally:
            self.is_sending_email = False

    @rx.event
    def go_back_to_patient(self):
        return rx.call_script("window.history.back()")

    @rx.event
    async def download_pdf(self):
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_certificate_pdf
                pdf_bytes = generate_certificate_pdf(self.certificate_id_param)
            cert_id = self.certificate_id_param
            return rx.download(data=pdf_bytes, filename=f"certificat_{cert_id[:8]}.pdf")
        except Exception as e:
            self.error_message = f"Erreur génération PDF : {e}"

    @rx.event
    async def view_pdf(self):
        """Open PDF in a new browser tab."""
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_certificate_pdf
                pdf_bytes = generate_certificate_pdf(self.certificate_id_param)
            import base64
            b64 = base64.b64encode(pdf_bytes).decode()
            return rx.call_script(
                f"const w=window.open();w.document.write('<iframe src=\"data:application/pdf;base64,{b64}\" width=\"100%\" height=\"100%\"></iframe>');"
            )
        except Exception as e:
            self.error_message = f"Erreur génération PDF : {e}"

    @rx.event
    async def toggle_archive(self):
        if not self.certificate:
            return
        self.is_archiving = True
        try:
            with await self.authenticate_user():
                from gws_care.certificate.medical_certificate import MedicalCertificateService
                if self.certificate.is_archived:
                    MedicalCertificateService.unarchive(self.certificate_id_param)
                else:
                    MedicalCertificateService.archive(self.certificate_id_param)
            await self._load_certificate()
        except Exception as e:
            self.error_message = f"Erreur : {e}"
        finally:
            self.is_archiving = False
