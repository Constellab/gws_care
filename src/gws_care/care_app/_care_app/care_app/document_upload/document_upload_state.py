"""State for the document upload / annotation page (/documents/upload).

Two ways to add documents to the annotation table:
  1. Browser upload  — rx.upload drop zone (single-file or multi-file)
  2. Lab folder      — pick a Folder resource from the lab via the built-in
                       ResourceSelectState picker (filtered to Folder type only)
"""

from __future__ import annotations

import reflex as rx
from pydantic import BaseModel

from gws_core.resource.resource_model import ResourceModel
from gws_reflex_main import ResourceSelectState

from ..common.patient_picker_state import PatientPickerRowDTO, PatientPickerState

# ── Document type options (value → translation key) ───────────────────────────

DOC_TYPE_OPTIONS: list[tuple[str, str]] = [
    ("prescription", "upload_doc_type_prescription"),
    ("medical_certificate", "upload_doc_type_medical_certificate"),
    ("medical_report", "upload_doc_type_medical_report"),
    ("medical_analysis", "upload_doc_type_medical_analysis"),
    ("letter", "upload_doc_type_letter"),
    ("xray", "upload_doc_type_xray"),
    ("ct_scan", "upload_doc_type_ct_scan"),
    ("mri", "upload_doc_type_mri"),
    ("ultrasound", "upload_doc_type_ultrasound"),
    ("other", "upload_doc_type_other"),
]


class DocumentAnnotationItemDTO(BaseModel):
    """One document ready for annotation."""

    index: int
    text_resource_id: str = ""
    file_resource_id: str = ""
    # Absolute path to the staged file on disk (set during upload, used in save)
    staged_file_path: str = ""
    original_name: str = ""
    detected_type: str = ""
    detected_date: str = ""
    detected_patient_name: str = ""
    suggested_patient_id: str = ""
    suggested_patient_label: str = ""
    analysis_hints: list[str] = []
    uploaded_document_id: str = ""
    is_saved: bool = False
    save_error: str = ""


class DocumentUploadState(PatientPickerState, ResourceSelectState):
    """State for the /documents/upload annotation page."""

    # ── Patient picker vars (required by PatientPickerState contract) ─────────
    picker_patients: list[PatientPickerRowDTO] = []
    picker_is_loading: bool = False
    picker_error: str = ""
    picker_filter_name: str = ""
    picker_filter_number: str = ""
    picker_account_id: str = ""
    picker_is_open: bool = False
    picker_selected_id: str = ""
    picker_selected_label: str = ""

    # ── Document list ─────────────────────────────────────────────────────────
    annotation_items: list[DocumentAnnotationItemDTO] = []

    # ── Single-file upload state ──────────────────────────────────────────────
    is_uploading: bool = False
    upload_error: str = ""

    # ── Folder import state ───────────────────────────────────────────────────
    is_importing: bool = False
    import_progress: str = ""
    import_error: str = ""
    _selected_folder_id: str = ""

    # ── Annotation dialog ─────────────────────────────────────────────────────
    annotation_dialog_open: bool = False
    editing_index: int = -1
    form_doc_type: str = ""
    form_date: str = ""
    form_description: str = ""
    form_notes: str = ""

    # ── Save ──────────────────────────────────────────────────────────────────
    is_saving: bool = False

    # ── ResourceSelectState overrides ─────────────────────────────────────────

    async def create_search_builder(self):
        """Restrict the resource picker to Folder resources only."""
        from gws_core.impl.file.folder import Folder
        builder = await super().create_search_builder()
        builder.add_resource_types_and_sub_types_filter([Folder])
        return builder

    async def on_resource_selected(self, resource_model: ResourceModel):
        """Store the selected folder id and kick off background analysis."""
        self._selected_folder_id = resource_model.id
        return DocumentUploadState.process_selected_folder

    # ── Patient picker events ─────────────────────────────────────────────────

    @rx.event
    async def open_patient_picker(self):
        await self._open_patient_picker()

    @rx.event
    def close_patient_picker(self):
        self.picker_is_open = False

    @rx.event
    def picker_clear_selection(self):
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

    # ── Page lifecycle ────────────────────────────────────────────────────────

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(
            self.is_operator, self.is_doctor, self.is_admin
        )
        if redirect:
            return redirect

    # ── Single-file browser upload ────────────────────────────────────────────

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Receive browser-uploaded files, extract text and run analysis."""
        if not files:
            return
        self.is_uploading = True
        self.upload_error = ""
        yield
        try:
            from gws_care.document_upload.document_analysis_service import (
                DocumentAnalysisService,
            )
            from gws_care.patient.patient import Patient

            patients = list(Patient.select().order_by(Patient.last_name))

            import uuid

            upload_dir = rx.get_upload_dir()
            upload_dir.mkdir(parents=True, exist_ok=True)

            for uf in files:
                data = await uf.read()
                name = uf.filename or f"document_{len(self.annotation_items) + 1}"
                mime = "application/pdf" if name.lower().endswith(".pdf") else "image/"
                text = DocumentAnalysisService.extract_text(data, mime)
                result = DocumentAnalysisService.analyze_text(text, patients)
                pid, plabel = "", ""
                if result.patient_name:
                    pid, plabel = DocumentAnalysisService.match_patient(
                        result.patient_name, patients
                    )
                # Stage the raw file bytes so save_document can register them as a gws_core resource
                safe_name = "".join(c for c in name if c.isalnum() or c in "._-")
                staged_filename = f"{uuid.uuid4().hex}_{safe_name}"
                staged_path = upload_dir / staged_filename
                staged_path.write_bytes(data)

                idx = len(self.annotation_items)
                self.annotation_items = self.annotation_items + [
                    DocumentAnnotationItemDTO(
                        index=idx,
                        original_name=name,
                        staged_file_path=str(staged_path),
                        detected_type=result.doc_type,
                        detected_date=result.doc_date,
                        detected_patient_name=result.patient_name,
                        suggested_patient_id=pid,
                        suggested_patient_label=plabel,
                        analysis_hints=result.hints,
                    )
                ]
        except Exception as exc:
            self.upload_error = str(exc)
        finally:
            self.is_uploading = False

    # ── Folder bulk import (background) ───────────────────────────────────────

    @rx.event(background=True)
    async def process_selected_folder(self):
        """Iterate all files in the selected Folder, extract text and analyze."""
        async with self:
            self.is_importing = True
            self.import_error = ""
            self.import_progress = "Loading folder..."
            folder_id = self._selected_folder_id

        try:
            import os

            from gws_core.impl.file.folder import Folder
            from gws_core.resource.resource_model import ResourceModel as RM

            from gws_care.document_upload.document_analysis_service import (
                DocumentAnalysisService,
            )
            from gws_care.patient.patient import Patient

            folder_model = RM.get_by_id_and_check(folder_id)
            folder: Folder = folder_model.get_resource()

            patients = list(Patient.select().order_by(Patient.last_name))

            supported = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
            all_paths = folder.list_all_file_paths()
            file_paths = [
                p for p in all_paths
                if os.path.splitext(p)[1].lower() in supported
            ]

            if not file_paths:
                async with self:
                    self.import_error = "No supported files found in the selected folder."
                    self.is_importing = False
                return

            total = len(file_paths)
            for i, path in enumerate(file_paths):
                name = os.path.basename(path)
                async with self:
                    self.import_progress = f"Analyzing {name} ({i + 1}/{total})..."
                try:
                    with open(path, "rb") as f:
                        data = f.read()
                    mime = "application/pdf" if name.lower().endswith(".pdf") else "image/"
                    text = DocumentAnalysisService.extract_text(data, mime)
                    result = DocumentAnalysisService.analyze_text(text, patients)
                    pid, plabel = "", ""
                    if result.patient_name:
                        pid, plabel = DocumentAnalysisService.match_patient(
                            result.patient_name, patients
                        )
                    async with self:
                        idx = len(self.annotation_items)
                        self.annotation_items = self.annotation_items + [
                            DocumentAnnotationItemDTO(
                                index=idx,
                                original_name=name,
                                staged_file_path=path,
                                detected_type=result.doc_type,
                                detected_date=result.doc_date,
                                detected_patient_name=result.patient_name,
                                suggested_patient_id=pid,
                                suggested_patient_label=plabel,
                                analysis_hints=result.hints,
                            )
                        ]
                except Exception as exc:
                    async with self:
                        idx = len(self.annotation_items)
                        self.annotation_items = self.annotation_items + [
                            DocumentAnnotationItemDTO(
                                index=idx,
                                original_name=name,
                                save_error=f"Analysis failed: {exc}",
                            )
                        ]

            async with self:
                self.import_progress = f"Done — {total} document(s) analyzed."

        except Exception as exc:
            async with self:
                self.import_error = str(exc)
        finally:
            async with self:
                self.is_importing = False

    # ── Annotation dialog ─────────────────────────────────────────────────────

    @rx.event
    def open_annotation_dialog(self, index: int):
        """Open the annotation dialog pre-filled with AI suggestions."""
        if index < 0 or index >= len(self.annotation_items):
            return
        item = self.annotation_items[index]
        self.editing_index = index
        self.form_doc_type = item.detected_type
        self.form_date = item.detected_date
        self.form_description = ""
        self.form_notes = ""
        self.picker_selected_id = item.suggested_patient_id
        self.picker_selected_label = item.suggested_patient_label
        self.annotation_dialog_open = True

    @rx.event
    def close_annotation_dialog(self):
        self.annotation_dialog_open = False

    # ── Form setters ──────────────────────────────────────────────────────────

    @rx.event
    def set_form_doc_type(self, value: str):
        self.form_doc_type = value

    @rx.event
    def set_form_date(self, value: str):
        self.form_date = value

    @rx.event
    def set_form_description(self, value: str):
        self.form_description = value

    @rx.event
    def set_form_notes(self, value: str):
        self.form_notes = value

    # ── Save ──────────────────────────────────────────────────────────────────

    @rx.event
    async def save_document(self):
        """Create or update an UploadedDocument DB record."""
        if self.editing_index < 0 or self.editing_index >= len(self.annotation_items):
            return
        self.is_saving = True
        item = self.annotation_items[self.editing_index]
        try:
            with await self.authenticate_user():
                from datetime import date

                from gws_care.document_upload.uploaded_document import UploadedDocument

                doc_date_str = self.form_date or None
                doc_date = date.fromisoformat(doc_date_str) if doc_date_str else None

                if item.uploaded_document_id:
                    doc = UploadedDocument.get_by_id(item.uploaded_document_id)
                else:
                    doc = UploadedDocument()
                    doc.original_name = item.original_name
                    # Register the staged file as a gws_core resource so it can be viewed/downloaded
                    resource_id = None
                    if item.staged_file_path:
                        import os
                        from gws_care.exam.exam_file_service import ExamFileService
                        staged = item.staged_file_path
                        if os.path.exists(staged):
                            with open(staged, "rb") as fh:
                                file_bytes = fh.read()
                            resource_id, _ = ExamFileService._save_bytes_as_gws_resource(file_bytes, item.original_name)
                    doc.resource_id = resource_id

                doc.patient_id = self.picker_selected_id or None
                doc.doc_type = self.form_doc_type or None
                doc.doc_date = doc_date
                doc.description = self.form_description or None
                doc.notes = self.form_notes or None
                doc.save()

            updated = list(self.annotation_items)
            updated[self.editing_index] = DocumentAnnotationItemDTO(
                **{
                    **item.dict(),
                    "uploaded_document_id": str(doc.id),
                    "is_saved": True,
                    "save_error": "",
                    # Override AI hints with the confirmed values so re-opening the dialog shows them
                    "detected_type": self.form_doc_type,
                    "detected_date": self.form_date,
                    "suggested_patient_id": self.picker_selected_id,
                    "suggested_patient_label": self.picker_selected_label,
                }
            )
            self.annotation_items = updated
            self.annotation_dialog_open = False
        except Exception as exc:
            updated = list(self.annotation_items)
            updated[self.editing_index] = DocumentAnnotationItemDTO(
                **{**item.dict(), "save_error": str(exc)}
            )
            self.annotation_items = updated
        finally:
            self.is_saving = False

    @rx.var
    def has_unsaved_items(self) -> bool:
        return any(not item.is_saved for item in self.annotation_items)

    @rx.event
    async def save_all_documents(self):
        """Save all pending documents using their detected/suggested values."""
        self.is_saving = True
        try:
            import os
            from datetime import date
            from gws_care.document_upload.uploaded_document import UploadedDocument
            from gws_care.exam.exam_file_service import ExamFileService

            with await self.authenticate_user():
                for i, item in enumerate(self.annotation_items):
                    if item.is_saved:
                        continue
                    try:
                        doc_date = date.fromisoformat(item.detected_date) if item.detected_date else None
                        if item.uploaded_document_id:
                            doc = UploadedDocument.get_by_id(item.uploaded_document_id)
                        else:
                            doc = UploadedDocument()
                            doc.original_name = item.original_name
                            resource_id = None
                            if item.staged_file_path and os.path.exists(item.staged_file_path):
                                with open(item.staged_file_path, "rb") as fh:
                                    file_bytes = fh.read()
                                resource_id, _ = ExamFileService._save_bytes_as_gws_resource(file_bytes, item.original_name)
                            doc.resource_id = resource_id
                        doc.patient_id = item.suggested_patient_id or None
                        doc.doc_type = item.detected_type or None
                        doc.doc_date = doc_date
                        doc.save()
                        updated = list(self.annotation_items)
                        updated[i] = DocumentAnnotationItemDTO(
                            **{**item.dict(), "uploaded_document_id": str(doc.id), "is_saved": True, "save_error": ""}
                        )
                        self.annotation_items = updated
                    except Exception as exc:
                        updated = list(self.annotation_items)
                        updated[i] = DocumentAnnotationItemDTO(**{**item.dict(), "save_error": str(exc)})
                        self.annotation_items = updated
        except Exception:
            pass
        finally:
            self.is_saving = False

    # ── Navigation ────────────────────────────────────────────────────────────

    @rx.event
    def go_back(self):
        return rx.call_script("window.history.back()")
