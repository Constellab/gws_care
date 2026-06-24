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
    id: str          # ExamTypeRef.id (primary key in the referential)
    code: str = ""   # kept for compatibility, unused for new exams
    name: str
    category: str = ""


class VisitRowDTO(BaseModel):
    id: str
    visit_number: str
    patient_name: str = ""
    patient_number: str = ""
    patient_id: str = ""
    campaign_id: str = ""
    campaign_visit_status: str = ""
    status_label: str = ""


class ExamTypeOptionDTO(BaseModel):
    id: str
    label: str


class PatientOptionDTO(BaseModel):
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

    # Add patient dialog (multi-select)
    add_patient_dialog_open: bool = False
    is_adding_patient: bool = False
    patient_options: list[PatientOptionDTO] = []
    selected_patient_ids: list[str] = []
    patient_search: str = ""
    _all_patient_options: list[PatientOptionDTO] = []

    # Add exam type dialog
    add_exam_type_dialog_open: bool = False
    exam_type_options: list[ExamTypeOptionDTO] = []
    selected_exam_type_id: str = ""
    is_adding_exam_type: bool = False

    # PDF download
    is_downloading_pdf: bool = False

    # Archive dialog
    archive_dialog_open: bool = False
    archive_reason_input: str = ""
    is_archiving: bool = False

    # ── Tabs ──────────────────────────────────────────────────────────────────
    active_tab: str = "patients"

    # ── Patient table filter + sort ────────────────────────────────────────────
    patient_filter_name: str = ""
    patient_filter_number: str = ""
    patient_sort_col: str = "full_name"
    patient_sort_dir: str = "asc"

    # ── Exam type table sort ───────────────────────────────────────────────────
    exam_sort_col: str = "name"
    exam_sort_dir: str = "asc"

    # ── Visit table filter + sort ──────────────────────────────────────────────
    visit_filter_name: str = ""
    visit_filter_number: str = ""
    visit_filter_visit_id: str = ""
    visit_filter_status: str = ""
    visit_sort_col: str = "patient_name"
    visit_sort_dir: str = "asc"

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_operator, self.is_doctor, self.is_account_admin, self.is_admin)
        if redirect:
            return redirect
        await self._load_program()

    @rx.event
    def go_back(self):
        return rx.call_script("window.history.back()")

    @rx.event
    def go_to_visit(self, visit_id: str):
        return rx.redirect(f"/visit/{visit_id}")

    @rx.event
    def go_to_patient_exams(self, campaign_id: str, patient_id: str):
        return rx.redirect(f"/campaign-patient/{campaign_id}/{patient_id}")

    @rx.event
    def set_active_tab(self, tab: str):
        self.active_tab = tab

    # ── Patient filter / sort ──────────────────────────────────────────────────

    @rx.event
    def set_patient_filter_name(self, v: str):
        self.patient_filter_name = v

    @rx.event
    def set_patient_filter_number(self, v: str):
        self.patient_filter_number = v

    @rx.event
    def sort_patients(self, col: str):
        if self.patient_sort_col == col:
            self.patient_sort_dir = "desc" if self.patient_sort_dir == "asc" else "asc"
        else:
            self.patient_sort_col = col
            self.patient_sort_dir = "asc"

    # ── Exam type sort ─────────────────────────────────────────────────────────

    @rx.event
    def sort_exam_types(self, col: str):
        if self.exam_sort_col == col:
            self.exam_sort_dir = "desc" if self.exam_sort_dir == "asc" else "asc"
        else:
            self.exam_sort_col = col
            self.exam_sort_dir = "asc"

    # ── Visit filter / sort ────────────────────────────────────────────────────

    @rx.event
    def set_visit_filter_name(self, v: str):
        self.visit_filter_name = v

    @rx.event
    def set_visit_filter_number(self, v: str):
        self.visit_filter_number = v

    @rx.event
    def set_visit_filter_visit_id(self, v: str):
        self.visit_filter_visit_id = v

    @rx.event
    def set_visit_filter_status(self, v: str):
        self.visit_filter_status = "" if v == "__all__" else v

    @rx.event
    def sort_visits(self, col: str):
        if self.visit_sort_col == col:
            self.visit_sort_dir = "desc" if self.visit_sort_dir == "asc" else "asc"
        else:
            self.visit_sort_col = col
            self.visit_sort_dir = "asc"

    @rx.var
    def program_status_index(self) -> int:
        """Return the 0-based index of the current program status in the workflow order."""
        order = ["draft", "validated", "terrain_exam", "sample_analysis", "closed", "archived"]
        if not self.program:
            return 0
        status = self.program.status
        # Collapse intermediate statuses into sample_analysis (same visual position)
        if status in ("lab_done", "doctor_clinic_validated", "doctor_company_validated"):
            status = "sample_analysis"
        try:
            return order.index(status)
        except ValueError:
            return 0

    @rx.var
    def filtered_patients(self) -> list[PatientRowDTO]:
        rows = list(self.patients)
        if self.patient_filter_name:
            q = self.patient_filter_name.lower()
            rows = [p for p in rows if q in p.full_name.lower()]
        if self.patient_filter_number:
            q = self.patient_filter_number.lower()
            rows = [p for p in rows if q in p.patient_number.lower()]
        rev = self.patient_sort_dir == "desc"
        if self.patient_sort_col == "patient_number":
            rows = sorted(rows, key=lambda p: p.patient_number.lower(), reverse=rev)
        else:
            rows = sorted(rows, key=lambda p: p.full_name.lower(), reverse=rev)
        return rows

    @rx.var
    def filtered_exam_types(self) -> list[ExamTypeRowDTO]:
        rows = list(self.exam_types)
        rev = self.exam_sort_dir == "desc"
        if self.exam_sort_col == "code":
            rows = sorted(rows, key=lambda e: e.code.lower(), reverse=rev)
        elif self.exam_sort_col == "category":
            rows = sorted(rows, key=lambda e: e.category.lower(), reverse=rev)
        else:
            rows = sorted(rows, key=lambda e: e.name.lower(), reverse=rev)
        return rows

    @rx.var
    def filtered_visits(self) -> list[VisitRowDTO]:
        rows = list(self.visits)
        if self.visit_filter_name:
            q = self.visit_filter_name.lower()
            rows = [v for v in rows if q in v.patient_name.lower()]
        if self.visit_filter_number:
            q = self.visit_filter_number.lower()
            rows = [v for v in rows if q in v.patient_number.lower()]
        if self.visit_filter_visit_id:
            q = self.visit_filter_visit_id.lower()
            rows = [v for v in rows if q in v.visit_number.lower()]
        if self.visit_filter_status:
            rows = [v for v in rows if v.campaign_visit_status == self.visit_filter_status]
        rev = self.visit_sort_dir == "desc"
        if self.visit_sort_col == "visit_number":
            rows = sorted(rows, key=lambda v: v.visit_number.lower(), reverse=rev)
        elif self.visit_sort_col == "status":
            rows = sorted(rows, key=lambda v: v.campaign_visit_status, reverse=rev)
        else:
            rows = sorted(rows, key=lambda v: v.patient_name.lower(), reverse=rev)
        return rows

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
            await self._load_program(preserve_tab=True)
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
            await self._load_program(preserve_tab=True)
            self.success_message = "Campaign validated successfully."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def start_campaign(self):
        """VALIDATED → TERRAIN_EXAM."""
        if not self.program:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.start_campaign(self.program.id)
            await self._load_program(preserve_tab=True)
            self.success_message = "Campagne démarrée."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def complete_terrain(self):
        """TERRAIN_EXAM → SAMPLE_ANALYSIS."""
        if not self.program:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.complete_terrain_phase(self.program.id)
            await self._load_program(preserve_tab=True)
            self.success_message = "Phase terrain terminée. Passez à la saisie des résultats."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def validate_lab(self):
        """SAMPLE_ANALYSIS → LAB_DONE (Operator)."""
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
            await self._load_program(preserve_tab=True)
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
            await self._load_program(preserve_tab=True)
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
            await self._load_program(preserve_tab=True)
            self.success_message = "Campaign closed successfully."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    @rx.event
    def open_archive_dialog(self):
        """Open the archive confirmation dialog."""
        self.archive_reason_input = ""
        self.archive_dialog_open = True

    @rx.event
    def close_archive_dialog(self):
        """Close the archive dialog without archiving."""
        self.archive_dialog_open = False
        self.archive_reason_input = ""

    @rx.event
    def set_archive_reason_input(self, value: str):
        self.archive_reason_input = value

    @rx.event
    async def archive_campaign(self):
        """Archive the campaign (CLOSED → ARCHIVED) with mandatory reason."""
        if not self.program:
            return
        reason = self.archive_reason_input.strip()
        if not reason:
            self.error_message = "Un motif d'archivage est obligatoire."
            return
        self.error_message = ""
        self.success_message = ""
        self.is_archiving = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.archive_campaign(self.program.id, reason=reason)
            self.archive_dialog_open = False
            self.archive_reason_input = ""
            await self._load_program(preserve_tab=True)
            self.success_message = "Campagne archivée."
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_archiving = False

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
            self.error_message = f"Erreur lors de la génération du PDF : {e}"
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
            self.error_message = f"Erreur lors de la génération du PDF : {e}"
        finally:
            self.is_downloading_pdf = False

    # ── Patient management ────────────────────────────────────────────────────

    @rx.event
    async def open_add_patient_dialog(self):
        if not self.program:
            return
        self.selected_patient_ids = []
        self.patient_search = ""
        self.patient_options = []
        self._all_patient_options = []
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                from gws_care.campaign.campaign_patient import CampaignPatient
                already_ids = {
                    str(cp.patient_id)
                    for cp in CampaignPatient.select().where(CampaignPatient.program == self.program.id)
                }
                patients = PatientService.search_patients(
                    account_id=self.program.account_id or None,
                    limit=200,
                )
                opts = [
                    PatientOptionDTO(
                        id=str(p.id),
                        label=f"{p.last_name} {p.first_name} ({p.patient_number})",
                    )
                    for p in patients
                    if str(p.id) not in already_ids
                ]
                self._all_patient_options = opts
                self.patient_options = opts
        except Exception as e:
            self.error_message = str(e)
        self.add_patient_dialog_open = True

    @rx.event
    def close_add_patient_dialog(self):
        self.add_patient_dialog_open = False
        self.selected_patient_ids = []
        self.patient_search = ""

    @rx.event
    def toggle_patient_selection(self, patient_id: str):
        if patient_id in self.selected_patient_ids:
            self.selected_patient_ids = [pid for pid in self.selected_patient_ids if pid != patient_id]
        else:
            self.selected_patient_ids = self.selected_patient_ids + [patient_id]

    @rx.event
    def search_patients(self, value: str):
        self.patient_search = value
        f = value.strip().lower()
        if not f:
            self.patient_options = self._all_patient_options
        else:
            self.patient_options = [p for p in self._all_patient_options if f in p.label.lower()]

    @rx.event
    async def confirm_add_patient(self):
        if not self.program or not self.selected_patient_ids:
            return
        self.is_adding_patient = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                for pid in self.selected_patient_ids:
                    CampaignService.add_patient(self.program.id, pid)
            self.add_patient_dialog_open = False
            self.selected_patient_ids = []
            self.patient_search = ""
            await self._load_program(preserve_tab=True)
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
            await self._load_program(preserve_tab=True)
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
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                enrolled_ids = {et.id for et in self.exam_types}
                all_refs = ExamTypeRefService.list_all(active_only=True)
                self.exam_type_options = [
                    ExamTypeOptionDTO(
                        id=r.id,
                        label=r.name,
                    )
                    for r in all_refs
                    if r.id not in enrolled_ids
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
                CampaignService.add_exam_ref(self.program.id, self.selected_exam_type_id)
            self.add_exam_type_dialog_open = False
            await self._load_program(preserve_tab=True)
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
                CampaignService.remove_exam_ref(self.program.id, exam_type_id)
            await self._load_program(preserve_tab=True)
        except Exception as e:
            self.error_message = str(e)

    # ── Internal loader ───────────────────────────────────────────────────────

    async def _load_program(self, preserve_tab: bool = False):
        if not await self.check_authentication():
            return
        self.is_loading = True
        self.error_message = ""
        saved_tab = self.active_tab if preserve_tab else None
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

                # ExamTypes — loaded from referential (ExamTypeRef)
                exam_refs = CampaignService.get_exam_refs(page_id)
                self.exam_types = [
                    ExamTypeRowDTO(
                        id=str(ref.id),
                        name=ref.name,
                        category=ref.get_category_label(),
                    )
                    for ref in exam_refs
                ]

                # Visits
                visits = CampaignVisitService.list_for_campaign(page_id)
                self.visits = [
                    VisitRowDTO(
                        id=str(v.id),
                        visit_number=v.visit_number,
                        patient_name=v.patient.get_full_name() if v.patient_id else "",
                        patient_number=v.patient.patient_number if v.patient_id else "",
                        patient_id=str(v.patient_id) if v.patient_id else "",
                        campaign_id=page_id,
                        campaign_visit_status=v.campaign_visit_status.value,
                        status_label=v.campaign_visit_status.get_label(),
                    )
                    for v in visits
                ]

                # Default tab: show visits once the campaign is validated or beyond
                if self.program.status in ("validated", "terrain_exam", "sample_analysis", "closed", "archived",
                                           "lab_done", "doctor_clinic_validated", "doctor_company_validated"):
                    self.active_tab = "visits"
                else:
                    self.active_tab = "patients"

                # Restore the tab the user was on if we're reloading after an operation
                if saved_tab is not None:
                    self.active_tab = saved_tab

        except Exception as e:
            self.error_message = str(e)
            self.program = None
        finally:
            self.is_loading = False
