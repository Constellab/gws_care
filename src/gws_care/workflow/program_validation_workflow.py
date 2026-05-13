"""ProgramValidationWorkflow model — audit trail of program validation steps."""

from datetime import datetime

from gws_core import EnumField, Model
from peewee import CompositeKey, DateTimeField, ForeignKeyField, TextField

from gws_care.medical_program.medical_program import MedicalProgram
from gws_care.core.care_db_manager import CareDbManager
from gws_care.user.user import User
from gws_care.workflow.program_validation_step import ProgramValidationStep


class ProgramValidationWorkflow(Model):
    """One row per completed validation step for a program.

    Uniqueness is enforced on (program, step): each step can only be
    recorded once per program, reflecting the sequential, non-reversible
    nature of the validation chain.

    Example query — full audit trail for a program:
        ProgramValidationWorkflow
            .select()
            .where(ProgramValidationWorkflow.program == program_id)
            .order_by(ProgramValidationWorkflow.validated_at)
    """

    program: MedicalProgram = ForeignKeyField(MedicalProgram, null=False, backref="validation_workflow", on_delete="CASCADE")
    step: ProgramValidationStep = EnumField(choices=ProgramValidationStep, null=False)
    validated_by: User = ForeignKeyField(User, null=True, backref="+")
    validated_at: datetime = DateTimeField(null=False)
    notes: str = TextField(null=True)

    class Meta:
        table_name = "gws_care_program_validation_workflow"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        primary_key = CompositeKey("program", "step")
