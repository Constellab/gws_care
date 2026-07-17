"""DB migration v0.68.11 — Backfill MedicalDoctor.user from UserCareRole.linked_doctor_id.

The "Médecin lié" dropdown in Settings → Rôles only ever wrote to
UserCareRole.linked_doctor_id, but every permission/scoping check in the app
(doctor scope resolution, the assigned-exams queue, appointment forms, etc.)
reads MedicalDoctor.user instead — which that dropdown never set (see the
matching fix in user_role_service.py::set_doctor_link). Any admin who used
that dropdown before this fix shipped therefore has a doctor who looks
"linked" in the UI but was never actually able to act.

This backfills MedicalDoctor.user for every such existing link, so past
attempts start working without the admin having to redo them. Only touches
doctors with no user linked yet, and skips a link if the target user is
already linked to a different doctor (MedicalDoctor.user is unique) rather
than risk creating an incorrect link — a no-op on any install where no such
links exist.
"""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration


@brick_migration(
    "0.68.11",
    short_description="Backfill MedicalDoctor.user from UserCareRole.linked_doctor_id",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration750(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        from gws_care.doctor.medical_doctor import MedicalDoctor
        from gws_care.role.care_role import CareRole
        from gws_care.role.user_care_role import UserCareRole

        links = list(
            UserCareRole.select().where(
                UserCareRole.role == CareRole.DOCTOR,
                UserCareRole.linked_doctor_id.is_null(False),
            )
        )
        for link in links:
            doctor = MedicalDoctor.get_or_none(MedicalDoctor.id == link.linked_doctor_id)
            if doctor is None or doctor.user_id is not None:
                continue  # already linked, or points at a since-deleted doctor
            if MedicalDoctor.get_or_none(MedicalDoctor.user == link.user_id):
                continue  # this user is already linked to a different doctor — don't overwrite
            doctor.user = link.user_id
            doctor.save()
