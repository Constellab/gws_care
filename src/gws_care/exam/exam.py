"""Exam session model."""

from datetime import date

from gws_core import EnumField
from gws_core.core.model.db_field import JSONField
from peewee import BooleanField, CharField, DateField, FloatField, ForeignKeyField, TextField

from gws_care.account.account import Account
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam.exam_type import ExamStatus, ExamType
from gws_care.patient.patient import Patient
from gws_care.user.user import User
from gws_care.visit.visit import Visit

from .exam_dto import ExamDTO


class Exam(ModelWithUser):
    """One exam session for a patient.

    An exam session covers a single exam type performed on a given date.
    Results are stored in ExamResult records linked to this exam.
    """

    patient: Patient = ForeignKeyField(Patient, null=False, backref="exams", on_delete="CASCADE")
    billing_account: Account = ForeignKeyField(Account, null=True, backref="exams", on_delete="SET NULL")
    exam_date: date = DateField(null=False, index=True)
    exam_type: ExamType = EnumField(choices=ExamType, null=False)
    status: ExamStatus = EnumField(choices=ExamStatus, default=ExamStatus.TODO, null=False)
    reason_for_visit: str = TextField(null=True)
    medical_history: str = TextField(null=True)
    weight: float = FloatField(null=True)        # kg
    height: float = FloatField(null=True)        # cm
    bmi: float = FloatField(null=True)
    blood_pressure: str = CharField(max_length=50, null=True)
    heart_rate: float = FloatField(null=True)    # bpm
    temperature: float = FloatField(null=True)   # °C
    lab_results: list = JSONField(null=True)  # list of {parameter, value, reference_range, status}
    interpretation: str = TextField(null=True)
    interpreted_by: User = ForeignKeyField(User, null=True, backref="+")
    # Terrain fields (Phase 4)
    tube_qr_code: str = CharField(max_length=100, null=True, index=True)
    is_done_on_site: bool = BooleanField(default=False, null=False)
    # visit FK — mandatory for EXAM-type visits, nullable for standalone exams (backward compat)
    visit: Visit = ForeignKeyField(Visit, null=True, backref="exams", on_delete="SET NULL")

    def to_dto(self) -> ExamDTO:
        return ExamDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            patient_id=str(self.patient_id),
            account_id=str(self.billing_account_id) if self.billing_account_id else None,
            exam_date=self.exam_date,
            exam_type=self.exam_type,
            status=self.status,
            reason_for_visit=self.reason_for_visit,
            medical_history=self.medical_history,
            weight=self.weight,
            height=self.height,
            bmi=self.bmi,
            blood_pressure=self.blood_pressure,
            heart_rate=self.heart_rate,
            temperature=self.temperature,
            lab_results=self.lab_results or [],
            interpretation=self.interpretation,
            interpreted_by_id=str(self.interpreted_by_id) if self.interpreted_by_id else None,
        )

    class Meta:
        table_name = "gws_care_exam"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
