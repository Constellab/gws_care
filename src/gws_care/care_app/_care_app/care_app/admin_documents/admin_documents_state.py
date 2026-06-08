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

from ..patient_portal.patient_documents_state import AllDocumentRowDTO, PatientDocumentsState


class AdminDocumentsState(PatientDocumentsState):
    """All-patient documents state for operator / doctor / admin roles."""

    admin_filter_patient_name: str = ""

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
                        docs.append(AllDocumentRowDTO(
                            id=str(e.id),
                            doc_type="exam",
                            date=e.exam_date.isoformat() if e.exam_date else "",
                            description=lbl,
                            sub_label=(
                                e.status.get_label()
                                if hasattr(e.status, "get_label")
                                else e.status.value
                            ),
                            extra=patient_name,
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
                        sub_label=ud.doc_type or "",
                        extra=patient_name,
                    ))

                docs.sort(key=lambda d: d.date or "", reverse=True)
                self.all_documents = docs
        except Exception as e:
            self.all_docs_error = f"Error: {e}"
        finally:
            self.all_docs_loading = False
