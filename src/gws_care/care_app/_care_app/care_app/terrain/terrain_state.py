"""State for the on-site page (Phase 7.4).

Route: /on-site/[program_id_param]

Used by the Opérateur Terrain (OT) to:
- View the list of patients in a program
- See each patient's QR code
- Search by patient name / QR scan result
- Mark exams as done on-site (is_done_on-site)
- Download the tube QR code grid PDF
"""

from __future__ import annotations

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class TerrainExamDTO(BaseModel):
    id: str
    exam_type_name: str
    exam_type_code: str
    is_done_on_site: bool = False
    tube_qr_code: str = ""
    patient_id: str = ""
    visit_id: str = ""


class TerrainPatientDTO(BaseModel):
    id: str
    patient_number: str
    full_name: str
    date_of_birth: str
    qr_code: str = ""  # base64 data URI
    visit_id: str = ""
    visit_number: str = ""
    visit_status: str = ""
    visit_status_label: str = ""
    exams: list[TerrainExamDTO] = []
    exams_total: int = 0
    exams_done: int = 0


class TerrainState(RoleState):
    """State for the /on-site/[program_id_param] page."""

    program_id: str = ""
    campaign_name: str = ""
    program_number: str = ""
    account_name: str = ""
    campaign_start_date: str = ""
    campaign_end_date: str = ""

    patients: list[TerrainPatientDTO] = []
    filtered_patients: list[TerrainPatientDTO] = []
    search_query: str = ""

    is_loading: bool = False
    is_downloading_pdf: bool = False
    error_message: str = ""
    success_message: str = ""

    # Scanning state
    scan_result: str = ""
    scan_found_patient: TerrainPatientDTO | None = None
    scan_error: str = ""
    scanner_active: bool = False  # camera scanner running

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_operator, self.is_admin)
        if redirect:
            return redirect
        await self._load_terrain()

    @rx.event
    def go_back(self):
        return rx.redirect(f"/campaign/{self.program_id}")

    @rx.event
    def set_search_query(self, value: str):
        self.search_query = value.lower()
        self._apply_filter()

    @rx.event
    def clear_search(self):
        self.search_query = ""
        self._apply_filter()

    @rx.event
    def toggle_scanner(self):
        """Open/close the camera QR scanner."""
        self.scanner_active = not self.scanner_active
        if self.scanner_active:
            self.scan_error = ""
            self.scan_found_patient = None

    @rx.event
    def close_scanner(self):
        self.scanner_active = False

    @rx.event
    def on_scan_detected(self, code: str):
        """Called by the camera scanner component when a QR code is detected."""
        if not code:
            return
        # Stop camera immediately to avoid repeated triggers
        self.scanner_active = False
        self.scan_result = code
        self.scan_error = ""
        self.scan_found_patient = None
        # Process the scanned code
        self._process_code(code)

    @rx.event
    def on_scan_error(self, message: str):
        """Called by the camera scanner component on error."""
        self.scanner_active = False
        self.scan_error = f"Scanner error: {message}"

    @rx.event
    def set_scan_result(self, value: str):
        self.scan_result = value

    @rx.event
    async def process_scan(self):
        """Look up a tube QR code or patient number from the scan input."""
        code = self.scan_result.strip()
        if not code:
            return
        self.scan_error = ""
        self.scan_found_patient = None
        self._process_code(code)

    def _process_code(self, code: str):
        """Shared lookup used by both text input and camera scanner."""
        # Try patient number match first
        for p in self.patients:
            if p.patient_number == code:
                self.scan_found_patient = p
                self.search_query = p.full_name.lower()
                self._apply_filter()
                return

        # Try tube QR code lookup (format: TUBE-<patient_number>-<exam_code>)
        if code.startswith("TUBE-"):
            parts = code.split("-")
            if len(parts) >= 3:
                patient_number = parts[1]
                for p in self.patients:
                    if p.patient_number == patient_number:
                        self.scan_found_patient = p
                        self.search_query = p.full_name.lower()
                        self._apply_filter()
                        return

        self.scan_error = f"Patient non trouvé pour : {code}"

    @rx.event
    def clear_scan(self):
        self.scan_result = ""
        self.scan_found_patient = None
        self.scan_error = ""

    @rx.event
    async def mark_exam_done(self, exam_id: str, patient_id: str, visit_id: str, exam_type_code: str):
        """Mark a single exam as done on-site, creating CampaignVisit/Exam records if they don't exist yet."""
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign_visit.campaign_visit import CampaignVisit
                from gws_care.campaign_visit.campaign_visit_service import CampaignVisitService
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_service import ExamService
                from gws_care.exam.exam_type import ExamStatus, ExamType
                from gws_care.patient.patient import Patient as PatientModel

                # Create a CampaignVisit for this patient if none exists yet
                if not visit_id:
                    existing_visit = CampaignVisit.get_or_none(
                        (CampaignVisit.program == self.program_id) & (CampaignVisit.patient == patient_id)
                    )
                    if existing_visit:
                        visit_id = str(existing_visit.id)
                    else:
                        new_visit = CampaignVisitService.create_visit(self.program_id, patient_id)
                        visit_id = str(new_visit.id)

                if not exam_id:
                    # No Exam record yet — create it now
                    from datetime import date
                    try:
                        exam_date = date.fromisoformat(self.campaign_start_date)
                    except Exception:
                        exam_date = date.today()
                    patient_obj = PatientModel.get_or_none(PatientModel.id == patient_id)
                    exam = Exam()
                    exam.patient = patient_obj
                    exam.exam_type = ExamType(exam_type_code)
                    exam.exam_date = exam_date
                    exam.visit_id = visit_id
                    exam.status = ExamStatus.DRAFT
                    exam.is_done_on_site = True
                    exam.save()
                    exam_id = str(exam.id)
                else:
                    ExamService.mark_terrain_done(exam_id)

            # Update local state: propagate the (possibly new) visit_id to all of this
            # patient's exam DTOs so subsequent markings in this session are consistent.
            updated_patients = []
            for p in self.patients:
                if p.id == patient_id:
                    updated_exams = [
                        TerrainExamDTO(**{
                            **e.dict(),
                            "id": exam_id,
                            "is_done_on_site": True,
                            "visit_id": visit_id,
                        }) if (e.exam_type_code == exam_type_code) else TerrainExamDTO(**{
                            **e.dict(),
                            "visit_id": visit_id,
                        })
                        for e in p.exams
                    ]
                    exams_done = sum(1 for e in updated_exams if e.is_done_on_site)
                    updated_patients.append(TerrainPatientDTO(**{
                        **p.dict(),
                        "visit_id": visit_id,
                        "exams": updated_exams,
                        "exams_done": exams_done,
                    }))
                else:
                    updated_patients.append(p)
            self.patients = updated_patients
            self._apply_filter()
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def mark_terrain_done(self, patient_id: str):
        """Mark the on-site phase as done for a patient's visit."""
        if not self.program_id:
            return
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign_visit.campaign_visit import CampaignVisit
                from gws_care.campaign_visit.campaign_visit_service import CampaignVisitService
                from gws_care.campaign_visit.campaign_visit_status import CampaignVisitStatus

                visit = CampaignVisit.get_or_none(
                    (CampaignVisit.program == self.program_id) & (CampaignVisit.patient == patient_id)
                )
                if visit and visit.status == CampaignVisitStatus.PENDING:
                    CampaignVisitService.mark_terrain_done(str(visit.id))

                    # Phase 5 — send on-site thank-you notification to the patient
                    try:
                        from gws_care.notification.notification_service import NotificationService
                        from gws_care.patient.patient import Patient
                        patient_obj = Patient.get_by_id(patient_id)
                        NotificationService.send_terrain_thank_you(patient_obj, visit)
                    except Exception:
                        pass  # Notification failure must never block the workflow

            # Update local patient entry
            self.patients = [
                TerrainPatientDTO(
                    **{
                        **p.dict(),
                        "visit_status": "visit_done",
                        "visit_status_label": "Visit Done",
                    }
                ) if p.id == patient_id else p
                for p in self.patients
            ]
            self._apply_filter()
            self.success_message = "On-site visit marked as done."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def download_pdf(self):
        """Generate and download the tube QR code grid PDF."""
        if not self.program_id:
            return
        self.is_downloading_pdf = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.qr_code import QrCodeService
                pdf_bytes = QrCodeService.generate_tube_qr_grid(self.program_id)

            filename = f"qr_grid_{self.program_number or self.program_id}.pdf"
            return rx.download(data=pdf_bytes, filename=filename)
        except Exception as e:
            self.error_message = f"PDF generation error: {e}"
        finally:
            self.is_downloading_pdf = False

    # ── Internal ───────────────────────────────────────────────────────────────

    def _apply_filter(self):
        q = self.search_query
        if not q:
            self.filtered_patients = list(self.patients)
        else:
            self.filtered_patients = [
                p for p in self.patients
                if q in p.full_name.lower() or q in p.patient_number.lower()
            ]

    async def _load_terrain(self):
        if not await self.check_authentication():
            return
        program_id = self.router.page.params.get("program_id_param", "")
        if not program_id:
            self.error_message = "No program ID"
            return
        self.program_id = program_id
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_exam_type import CampaignExamType
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.campaign_visit.campaign_visit import CampaignVisit
                from gws_care.campaign_visit.campaign_visit_status import CampaignVisitStatus
                from gws_care.exam.exam import Exam

                program = CampaignService.get_campaign(program_id)
                self.campaign_name = program.name
                self.program_number = program.program_number
                self.account_name = program.account.name if program.account_id else ""
                self.campaign_start_date = str(program.start_date)
                self.campaign_end_date = str(program.end_date)

                # Load the program's configured exam types once (source of truth)
                program_exam_types = list(
                    CampaignExamType.select()
                    .where(CampaignExamType.program == program_id)
                )

                patients = CampaignService.get_patients(program_id)

                result = []
                for patient in patients:
                    # Ensure QR code is generated
                    if not patient.qr_code:
                        try:
                            from gws_care.qr_code import generate_patient_qr_data_uri
                            patient.qr_code = generate_patient_qr_data_uri(patient.patient_number)
                            patient.save()
                        except Exception:
                            pass

                    # Find the visit for this patient in this program
                    visit = CampaignVisit.get_or_none(
                        (CampaignVisit.program == program_id) & (CampaignVisit.patient == patient.id)
                    )
                    visit_id = str(visit.id) if visit else ""
                    visit_number = visit.visit_number if visit else ""
                    visit_status = visit.status.value if visit else ""
                    visit_status_label = visit.status.get_label() if visit else ""

                    # Load exams belonging to this patient's visit in this program
                    visit_exams = []
                    if visit:
                        visit_exams = list(
                            Exam.select()
                            .where(Exam.visit_id == str(visit.id))
                        )

                    # Map exam_type enum value → exam record for quick lookup
                    exam_by_code: dict = {}
                    for ex in visit_exams:
                        if ex.exam_type:
                            exam_by_code[ex.exam_type.value] = ex

                    # Build exam DTOs from the program's configured exam types (source of truth)
                    exam_dtos = []
                    for cet in program_exam_types:
                        et_model = cet.exam_type
                        ex = exam_by_code.get(et_model.code)
                        exam_dtos.append(TerrainExamDTO(
                            id=str(ex.id) if ex else "",
                            exam_type_name=et_model.name,
                            exam_type_code=et_model.code,
                            is_done_on_site=bool(ex.is_done_on_site) if ex else False,
                            tube_qr_code=(ex.tube_qr_code or "") if ex else "",
                            patient_id=str(patient.id),
                            visit_id=visit_id,
                        ))
                    exams_done = sum(1 for e in exam_dtos if e.is_done_on_site)

                    result.append(TerrainPatientDTO(
                        id=str(patient.id),
                        patient_number=patient.patient_number,
                        full_name=patient.get_full_name(),
                        date_of_birth=str(patient.date_of_birth),
                        qr_code=patient.qr_code or "",
                        visit_id=visit_id,
                        visit_number=visit_number,
                        visit_status=visit_status,
                        visit_status_label=visit_status_label,
                        exams=exam_dtos,
                        exams_total=len(exam_dtos),
                        exams_done=exams_done,
                    ))

                self.patients = result
                self._apply_filter()
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_loading = False
