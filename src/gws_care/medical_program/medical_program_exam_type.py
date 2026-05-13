"""Junction table: MedicalProgram ↔ ExamTypeModel (many-to-many)."""

from gws_care.medical_program.medical_program import MedicalProgram
from gws_care.core.care_db_manager import CareDbManager
from gws_care.exam.exam_type_model import ExamTypeModel
from gws_core import Model
from peewee import ForeignKeyField


class ProgramExamType(Model):
    """Associates an ExamTypeModel with a MedicalProgram.

    Defines which exam types are to be performed during the program.
    """

    program: MedicalProgram = ForeignKeyField(MedicalProgram, null=False, backref="program_exam_types", on_delete="CASCADE")
    exam_type: ExamTypeModel = ForeignKeyField(ExamTypeModel, null=False, backref="program_exam_types", on_delete="CASCADE")

    class Meta:
        table_name = "gws_care_program_exam_type"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = (
            (("program", "exam_type"), True),  # unique per pair
        )
