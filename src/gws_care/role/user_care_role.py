"""UserCareRole model — join table linking a local User to a CareRole."""

from gws_core import EnumField, Model
from peewee import CharField, ForeignKeyField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.role.care_role import CareRole
from gws_care.user.user import User


class DoctorSpecialty(str):
    """Free-text specialty constants for doctors (not an Enum so new values can be added freely)."""
    GENERALISTE = "Généraliste"
    CARDIOLOGUE = "Cardiologue"
    PNEUMOLOGUE = "Pneumologue"
    OPHTALMOLOGUE = "Ophtalmologue"
    ORL = "ORL"
    RADIOLOGUE = "Radiologue"
    REHUMATOLOGUE = "Rhumatologue"
    NEUROLOGUE = "Neurologue"
    DERMATOLOGUE = "Dermatologue"
    GYNECOLOGUE = "Gynécologue"
    PEDIATRE = "Pédiatre"
    ENDOCRINOLOGUE = "Endocrinologue"
    NEPHROLOGUE = "Néphrologue"
    GASTROENTEROLOGUE = "Gastro-entérologue"
    INFECTIOLOGUE = "Infectiologue"
    MEDECIN_TRAVAIL = "Médecin du travail"
    OTHER = "Autre"

    @classmethod
    def choices(cls) -> list[str]:
        return [
            cls.GENERALISTE, cls.CARDIOLOGUE, cls.PNEUMOLOGUE, cls.OPHTALMOLOGUE,
            cls.ORL, cls.RADIOLOGUE, cls.REHUMATOLOGUE, cls.NEUROLOGUE,
            cls.DERMATOLOGUE, cls.GYNECOLOGUE, cls.PEDIATRE, cls.ENDOCRINOLOGUE,
            cls.NEPHROLOGUE, cls.GASTROENTEROLOGUE, cls.INFECTIOLOGUE,
            cls.MEDECIN_TRAVAIL, cls.OTHER,
        ]


class UserCareRole(Model):
    """Associates a CareRole with a local User.

    One row per (user, role) pair — a user may hold multiple roles.
    For ACCOUNT_ADMIN and PATIENT roles the optional ID columns link the user
    to their associated account or patient record.
    For MEDECIN_PSC / MEDECIN_ENTREPRISE the specialty column stores the
    doctor's specialty (free-text, see DoctorSpecialty constants).
    """

    user: User = ForeignKeyField(User, null=False, backref="care_roles", on_delete="CASCADE")
    role: CareRole = EnumField(choices=CareRole, null=False)
    # Optional links — only populated for ACCOUNT_ADMIN / PATIENT roles
    linked_account_id: str = CharField(max_length=36, null=True)
    linked_patient_id: str = CharField(max_length=36, null=True)
    # Doctor specialty — only populated for MEDECIN_PSC / MEDECIN_ENTREPRISE roles
    specialty: str = CharField(max_length=100, null=True, default=None)

    class Meta:
        table_name = "gws_care_user_role"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = (
            (("user", "role"), True),   # unique constraint: one role per user
        )
