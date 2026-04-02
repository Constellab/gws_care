"""Dashboard state — aggregated statistics for the home dashboard."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


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


class AccountOptionDTO(BaseModel):
    """Lightweight account option for filter dropdown."""

    id: str
    name: str


class DashboardState(ReflexMainState):
    """State for the /dashboard statistics page."""

    total_patients: int = 0
    total_exams: int = 0
    total_appointments: int = 0
    total_certificates: int = 0

    exams_by_type: list[ExamTypeStat] = []
    appointments_by_status: list[AppointmentStatusStat] = []
    monthly_exams: list[MonthlyExamStat] = []

    companies: list[AccountOptionDTO] = []
    filter_account_id: str = ""

    is_loading: bool = False
    error_message: str = ""

    @rx.event
    async def on_load(self):
        await self._load_companies()
        await self._load_stats()

    @rx.event
    async def set_filter_account(self, value: str):
        """Filter all dashboard stats by account."""
        self.filter_account_id = value if value != "ALL" else ""
        await self._load_stats()

    async def _load_companies(self):
        """Internal: load active accounts for the filter dropdown."""
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                comps = AccountService.list_accounts()
                self.companies = [
                    AccountOptionDTO(id=str(c.id), name=c.name) for c in comps
                ]
        except Exception:
            self.companies = []

    async def _load_stats(self):
        if not await self.check_authentication():
            return

        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.appointment.appointment import Appointment
                from gws_care.appointment.appointment_status import AppointmentStatus
                from gws_care.certificate.medical_certificate import MedicalCertificate
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamType
                from gws_care.patient.patient import Patient

                cid = self.filter_account_id or None

                patient_q = Patient.select()
                exam_q = Exam.select()
                appt_q = Appointment.select()
                cert_q = MedicalCertificate.select()

                if cid:
                    patient_q = patient_q.where(Patient.billing_account == cid)
                    exam_q = exam_q.where(Exam.billing_account == cid)
                    appt_q = appt_q.where(Appointment.billing_account == cid)
                    cert_q = cert_q.join(Patient).where(Patient.billing_account == cid)

                self.total_patients = patient_q.count()
                self.total_exams = exam_q.count()
                self.total_appointments = appt_q.count()
                self.total_certificates = cert_q.count()

                # Exams by type
                from peewee import fn
                type_q = (
                    Exam.select(Exam.exam_type, fn.COUNT(Exam.id).alias("cnt"))
                    .group_by(Exam.exam_type)
                )
                if cid:
                    type_q = type_q.where(Exam.billing_account == cid)
                self.exams_by_type = [
                    ExamTypeStat(
                        label=ExamType(row[0]).get_label(),
                        count=row[1],
                    )
                    for row in type_q.tuples()
                ]

                # Appointments by status
                status_q = (
                    Appointment.select(
                        Appointment.status, fn.COUNT(Appointment.id).alias("cnt")
                    )
                    .group_by(Appointment.status)
                )
                if cid:
                    status_q = status_q.where(Appointment.billing_account == cid)
                _STATUS_LABELS = {
                    "SCHEDULED": "Scheduled",
                    "IN_PROGRESS": "In Progress",
                    "DONE": "Done",
                    "CANCELLED": "Cancelled",
                }
                self.appointments_by_status = [
                    AppointmentStatusStat(
                        status=row[0],
                        label=_STATUS_LABELS.get(row[0], row[0]),
                        count=row[1],
                    )
                    for row in status_q.tuples()
                ]

                # Monthly exams — last 12 months (MariaDB: DATE_FORMAT)
                from peewee import SQL
                from peewee import fn as pfn
                monthly_q = (
                    Exam.select(
                        pfn.DATE_FORMAT(Exam.exam_date, "%Y-%m").alias("month"),
                        pfn.COUNT(Exam.id).alias("cnt"),
                    )
                    .group_by(SQL("month"))
                    .order_by(SQL("month").desc())
                    .limit(12)
                )
                if cid:
                    monthly_q = monthly_q.where(Exam.billing_account == cid)
                self.monthly_exams = list(reversed([
                    MonthlyExamStat(month=row[0], count=row[1])
                    for row in monthly_q.tuples()
                ]))

        except Exception as e:
            self.error_message = f"Error loading dashboard: {e}"
        finally:
            self.is_loading = False
