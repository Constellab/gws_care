"""Exam session model."""

from datetime import date

from gws_core import EnumField
from gws_core.core.model.db_field import JSONField
from peewee import BooleanField, CharField, DateField, FloatField, ForeignKeyField, TextField  # noqa: F401 (CharField used for exam_type_ref_id)

from gws_care.account.account import Account
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam.exam_type import ExamStatus, ExamType
from gws_care.patient.patient import Patient
from gws_care.user.user import User

from .exam_dto import ExamDTO


class Exam(ModelWithUser):
    """One exam session for a patient.

    An exam session covers a single exam type performed on a given date.
    Results are stored in ExamResult records linked to this exam.

    When consultation_id is set, the clinical context (reason, history, vitals)
    is shared with the parent Consultation record and should not be edited per-exam.
    """

    patient: Patient = ForeignKeyField(Patient, null=False, backref="exams", on_delete="CASCADE")
    billing_account: Account = ForeignKeyField(Account, null=True, backref="exams", on_delete="SET NULL")
    # consultation_id links this exam to a parent Consultation (nullable for standalone exams)
    consultation_id: str = CharField(max_length=36, null=True, default=None, index=True)
    exam_date: date = DateField(null=False, index=True)
    exam_type: ExamType = EnumField(choices=ExamType, null=False)
    exam_type_ref_id: str = CharField(max_length=36, null=True, default=None)
    status: ExamStatus = EnumField(choices=ExamStatus, default=ExamStatus.DRAFT, null=False)
    reason_for_visit: str = TextField(null=True)
    medical_history: str = TextField(null=True)
    weight: float = FloatField(null=True)        # kg
    height: float = FloatField(null=True)        # cm
    bmi: float = FloatField(null=True)
    blood_pressure: str = CharField(max_length=50, null=True)
    heart_rate: float = FloatField(null=True)    # bpm
    temperature: float = FloatField(null=True)   # °C
    conclusion: str = TextField(null=True)
    lab_results: list = JSONField(null=True)  # list of {parameter, value, reference_range, status}
    requested_param_ids: list = JSONField(null=True)  # list of ExamParameter.id strings — tests requested by doctor
    # ExamTypeRef.id strings prescribed by doctor for follow-up (blood test, X-ray, etc.)
    prescribed_exam_ref_ids: list = JSONField(null=True)
    # Exam.id strings of the actual follow-up Exam records created from prescribed_exam_ref_ids
    follow_up_exam_ids: list = JSONField(null=True)
    # True when this exam was created as a follow-up prescription (simplified lab view)
    is_follow_up: bool = BooleanField(default=False, null=False)
    interpretation: str = TextField(null=True)
    interpreted_by: User = ForeignKeyField(User, null=True, backref="+")

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
            conclusion=self.conclusion,
            lab_results=self.lab_results or [],
            requested_param_ids=self.requested_param_ids or [],
            prescribed_exam_ref_ids=self.prescribed_exam_ref_ids or [],
            follow_up_exam_ids=self.follow_up_exam_ids or [],
            is_follow_up=bool(self.is_follow_up),
            interpretation=self.interpretation,
            interpreted_by_id=str(self.interpreted_by_id) if self.interpreted_by_id else None,
            consultation_id=self.consultation_id or "",
        )

    class Meta:
        table_name = "gws_care_exam"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
