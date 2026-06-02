"""State for the create exam dialog (opened from patient detail)."""

import mimetypes
import uuid
from typing import AsyncGenerator

import reflex as rx
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class StagedFile(BaseModel):
    """A file selected by the user but not yet persisted to an exam."""

    stored_filename: str
    original_name: str
    mime_type: str
    file_size: int
    document_type: str = ""  # DocumentType enum value, empty means unset


class ExamTypeOption(BaseModel):
    id: str   # ExamTypeRef.id (used as exam_type value)
    name: str
    category_label: str


class ExamParamOption(BaseModel):
    """An ExamParameter available for selection when creating an exam."""

    id: str
    name: str
    unit: str = ""


class ExamFormState(FormDialogState, rx.State):
    """Manages the create exam dialog on the patient detail page."""

    # Form fields
    form_exam_date: str = ""
    form_exam_type: str = ""    # ExamTypeRef.id
    form_account_id: str = ""
    form_reason_for_visit: str = ""
    form_medical_history: str = ""
    form_weight: str = ""
    form_height: str = ""
    form_bmi: str = ""
    form_blood_pressure: str = ""
    form_heart_rate: str = ""
    form_temperature: str = ""
    form_conclusion: str = ""

    # Exam type options loaded from referential
    exam_type_options: list[ExamTypeOption] = []

    # Parameters available for the selected exam type
    available_exam_params: list[ExamParamOption] = []
    # IDs of params the doctor has checked
    selected_param_ids: list[str] = []
    # Error message from loading exam parameters
    load_error: str = ""
    # Error message for form validation
    form_error: str = ""

    # Staged file attachments (selected but exam not yet created)
    staged_files: list[StagedFile] = []
    is_uploading: bool = False

    # Context: which patient are we creating an exam for?
    _patient_id: str = ""

    # ── Setters ───────────────────────────────────────────────────────────────

    @rx.event
    def set_form_exam_date(self, value: str):
        self.form_exam_date = value

    @rx.event
    def set_form_exam_type(self, value: str):
        self.form_exam_type = value
        self._load_params_for_type(value)

    def _load_params_for_type(self, exam_type_ref_id: str):
        """Load ExamParameter records for the selected exam type from the referential."""
        self.load_error = ""
        if not exam_type_ref_id:
            self.available_exam_params = []
            self.selected_param_ids = []
            return
        try:
            from gws_care.exam_type_ref.exam_parameter import ExamParameter
            params = (
                ExamParameter.select()
                .where(ExamParameter.exam_type_ref == exam_type_ref_id)
                .order_by(ExamParameter.display_order)
            )
            self.available_exam_params = [
                ExamParamOption(id=str(p.id), name=p.name, unit=p.unit or "")
                for p in params
            ]
            # Pre-select all parameters by default
            self.selected_param_ids = [str(p.id) for p in params]
        except Exception as exc:
            self.available_exam_params = []
            self.selected_param_ids = []
            self.load_error = str(exc)

    @rx.event
    def toggle_param_selection(self, param_id: str):
        """Toggle a parameter in/out of the selected list."""
        if param_id in self.selected_param_ids:
            self.selected_param_ids = [p for p in self.selected_param_ids if p != param_id]
        else:
            self.selected_param_ids = self.selected_param_ids + [param_id]

    @rx.event
    def set_form_account_id(self, value: str):
        self.form_account_id = value

    @rx.event
    def set_form_reason_for_visit(self, value: str):
        self.form_reason_for_visit = value

    @rx.event
    def set_form_medical_history(self, value: str):
        self.form_medical_history = value

    @rx.event
    def set_form_weight(self, value: str):
        self.form_weight = value

    @rx.event
    def set_form_height(self, value: str):
        self.form_height = value

    @rx.event
    def set_form_bmi(self, value: str):
        self.form_bmi = value

    @rx.event
    def set_form_blood_pressure(self, value: str):
        self.form_blood_pressure = value

    @rx.event
    def set_form_heart_rate(self, value: str):
        self.form_heart_rate = value

    @rx.event
    def set_form_temperature(self, value: str):
        self.form_temperature = value

    @rx.event
    def set_form_conclusion(self, value: str):
        self.form_conclusion = value

    @rx.event
    def set_staged_file_document_type(self, stored_filename: str, document_type: str):
        """Update the document_type for a staged file."""
        self.staged_files = [
            StagedFile(**{**sf.dict(), "document_type": document_type})
            if sf.stored_filename == stored_filename
            else sf
            for sf in self.staged_files
        ]

    # ── File upload ───────────────────────────────────────────────────────────

    @rx.event
    async def handle_file_upload(self, files: list[rx.UploadFile]):
        """Save dropped / selected files to the upload dir and stage them."""
        self.is_uploading = True
        yield
        upload_dir = rx.get_upload_dir()
        upload_dir.mkdir(parents=True, exist_ok=True)

        for uf in files:
            data = await uf.read()
            ext = "".join(
                c for c in (uf.filename or "file") if c in "._-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            )
            # Build a unique stored filename to avoid collisions
            stored_name = f"{uuid.uuid4().hex}_{ext}"
            out_path = upload_dir / stored_name
            with out_path.open("wb") as fh:
                fh.write(data)

            mime = mimetypes.guess_type(uf.filename or "")[0] or "application/octet-stream"
            self.staged_files = self.staged_files + [
                StagedFile(
                    stored_filename=stored_name,
                    original_name=uf.filename or stored_name,
                    mime_type=mime,
                    file_size=len(data),
                )
            ]

        self.is_uploading = False

    @rx.event
    def remove_staged_file(self, stored_filename: str):
        """Remove a staged file (delete from disk + state)."""
        import os

        upload_dir = rx.get_upload_dir()
        path = upload_dir / stored_filename
        if path.exists():
            try:
                os.remove(path)
            except OSError:
                pass
        self.staged_files = [f for f in self.staged_files if f.stored_filename != stored_filename]

    # ── Open ──────────────────────────────────────────────────────────────────

    @rx.event
    def open_create_dialog(self, patient_id: str):
        """Open the dialog to create a new exam for the given patient."""
        from datetime import date

        self._patient_id = patient_id
        self.form_exam_date = date.today().isoformat()
        self.form_exam_type = ""
        self.form_account_id = ""
        self.form_reason_for_visit = ""
        self.form_medical_history = ""
        self.form_weight = ""
        self.form_height = ""
        self.form_bmi = ""
        self.form_blood_pressure = ""
        self.form_heart_rate = ""
        self.form_temperature = ""
        self.form_conclusion = ""
        self.staged_files = []
        self.is_uploading = False
        self.is_update_mode = False
        # Load exam type options from referential (exclude CLINICAL — physical exams go to appointments)
        try:
            from gws_care.exam_type_ref.exam_type_ref import ExamCategory, ExamTypeRef
            refs = (
                ExamTypeRef.select()
                .where(
                    ExamTypeRef.is_active == True,
                    ExamTypeRef.category != ExamCategory.CLINICAL.value,
                )
                .order_by(ExamTypeRef.category, ExamTypeRef.name)
            )
            self.exam_type_options = [
                ExamTypeOption(id=str(r.id), name=r.name, category_label=r.get_category_label())
                for r in refs
            ]
            if self.exam_type_options:
                self.form_exam_type = self.exam_type_options[0].id
                self._load_params_for_type(self.exam_type_options[0].id)
        except Exception as exc:
            self.exam_type_options = []
            print(f"[exam_form] exam_type_options load error: {exc}")
        self.dialog_opened = True

    # ── FormDialogState implementation ───────────────────────────────────────

    async def _clear_form_state(self) -> None:
        from datetime import date
        self.form_exam_date = date.today().isoformat()
        self.form_exam_type = ""
        self.form_account_id = ""
        self.form_reason_for_visit = ""
        self.form_medical_history = ""
        self.form_weight = ""
        self.form_height = ""
        self.form_bmi = ""
        self.form_blood_pressure = ""
        self.form_heart_rate = ""
        self.form_temperature = ""
        self.form_conclusion = ""
        self.staged_files = []
        self.is_uploading = False
        self._patient_id = ""
        self.is_update_mode = False
        self.available_exam_params = []
        self.selected_param_ids = []
        self.load_error = ""
        self.form_error = ""

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new exam and attach any staged files."""
        async with self:
            self.form_error = ""
        if not self.form_exam_date or not self.form_exam_type:
            async with self:
                self.form_error = "Exam date and type are required."
            return

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            from gws_care.exam.exam_dto import SaveExamDTO
            from gws_care.exam.exam_file_service import ExamFileService
            from gws_care.exam.exam_service import ExamService

            def _to_float(val: str) -> float | None:
                val = val.strip()
                if not val:
                    return None
                try:
                    return float(val)
                except ValueError:
                    return None

            dto = SaveExamDTO(
                patient_id=self._patient_id,
                exam_date=self.form_exam_date,
                exam_type_ref_id=self.form_exam_type,
                account_id=self.form_account_id or None,
                reason_for_visit=self.form_reason_for_visit or None,
                medical_history=self.form_medical_history or None,
                weight=_to_float(self.form_weight),
                height=_to_float(self.form_height),
                bmi=_to_float(self.form_bmi),
                blood_pressure=self.form_blood_pressure or None,
                heart_rate=_to_float(self.form_heart_rate),
                temperature=_to_float(self.form_temperature),
                conclusion=self.form_conclusion or None,
                requested_param_ids=list(self.selected_param_ids) if self.selected_param_ids else [],
            )
            exam = ExamService.create_exam(dto)
            exam_id = str(exam.id)

            # Notify all OPERATEUR_LABO users if lab tests were requested
            if self.selected_param_ids:
                from gws_care.notification.notification_service import NotificationService
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_care_role import UserCareRole
                from gws_care.patient.patient import Patient as PatientModel
                try:
                    patient_obj = PatientModel.get_or_none(PatientModel.id == self._patient_id)
                    patient_name = (
                        f"{patient_obj.first_name} {patient_obj.last_name}"
                        if patient_obj else "patient"
                    )
                    exam_type_label = (
                        self.exam_type_options[
                            next((i for i, o in enumerate(self.exam_type_options) if o.id == self.form_exam_type), 0)
                        ].name
                        if self.exam_type_options else self.form_exam_type
                    )
                    labo_roles = (
                        UserCareRole.select()
                        .where(UserCareRole.role == CareRole.OPERATEUR_LABO.value)
                    )
                    for ur in labo_roles:
                        NotificationService.create_bell(
                            user_id=str(ur.user_id),
                            message=f"Nouvelle analyse à traiter — {patient_name} ({exam_type_label})",
                        )
                except Exception as notify_exc:
                    print(f"[ExamFormState] Lab notification failed: {notify_exc}")

            # Persist staged files as ExamFile records, registering each as a gws_core Resource
            for sf in self.staged_files:
                ExamFileService.attach_staged_file(
                    exam_id=exam_id,
                    original_name=sf.original_name,
                    stored_filename=sf.stored_filename,
                    mime_type=sf.mime_type,
                    file_size=sf.file_size,
                    document_type=sf.document_type or None,
                )

        yield rx.toast.success("Exam created")
        from .patient_detail_state import PatientDetailState
        yield PatientDetailState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Exams cannot be edited through this dialog."""
        async with self:
            self.form_error = "Exams cannot be edited."
        return
        yield  # make it a generator
