"""State for the doctor schedule management page."""

import reflex as rx
from pydantic import BaseModel
from gws_reflex_main import ReflexMainState


_DAY_LABELS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
_MONTH_LABELS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


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
    id: str = ""          # MedicalDoctor.id (used by DoctorSchedule FK)
    name: str = ""
    specialty: str = ""


class UnavailableDayDTO(BaseModel):
    id: str = ""
    doctor_id: str = ""
    doctor_name: str = ""
    date: str = ""
    date_end: str = ""
    half_day: str = "FULL"
    reason: str = ""


class CalendarDayDTO(BaseModel):
    date_str: str = ""
    day_num: int = 0
    is_today: bool = False
    is_padding: bool = True
    full_blocked: bool = False
    am_blocked: bool = False
    pm_blocked: bool = False
    blocked_reason: str = ""


class DoctorScheduleState(ReflexMainState):
    blocks: list[ScheduleBlockDTO] = []
    doctors: list[DoctorOptionDTO] = []
    is_loading: bool = False
    error_message: str = ""
    selected_doctor_id: str = "ALL"   # MedicalDoctor.id or "ALL"

    # ── Search / filter ───────────────────────────────────────────────────────
    search_name: str = ""
    filter_specialty: str = ""

    # ── Create block form ─────────────────────────────────────────────────────
    create_dialog_open: bool = False
    form_doctor_id: str = ""
    form_days: list[int] = []
    form_start: str = "09:00"
    form_end: str = "12:00"
    form_slot: int = 30
    form_room: str = ""

    # ── Unavailable days ──────────────────────────────────────────────────────
    unavailable_days: list[UnavailableDayDTO] = []
    unavail_form_open: bool = False
    unavail_form_doctor_id: str = ""
    unavail_form_date: str = ""
    unavail_form_date_end: str = ""
    unavail_form_half_day: str = "FULL"
    unavail_form_reason: str = ""
    unavail_error: str = ""

    # ── Calendar view ─────────────────────────────────────────────────────────
    cal_year: int = 2026
    cal_month: int = 6

    # ── Computed vars ─────────────────────────────────────────────────────────

    @rx.var
    def available_specialties(self) -> list[str]:
        return sorted({d.specialty for d in self.doctors if d.specialty})

    @rx.var
    def filtered_doctors(self) -> list[DoctorOptionDTO]:
        result = self.doctors
        if self.filter_specialty:
            result = [d for d in result if d.specialty == self.filter_specialty]
        if self.search_name:
            q = self.search_name.strip().lower()
            result = [d for d in result if q in d.name.lower()]
        return result

    @rx.var
    def selected_doctor_name(self) -> str:
        for d in self.doctors:
            if d.id == self.selected_doctor_id:
                return d.name
        return "Tous les médecins"

    @rx.var
    def selected_doctor_specialty(self) -> str:
        for d in self.doctors:
            if d.id == self.selected_doctor_id:
                return d.specialty
        return ""

    @rx.var
    def schedulable_doctors(self) -> list[DoctorOptionDTO]:
        """All active doctors — used for select dropdowns in create/unavailability dialogs."""
        return self.doctors

    @rx.var
    def cal_month_label(self) -> str:
        return f"{_MONTH_LABELS[self.cal_month - 1]} {self.cal_year}"

    @rx.var
    def calendar_cells(self) -> list[CalendarDayDTO]:
        from calendar import monthrange
        from datetime import date, timedelta

        today = date.today()
        first_day = date(self.cal_year, self.cal_month, 1)
        num_days = monthrange(self.cal_year, self.cal_month)[1]
        start_weekday = first_day.weekday()

        blocked: dict[str, dict] = {}
        for u in self.unavailable_days:
            if self.selected_doctor_id != "ALL" and u.doctor_id != self.selected_doctor_id:
                continue
            try:
                d = date.fromisoformat(u.date)
                end_d = date.fromisoformat(u.date_end) if u.date_end else d
            except ValueError:
                continue
            hd = u.half_day or "FULL"
            cur = d
            while cur <= end_d:
                ds = cur.strftime("%Y-%m-%d")
                entry = blocked.setdefault(ds, {"full": False, "am": False, "pm": False, "reasons": []})
                if hd == "FULL":
                    entry["full"] = True
                elif hd == "AM":
                    entry["am"] = True
                elif hd == "PM":
                    entry["pm"] = True
                if u.reason:
                    entry["reasons"].append(u.reason)
                cur += timedelta(days=1)

        cells: list[CalendarDayDTO] = []
        for _ in range(start_weekday):
            cells.append(CalendarDayDTO(is_padding=True))
        for day_n in range(1, num_days + 1):
            d = date(self.cal_year, self.cal_month, day_n)
            ds = d.strftime("%Y-%m-%d")
            entry = blocked.get(ds, {})
            full = entry.get("full", False)
            am = entry.get("am", False)
            pm = entry.get("pm", False)
            reasons = entry.get("reasons", [])
            cells.append(CalendarDayDTO(
                date_str=ds,
                day_num=day_n,
                is_today=(d == today),
                is_padding=False,
                full_blocked=full,
                am_blocked=am and not full,
                pm_blocked=pm and not full,
                blocked_reason=", ".join(reasons) if reasons else "",
            ))
        while len(cells) % 7 != 0:
            cells.append(CalendarDayDTO(is_padding=True))
        return cells

    @rx.var
    def filtered_blocks(self) -> list[ScheduleBlockDTO]:
        if self.selected_doctor_id == "ALL":
            return self.blocks
        return [b for b in self.blocks if b.doctor_id == self.selected_doctor_id]

    @rx.var
    def filtered_unavail_days(self) -> list[UnavailableDayDTO]:
        if self.selected_doctor_id == "ALL":
            return self.unavailable_days
        return [d for d in self.unavailable_days if d.doctor_id == self.selected_doctor_id]

    # ── Filter events ─────────────────────────────────────────────────────────

    @rx.event
    def set_search_name(self, value: str):
        self.search_name = value

    @rx.event
    def set_filter_specialty(self, value: str):
        self.filter_specialty = "" if value == "_all_" else value

    @rx.event
    def select_doctor(self, doctor_id: str):
        """Select a doctor card to filter the schedule."""
        self.selected_doctor_id = doctor_id

    @rx.event
    def clear_doctor_selection(self):
        self.selected_doctor_id = "ALL"

    # ── Calendar navigation ───────────────────────────────────────────────────

    @rx.event
    def prev_month(self):
        if self.cal_month == 1:
            self.cal_month = 12
            self.cal_year -= 1
        else:
            self.cal_month -= 1

    @rx.event
    def next_month(self):
        if self.cal_month == 12:
            self.cal_month = 1
            self.cal_year += 1
        else:
            self.cal_month += 1

    # ── Create block dialog ───────────────────────────────────────────────────

    @rx.event
    def open_create_dialog(self):
        self.create_dialog_open = True
        # Pre-select the current doctor if one is selected
        self.form_doctor_id = "" if self.selected_doctor_id == "ALL" else self.selected_doctor_id
        self.form_days = []
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
    def toggle_form_day(self, day: int):
        if day in self.form_days:
            self.form_days = [d for d in self.form_days if d != day]
        else:
            self.form_days = sorted(self.form_days + [day])

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
            if not self.form_days:
                self.error_message = "Veuillez sélectionner au moins un jour."
                return
            with await self.authenticate_user():
                from gws_care.scheduling.doctor_schedule import DoctorSchedule
                for day in self.form_days:
                    DoctorSchedule.create(
                        doctor_id=self.form_doctor_id,
                        day_of_week=day,
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

    # ── Unavailable days ──────────────────────────────────────────────────────

    @rx.event
    def open_unavail_form(self):
        self.unavail_form_open = True
        self.unavail_form_doctor_id = "" if self.selected_doctor_id == "ALL" else self.selected_doctor_id
        self.unavail_form_date = ""
        self.unavail_form_date_end = ""
        self.unavail_form_half_day = "FULL"
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
        if not self.unavail_form_date_end:
            self.unavail_form_date_end = v

    @rx.event
    def set_unavail_date_end(self, v: str):
        self.unavail_form_date_end = v

    @rx.event
    def set_unavail_half_day(self, v: str):
        self.unavail_form_half_day = v

    @rx.event
    def set_unavail_reason(self, v: str):
        self.unavail_form_reason = v

    @rx.event
    async def save_unavail_day(self):
        if not self.unavail_form_doctor_id:
            self.unavail_error = "Sélectionnez un médecin."
            return
        if not self.unavail_form_date:
            self.unavail_error = "Sélectionnez une date de début."
            return
        date_end = self.unavail_form_date_end or self.unavail_form_date
        if date_end < self.unavail_form_date:
            self.unavail_error = "La date de fin doit être >= à la date de début."
            return
        try:
            with await self.authenticate_user():
                from gws_care.scheduling.doctor_schedule import DoctorScheduleService
                DoctorScheduleService.mark_unavailable(
                    self.unavail_form_doctor_id,
                    self.unavail_form_date,
                    date_end if date_end != self.unavail_form_date else None,
                    self.unavail_form_reason or None,
                    self.unavail_form_half_day,
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

    # ── Data loader ───────────────────────────────────────────────────────────

    @rx.event
    async def on_load(self):
        self.is_loading = True
        self.error_message = ""
        from datetime import date
        today = date.today()
        self.cal_year = today.year
        self.cal_month = today.month
        try:
            with await self.authenticate_user():
                from gws_care.doctor.medical_doctor import MedicalDoctor

                # Load doctors from MedicalDoctor (active + not archived)
                medical_doctors = list(
                    MedicalDoctor.select()
                    .where(
                        (MedicalDoctor.is_active == True)
                        & (MedicalDoctor.is_archived == False)
                    )
                    .order_by(MedicalDoctor.last_name, MedicalDoctor.first_name)
                )

                doctor_opts: list[DoctorOptionDTO] = []
                doc_name_map: dict[str, str] = {}  # MedicalDoctor.id -> display name

                for md in medical_doctors:
                    mid = str(md.id)
                    name = md.get_full_name()
                    doctor_opts.append(DoctorOptionDTO(
                        id=mid,
                        name=name,
                        specialty=md.specialization or "",
                    ))
                    doc_name_map[mid] = name

                self.doctors = doctor_opts

                from gws_care.scheduling.doctor_schedule import DoctorSchedule
                all_blocks = list(
                    DoctorSchedule.select()
                    .order_by(DoctorSchedule.day_of_week, DoctorSchedule.start_time)
                    .limit(2000)
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

                from gws_care.scheduling.doctor_schedule import DoctorUnavailableDay
                all_unavail = list(
                    DoctorUnavailableDay.select()
                    .order_by(DoctorUnavailableDay.date)
                    .limit(2000)
                )
                self.unavailable_days = [
                    UnavailableDayDTO(
                        id=str(u.id),
                        doctor_id=str(u.doctor_id),
                        doctor_name=doc_name_map.get(str(u.doctor_id), "—"),
                        date=u.date,
                        date_end=u.date_end or "",
                        half_day=u.half_day or "FULL",
                        reason=u.reason or "",
                    )
                    for u in all_unavail
                ]
        except Exception as exc:
            self.error_message = str(exc)
            print(f"[schedule] Erreur chargement: {exc}")
        finally:
            self.is_loading = False
