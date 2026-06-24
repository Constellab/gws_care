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


class ExamTypeRefOption(BaseModel):
    """A row from the exam type referential for the dropdown selector."""

    id: str
    name: str
    category_label: str
    department: str = ""
    parameter_count: int = 0


class ExamParamOption(BaseModel):
    """A single test/parameter belonging to an exam type ref."""

    id: str
    name: str
    unit: str = ""
    value_type: str = "NUMERIC"
    is_required: bool = False
    is_selected: bool = False


class ExamFormState(FormDialogState, rx.State):
    """Manages the create exam dialog on the patient detail page."""

    # Form fields
    form_exam_date: str = ""
    form_exam_type_ref_id: str = ""
    form_exam_type_ref_name: str = ""
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

    # Exam type referential
    exam_type_ref_options: list[ExamTypeRefOption] = []
    available_params: list[ExamParamOption] = []
    is_loading_exam_types: bool = False

    @rx.var
    def selected_param_count(self) -> int:
        return sum(1 for p in self.available_params if p.is_selected)

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

    # ── Exam type ref selection ───────────────────────────────────────────────

    @rx.event
    async def select_exam_type_ref(self, ref_id: str):
        """Load parameters for the selected exam type ref and auto-select required ones."""
        self.form_exam_type_ref_id = ref_id
        found = next((o for o in self.exam_type_ref_options if o.id == ref_id), None)
        self.form_exam_type_ref_name = found.name if found else ""
        self.available_params = []
        if not ref_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                detail = ExamTypeRefService.get(ref_id)
                self.available_params = [
                    ExamParamOption(
                        id=p.id,
                        name=p.name,
                        unit=p.unit or "",
                        value_type=p.value_type,
                        is_required=p.is_required,
                        is_selected=p.is_required,  # auto-select required params
                    )
                    for p in detail.parameters
                ]
        except Exception:
            pass

    @rx.event
    def toggle_param(self, param_id: str):
        """Toggle a test/parameter in the selection."""
        self.available_params = [
            ExamParamOption(**{**p.dict(), "is_selected": not p.is_selected})
            if p.id == param_id
            else p
            for p in self.available_params
        ]

    @rx.event
    def select_all_params(self):
        """Select all available parameters."""
        self.available_params = [
            ExamParamOption(**{**p.dict(), "is_selected": True})
            for p in self.available_params
        ]

    @rx.event
    def clear_all_params(self):
        """Deselect all parameters."""
        self.available_params = [
            ExamParamOption(**{**p.dict(), "is_selected": False})
            for p in self.available_params
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
    async def open_create_dialog(self, patient_id: str):
        """Open the dialog to create a new exam for the given patient."""
        from datetime import date

        self._patient_id = patient_id
        self.form_exam_date = date.today().isoformat()
        self.form_exam_type_ref_id = ""
        self.form_exam_type_ref_name = ""
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
        self.available_params = []
        self.is_update_mode = False
        await self._load_exam_type_refs()
        self.dialog_opened = True

    async def _load_exam_type_refs(self):
        """Load active exam type refs from the referential."""
        self.is_loading_exam_types = True
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                rows = ExamTypeRefService.list_all(active_only=True)
                self.exam_type_ref_options = [
                    ExamTypeRefOption(
                        id=r.id,
                        name=r.name,
                        category_label=r.category_label,
                        department=r.department or "",
                        parameter_count=r.parameter_count,
                    )
                    for r in rows
                ]
        except Exception:
            self.exam_type_ref_options = []
        finally:
            self.is_loading_exam_types = False

    # ── FormDialogState implementation ───────────────────────────────────────

    async def _clear_form_state(self) -> None:
        from datetime import date
        self.form_exam_date = date.today().isoformat()
        self.form_exam_type_ref_id = ""
        self.form_exam_type_ref_name = ""
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
        self.available_params = []
        self.exam_type_ref_options = []
        self.is_loading_exam_types = False
        self._patient_id = ""
        self.is_update_mode = False

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new exam and attach any staged files."""
        if not self.form_exam_date or not self.form_exam_type_ref_id:
            yield rx.toast.error("La date et le type d'examen sont obligatoires.")
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
                exam_type="other",
                exam_type_ref_id=self.form_exam_type_ref_id or None,
                requested_param_ids=[p.id for p in self.available_params if p.is_selected],
                account_id=self.form_account_id or None,
                reason_for_visit=self.form_reason_for_visit or None,
                medical_history=self.form_medical_history or None,
                weight=_to_float(self.form_weight),
                height=_to_float(self.form_height),
                bmi=_to_float(self.form_bmi),
                blood_pressure=self.form_blood_pressure or None,
                heart_rate=_to_float(self.form_heart_rate),
                temperature=_to_float(self.form_temperature),
            )
            exam = ExamService.create_exam(dto)
            exam_id = str(exam.id)

            # Persist staged files as ExamFile records
            for sf in self.staged_files:
                ExamFileService.attach_staged_file(
                    exam_id=exam_id,
                    original_name=sf.original_name,
                    stored_filename=sf.stored_filename,
                    mime_type=sf.mime_type,
                    file_size=sf.file_size,
                    document_type=sf.document_type or None,
                )

        yield rx.toast.success("Examen créé avec succès")
        from .patient_detail_state import PatientDetailState
        yield PatientDetailState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Exams cannot be edited through this dialog."""
        yield rx.toast.error("Exams cannot be edited.")
