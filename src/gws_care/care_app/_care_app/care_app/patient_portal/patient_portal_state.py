"""State for the patient portal pages (7.5).

The portal has four routes sharing a single state:
  /my-results       — visits with doctor_company_validated status
  /my-appointments  — all appointments for the patient
  /my-messages      — notifications/messages received by the patient
  /my-documents     — medical certificates + exam files
"""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class PortalExamResultDTO(BaseModel):
    id: str
    exam_type_label: str
    exam_date: str
    status: str
    status_label: str
    interpretation: str = ""
    visit_number: str = ""
    campaign_name: str = ""
    visit_type: str = ""


class PortalAppointmentDTO(BaseModel):
    id: str
    visit_number: str
    scheduled_at: str
    status: str
    status_label: str


class PortalDocumentDTO(BaseModel):
    id: str
    issue_date: str
    conclusion: str
    is_fit_for_work: bool
    restrictions: str = ""
    issued_by: str = ""


class PortalMessageDTO(BaseModel):
    id: str
    subject: str
    body: str
    notification_type: str = ""
    channel: str = ""
    sent_at: str = ""
    status: str = ""


class PatientPortalState(RoleState):
    """State shared by all three patient-portal pages."""

    # My Results
    portal_exam_results: list[PortalExamResultDTO] = []
    visits_loading: bool = False
    visits_error: str = ""

    # My Appointments
    portal_appointments: list[PortalAppointmentDTO] = []
    appointments_loading: bool = False
    appointments_error: str = ""

    # My Documents
    portal_documents: list[PortalDocumentDTO] = []
    documents_loading: bool = False
    documents_error: str = ""

    # My Messages
    portal_messages: list[PortalMessageDTO] = []
    messages_loading: bool = False
    messages_error: str = ""

    # ── Page guards ───────────────────────────────────────────────────────────

    @rx.event
    async def on_load_results(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user)
        if redirect:
            return redirect
        await self._load_visits()

    @rx.event
    async def on_load_appointments(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user)
        if redirect:
            return redirect
        await self._load_appointments()

    @rx.event
    async def on_load_documents(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user)
        if redirect:
            return redirect
        await self._load_documents()

    @rx.event
    async def on_load_messages(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user)
        if redirect:
            return redirect
        await self._load_messages()

    # ── Navigation ────────────────────────────────────────────────────────────

    @rx.event
    def go_to_results(self):
        return rx.redirect("/my-results")

    @rx.event
    def go_to_appointments(self):
        return rx.redirect("/my-appointments")

    @rx.event
    def go_to_messages(self):
        return rx.redirect("/my-messages")

    @rx.event
    def go_to_documents(self):
        return rx.redirect("/my-documents")

    # ── Loaders ───────────────────────────────────────────────────────────────

    async def _load_visits(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.portal_visits = []
            return
        self.visits_loading = True
        self.visits_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                exams = list(
                    Exam.select()
                    .where(Exam.patient == patient_id)
                    .order_by(Exam.exam_date.desc())
                )
                results = []
                for e in exams:
                    visit_number = ""
                    campaign_name = ""
                    visit_type = ""
                    try:
                        if e.visit_id:
                            visit_number = e.visit.visit_number or ""
                            visit_type = e.visit.visit_type.value if e.visit.visit_type else ""
                            if e.visit.campaign_id:
                                campaign_name = e.visit.campaign.name
                    except Exception:
                        pass
                    results.append(PortalExamResultDTO(
                        id=str(e.id),
                        exam_type_label=e.exam_type.get_label() if hasattr(e.exam_type, "get_label") else str(e.exam_type.value),
                        exam_date=str(e.exam_date),
                        status=e.status.value,
                        status_label=e.status.get_label() if hasattr(e.status, "get_label") else e.status.value,
                        interpretation=e.interpretation or "",
                        visit_number=visit_number,
                        campaign_name=campaign_name,
                        visit_type=visit_type,
                    ))
                self.portal_exam_results = results
        except Exception as e:
            self.visits_error = str(e)
        finally:
            self.visits_loading = False

    async def _load_appointments(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.portal_appointments = []
            return
        self.appointments_loading = True
        self.appointments_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.consultation_service import ConsultationService
                visits = ConsultationService.list_for_patient(patient_id)
                self.portal_appointments = [
                    PortalAppointmentDTO(
                        id=str(v.id),
                        visit_number=v.visit_number or "",
                        scheduled_at=str(v.scheduled_at) if v.scheduled_at else "",
                        status=v.consultation_visit_status.value if v.consultation_visit_status else "",
                        status_label=v.consultation_visit_status.get_label() if v.consultation_visit_status else "",
                    )
                    for v in visits
                ]
        except Exception as e:
            self.appointments_error = str(e)
        finally:
            self.appointments_loading = False

    async def _load_documents(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.portal_documents = []
            return
        self.documents_loading = True
        self.documents_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.certificate.medical_certificate import MedicalCertificateService
                certs = MedicalCertificateService.list_for_patient(patient_id)
                docs = []
                for cert in certs:
                    issued_by_name = ""
                    if cert.issued_by_id:
                        try:
                            from gws_care.user.user import User
                            u = User.get_by_id(str(cert.issued_by_id))
                            issued_by_name = f"Dr. {u.last_name} {u.first_name}"
                        except Exception:
                            pass
                    docs.append(PortalDocumentDTO(
                        id=str(cert.id),
                        issue_date=str(cert.issue_date),
                        conclusion=cert.conclusion or "",
                        is_fit_for_work=cert.is_fit_for_work,
                        restrictions=cert.restrictions or "",
                        issued_by=issued_by_name,
                    ))
                self.portal_documents = docs
        except Exception as e:
            self.documents_error = str(e)
        finally:
            self.documents_loading = False

    # ── Phase 8 — Certificate PDF download ───────────────────────────────────

    @rx.event
    async def download_certificate_pdf(self, certificate_id: str):
        """Generate and download a medical certificate PDF for the patient."""
        self.documents_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_certificate_pdf
                pdf_bytes = generate_certificate_pdf(certificate_id)
            return rx.download(data=pdf_bytes, filename=f"certificat_{certificate_id[:8]}.pdf")
        except Exception as e:
            self.documents_error = f"Erreur génération PDF : {e}"

    # ── Messages loader ───────────────────────────────────────────────────────

    async def _load_messages(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.portal_messages = []
            return
        self.messages_loading = True
        self.messages_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_models import NotificationLog
                logs = list(
                    NotificationLog.select()
                    .where(NotificationLog.patient == patient_id)
                    .order_by(NotificationLog.created_at.desc())
                    .limit(100)
                )
                self.portal_messages = [
                    PortalMessageDTO(
                        id=str(log.id),
                        subject=log.subject or "",
                        body=log.body or "",
                        notification_type=log.notification_type.value if log.notification_type else "",
                        channel=log.channel.value if log.channel else "",
                        sent_at=str(log.created_at)[:16] if log.created_at else "",
                        status=log.status.value if log.status else "",
                    )
                    for log in logs
                ]
        except Exception as e:
            self.messages_error = str(e)
        finally:
            self.messages_loading = False
