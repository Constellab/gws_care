"""State for the campaign detail page."""

import reflex as rx
from pydantic import BaseModel

from ..common.patient_picker_state import PatientPickerRowDTO, PatientPickerState

# Ordered visit statuses from earliest to latest (cancelled excluded — treated separately)
_VISIT_STATUS_ORDER = [
    "pending",
    "visit_done",
    "lab_done",
    "doctor_clinic_validated",
    "doctor_company_validated",
]


class CampaignDetailStateDTO(BaseModel):
    id: str
    campaign_number: str
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
    campaign_visit_status: str = ""
    status_label: str = ""


class ExamTypeOptionDTO(BaseModel):
    id: str
    label: str


class CampaignDetailState(PatientPickerState):
    """State for the /program/[id] detail page."""

    # ── Patient picker vars (declared here for independent state storage) ─────
    picker_patients: list[PatientPickerRowDTO] = []
    picker_is_loading: bool = False
    picker_error: str = ""
    picker_filter_name: str = ""
    picker_filter_number: str = ""
    picker_account_id: str = ""
    picker_is_open: bool = False
    picker_selected_id: str = ""
    picker_selected_label: str = ""

    # ── Patient picker events ─────────────────────────────────────────────────────

    @rx.event
    async def open_patient_picker(self):
        await self._open_patient_picker()

    @rx.event
    def close_patient_picker(self):
        self.picker_is_open = False

    @rx.event
    async def picker_clear_selection(self):
        self.picker_selected_id = ""
        self.picker_selected_label = ""

    @rx.event
    async def picker_set_filter_name(self, value: str):
        await self._picker_set_filter_name(value)

    @rx.event
    async def picker_set_filter_number(self, value: str):
        await self._picker_set_filter_number(value)

    @rx.event
    async def picker_clear_filters(self):
        await self._picker_clear_filters()

    @rx.event
    def picker_select_patient(self, patient_id: str, label: str):
        self.picker_selected_id = patient_id
        self.picker_selected_label = label
        self.picker_is_open = False

    program: CampaignDetailStateDTO | None = None
    patients: list[PatientRowDTO] = []
    exam_types: list[ExamTypeRowDTO] = []
    visits: list[VisitRowDTO] = []
    is_loading: bool = True
    error_message: str = ""
    success_message: str = ""

    # Add patient dialog
    add_patient_dialog_open: bool = False
    is_adding_patient: bool = False

    # Add exam type dialog
    add_exam_type_dialog_open: bool = False
    exam_type_options: list[ExamTypeOptionDTO] = []
    selected_exam_type_id: str = ""
    is_adding_exam_type: bool = False

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
        return rx.redirect("/campaigns")

    @rx.event
    def go_to_visit(self, visit_id: str):
        return rx.redirect(f"/visit/{visit_id}")

    @rx.var
    def program_status_index(self) -> int:
        """Return the 0-based index of the current program status in the workflow order."""
        order = ["draft", "validated", "in_progress", "closed", "archived"]
        if not self.program:
            return 0
        # Map doctor_company_validated to in_progress (same visual position)
        status = self.program.status
        if status == "doctor_company_validated":
            status = "in_progress"
        try:
            return order.index(status)
        except ValueError:
            return 0

    @rx.var
    def can_validate_program(self) -> bool:
        """True if the program has at least one patient and one exam type."""
        return len(self.patients) > 0 and len(self.exam_types) > 0

    @rx.var
    def all_visits_lab_ready(self) -> bool:
        """True if every non-cancelled visit has reached at least LAB_VALIDATED."""
        non_cancelled = [v for v in self.visits if v.campaign_visit_status != "cancelled"]
        if not non_cancelled:
            return False
        min_idx = _VISIT_STATUS_ORDER.index("lab_done")
        compliant_statuses = set(_VISIT_STATUS_ORDER[min_idx:])
        return all(v.campaign_visit_status in compliant_statuses for v in non_cancelled)

    @rx.var
    def all_visits_clinic_ready(self) -> bool:
        """True if every non-cancelled visit has reached at least DOCTOR_CLINIC_VALIDATED."""
        non_cancelled = [v for v in self.visits if v.campaign_visit_status != "cancelled"]
        if not non_cancelled:
            return False
        min_idx = _VISIT_STATUS_ORDER.index("doctor_clinic_validated")
        compliant_statuses = set(_VISIT_STATUS_ORDER[min_idx:])
        return all(v.campaign_visit_status in compliant_statuses for v in non_cancelled)

    @rx.var
    def all_visits_company_validated(self) -> bool:
        """True if every non-cancelled visit has reached DOCTOR_COMPANY_VALIDATED."""
        non_cancelled = [v for v in self.visits if v.campaign_visit_status != "cancelled"]
        if not non_cancelled:
            return False
        return all(v.campaign_visit_status == "doctor_company_validated" for v in non_cancelled)

    @rx.event
    async def set_workflow_status(self, status: str):
        """Force-set program to any workflow status (supports going back)."""
        if not self.program:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.force_set_status(self.program.id, status)
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
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.user.user import User
                user = User.get_by_id(str(auth_user.id))
                CampaignService.validate_campaign(self.program.id, user)
            await self._load_program()
            self.success_message = "Campaign validated successfully."
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
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.start_campaign(self.program.id)
            await self._load_program()
            self.success_message = "Campaign started."
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
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.user.user import User
                user = User.get_by_id(str(auth_user.id))
                CampaignService.validate_lab_campaign(self.program.id, user)
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
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.user.user import User
                user = User.get_by_id(str(auth_user.id))
                CampaignService.validate_doctor_clinic_campaign(self.program.id, user)
            await self._load_program()
            self.success_message = "Clinic validation completed."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def close_campaign(self):
        """Close the campaign (→ CLOSED)."""
        if not self.program:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.close_campaign(self.program.id)
            await self._load_program()
            self.success_message = "Campaign closed successfully."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def archive_campaign(self):
        """Archive the campaign (CLOSED → ARCHIVED)."""
        if not self.program:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.archive_campaign(self.program.id)
            await self._load_program()
            self.success_message = "Campaign archived successfully."
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
            filename = f"qr_grid_{self.program.campaign_number}.pdf"
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
            filename = f"rapport_{self.program.campaign_number}.pdf"
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
        # Open the picker restricted to the program's billing account
        await self._open_picker(account_id=self.program.account_id or "")
        self.add_patient_dialog_open = True

    @rx.event
    def close_add_patient_dialog(self):
        self.add_patient_dialog_open = False

    @rx.event
    async def confirm_add_patient(self):
        if not self.program or not self.picker_selected_id:
            return
        self.is_adding_patient = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.add_patient(self.program.id, self.picker_selected_id)
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
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.remove_patient(self.program.id, patient_id)
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
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.add_exam_type(self.program.id, self.selected_exam_type_id)
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
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.remove_exam_type(self.program.id, exam_type_id)
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
            page_id = self.router.page.params.get("campaign_id_param", "")
            if not page_id:
                self.program = None
                return

            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.visit.campaign_visit_service import CampaignVisitService

                program = CampaignService.get_campaign(page_id)
                self.program = CampaignDetailStateDTO(
                    id=str(program.id),
                    campaign_number=program.campaign_number,
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
                patients = CampaignService.get_patients(page_id)
                self.patients = [
                    PatientRowDTO(
                        id=str(p.id),
                        patient_number=p.patient_number,
                        full_name=p.get_full_name(),
                    )
                    for p in patients
                ]

                # ExamTypes
                exam_types = CampaignService.get_exam_types(page_id)
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
                visits = CampaignVisitService.list_for_campaign(page_id)
                self.visits = [
                    VisitRowDTO(
                        id=str(v.id),
                        visit_number=v.visit_number,
                        patient_name=v.patient.get_full_name() if v.patient_id else "",
                        patient_number=v.patient.patient_number if v.patient_id else "",
                        campaign_visit_status=v.campaign_visit_status.value,
                        status_label=v.campaign_visit_status.get_label(),
                    )
                    for v in visits
                ]

        except Exception as e:
            self.error_message = str(e)
            self.program = None
        finally:
            self.is_loading = False
