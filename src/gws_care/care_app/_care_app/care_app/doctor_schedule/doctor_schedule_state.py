"""State for the doctor schedule management page."""

import reflex as rx
from pydantic import BaseModel
from gws_reflex_main import ReflexMainState


_DAY_LABELS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


class ScheduleBlockDTO(BaseModel):
    id: str = ""
    doctor_id: str = ""
    doctor_name: str = ""
    day_of_week: int = 0
    day_label: str = ""
    start_time: str = ""
    end_time: str = ""
    slot_duration_minutes: int = 30
    room: str = ""
    is_active: bool = True


class DoctorOptionDTO(BaseModel):
    id: str = ""
    name: str = ""
    specialty: str = ""


class UnavailableDayDTO(BaseModel):
    id: str = ""
    doctor_id: str = ""
    doctor_name: str = ""
    date: str = ""
    reason: str = ""


class DoctorScheduleState(ReflexMainState):
    blocks: list[ScheduleBlockDTO] = []
    doctors: list[DoctorOptionDTO] = []
    is_loading: bool = False
    error_message: str = ""
    selected_doctor_id: str = "ALL"
    # Create block form
    create_dialog_open: bool = False
    form_doctor_id: str = ""
    form_day: int = 0
    form_start: str = "09:00"
    form_end: str = "12:00"
    form_slot: int = 30
    form_room: str = ""
    # Unavailable days
    unavailable_days: list[UnavailableDayDTO] = []
    unavail_form_open: bool = False
    unavail_form_doctor_id: str = ""
    unavail_form_date: str = ""
    unavail_form_reason: str = ""
    unavail_error: str = ""

    @rx.var
    def filtered_blocks(self) -> list[ScheduleBlockDTO]:
        if self.selected_doctor_id == "ALL":
            return self.blocks
        return [b for b in self.blocks if b.doctor_id == self.selected_doctor_id]

    @rx.event
    def set_doctor_filter(self, value: str):
        self.selected_doctor_id = value

    @rx.event
    def open_create_dialog(self):
        self.create_dialog_open = True
        self.form_doctor_id = ""
        self.form_day = 0
        self.form_start = "09:00"
        self.form_end = "12:00"
        self.form_slot = 20
        self.form_room = ""
        self.error_message = ""

    @rx.event
    def close_create_dialog(self):
        self.create_dialog_open = False

    @rx.event
    def set_form_doctor(self, v: str):
        self.form_doctor_id = v

    @rx.event
    def set_form_day(self, v: str):
        try:
            self.form_day = int(v)
        except ValueError:
            pass

    @rx.event
    def set_form_start(self, v: str):
        self.form_start = v

    @rx.event
    def set_form_end(self, v: str):
        self.form_end = v

    @rx.event
    def set_form_slot(self, v: str):
        try:
            self.form_slot = int(v)
        except ValueError:
            pass

    @rx.event
    def set_form_room(self, v: str):
        self.form_room = v

    @rx.event
    async def save_block(self):
        try:
            if not self.form_doctor_id:
                self.error_message = "Veuillez sélectionner un médecin."
                return
            with await self.authenticate_user():
                from gws_care.scheduling.doctor_schedule import DoctorSchedule
                DoctorSchedule.create(
                    doctor_id=self.form_doctor_id,
                    day_of_week=self.form_day,
                    start_time=self.form_start,
                    end_time=self.form_end,
                    slot_duration_minutes=self.form_slot,
                    room=self.form_room or None,
                    is_active=True,
                )
            self.create_dialog_open = False
            await self.on_load()  # type: ignore[misc]
        except Exception as exc:
            self.error_message = str(exc)
            print(f"[schedule] Erreur création: {exc}")

    @rx.event
    async def toggle_block_active(self, block_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.scheduling.doctor_schedule import DoctorSchedule
                block = DoctorSchedule.get_by_id(block_id)
                block.is_active = not block.is_active
                block.save()
            await self.on_load()  # type: ignore[misc]
        except Exception as exc:
            self.error_message = str(exc)

    @rx.event
    async def delete_block(self, block_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.scheduling.doctor_schedule import DoctorSchedule
                DoctorSchedule.get_by_id(block_id).delete_instance()
            await self.on_load()  # type: ignore[misc]
        except Exception as exc:
            self.error_message = str(exc)

    @rx.event
    async def on_load(self):
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.scheduling.doctor_schedule import DoctorSchedule
                from gws_care.role.user_care_role import UserCareRole
                from gws_care.role.care_role import CareRole
                from gws_care.user.user import User

                # Load all doctors (MEDECIN_PSC + MEDECIN_ENTREPRISE)
                doctor_role_rows = list(
                    UserCareRole.select(UserCareRole, User)
                    .join(User)
                    .where(UserCareRole.role.in_([CareRole.MEDECIN_PSC.value, CareRole.MEDECIN_ENTREPRISE.value]))
                    .order_by(User.last_name)
                )
                seen_ids: set[str] = set()
                doctor_opts: list[DoctorOptionDTO] = []
                for row in doctor_role_rows:
                    uid = str(row.user.id)
                    if uid not in seen_ids:
                        seen_ids.add(uid)
                        u = row.user
                        sp = getattr(row, "specialty", None) or ""
                        doctor_opts.append(DoctorOptionDTO(
                            id=uid,
                            name=f"{u.first_name} {u.last_name}".strip() or u.email,
                            specialty=sp,
                        ))
                self.doctors = doctor_opts

                # Build doctor name map
                doc_name_map = {d.id: d.name for d in self.doctors}

                # Load all schedule blocks
                all_blocks = list(
                    DoctorSchedule.select()
                    .order_by(DoctorSchedule.day_of_week, DoctorSchedule.start_time)
                    .limit(1000)
                )
                self.blocks = [
                    ScheduleBlockDTO(
                        id=str(b.id),
                        doctor_id=str(b.doctor_id),
                        doctor_name=doc_name_map.get(str(b.doctor_id), "—"),
                        day_of_week=b.day_of_week,
                        day_label=_DAY_LABELS[b.day_of_week] if 0 <= b.day_of_week <= 6 else str(b.day_of_week),
                        start_time=b.start_time,
                        end_time=b.end_time,
                        slot_duration_minutes=b.slot_duration_minutes,
                        room=b.room or "",
                        is_active=bool(b.is_active),
                    )
                    for b in all_blocks
                ]

                # Load unavailable days
                from gws_care.scheduling.doctor_schedule import DoctorUnavailableDay
                all_unavail = list(
                    DoctorUnavailableDay.select()
                    .order_by(DoctorUnavailableDay.date)
                    .limit(1000)
                )
                self.unavailable_days = [
                    UnavailableDayDTO(
                        id=str(u.id),
                        doctor_id=str(u.doctor_id),
                        doctor_name=doc_name_map.get(str(u.doctor_id), "—"),
                        date=u.date,
                        reason=u.reason or "",
                    )
                    for u in all_unavail
                ]
        except Exception as exc:
            self.error_message = str(exc)
            print(f"[schedule] Erreur chargement: {exc}")
        finally:
            self.is_loading = False

    # ── Unavailable days ──────────────────────────────────────────────────────

    @rx.event
    def open_unavail_form(self):
        self.unavail_form_open = True
        self.unavail_form_doctor_id = self.form_doctor_id or (self.doctors[0].id if self.doctors else "")
        self.unavail_form_date = ""
        self.unavail_form_reason = ""
        self.unavail_error = ""

    @rx.event
    def close_unavail_form(self):
        self.unavail_form_open = False

    @rx.event
    def set_unavail_doctor(self, v: str):
        self.unavail_form_doctor_id = v

    @rx.event
    def set_unavail_date(self, v: str):
        self.unavail_form_date = v

    @rx.event
    def set_unavail_reason(self, v: str):
        self.unavail_form_reason = v

    @rx.event
    async def save_unavail_day(self):
        if not self.unavail_form_doctor_id:
            self.unavail_error = "Sélectionnez un médecin."
            return
        if not self.unavail_form_date:
            self.unavail_error = "Sélectionnez une date."
            return
        try:
            with await self.authenticate_user():
                from gws_care.scheduling.doctor_schedule import DoctorScheduleService
                DoctorScheduleService.mark_unavailable(
                    self.unavail_form_doctor_id,
                    self.unavail_form_date,
                    self.unavail_form_reason or None,
                )
            self.unavail_form_open = False
            await self.on_load()  # type: ignore[misc]
        except Exception as exc:
            self.unavail_error = str(exc)

    @rx.event
    async def delete_unavail_day(self, day_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.scheduling.doctor_schedule import DoctorScheduleService
                DoctorScheduleService.unmark_unavailable(day_id)
            await self.on_load()  # type: ignore[misc]
        except Exception as exc:
            self.error_message = str(exc)

    @rx.var
    def filtered_unavail_days(self) -> list[UnavailableDayDTO]:
        if self.selected_doctor_id == "ALL":
            return self.unavailable_days
        return [d for d in self.unavailable_days if d.doctor_id == self.selected_doctor_id]

    @rx.event
    async def set_doctor_specialty(self, doctor_id: str, specialty: str):
        """Update the specialty for a doctor's UserCareRole row."""
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_care_role import UserCareRole
                # Find any doctor role for this user and update specialty
                role_row = UserCareRole.get_or_none(
                    (UserCareRole.user == doctor_id)
                    & (UserCareRole.role.in_([CareRole.MEDECIN_PSC.value, CareRole.MEDECIN_ENTREPRISE.value]))
                )
                if role_row:
                    role_row.specialty = None if specialty == "__none__" else (specialty or None)
                    role_row.save()
                    # Update local state immediately
                    self.doctors = [
                        DoctorOptionDTO(
                            id=d.id,
                            name=d.name,
                            specialty=specialty if d.id == doctor_id else d.specialty,
                        )
                        for d in self.doctors
                    ]
        except Exception as exc:
            self.error_message = str(exc)
