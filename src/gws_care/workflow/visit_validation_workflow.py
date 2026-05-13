"""VisitValidationWorkflow model — audit trail of visit validation steps."""

from datetime import datetime

from gws_core import EnumField, Model
from peewee import CompositeKey, DateTimeField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.user.user import User
from gws_care.visit.visit import Visit
from gws_care.workflow.visit_validation_step import VisitValidationStep


class VisitValidationWorkflow(Model):
    """One row per completed validation step for a visit.

    Uniqueness is enforced on (visit, step): each step can only be
    recorded once per visit, reflecting the sequential, non-reversible
    nature of the validation chain.

    Example query — full audit trail for a visit:
        VisitValidationWorkflow
            .select()
            .where(VisitValidationWorkflow.visit == visit_id)
            .order_by(VisitValidationWorkflow.validated_at)
    """

    visit: Visit = ForeignKeyField(Visit, null=False, backref="validation_workflow", on_delete="CASCADE")
    step: VisitValidationStep = EnumField(choices=VisitValidationStep, null=False)
    validated_by: User = ForeignKeyField(User, null=True, backref="+")
    validated_at: datetime = DateTimeField(null=False)
    notes: str = TextField(null=True)

    class Meta:
        table_name = "gws_care_visit_validation_workflow"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        primary_key = CompositeKey("visit", "step")
