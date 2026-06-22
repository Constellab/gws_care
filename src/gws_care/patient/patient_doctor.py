"""PatientDoctor — many-to-many between Patient and MedicalDoctor.

One row per (patient, doctor) pair. The is_referent flag marks the
médecin traitant; at most one row per patient may have is_referent=True.
"""

from peewee import BooleanField, ForeignKeyField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.doctor.medical_doctor import MedicalDoctor
from gws_care.patient.patient import Patient


class PatientDoctor(ModelWithUser):
    patient: Patient = ForeignKeyField(Patient, null=False, backref="patient_doctors", on_delete="CASCADE")
    doctor: MedicalDoctor = ForeignKeyField(MedicalDoctor, null=False, backref="patient_doctors", on_delete="CASCADE")
    is_referent: bool = BooleanField(default=False, null=False)

    class Meta:
        table_name = "gws_care_patient_doctor"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = ((("patient_id", "doctor_id"), True),)
