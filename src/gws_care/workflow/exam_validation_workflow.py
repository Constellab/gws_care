"""ExamValidationWorkflow model — audit trail of exam validation steps."""

from datetime import datetime

from gws_core import EnumField, Model
from peewee import DateTimeField, ForeignKeyField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.exam.exam import Exam
from gws_care.user.user import User
from gws_care.workflow.exam_validation_step import ExamValidationStep


class ExamValidationWorkflow(Model):
    """One row per completed validation step for an exam.

    Records who triggered each step and when, providing a complete
    audit trail of the exam lifecycle.

    Example query — full audit trail for an exam:
        ExamValidationWorkflow
            .select()
            .where(ExamValidationWorkflow.exam == exam_id)
            .order_by(ExamValidationWorkflow.reached_at)
    """

    exam: Exam = ForeignKeyField(Exam, null=False, backref="validation_workflow", on_delete="CASCADE", column_name="exam_id")
    step: ExamValidationStep = EnumField(choices=ExamValidationStep, null=False)
    reached_by: User = ForeignKeyField(User, null=True, backref="+")
    reached_at: datetime = DateTimeField(null=False)

    class Meta:
        table_name = "gws_care_exam_validation_workflow"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
