"""State for the messaging page — doctor ↔ patient direct messaging."""

from pydantic import BaseModel
import reflex as rx
from gws_reflex_main import ReflexMainState


class ThreadRowDTO(BaseModel):
    patient_id: str = ""
    patient_name: str = ""
    patient_number: str = ""
    last_message: str = ""
    last_message_at: str = ""
    unread_count: int = 0


class MessageDTO(BaseModel):
    id: str = ""
    sender_role: str = ""   # "doctor" | "patient"
    sender_name: str = ""
    content: str = ""
    sent_at: str = ""
    is_read_by_recipient: bool = False


class MessagingState(ReflexMainState):
    """Messaging hub state — thread list for doctors, conversation for patient portal."""

    threads: list[ThreadRowDTO] = []
    active_patient_id: str = ""
    active_patient_name: str = ""
    messages: list[MessageDTO] = []
    compose_text: str = ""
    is_loading: bool = False
    error: str = ""
    # current user's role in this context ("doctor" | "patient")
    my_role: str = "doctor"
    my_user_id: str = ""
    # Auto-refresh: tracks message count to detect new messages without full reload
    _last_message_count: int = 0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @rx.event
    async def on_load(self):
        """Load thread list for doctor or conversation for patient."""
        self.is_loading = True
        self.error = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.role.user_role_service import UserRoleService
                self.my_user_id = str(auth_user.id)
                roles = [r.value for r in UserRoleService.get_roles_for_user(str(auth_user.id))]

                if "PATIENT" in roles:
                    self.my_role = "patient"
                    # Load the patient record linked to this user
                    linked_patient_id = UserRoleService.get_linked_patient_id(str(auth_user.id)) or ""
                    if linked_patient_id:
                        self.active_patient_id = linked_patient_id
                        from gws_care.patient.patient import Patient
                        p = Patient.get_by_id(linked_patient_id)
                        self.active_patient_name = p.get_full_name()
                        await self._load_conversation(linked_patient_id)
                else:
                    self.my_role = "doctor"
                    await self._load_threads()
        except Exception as exc:
            self.error = str(exc)
        finally:
            self.is_loading = False

    @rx.event
    async def refresh(self):
        """Manual refresh — reload threads or current conversation."""
        if not await self.check_authentication():
            return
        try:
            if self.active_patient_id:
                await self._load_conversation(self.active_patient_id)
            else:
                await self._load_threads()
        except Exception as exc:
            self.error = str(exc)

    @rx.event
    async def open_thread(self, patient_id: str):
        """Doctor opens a conversation with a patient."""
        self.active_patient_id = patient_id
        self.error = ""
        # Find name from threads list
        for t in self.threads:
            if t.patient_id == patient_id:
                self.active_patient_name = t.patient_name
                break
        await self._load_conversation(patient_id)
        # Mark messages as read
        try:
            with await self.authenticate_user():
                from gws_care.messaging.patient_message import PatientMessageService
                PatientMessageService.mark_read_by_recipient(patient_id, "doctor")
                # Refresh unread counts
                for t in self.threads:
                    if t.patient_id == patient_id:
                        t.unread_count = 0
        except Exception as exc:
            pass

    @rx.event
    async def send_message(self):
        """Send a message in the active conversation."""
        if not self.compose_text.strip():
            return
        if not self.active_patient_id:
            return
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.messaging.patient_message import PatientMessageService
                PatientMessageService.send(
                    patient_id=self.active_patient_id,
                    sender_user_id=str(auth_user.id),
                    sender_role=self.my_role,
                    content=self.compose_text,
                )
                self.compose_text = ""
                await self._load_conversation(self.active_patient_id)
                if self.my_role == "doctor":
                    await self._load_threads()
        except Exception as exc:
            self.error = str(exc)

    @rx.event
    def set_compose_text(self, value: str):
        self.compose_text = value

    @rx.event
    def back_to_threads(self):
        self.active_patient_id = ""
        self.active_patient_name = ""
        self.messages = []

    # ── Internals ─────────────────────────────────────────────────────────────

    async def _load_threads(self):
        from gws_care.messaging.patient_message import PatientMessageService
        threads_data = PatientMessageService.list_threads_for_doctor(limit=50)
        self.threads = [
            ThreadRowDTO(
                patient_id=t["patient_id"],
                patient_name=t["patient_name"],
                patient_number=t["patient_number"],
                last_message=t["last_message"],
                last_message_at=t["last_message_at"],
                unread_count=t["unread_count"],
            )
            for t in threads_data
        ]

    async def _load_conversation(self, patient_id: str):
        from gws_care.messaging.patient_message import PatientMessageService
        from gws_care.user.user import User as UserModel
        msgs = PatientMessageService.list_for_patient(patient_id, limit=100)
        # Pre-fetch all senders in one query to avoid N+1
        sender_ids = list({str(m.sender_user_id) for m in msgs if m.sender_user_id})
        users_by_id: dict[str, UserModel] = {}
        if sender_ids:
            for u in UserModel.select().where(UserModel.id.in_(sender_ids)):
                users_by_id[str(u.id)] = u
        result = []
        for m in msgs:
            u = users_by_id.get(str(m.sender_user_id)) if m.sender_user_id else None
            if u is not None:
                sender_name = getattr(u, "get_full_name", lambda: "")() or getattr(u, "email", "?")
            else:
                sender_name = "Utilisateur"
            result.append(MessageDTO(
                id=str(m.id),
                sender_role=m.sender_role,
                sender_name=sender_name,
                content=m.content,
                sent_at=m.sent_at.strftime("%d/%m/%Y %H:%M"),
                is_read_by_recipient=m.is_read_by_recipient,
            ))
        self.messages = result
