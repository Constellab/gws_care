"""State for the program detail page."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class ProgramDetailDTO(BaseModel):
    id: str
    program_number: str
    name: str
    account_id: str = ""
    account_name: str = ""
    start_date: str
    end_date: str
    status: str
    status_label: str
    notes: str = ""
    is_individual: bool = False


class PatientRowDTO(BaseModel):
    id: str
    patient_number: str
    full_name: str


class ExamTypeRowDTO(BaseModel):
    id: str
    code: str
    name: str
    category: str = ""


class VisitRowDTO(BaseModel):
    id: str
    visit_number: str
    patient_name: str = ""
    patient_number: str = ""
    status: str
    status_label: str


class PatientOptionDTO(BaseModel):
    id: str
    label: str


class ExamTypeOptionDTO(BaseModel):
    id: str
    label: str


class ProgramDetailState(RoleState):
    """State for the /program/[id] detail page."""

    program: ProgramDetailDTO | None = None
    patients: list[PatientRowDTO] = []
    exam_types: list[ExamTypeRowDTO] = []
    visits: list[VisitRowDTO] = []
    is_loading: bool = True
    error_message: str = ""
    success_message: str = ""

    # Add patient dialog
    add_patient_dialog_open: bool = False
    patient_search_query: str = ""
    patient_search_results: list[PatientOptionDTO] = []
    patient_search_error: str = ""
    selected_patient_id: str = ""
    selected_patient_label: str = ""
    is_adding_patient: bool = False

    # Add exam type dialog
    add_exam_type_dialog_open: bool = False
    exam_type_options: list[ExamTypeOptionDTO] = []
    selected_exam_type_id: str = ""
    is_adding_exam_type: bool = False

    # Counts for progress bar
    visits_pending: int = 0
    visits_lab_validated: int = 0
    visits_clinic_validated: int = 0
    visits_company_validated: int = 0

    # PDF download
    is_downloading_pdf: bool = False

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_operator, self.is_doctor, self.is_account_admin, self.is_admin)
        if redirect:
            return redirect
        await self._load_program()

    @rx.event
    def go_back(self):
        return rx.redirect("/programs")

    @rx.event
    def go_to_visit(self, visit_id: str):
        return rx.redirect(f"/visit/{visit_id}")

    @rx.var
    def program_status_index(self) -> int:
        """Return the 0-based index of the current program status in the workflow order."""
        order = ["draft", "validated", "in_progress", "lab_done", "doctor_clinic_validated", "doctor_company_validated"]
        if not self.program:
            return 0
        try:
            return order.index(self.program.status)
        except ValueError:
            return 0

    @rx.event
    async def set_workflow_status(self, status: str):
        """Force-set program to any workflow status (supports going back)."""
        if not self.program:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                MedicalProgramService.force_set_status(self.program.id, status)
            await self._load_program()
        except Exception as e:
            self.error_message = str(e)

    # ── Workflow actions ──────────────────────────────────────────────────────

    @rx.event
    async def validate_program(self):
        """DRAFT → VALIDATED (Doctor/Admin)."""
        if not self.program:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                from gws_care.user.user import User
                user = User.get_by_id(str(auth_user.id))
                MedicalProgramService.validate_program(self.program.id, user)
            await self._load_program()
            self.success_message = "MedicalProgram validated successfully."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def start_campaign(self):
        """VALIDATED → IN_PROGRESS."""
        if not self.program:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                MedicalProgramService.start_campaign(self.program.id)
            await self._load_program()
            self.success_message = "MedicalProgram started."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def validate_lab(self):
        """IN_PROGRESS → LAB_DONE (Operator)."""
        if not self.program:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                from gws_care.user.user import User
                user = User.get_by_id(str(auth_user.id))
                MedicalProgramService.validate_lab_campaign(self.program.id, user)
            await self._load_program()
            self.success_message = "Lab validation completed."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def validate_clinic(self):
        """LAB_DONE → DOCTOR_CLINIC_VALIDATED (Doctor)."""
        if not self.program:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                from gws_care.user.user import User
                user = User.get_by_id(str(auth_user.id))
                MedicalProgramService.validate_doctor_clinic_campaign(self.program.id, user)
            await self._load_program()
            self.success_message = "Clinic validation completed."
        except Exception as e:
            self.error_message = str(e)

    # ── PDF downloads ─────────────────────────────────────────────────────────

    @rx.event
    async def download_tube_qr_pdf(self):
        """Generate and download the tube QR code grid PDF for this program."""
        if not self.program:
            return
        self.is_downloading_pdf = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.qr_code import QrCodeService
                pdf_bytes = QrCodeService.generate_tube_qr_grid(self.program.id)
            filename = f"qr_grid_{self.program.program_number}.pdf"
            return rx.download(data=pdf_bytes, filename=filename)
        except Exception as e:
            self.error_message = f"PDF generation error: {e}"
        finally:
            self.is_downloading_pdf = False

    @rx.event
    async def download_campaign_report_pdf(self):
        """Generate and download the program presence/absence report PDF."""
        if not self.program:
            return
        self.is_downloading_pdf = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_campaign_report_pdf
                pdf_bytes = generate_campaign_report_pdf(self.program.id)
            filename = f"rapport_{self.program.program_number}.pdf"
            return rx.download(data=pdf_bytes, filename=filename)
        except Exception as e:
            self.error_message = f"PDF generation error: {e}"
        finally:
            self.is_downloading_pdf = False

    # ── Patient management ────────────────────────────────────────────────────

    @rx.event
    async def open_add_patient_dialog(self):
        if not self.program:
            return
        self.patient_search_query = ""
        self.patient_search_results = []
        self.patient_search_error = ""
        self.selected_patient_id = ""
        self.selected_patient_label = ""
        self.add_patient_dialog_open = True

    @rx.event
    def close_add_patient_dialog(self):
        self.add_patient_dialog_open = False

    @rx.event
    async def search_patients(self, query: str):
        self.patient_search_query = query
        self.patient_search_results = []
        self.selected_patient_id = ""
        self.selected_patient_label = ""
        self.patient_search_error = ""
        if len(query.strip()) < 2:
            return
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                enrolled_ids = {p.id for p in self.patients}
                patients = PatientService.search_patients(search=query.strip(), limit=20)
                # Also search by patient number prefix
                pn_term = query.strip().upper()
                if not pn_term.startswith("PAT-"):
                    pn_term = f"PAT-{pn_term}"
                pn_patients = PatientService.search_patients(patient_number_prefix=pn_term, limit=20)
                # Merge, deduplicate by id
                seen = set()
                merged = []
                for p in list(patients) + list(pn_patients):
                    pid = str(p.id)
                    if pid not in seen:
                        seen.add(pid)
                        merged.append(p)
                self.patient_search_results = [
                    PatientOptionDTO(
                        id=str(p.id),
                        label=f"{p.last_name} {p.first_name} ({p.patient_number})",
                    )
                    for p in merged
                    if str(p.id) not in enrolled_ids
                ]
        except Exception as e:
            self.patient_search_error = str(e)

    @rx.event
    def select_patient(self, patient_id: str, label: str):
        self.selected_patient_id = patient_id
        self.selected_patient_label = label
        self.patient_search_query = label
        self.patient_search_results = []

    @rx.event
    async def confirm_add_patient(self):
        if not self.program or not self.selected_patient_id:
            return
        self.is_adding_patient = True
        try:
            with await self.authenticate_user():
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                MedicalProgramService.add_patient(self.program.id, self.selected_patient_id)
            self.add_patient_dialog_open = False
            await self._load_program()
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_adding_patient = False

    @rx.event
    async def remove_patient(self, patient_id: str):
        if not self.program:
            return
        try:
            with await self.authenticate_user():
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                MedicalProgramService.remove_patient(self.program.id, patient_id)
            await self._load_program()
        except Exception as e:
            self.error_message = str(e)

    # ── ExamType management ───────────────────────────────────────────────────

    @rx.event
    async def open_add_exam_type_dialog(self):
        if not self.program:
            return
        self.error_message = ""
        self.selected_exam_type_id = ""
        self.exam_type_options = []
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam_type_service import ExamTypeService
                # Seed exam types if not yet present (idempotent; startup seed may
                # have failed due to missing auth context)
                ExamTypeService.seed_from_enum()
                all_types = ExamTypeService.list_exam_types(active_only=True)
                enrolled_ids = {et.id for et in self.exam_types}
                self.exam_type_options = [
                    ExamTypeOptionDTO(
                        id=str(et.id),
                        label=f"{et.name} ({et.code})",
                    )
                    for et in all_types
                    if str(et.id) not in enrolled_ids
                ]
        except Exception as e:
            self.error_message = str(e)
        self.add_exam_type_dialog_open = True

    @rx.event
    def close_add_exam_type_dialog(self):
        self.add_exam_type_dialog_open = False

    @rx.event
    def set_selected_exam_type(self, value: str):
        self.selected_exam_type_id = value

    @rx.event
    async def confirm_add_exam_type(self):
        if not self.program or not self.selected_exam_type_id:
            return
        self.is_adding_exam_type = True
        try:
            with await self.authenticate_user():
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                MedicalProgramService.add_exam_type(self.program.id, self.selected_exam_type_id)
            self.add_exam_type_dialog_open = False
            await self._load_program()
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_adding_exam_type = False

    @rx.event
    async def remove_exam_type(self, exam_type_id: str):
        if not self.program:
            return
        try:
            with await self.authenticate_user():
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                MedicalProgramService.remove_exam_type(self.program.id, exam_type_id)
            await self._load_program()
        except Exception as e:
            self.error_message = str(e)

    # ── Internal loader ───────────────────────────────────────────────────────

    async def _load_program(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        self.error_message = ""
        try:
            page_id = self.router.page.params.get("program_id_param", "")
            if not page_id:
                self.program = None
                return

            with await self.authenticate_user():
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                from gws_care.visit.visit_service import VisitService
                from gws_care.visit.visit_status import VisitStatus

                program = MedicalProgramService.get_program(page_id)
                self.program = ProgramDetailDTO(
                    id=str(program.id),
                    program_number=program.program_number,
                    name=program.name,
                    account_id=str(program.account_id) if program.account_id else "",
                    account_name=program.account.name if program.account_id else "",
                    start_date=str(program.start_date),
                    end_date=str(program.end_date),
                    status=program.status.value,
                    status_label=program.status.get_label(),
                    notes=program.notes or "",
                    is_individual=bool(program.is_individual),
                )

                # Patients
                patients = MedicalProgramService.get_patients(page_id)
                self.patients = [
                    PatientRowDTO(
                        id=str(p.id),
                        patient_number=p.patient_number,
                        full_name=p.get_full_name(),
                    )
                    for p in patients
                ]

                # ExamTypes
                exam_types = MedicalProgramService.get_exam_types(page_id)
                self.exam_types = [
                    ExamTypeRowDTO(
                        id=str(et.id),
                        code=et.code,
                        name=et.name,
                        category=et.category.value if hasattr(et.category, "value") else str(et.category),
                    )
                    for et in exam_types
                ]

                # Visits
                visits = VisitService.list_for_campaign(page_id)
                self.visits = [
                    VisitRowDTO(
                        id=str(v.id),
                        visit_number=v.visit_number,
                        patient_name=v.patient.get_full_name() if v.patient_id else "",
                        patient_number=v.patient.patient_number if v.patient_id else "",
                        status=v.status.value,
                        status_label=v.status.get_label(),
                    )
                    for v in visits
                ]

                # Progress counters
                self.visits_pending = sum(1 for v in visits if v.status == VisitStatus.PENDING)
                self.visits_lab_validated = sum(1 for v in visits if v.status == VisitStatus.LAB_VALIDATED)
                self.visits_clinic_validated = sum(1 for v in visits if v.status == VisitStatus.DOCTOR_CLINIC_VALIDATED)
                self.visits_company_validated = sum(1 for v in visits if v.status == VisitStatus.DOCTOR_COMPANY_VALIDATED)

        except Exception as e:
            self.error_message = str(e)
            self.program = None
        finally:
            self.is_loading = False
