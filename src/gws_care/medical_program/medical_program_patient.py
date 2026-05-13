"""Junction table: MedicalProgram ↔ Patient (many-to-many)."""

from gws_care.medical_program.medical_program import MedicalProgram
from gws_care.core.care_db_manager import CareDbManager
from gws_care.patient.patient import Patient
from gws_core import Model
from peewee import ForeignKeyField


class ProgramPatient(Model):
    """Associates a Patient with a MedicalProgram.

    All patients in a program must belong to the program's billing account.
    """

    program: MedicalProgram = ForeignKeyField(MedicalProgram, null=False, backref="program_patients", on_delete="CASCADE")
    patient: Patient = ForeignKeyField(Patient, null=False, backref="program_patients", on_delete="CASCADE")

    class Meta:
        table_name = "gws_care_program_patient"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = (
            (("program", "patient"), True),  # unique: one row per (program, patient)
        )
