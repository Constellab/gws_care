"""State for the patient portal document pages.

Handles four routes sharing a common patient-scoped data loader:
  /my-exams           — exam list
  /my-prescriptions   — prescription list
  /my-certificates    — certificate list
  /my-all-documents   — all three types combined with type filter
"""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


# ── DTOs ──────────────────────────────────────────────────────────────────────


class PatientExamRowDTO(BaseModel):
    id: str
    exam_date: str = ""
    exam_type_label: str = ""
    status: str = ""
    status_label: str = ""
    interpretation: str = ""


class PatientPrescriptionRowDTO(BaseModel):
    id: str
    prescription_date: str = ""
    diagnosis: str = ""
    drug_count: int = 0
    prescribed_by_name: str = ""
    is_archived: bool = False


class PatientCertificateRowDTO(BaseModel):
    id: str
    issue_date: str = ""
    certificate_type_label: str = ""
    conclusion: str = ""
    is_fit_for_work: bool = True
    issued_by_name: str = ""
    is_archived: bool = False


class AllDocumentRowDTO(BaseModel):
    """Unified row for the All Documents view."""

    id: str
    doc_type: str  # "exam" | "prescription" | "certificate" | "uploaded"
    date: str = ""
    description: str = ""
    sub_label: str = ""   # exam type / drug count / cert type
    extra: str = ""       # e.g. issued_by / prescribed_by / patient name
    icon: str = "file"    # Lucide icon name based on doc type / file extension


# ── State ─────────────────────────────────────────────────────────────────────


class PatientDocumentsState(RoleState):
    """State shared by all four patient document pages."""

    # Exams
    exams: list[PatientExamRowDTO] = []
    exams_loading: bool = False
    exams_error: str = ""
    exam_filter_from: str = ""
    exam_filter_to: str = ""
    exam_filter_type: str = ""
    exam_filter_status: str = ""
    exam_type_options: list[str] = []
    exam_sort_column: str = "exam_date"
    exam_sort_ascending: bool = False

    # Prescriptions
    prescriptions: list[PatientPrescriptionRowDTO] = []
    prescriptions_loading: bool = False
    prescriptions_error: str = ""
    presc_filter_from: str = ""
    presc_filter_to: str = ""
    presc_show_archived: bool = False
    presc_sort_column: str = "prescription_date"
    presc_sort_ascending: bool = False

    # Certificates
    certificates: list[PatientCertificateRowDTO] = []
    certificates_loading: bool = False
    certificates_error: str = ""
    cert_filter_from: str = ""
    cert_filter_to: str = ""
    cert_show_archived: bool = False
    cert_sort_column: str = "issue_date"
    cert_sort_ascending: bool = False

    # All documents combined
    all_documents: list[AllDocumentRowDTO] = []
    all_docs_loading: bool = False
    all_docs_error: str = ""
    all_docs_filter_type: str = "ALL"
    all_docs_filter_from: str = ""
    all_docs_filter_to: str = ""
    all_docs_sort_column: str = "date"
    all_docs_sort_ascending: bool = False

    # PDF download error
    pdf_error: str = ""

    # ── Page guards ───────────────────────────────────────────────────────

    @rx.event
    async def on_load_exams(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user, redirect_to="/dashboard")
        if redirect:
            return redirect
        await self._load_exams()

    @rx.event
    async def on_load_prescriptions(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user, redirect_to="/dashboard")
        if redirect:
            return redirect
        await self._load_prescriptions()

    @rx.event
    async def on_load_certificates(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user, redirect_to="/dashboard")
        if redirect:
            return redirect
        await self._load_certificates()

    @rx.event
    async def on_load_all_documents(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user, redirect_to="/dashboard")
        if redirect:
            return redirect
        await self._load_all_documents()

    # ── Navigation ─────────────────────────────────────────────────────────

    @rx.event
    def go_to_exam(self, exam_id: str):
        return rx.redirect(f"/exam/{exam_id}")

    @rx.event
    def go_to_prescription(self, prescription_id: str):
        return rx.redirect(f"/prescription/{prescription_id}")

    @rx.event
    def go_to_certificate(self, certificate_id: str):
        return rx.redirect(f"/certificate/{certificate_id}")

    # ── Exam filter + sort events ─────────────────────────────────────────

    @rx.event
    def set_exam_filter_from(self, value: str):
        self.exam_filter_from = value

    @rx.event
    def set_exam_filter_to(self, value: str):
        self.exam_filter_to = value

    @rx.event
    def set_exam_filter_type(self, value: str):
        self.exam_filter_type = "" if value == "ALL" else value

    @rx.event
    def set_exam_filter_status(self, value: str):
        self.exam_filter_status = "" if value == "ALL" else value

    @rx.event
    def clear_exam_filters(self):
        self.exam_filter_from = ""
        self.exam_filter_to = ""
        self.exam_filter_type = ""
        self.exam_filter_status = ""

    @rx.event
    def set_exam_sort(self, column: str):
        if self.exam_sort_column == column:
            self.exam_sort_ascending = not self.exam_sort_ascending
        else:
            self.exam_sort_column = column
            self.exam_sort_ascending = True

    @rx.var
    def filtered_exams(self) -> list[PatientExamRowDTO]:
        rows = self.exams
        if self.exam_filter_from:
            rows = [r for r in rows if r.exam_date >= self.exam_filter_from]
        if self.exam_filter_to:
            rows = [r for r in rows if r.exam_date <= self.exam_filter_to]
        if self.exam_filter_type:
            rows = [r for r in rows if r.exam_type_label == self.exam_filter_type]
        if self.exam_filter_status:
            rows = [r for r in rows if r.status == self.exam_filter_status]
        col = self.exam_sort_column
        return sorted(rows, key=lambda r: str(getattr(r, col) or "").lower(), reverse=not self.exam_sort_ascending)

    # ── Prescription filter + sort events ────────────────────────────────

    @rx.event
    def set_presc_filter_from(self, value: str):
        self.presc_filter_from = value

    @rx.event
    def set_presc_filter_to(self, value: str):
        self.presc_filter_to = value

    @rx.event
    def toggle_presc_show_archived(self):
        self.presc_show_archived = not self.presc_show_archived

    @rx.event
    def clear_presc_filters(self):
        self.presc_filter_from = ""
        self.presc_filter_to = ""
        self.presc_show_archived = False

    @rx.event
    def set_presc_sort(self, column: str):
        if self.presc_sort_column == column:
            self.presc_sort_ascending = not self.presc_sort_ascending
        else:
            self.presc_sort_column = column
            self.presc_sort_ascending = True

    @rx.var
    def filtered_prescriptions(self) -> list[PatientPrescriptionRowDTO]:
        rows = self.prescriptions
        if not self.presc_show_archived:
            rows = [r for r in rows if not r.is_archived]
        if self.presc_filter_from:
            rows = [r for r in rows if r.prescription_date >= self.presc_filter_from]
        if self.presc_filter_to:
            rows = [r for r in rows if r.prescription_date <= self.presc_filter_to]
        col = self.presc_sort_column
        return sorted(rows, key=lambda r: str(getattr(r, col) or "").lower(), reverse=not self.presc_sort_ascending)

    # ── Certificate filter + sort events ──────────────────────────────────

    @rx.event
    def set_cert_filter_from(self, value: str):
        self.cert_filter_from = value

    @rx.event
    def set_cert_filter_to(self, value: str):
        self.cert_filter_to = value

    @rx.event
    def toggle_cert_show_archived(self):
        self.cert_show_archived = not self.cert_show_archived

    @rx.event
    def clear_cert_filters(self):
        self.cert_filter_from = ""
        self.cert_filter_to = ""
        self.cert_show_archived = False

    @rx.event
    def set_cert_sort(self, column: str):
        if self.cert_sort_column == column:
            self.cert_sort_ascending = not self.cert_sort_ascending
        else:
            self.cert_sort_column = column
            self.cert_sort_ascending = True

    @rx.var
    def filtered_certificates(self) -> list[PatientCertificateRowDTO]:
        rows = self.certificates
        if not self.cert_show_archived:
            rows = [r for r in rows if not r.is_archived]
        if self.cert_filter_from:
            rows = [r for r in rows if r.issue_date >= self.cert_filter_from]
        if self.cert_filter_to:
            rows = [r for r in rows if r.issue_date <= self.cert_filter_to]
        col = self.cert_sort_column
        return sorted(rows, key=lambda r: str(getattr(r, col) or "").lower(), reverse=not self.cert_sort_ascending)

    # ── All documents filter + sort events ────────────────────────────────

    @rx.event
    def set_all_docs_filter_type(self, value: str):
        self.all_docs_filter_type = value

    @rx.event
    def set_all_docs_filter_from(self, value: str):
        self.all_docs_filter_from = value

    @rx.event
    def set_all_docs_filter_to(self, value: str):
        self.all_docs_filter_to = value

    @rx.event
    def clear_all_docs_filters(self):
        self.all_docs_filter_type = "ALL"
        self.all_docs_filter_from = ""
        self.all_docs_filter_to = ""

    @rx.event
    def set_all_docs_sort(self, column: str):
        if self.all_docs_sort_column == column:
            self.all_docs_sort_ascending = not self.all_docs_sort_ascending
        else:
            self.all_docs_sort_column = column
            self.all_docs_sort_ascending = True

    @rx.var
    def filtered_all_documents(self) -> list[AllDocumentRowDTO]:
        rows = self.all_documents
        if self.all_docs_filter_type and self.all_docs_filter_type != "ALL":
            rows = [r for r in rows if r.doc_type == self.all_docs_filter_type]
        if self.all_docs_filter_from:
            rows = [r for r in rows if r.date >= self.all_docs_filter_from]
        if self.all_docs_filter_to:
            rows = [r for r in rows if r.date <= self.all_docs_filter_to]
        col = self.all_docs_sort_column
        return sorted(rows, key=lambda r: str(getattr(r, col) or "").lower(), reverse=not self.all_docs_sort_ascending)

    # ── PDF download ───────────────────────────────────────────────────────

    @rx.event
    async def download_certificate_pdf(self, certificate_id: str):
        """Generate and download a certificate PDF."""
        self.pdf_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_certificate_pdf
                pdf_bytes = generate_certificate_pdf(certificate_id)
            return rx.download(data=pdf_bytes, filename=f"certificat_{certificate_id[:8]}.pdf")
        except Exception as e:
            self.pdf_error = f"PDF error: {e}"

    @rx.event
    async def download_prescription_pdf(self, prescription_id: str):
        """Generate and download a prescription PDF."""
        self.pdf_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_prescription_pdf
                pdf_bytes = generate_prescription_pdf(prescription_id)
            return rx.download(data=pdf_bytes, filename=f"ordonnance_{prescription_id[:8]}.pdf")
        except Exception as e:
            self.pdf_error = f"PDF error: {e}"

    # ── Data loaders ───────────────────────────────────────────────────────

    async def _load_exams(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.exams = []
            return
        self.exams_loading = True
        self.exams_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam_service import ExamService
                exams = ExamService.list_exams_for_patient(patient_id)
                seen: set[str] = set()
                options: list[str] = []
                rows = []
                for e in exams:
                    lbl = e.exam_type.get_label() if hasattr(e.exam_type, "get_label") else str(e.exam_type.value)
                    if lbl not in seen:
                        seen.add(lbl)
                        options.append(lbl)
                    rows.append(PatientExamRowDTO(
                        id=str(e.id),
                        exam_date=e.exam_date.isoformat() if e.exam_date else "",
                        exam_type_label=lbl,
                        status=e.status.value,
                        status_label=e.status.get_label() if hasattr(e.status, "get_label") else e.status.value,
                        interpretation=e.interpretation or "",
                    ))
                self.exams = rows
                self.exam_type_options = sorted(options)
        except Exception as e:
            self.exams_error = f"Error: {e}"
        finally:
            self.exams_loading = False

    async def _load_prescriptions(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.prescriptions = []
            return
        self.prescriptions_loading = True
        self.prescriptions_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.prescription.prescription import PrescriptionService
                rows = PrescriptionService.list_for_patient(patient_id, include_archived=True)
                self.prescriptions = [
                    PatientPrescriptionRowDTO(
                        id=str(r.id),
                        prescription_date=r.prescription_date.isoformat() if r.prescription_date else "",
                        diagnosis=r.diagnosis or "",
                        drug_count=len(r.drugs),
                        prescribed_by_name=r.to_row_dto().prescribed_by_name if hasattr(r, "to_row_dto") else "",
                        is_archived=bool(r.is_archived),
                    )
                    for r in rows
                ]
        except Exception as e:
            self.prescriptions_error = f"Error: {e}"
        finally:
            self.prescriptions_loading = False

    async def _load_certificates(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.certificates = []
            return
        self.certificates_loading = True
        self.certificates_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.certificate.medical_certificate import (
                    CERTIFICATE_TYPES,
                    MedicalCertificateService,
                )
                rows = MedicalCertificateService.list_for_patient(patient_id, include_archived=True)
                issued_cache: dict = {}

                def _get_issued_by(cert) -> str:
                    if not cert.issued_by_id:
                        return ""
                    uid = str(cert.issued_by_id)
                    if uid not in issued_cache:
                        try:
                            from gws_care.user.user import User
                            u = User.get_by_id(uid)
                            issued_cache[uid] = f"Dr. {u.first_name} {u.last_name}"
                        except Exception:
                            issued_cache[uid] = ""
                    return issued_cache[uid]

                self.certificates = [
                    PatientCertificateRowDTO(
                        id=str(c.id),
                        issue_date=c.issue_date.isoformat() if c.issue_date else "",
                        certificate_type_label=CERTIFICATE_TYPES.get(
                            c.certificate_type or "APTITUDE", c.certificate_type or ""
                        ),
                        conclusion=c.conclusion or "",
                        is_fit_for_work=c.is_fit_for_work,
                        issued_by_name=_get_issued_by(c),
                        is_archived=bool(c.is_archived),
                    )
                    for c in rows
                ]
        except Exception as e:
            self.certificates_error = f"Error: {e}"
        finally:
            self.certificates_loading = False

    async def _load_all_documents(self):
        """Load all documents (exams + prescriptions + certificates) into a unified list."""
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.all_documents = []
            return
        self.all_docs_loading = True
        self.all_docs_error = ""
        try:
            await self._load_exams()
            await self._load_prescriptions()
            await self._load_certificates()
            docs: list[AllDocumentRowDTO] = []

            for e in self.exams:
                docs.append(AllDocumentRowDTO(
                    id=e.id,
                    doc_type="exam",
                    date=e.exam_date,
                    description=e.exam_type_label,
                    sub_label=e.interpretation or e.status_label,
                    extra="",
                    icon="stethoscope",
                ))

            for p in self.prescriptions:
                docs.append(AllDocumentRowDTO(
                    id=p.id,
                    doc_type="prescription",
                    date=p.prescription_date,
                    description=p.diagnosis or "(no diagnosis)",
                    sub_label=f"{p.drug_count} drug(s)" if p.drug_count else "",
                    extra=p.prescribed_by_name,
                    icon="pill",
                ))

            for c in self.certificates:
                docs.append(AllDocumentRowDTO(
                    id=c.id,
                    doc_type="certificate",
                    date=c.issue_date,
                    description=c.certificate_type_label,
                    sub_label=c.conclusion[:80] if c.conclusion else "",
                    extra=c.issued_by_name,
                    icon="award",
                ))

            # Sort all by date desc
            docs.sort(key=lambda d: d.date or "", reverse=True)
            self.all_documents = docs
        except Exception as e:
            self.all_docs_error = f"Error: {e}"
        finally:
            self.all_docs_loading = False
