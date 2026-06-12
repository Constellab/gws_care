"""State for the admin 'Gestion des documents' page.

Extends PatientDocumentsState to remove the _linked_patient_id restriction,
so operators, doctors, and admins can browse documents across all patients.

Only _load_all_documents is overridden — the admin view uses a single combined
table (type-filtered via the inherited all_docs_filter_type var). Individual
exam/prescription/certificate sub-lists are not needed in the admin UI.

The `extra` field of AllDocumentRowDTO is repurposed here to carry the
patient's full name, which the reused _all_doc_row component renders in its
last data column.
"""

import reflex as rx

from ..common.patient_picker_state import PatientPickerRowDTO
from ..patient_portal.patient_documents_state import AllDocumentRowDTO, PatientDocumentsState

def _get_file_icon(original_name: str) -> str:
    """Return a Lucide icon name based on file extension."""
    if not original_name or "." not in original_name:
        return "file"
    ext = original_name.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return "file-text"
    if ext in ("png", "jpg", "jpeg", "bmp", "tiff", "tif", "webp", "gif", "svg"):
        return "image"
    if ext in ("xlsx", "xls", "csv", "ods"):
        return "file-spreadsheet"
    if ext in ("docx", "doc", "odt", "txt", "rtf", "odp", "ppt", "pptx"):
        return "file-text"
    if ext in ("dcm", "nii"):
        return "scan"
    return "file"


_UPLOADED_TYPE_LABELS: dict[str, str] = {
    "prescription": "Ordonnance",
    "medical_certificate": "Certificat médical",
    "medical_report": "Compte-rendu médical",
    "medical_analysis": "Analyse médicale",
    "letter": "Courrier",
    "xray": "Radiographie",
    "ct_scan": "Scanner",
    "mri": "IRM",
    "ultrasound": "Échographie",
    "other": "Autre",
}


class AdminDocumentsState(PatientDocumentsState):
    """All-patient documents state for operator / doctor / admin roles."""

    admin_filter_patient_name: str = ""

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

    # ── Edit uploaded document dialog ─────────────────────────────────────────
    edit_uploaded_open: bool = False
    edit_uploaded_id: str = ""
    edit_form_doc_type: str = ""
    edit_form_date: str = ""
    edit_form_description: str = ""
    edit_form_notes: str = ""
    edit_uploaded_error: str = ""
    edit_uploaded_is_saving: bool = False

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(
            self.is_operator, self.is_doctor, self.is_admin
        )
        if redirect:
            return redirect
        await self._load_all_documents()

    @rx.event
    def set_admin_filter_patient_name(self, value: str):
        self.admin_filter_patient_name = value

    @rx.event
    def clear_admin_docs_filters(self):
        self.all_docs_filter_type = "ALL"
        self.all_docs_filter_from = ""
        self.all_docs_filter_to = ""
        self.admin_filter_patient_name = ""

    @rx.var
    def admin_filtered_documents(self) -> list[AllDocumentRowDTO]:
        """Filtered + sorted documents with an extra patient-name search."""
        rows = self.all_documents
        if self.all_docs_filter_type and self.all_docs_filter_type != "ALL":
            rows = [r for r in rows if r.doc_type == self.all_docs_filter_type]
        if self.all_docs_filter_from:
            rows = [r for r in rows if r.date >= self.all_docs_filter_from]
        if self.all_docs_filter_to:
            rows = [r for r in rows if r.date <= self.all_docs_filter_to]
        if self.admin_filter_patient_name:
            q = self.admin_filter_patient_name.lower()
            rows = [r for r in rows if q in r.extra.lower()]
        col = self.all_docs_sort_column
        return sorted(
            rows,
            key=lambda r: str(getattr(r, col) or "").lower(),
            reverse=not self.all_docs_sort_ascending,
        )

    async def _load_all_documents(self):
        """Load documents across all patients (or filtered subset).

        Populates AllDocumentRowDTO.extra with the patient full name so the
        shared _all_doc_row component displays it in the last data column.
        """
        if not await self.check_authentication():
            return
        self.all_docs_loading = True
        self.all_docs_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.certificate.medical_certificate import (
                    CERTIFICATE_TYPES,
                    MedicalCertificateService,
                )
                from gws_care.exam.exam_service import ExamService
                from gws_care.patient.patient import Patient
                from gws_care.prescription.prescription import PrescriptionService

                patients = list(Patient.select().order_by(Patient.last_name))

                docs: list[AllDocumentRowDTO] = []
                for patient in patients:
                    patient_name = patient.get_full_name()
                    pid = str(patient.id)

                    exams = ExamService.list_exams_for_patient(pid)
                    for e in exams:
                        lbl = (
                            e.exam_type.get_label()
                            if hasattr(e.exam_type, "get_label")
                            else str(e.exam_type.value)
                        )
                        status_lbl = e.status.get_label() if hasattr(e.status, "get_label") else e.status.value
                        docs.append(AllDocumentRowDTO(
                            id=str(e.id),
                            doc_type="exam",
                            date=e.exam_date.isoformat() if e.exam_date else "",
                            description=lbl,
                            sub_label=e.interpretation or status_lbl,
                            extra=patient_name,
                            icon="stethoscope",
                        ))

                    prescriptions = PrescriptionService.list_for_patient(pid, include_archived=True)
                    for p in prescriptions:
                        drug_count = len(p.drugs) if hasattr(p, "drugs") else 0
                        docs.append(AllDocumentRowDTO(
                            id=str(p.id),
                            doc_type="prescription",
                            date=p.prescription_date.isoformat() if p.prescription_date else "",
                            description=p.diagnosis or "(no diagnosis)",
                            sub_label=f"{drug_count} drug(s)" if drug_count else "",
                            extra=patient_name,
                            icon="pill",
                        ))

                    certificates = MedicalCertificateService.list_for_patient(pid, include_archived=True)
                    for c in certificates:
                        docs.append(AllDocumentRowDTO(
                            id=str(c.id),
                            doc_type="certificate",
                            date=c.issue_date.isoformat() if c.issue_date else "",
                            description=CERTIFICATE_TYPES.get(
                                c.certificate_type or "APTITUDE", c.certificate_type or ""
                            ),
                            sub_label=c.conclusion[:80] if c.conclusion else "",
                            extra=patient_name,
                            icon="award",
                        ))

                # ── Uploaded documents ─────────────────────────────────────
                from gws_care.document_upload.uploaded_document import UploadedDocument

                for ud in UploadedDocument.select().order_by(UploadedDocument.doc_date.desc(nulls="LAST")):
                    patient_name = ""
                    if ud.patient_id:
                        try:
                            p = Patient.get_by_id(str(ud.patient_id))
                            patient_name = p.get_full_name()
                        except Exception:
                            pass
                    docs.append(AllDocumentRowDTO(
                        id=str(ud.id),
                        doc_type="uploaded",
                        date=ud.doc_date.isoformat() if ud.doc_date else "",
                        description=ud.description or ud.original_name or "",
                        sub_label=_UPLOADED_TYPE_LABELS.get(ud.doc_type or "", ud.doc_type or ""),
                        extra=patient_name,
                        icon=_get_file_icon(ud.original_name or ""),
                    ))

                docs.sort(key=lambda d: d.date or "", reverse=True)
                self.all_documents = docs
        except Exception as e:
            self.all_docs_error = f"Error: {e}"
        finally:
            self.all_docs_loading = False

    # ── Patient picker private helpers (inlined from PatientPickerState) ─────

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

    # ── Patient picker events ─────────────────────────────────────────────────

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

    # ── Edit uploaded document events ─────────────────────────────────────────

    @rx.event
    async def open_edit_uploaded(self, doc_id: str):
        """Load an existing UploadedDocument and open the edit dialog."""
        self.edit_uploaded_id = doc_id
        self.edit_form_doc_type = ""
        self.edit_form_date = ""
        self.edit_form_description = ""
        self.edit_form_notes = ""
        self.edit_uploaded_error = ""
        self.picker_selected_id = ""
        self.picker_selected_label = ""
        try:
            with await self.authenticate_user():
                from gws_care.document_upload.uploaded_document import UploadedDocument
                doc = UploadedDocument.get_by_id(doc_id)
                self.edit_form_doc_type = doc.doc_type or ""
                self.edit_form_date = doc.doc_date.isoformat() if doc.doc_date else ""
                self.edit_form_description = doc.description or ""
                self.edit_form_notes = doc.notes or ""
                if doc.patient_id:
                    from gws_care.patient.patient import Patient
                    try:
                        p = Patient.get_by_id(str(doc.patient_id))
                        self.picker_selected_id = str(doc.patient_id)
                        self.picker_selected_label = p.get_full_name()
                    except Exception:
                        pass
        except Exception as e:
            self.edit_uploaded_error = str(e)
        self.edit_uploaded_open = True

    @rx.event
    def close_edit_uploaded(self):
        self.edit_uploaded_open = False
        self.edit_uploaded_error = ""

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
    def navigate_to_document(self, doc_id: str, doc_type: str):
        if doc_type == "exam":
            return rx.redirect(f"/exam/{doc_id}")
        elif doc_type == "prescription":
            return rx.redirect(f"/prescription/{doc_id}")
        elif doc_type == "certificate":
            return rx.redirect(f"/certificate/{doc_id}")
        elif doc_type == "uploaded":
            return rx.redirect(f"/document/{doc_id}")

    @rx.event
    async def save_edit_uploaded(self):
        """Update the UploadedDocument record."""
        self.edit_uploaded_is_saving = True
        self.edit_uploaded_error = ""
        try:
            with await self.authenticate_user():
                from datetime import date
                from gws_care.document_upload.uploaded_document import UploadedDocument
                doc = UploadedDocument.get_by_id(self.edit_uploaded_id)
                doc.patient_id = self.picker_selected_id or None
                doc.doc_type = self.edit_form_doc_type or None
                doc.doc_date = date.fromisoformat(self.edit_form_date) if self.edit_form_date else None
                doc.description = self.edit_form_description or None
                doc.notes = self.edit_form_notes or None
                doc.save()
            self.edit_uploaded_open = False
            await self._load_all_documents()
        except Exception as e:
            self.edit_uploaded_error = str(e)
        finally:
            self.edit_uploaded_is_saving = False
