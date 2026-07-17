"""State for the prescription detail page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class DrugLineDTO(BaseModel):
    name: str = ""
    dosage: str = ""
    frequency: str = ""
    duration: str = ""


class PrescriptionDetailDTO(BaseModel):
    id: str
    prescription_date: str
    diagnosis: str = ""
    instructions: str = ""
    prescribed_by_name: str = ""
    patient_id: str = ""
    patient_name: str = ""
    patient_number: str = ""
    patient_date_of_birth: str = ""
    drugs: list[DrugLineDTO] = []
    is_archived: bool = False


class PrescriptionDetailState(ReflexMainState):
    """State for the prescription detail page."""

    prescription: PrescriptionDetailDTO | None = None
    is_loading: bool = False
    error_message: str = ""
    is_archiving: bool = False
    is_sending_email: bool = False
    is_deleting: bool = False
    confirm_delete_open: bool = False

    @rx.event
    async def on_load(self):
        await self._load_prescription()

    async def _load_prescription(self):
        prescription_id = self.prescription_id_param
        if not prescription_id:
            self.error_message = "No prescription ID in URL"
            return
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient import Patient
                from gws_care.prescription.prescription import PrescriptionService
                from gws_care.user.user import User
                p = PrescriptionService.get(prescription_id)
                patient = Patient.get_by_id(str(p.patient_id))
                prescribed_by = ""
                if p.prescribed_by_id:
                    try:
                        u = User.get_by_id(str(p.prescribed_by_id))
                        prescribed_by = f"Dr. {u.first_name} {u.last_name}".strip()
                    except Exception:
                        pass
                self.prescription = PrescriptionDetailDTO(
                    id=str(p.id),
                    prescription_date=p.prescription_date.isoformat(),
                    diagnosis=p.diagnosis or "",
                    instructions=p.instructions or "",
                    prescribed_by_name=prescribed_by,
                    patient_id=str(patient.id),
                    patient_name=f"{patient.first_name} {patient.last_name}".strip(),
                    patient_number=patient.patient_number,
                    patient_date_of_birth=patient.date_of_birth.isoformat() if patient.date_of_birth else "",
                    drugs=[DrugLineDTO(**d) for d in p.drugs],
                    is_archived=bool(p.is_archived),
                )
        except Exception as e:
            self.error_message = f"Erreur : {e}"
        finally:
            self.is_loading = False

    @rx.event
    def go_back(self):
        if self.prescription:
            return rx.redirect(f"/patient/{self.prescription.patient_number}")
        return rx.redirect("/")

    @rx.event
    def go_to_patient(self):
        """Navigate to the patient detail page."""
        if self.prescription and self.prescription.patient_id:
            return rx.redirect(f"/patient/{self.prescription.patient_id}")
        return rx.redirect("/")

    @rx.event
    async def send_pdf_email(self):
        """Send the prescription PDF to the patient by email."""
        if not self.prescription:
            return
        self.error_message = ""
        self.is_sending_email = True
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.notification.notification_service import NotificationService
                from gws_care.pdf import generate_prescription_pdf
                from gws_care.user.user import User
                pdf_bytes = generate_prescription_pdf(self.prescription_id_param)
                doctor = User.get_by_id(str(auth_user.id))
                NotificationService.send_pdf_to_patient(
                    patient_id=self.prescription.patient_id,
                    subject=f"Ordonnance du {self.prescription.prescription_date}",
                    body=(
                        f"Cher(e) {self.prescription.patient_name},\n\n"
                        f"Veuillez trouver ci-joint votre ordonnance "
                        f"du {self.prescription.prescription_date}.\n\n"
                        f"Cordialement,\nConstellab Care"
                    ),
                    pdf_bytes=pdf_bytes,
                    filename=f"ordonnance_{self.prescription_id_param[:8]}.pdf",
                    sent_by=doctor,
                )
        except Exception as e:
            self.error_message = f"Erreur envoi email : {e}"
        finally:
            self.is_sending_email = False

    @rx.event
    def go_back_to_patient(self):
        """Navigate back using browser history."""
        return rx.call_script("window.history.back()")

    @rx.event
    async def download_pdf(self):
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_prescription_pdf
                pdf_bytes = generate_prescription_pdf(self.prescription_id_param)
            presc_id = self.prescription_id_param
            return rx.download(data=pdf_bytes, filename=f"ordonnance_{presc_id[:8]}.pdf")
        except Exception as e:
            self.error_message = f"Erreur génération PDF : {e}"

    @rx.event
    async def view_pdf(self):
        """Open PDF in a new browser tab."""
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_prescription_pdf
                pdf_bytes = generate_prescription_pdf(self.prescription_id_param)
            import base64
            b64 = base64.b64encode(pdf_bytes).decode()
            return rx.call_script(
                f"const w=window.open();w.document.write('<iframe src=\"data:application/pdf;base64,{b64}\" width=\"100%\" height=\"100%\"></iframe>');"
            )
        except Exception as e:
            self.error_message = f"Erreur génération PDF : {e}"

    @rx.event
    async def toggle_archive(self):
        if not self.prescription:
            return
        self.is_archiving = True
        try:
            with await self.authenticate_user():
                from gws_care.prescription.prescription import PrescriptionService
                if self.prescription.is_archived:
                    PrescriptionService.unarchive(self.prescription_id_param)
                else:
                    PrescriptionService.archive(self.prescription_id_param)
            await self._load_prescription()
        except Exception as e:
            self.error_message = f"Erreur : {e}"
        finally:
            self.is_archiving = False

    @rx.event
    def open_confirm_delete(self):
        self.confirm_delete_open = True

    @rx.event
    def close_confirm_delete(self):
        self.confirm_delete_open = False

    @rx.event
    async def delete_prescription(self):
        if not self.prescription:
            return
        self.is_deleting = True
        patient_id = self.prescription.patient_id
        try:
            with await self.authenticate_user():
                from gws_care.prescription.prescription import PrescriptionService
                PrescriptionService.delete(self.prescription_id_param)
            self.confirm_delete_open = False
            return rx.redirect(f"/patient/{patient_id}")
        except Exception as e:
            self.error_message = f"Erreur : {e}"
        finally:
            self.is_deleting = False
