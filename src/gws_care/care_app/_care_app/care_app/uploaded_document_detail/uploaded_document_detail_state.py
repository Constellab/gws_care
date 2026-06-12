"""State for /document/[doc_id] — view and edit an uploaded document."""

import reflex as rx

from ..common.patient_picker_state import PatientPickerRowDTO
from ..common.role_state import RoleState


class UploadedDocumentDetailState(RoleState):

    is_loading: bool = True
    not_found: bool = False
    error_message: str = ""

    original_name: str = ""
    doc_type_label: str = ""
    doc_date: str = ""
    description: str = ""
    notes: str = ""
    patient_name: str = ""
    patient_id: str = ""
    download_url: str = ""
    has_file: bool = False
    viewer_open: bool = False

    # Backend vars — not exposed to frontend, avoids route-param shadow
    _loaded_doc_id: str = ""
    _resource_id: str = ""

    # ── Patient picker vars ────────────────────────────────────────────────
    picker_patients: list[PatientPickerRowDTO] = []
    picker_is_loading: bool = False
    picker_error: str = ""
    picker_filter_name: str = ""
    picker_filter_number: str = ""
    picker_account_id: str = ""
    picker_is_open: bool = False
    picker_selected_id: str = ""
    picker_selected_label: str = ""

    # ── Edit dialog vars ───────────────────────────────────────────────────
    edit_open: bool = False
    edit_form_doc_type: str = ""
    edit_form_date: str = ""
    edit_form_description: str = ""
    edit_form_notes: str = ""
    edit_error: str = ""
    edit_is_saving: bool = False

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(
            self.is_operator, self.is_doctor, self.is_admin
        )
        if redirect:
            return redirect
        await self._load_document()

    async def _load_document(self):
        self.is_loading = True
        self.error_message = ""
        self.not_found = False
        try:
            with await self.authenticate_user():
                from gws_care.document_upload.uploaded_document import UploadedDocument
                from gws_care.exam.exam_file_service import ExamFileService

                doc_id = self.router.page.params.get("doc_id", "")
                if not doc_id:
                    self.not_found = True
                    return
                self._loaded_doc_id = doc_id
                try:
                    doc = UploadedDocument.get_by_id(doc_id)
                except Exception:
                    self.not_found = True
                    return

                self.original_name = doc.original_name or ""
                self.doc_date = doc.doc_date.isoformat() if doc.doc_date else ""
                self.description = doc.description or ""
                self.notes = doc.notes or ""

                from gws_care.care_app._care_app.care_app.admin_documents.admin_documents_state import _UPLOADED_TYPE_LABELS
                self.doc_type_label = _UPLOADED_TYPE_LABELS.get(doc.doc_type or "", doc.doc_type or "")

                if doc.patient_id:
                    try:
                        from gws_care.patient.patient import Patient
                        p = Patient.get_by_id(str(doc.patient_id))
                        self.patient_name = p.get_full_name()
                        self.patient_id = str(doc.patient_id)
                    except Exception:
                        self.patient_name = ""
                        self.patient_id = ""
                else:
                    self.patient_name = ""
                    self.patient_id = ""

                if doc.resource_id:
                    self.has_file = True
                    self._resource_id = doc.resource_id
                    try:
                        self.download_url = ExamFileService.get_resource_download_url(doc.resource_id)
                    except Exception:
                        self.download_url = ""
                else:
                    self.has_file = False
                    self._resource_id = ""
                    self.download_url = ""

        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_loading = False

    @rx.event
    def go_back(self):
        return rx.redirect("/documents")

    @rx.event
    def go_to_patient(self):
        return rx.redirect(f"/patient/{self.patient_id}")

    @rx.var
    def file_extension(self) -> str:
        name = self.original_name.lower()
        return name.rsplit(".", 1)[-1] if "." in name else ""

    @rx.var
    def viewer_type(self) -> str:
        ext = self.file_extension
        if ext in ("png", "jpg", "jpeg", "webp", "gif", "svg"):
            return "image"
        if ext == "pdf":
            return "pdf"
        return "other"

    @rx.event
    def open_viewer(self):
        self.viewer_open = True

    @rx.event
    def close_viewer(self):
        self.viewer_open = False

    @rx.event
    def open_file(self):
        url = self.download_url
        if not url and self._resource_id:
            from gws_care.exam.exam_file_service import ExamFileService
            url = ExamFileService.get_resource_download_url(self._resource_id)
        if url:
            return rx.call_script(f"window.open('{url}', '_blank')")

    # ── Patient picker private helpers ─────────────────────────────────────

    async def _run_picker_search(self):
        self.picker_is_loading = True
        self.picker_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                name_term = self.picker_filter_name.strip() or None
                raw_pn = self.picker_filter_number.strip()
                if raw_pn.upper().startswith("PAT-"):
                    raw_pn = raw_pn[4:]
                pn_prefix = f"PAT-{raw_pn}" if raw_pn else None
                patients = PatientService.search_patients(
                    search=name_term,
                    patient_number_prefix=pn_prefix,
                    limit=50,
                )
                from gws_care.account.account import Account
                from gws_care.patient.patient_account import PatientAccount
                patient_ids = [p.id for p in patients]
                account_names_by_patient: dict[str, list[str]] = {}
                if patient_ids:
                    links = (
                        PatientAccount.select(PatientAccount, Account)
                        .join(Account)
                        .where(PatientAccount.patient_id.in_(patient_ids))
                    )
                    for link in links:
                        pid = str(link.patient_id)
                        account_names_by_patient.setdefault(pid, []).append(link.account.name)
                self.picker_patients = [
                    PatientPickerRowDTO(
                        id=str(p.id),
                        patient_number=p.patient_number,
                        first_name=p.first_name,
                        last_name=p.last_name,
                        date_of_birth=p.date_of_birth.isoformat() if p.date_of_birth else "",
                        gender=p.gender or "",
                        account_name=", ".join(account_names_by_patient.get(str(p.id), [])),
                    )
                    for p in patients
                ]
        except Exception as e:
            self.picker_error = str(e)
        finally:
            self.picker_is_loading = False

    async def _open_picker(self):
        self.picker_filter_name = ""
        self.picker_filter_number = ""
        self.picker_error = ""
        self.picker_patients = []
        await self._run_picker_search()

    # ── Patient picker events ──────────────────────────────────────────────

    @rx.event
    async def open_patient_picker(self):
        await self._open_picker()
        self.picker_is_open = True

    @rx.event
    def close_patient_picker(self):
        self.picker_is_open = False

    @rx.event
    def picker_clear_selection(self):
        self.picker_selected_id = ""
        self.picker_selected_label = ""

    @rx.event
    async def picker_set_filter_name(self, value: str):
        self.picker_filter_name = value
        await self._run_picker_search()

    @rx.event
    async def picker_set_filter_number(self, value: str):
        self.picker_filter_number = value
        await self._run_picker_search()

    @rx.event
    async def picker_clear_filters(self):
        self.picker_filter_name = ""
        self.picker_filter_number = ""
        await self._run_picker_search()

    @rx.event
    def picker_select_patient(self, patient_id: str, label: str):
        self.picker_selected_id = patient_id
        self.picker_selected_label = label
        self.picker_is_open = False

    # ── Edit dialog events ─────────────────────────────────────────────────

    @rx.event
    async def open_edit(self):
        """Populate edit form from current state and open the dialog."""
        from gws_care.care_app._care_app.care_app.admin_documents.admin_documents_state import _UPLOADED_TYPE_LABELS
        # Find the original doc_type key from the label
        doc_type_key = ""
        for k, v in _UPLOADED_TYPE_LABELS.items():
            if v == self.doc_type_label:
                doc_type_key = k
                break
        self.edit_form_doc_type = doc_type_key
        self.edit_form_date = self.doc_date
        self.edit_form_description = self.description
        self.edit_form_notes = self.notes
        self.picker_selected_id = self.patient_id
        self.picker_selected_label = self.patient_name
        self.edit_error = ""
        self.edit_open = True

    @rx.event
    def close_edit(self):
        self.edit_open = False
        self.edit_error = ""

    @rx.event
    def set_edit_form_doc_type(self, value: str):
        self.edit_form_doc_type = value

    @rx.event
    def set_edit_form_date(self, value: str):
        self.edit_form_date = value

    @rx.event
    def set_edit_form_description(self, value: str):
        self.edit_form_description = value

    @rx.event
    def set_edit_form_notes(self, value: str):
        self.edit_form_notes = value

    @rx.event
    async def save_edit(self):
        self.edit_is_saving = True
        self.edit_error = ""
        try:
            with await self.authenticate_user():
                from datetime import date
                from gws_care.document_upload.uploaded_document import UploadedDocument
                doc = UploadedDocument.get_by_id(self._loaded_doc_id)
                doc.patient_id = self.picker_selected_id or None
                doc.doc_type = self.edit_form_doc_type or None
                doc.doc_date = date.fromisoformat(self.edit_form_date) if self.edit_form_date else None
                doc.description = self.edit_form_description or None
                doc.notes = self.edit_form_notes or None
                doc.save()
            self.edit_open = False
            await self._load_document()
        except Exception as e:
            self.edit_error = str(e)
        finally:
            self.edit_is_saving = False
