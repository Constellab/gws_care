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
    # Medical / identity fields
    social_security_number: str | None = None
    sex: str | None = None
    qr_code: str | None = None


class ExamRowDTO(BaseModel):
    """Lightweight exam row for the patient detail exam list."""

    id: str
    exam_date: str
    exam_type_label: str
    status: str


class PatientVisitRowDTO(BaseModel):
    """Lightweight visit row for the patient detail visits list."""

    id: str
    visit_number: str
    campaign_name: str = ""
    program_id: str = ""
    scheduled_at: str = ""
    status: str
    status_label: str = ""


class AccountForVisitDTO(BaseModel):
    """Account option for the create-visit form select."""

    id: str
    name: str


class PatientDetailState(ReflexMainState):
    """State for the patient detail page."""

    patient: PatientDetailDTO | None = None
    exams: list[ExamRowDTO] = []
    patient_visits: list[PatientVisitRowDTO] = []
    is_loading: bool = False
    error_message: str = ""
    show_id_card: bool = False

    # Create standalone visit dialog
    show_create_visit_dialog: bool = False
    create_visit_scheduled_at: str = ""
    create_visit_account_id: str = ""
    create_visit_error: str = ""
    patient_accounts: list[AccountForVisitDTO] = []

    # ── Sort state ─────────────────────────────────────────────
    exam_sort_column: str = "exam_date"
    exam_sort_ascending: bool = False
    @rx.event
    async def set_exam_sort(self, column: str):
        if self.exam_sort_column == column:
            self.exam_sort_ascending = not self.exam_sort_ascending
        else:
            self.exam_sort_column = column
            self.exam_sort_ascending = True


    @rx.var
    def sorted_exams(self) -> list[ExamRowDTO]:
        col = self.exam_sort_column
        return sorted(
            self.exams,
            key=lambda e: (getattr(e, col) or "").lower(),
            reverse=not self.exam_sort_ascending,
        )


    @rx.event
    async def on_load(self):
        """Load patient data and exam list when the page is mounted."""
        await self._load_patient()

    @rx.event
    def go_back(self):
        """Navigate back to the patient list."""
        return rx.redirect("/")

    @rx.event
    def open_id_card(self):
        """Open the patient ID card dialog."""
        self.show_id_card = True

    @rx.event
    def close_id_card(self):
        """Close the patient ID card dialog."""
        self.show_id_card = False

    @rx.event
    async def download_id_card_pdf(self):
        """Generate and download the patient ID card as a PDF."""
        if not self.patient:
            return
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_patient_id_card_pdf
                pdf_bytes = generate_patient_id_card_pdf(self.patient.id)
            filename = f"carte_patient_{self.patient.patient_number}.pdf"
            return rx.download(data=pdf_bytes, filename=filename)
        except Exception as e:
            self.error_message = f"PDF generation error: {e}"

    @rx.event
    def go_to_exam(self, exam_id: str):
        """Navigate to the exam detail page."""
        return rx.redirect(f"/exam/{exam_id}")

    @rx.event
    def go_to_visit(self, visit_id: str):
        """Navigate to the visit detail page."""
        return rx.redirect(f"/visit/{visit_id}")

    @rx.event
    def go_to_program(self, program_id: str):
        """Navigate to the program detail page."""
        return rx.redirect(f"/program/{program_id}")

    @rx.event
    def go_to_visits(self):
        """Navigate to the visits page."""
        return rx.redirect("/visits")

    # ── Standalone visit creation ─────────────────────────────────────────────

    @rx.event
    def open_create_visit_dialog(self):
        self.show_create_visit_dialog = True
        self.create_visit_scheduled_at = ""
        self.create_visit_account_id = ""
        self.create_visit_error = ""

    @rx.event
    def close_create_visit_dialog(self):
        self.show_create_visit_dialog = False

    @rx.event
    def set_create_visit_scheduled_at(self, value: str):
        self.create_visit_scheduled_at = value

    @rx.event
    def set_create_visit_account_id(self, value: str):
        self.create_visit_account_id = "" if value == "none" else value

    @rx.event
    async def save_create_visit(self):
        if not self.patient:
            return
        if not self.create_visit_scheduled_at:
            self.create_visit_error = "Veuillez sélectionner une date et une heure."
            return
        self.create_visit_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.visit_dto import SaveStandaloneVisitDTO
                from gws_care.visit.visit_service import VisitService
                dto = SaveStandaloneVisitDTO(
                    patient_id=self.patient.id,
                    billing_account_id=self.create_visit_account_id or None,
                    scheduled_at=self.create_visit_scheduled_at,
                )
                _visit, program = VisitService.create_visit_with_default_program(
                    patient_id=dto.patient_id,
                    scheduled_at_str=dto.scheduled_at,
                    billing_account_id=dto.billing_account_id,
                )
            self.show_create_visit_dialog = False
            return rx.redirect(f"/program/{program.id}")
        except Exception as e:
            self.create_visit_error = str(e)

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
                from gws_care.account.account_service import AccountService
                from gws_care.exam.exam_service import ExamService
                from gws_care.patient.patient_service import PatientService
                from gws_care.visit.visit_service import VisitService
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
                    social_security_number=p.social_security_number,
                    sex=p.sex,
                    qr_code=p.qr_code,
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
                visits = VisitService.list_for_patient(patient_id)
                self.patient_visits = [
                    PatientVisitRowDTO(
                        id=str(v.id),
                        visit_number=v.visit_number,
                        campaign_name=v.program.name if v.program_id else "",
                        program_id=str(v.program_id) if v.program_id else "",
                        scheduled_at=v.scheduled_at.isoformat() if v.scheduled_at else "",
                        status=v.status.value,
                        status_label=v.status.get_label(),
                    )
                    for v in visits
                ]
                accounts = AccountService.list_accounts()
                self.patient_accounts = [
                    AccountForVisitDTO(id=str(a.id), name=a.name) for a in accounts
                ]
        except Exception as e:
            self.error_message = f"Error loading patient: {e}"
        finally:
            self.is_loading = False

    async def _reload_visits(self):
        """Reload only the visits list for the current patient."""
        patient_id = self.patient_id_param
        if not patient_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.visit.visit_service import VisitService
                visits = VisitService.list_for_patient(patient_id)
                self.patient_visits = [
                    PatientVisitRowDTO(
                        id=str(v.id),
                        visit_number=v.visit_number,
                        campaign_name=v.program.name if v.program_id else "",
                        program_id=str(v.program_id) if v.program_id else "",
                        scheduled_at=v.scheduled_at.isoformat() if v.scheduled_at else "",
                        status=v.status.value,
                        status_label=v.status.get_label(),
                    )
                    for v in visits
                ]
        except Exception:
            pass
