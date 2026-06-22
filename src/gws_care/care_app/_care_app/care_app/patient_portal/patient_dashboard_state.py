"""State for the patient portal Dashboard page (/patient-dashboard).

Same data structure as DashboardState (admin) but every query is scoped to the
logged-in patient.  No account picker — the filter is always self._linked_patient_id.
"""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


# ── DTOs — identical to the admin DashboardState ─────────────────────────────


class ExamTypeStat(BaseModel):
    label: str
    count: int


class AppointmentStatusStat(BaseModel):
    status: str
    label: str
    count: int


class MonthlyExamStat(BaseModel):
    month: str   # "YYYY-MM"
    count: int


# ── State ─────────────────────────────────────────────────────────────────────


class PatientDashboardState(RoleState):
    """State for the /patient-dashboard page."""

    total_exams: int = 0
    total_appointments: int = 0
    total_certificates: int = 0
    total_notifications: int = 0

    exams_by_type: list[ExamTypeStat] = []
    appointments_by_status: list[AppointmentStatusStat] = []
    monthly_exams: list[MonthlyExamStat] = []

    is_loading: bool = False
    error_message: str = ""

    # ── Page guard ────────────────────────────────────────────────────────────

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user, redirect_to="/dashboard")
        if redirect:
            return redirect
        await self._load_stats()

    # ── Data loader ────────────────────────────────────────────────────────────

    async def _load_stats(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            return

        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from peewee import fn, SQL

                from gws_care.certificate.medical_certificate import MedicalCertificate
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamType
                from gws_care.notification.notification_models import NotificationLog
                from gws_care.visit.consultation_visit_status import ConsultationVisitStatus
                from gws_care.visit.visit import Visit
                from gws_care.visit.visit_type import VisitType

                # ── KPIs ──────────────────────────────────────────────────────
                self.total_exams = (
                    Exam.select()
                    .where(Exam.patient == patient_id)
                    .count()
                )
                # Count consultations only (what the patient-facing portal tracks)
                self.total_appointments = (
                    Visit.select()
                    .where(
                        (Visit.patient == patient_id)
                        & (Visit.visit_type == VisitType.CONSULTATION)
                    )
                    .count()
                )
                self.total_certificates = (
                    MedicalCertificate.select()
                    .where(MedicalCertificate.patient == patient_id)
                    .count()
                )
                self.total_notifications = (
                    NotificationLog.select()
                    .where(NotificationLog.patient == patient_id)
                    .count()
                )

                # ── Exams by type ─────────────────────────────────────────────
                type_q = (
                    Exam.select(Exam.exam_type, fn.COUNT(Exam.id).alias("cnt"))
                    .where(Exam.patient == patient_id)
                    .group_by(Exam.exam_type)
                )
                self.exams_by_type = [
                    ExamTypeStat(
                        label=ExamType(row[0]).get_label(),
                        count=row[1],
                    )
                    for row in type_q.tuples()
                ]

                # ── Consultations by status ────────────────────────────────────
                status_q = (
                    Visit.select(
                        Visit.consultation_visit_status,
                        fn.COUNT(Visit.id).alias("cnt"),
                    )
                    .where(
                        (Visit.patient == patient_id)
                        & (Visit.visit_type == VisitType.CONSULTATION)
                        & Visit.consultation_visit_status.is_null(False)
                    )
                    .group_by(Visit.consultation_visit_status)
                )
                self.appointments_by_status = [
                    AppointmentStatusStat(
                        status=row[0],
                        label=ConsultationVisitStatus(row[0]).get_label(),
                        count=row[1],
                    )
                    for row in status_q.tuples()
                ]

                # ── Monthly exams — last 12 months ────────────────────────────
                monthly_q = (
                    Exam.select(
                        fn.DATE_FORMAT(Exam.exam_date, "%Y-%m").alias("month"),
                        fn.COUNT(Exam.id).alias("cnt"),
                    )
                    .where(Exam.patient == patient_id)
                    .group_by(SQL("month"))
                    .order_by(SQL("month").desc())
                    .limit(12)
                )
                self.monthly_exams = list(reversed([
                    MonthlyExamStat(month=row[0], count=row[1])
                    for row in monthly_q.tuples()
                ]))

        except Exception as e:
            self.error_message = f"Error loading dashboard: {e}"
        finally:
            self.is_loading = False
