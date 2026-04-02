"""State management for the patient detail page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class PatientDetailDTO(BaseModel):
    """Full patient details DTO for the detail page."""

    id: str
    patient_number: str
    last_name: str
    first_name: str
    birth_name: str | None = None
    date_of_birth: str
    gender: str
    photo: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    phone: str | None = None
    email: str | None = None
    primary_physician_name: str | None = None
    primary_physician_phone: str | None = None


class ExamRowDTO(BaseModel):
    """Lightweight exam row for the patient detail exam list."""

    id: str
    exam_date: str
    exam_type_label: str
    status: str


class AppointmentRowDTO(BaseModel):
    """Lightweight appointment row for the patient detail appointments list."""

    id: str
    scheduled_at: str
    exam_type_label: str
    status: str
    account_name: str | None = None


class PatientDetailState(ReflexMainState):
    """State for the patient detail page."""

    patient: PatientDetailDTO | None = None
    exams: list[ExamRowDTO] = []
    appointments: list[AppointmentRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    @rx.event
    async def on_load(self):
        """Load patient data and exam list when the page is mounted."""
        await self._load_patient()

    @rx.event
    def go_back(self):
        """Navigate back to the patient list."""
        return rx.redirect("/")

    @rx.event
    def go_to_exam(self, exam_id: str):
        """Navigate to the exam detail page."""
        return rx.redirect(f"/exam/{exam_id}")

    @rx.event
    def go_to_appointments(self):
        """Navigate to the appointments page."""
        return rx.redirect("/appointments")

    @rx.event
    async def download_exam_history(self):
        """Generate and download the patient's exam history as CSV."""
        if not self.patient:
            return
        try:
            with await self.authenticate_user():
                from gws_care.export.csv_export_service import generate_exam_history_csv
                csv_bytes = generate_exam_history_csv(self.patient.id)

            filename = f"exam_history_{self.patient.patient_number}.csv"
            return rx.download(data=csv_bytes, filename=filename)
        except Exception as e:
            self.error_message = f"Export error: {e}"

    async def _load_patient(self):
        """Internal: fetch patient and their exams from DB using URL param."""
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return

        patient_id = self.patient_id_param
        if not patient_id:
            self.error_message = "No patient ID in URL"
            return

        self.is_loading = True
        self.error_message = ""

        try:
            with await self.authenticate_user():
                from gws_care.appointment.appointment_service import AppointmentService
                from gws_care.exam.exam_service import ExamService
                from gws_care.patient.patient_service import PatientService
                p = PatientService.get_patient(patient_id)
                self.patient = PatientDetailDTO(
                    id=str(p.id),
                    patient_number=p.patient_number,
                    last_name=p.last_name,
                    first_name=p.first_name,
                    birth_name=p.birth_name,
                    date_of_birth=p.date_of_birth.isoformat(),
                    gender=p.gender,
                    photo=p.photo,
                    address=p.address,
                    postal_code=p.postal_code,
                    city=p.city,
                    phone=p.phone,
                    email=p.email,
                    primary_physician_name=p.primary_physician_name,
                    primary_physician_phone=p.primary_physician_phone,
                )
                exams = ExamService.list_exams_for_patient(patient_id)
                self.exams = [
                    ExamRowDTO(
                        id=str(e.id),
                        exam_date=e.exam_date.isoformat(),
                        exam_type_label=e.exam_type.get_label(),
                        status=e.status.value,
                    )
                    for e in exams
                ]
                appointments = AppointmentService.list_for_patient(patient_id)
                self.appointments = [
                    AppointmentRowDTO(
                        id=str(a.id),
                        scheduled_at=a.scheduled_at.isoformat(),
                        exam_type_label=a.exam_type.get_label(),
                        status=a.status.value,
                        account_name=a.billing_account.name if a.billing_account_id else None,
                    )
                    for a in appointments
                ]
        except Exception as e:
            self.error_message = f"Error loading patient: {e}"
        finally:
            self.is_loading = False
