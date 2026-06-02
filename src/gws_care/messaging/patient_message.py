"""Message model — direct messaging between doctor and patient.

Each thread is identified by (patient_id, doctor_user_id).
Messages are simple text, with a read flag per recipient side.
"""

from datetime import datetime

from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.patient.patient import Patient
from gws_care.user.user import User
from gws_core import Model


class PatientMessage(Model):
    """One message in a doctor-patient thread."""

    patient: Patient = ForeignKeyField(
        Patient, null=False, backref="messages", on_delete="CASCADE", index=True
    )
    # The user who wrote the message (could be a doctor or a patient-linked user)
    sender_user: User = ForeignKeyField(
        User, null=False, backref="+", on_delete="CASCADE"
    )
    # "doctor" | "patient"
    sender_role: str = CharField(max_length=20, null=False, default="doctor")
    content: str = TextField(null=False)
    sent_at: datetime = DateTimeField(null=False, default=datetime.now, index=True)
    # Has the other party read this message?
    is_read_by_recipient: bool = BooleanField(default=False, null=False)

    class Meta:
        table_name = "gws_care_patient_message"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class PatientMessageService:
    """CRUD for doctor-patient messages."""

    @classmethod
    def send(
        cls,
        patient_id: str,
        sender_user_id: str,
        sender_role: str,   # "doctor" | "patient"
        content: str,
    ) -> PatientMessage:
        if not content.strip():
            raise ValueError("Le message ne peut pas être vide.")
        if len(content) > 5000:
            raise ValueError("Le message est trop long (maximum 5 000 caractères).")
        msg = PatientMessage()
        msg.patient_id = patient_id
        msg.sender_user_id = sender_user_id
        msg.sender_role = sender_role
        msg.content = content.strip()
        msg.sent_at = datetime.now()
        msg.is_read_by_recipient = False
        msg.save()
        return msg

    @classmethod
    def list_for_patient(cls, patient_id: str, limit: int = 100) -> list[PatientMessage]:
        return list(
            PatientMessage.select()
            .where(PatientMessage.patient == patient_id)
            .order_by(PatientMessage.sent_at.asc())
            .limit(limit)
        )

    @classmethod
    def mark_read_by_recipient(cls, patient_id: str, recipient_role: str) -> None:
        """Mark all unread messages sent to *recipient_role* in this thread as read."""
        # If recipient is "patient", mark all doctor messages as read, and vice versa
        sender_role = "doctor" if recipient_role == "patient" else "patient"
        (
            PatientMessage.update(is_read_by_recipient=True)
            .where(
                (PatientMessage.patient == patient_id)
                & (PatientMessage.sender_role == sender_role)
                & (PatientMessage.is_read_by_recipient == False)  # noqa: E712
            )
            .execute()
        )

    @classmethod
    def unread_count_for_doctor(cls, patient_id: str) -> int:
        """Count unread messages sent by the patient that the doctor hasn't read."""
        return (
            PatientMessage.select()
            .where(
                (PatientMessage.patient == patient_id)
                & (PatientMessage.sender_role == "patient")
                & (PatientMessage.is_read_by_recipient == False)  # noqa: E712
            )
            .count()
        )

    @classmethod
    def list_threads_for_doctor(cls, limit: int = 50) -> list[dict]:
        """Return one record per patient that has messages, with last message preview."""
        from peewee import fn
        from gws_care.patient.patient import Patient as PatientModel

        # Pre-compute unread counts per patient in ONE aggregate query (avoids N+1)
        unread_map: dict[str, int] = dict(
            PatientMessage.select(PatientMessage.patient, fn.COUNT(PatientMessage.id).alias("cnt"))
            .where(
                (PatientMessage.sender_role == "patient")
                & (PatientMessage.is_read_by_recipient == False)  # noqa: E712
            )
            .group_by(PatientMessage.patient)
            .tuples()
        )

        results = []
        seen: set[str] = set()
        msgs = (
            PatientMessage.select(PatientMessage, PatientModel)
            .join(PatientModel)
            .order_by(PatientMessage.sent_at.desc())
            .limit(500)
        )
        for m in msgs:
            pid = str(m.patient_id)
            if pid in seen:
                continue
            seen.add(pid)
            results.append({
                "patient_id": pid,
                "patient_name": m.patient.get_full_name(),
                "patient_number": m.patient.patient_number,
                "last_message": m.content[:80],
                "last_message_at": m.sent_at.strftime("%d/%m/%Y %H:%M"),
                "unread_count": unread_map.get(pid, 0),
            })
            if len(results) >= limit:
                break
        return results
