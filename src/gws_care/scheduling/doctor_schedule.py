"""DoctorSchedule + enhanced Appointment handling for private clinic agenda.

DoctorSchedule defines a doctor's weekly availability slots.
Appointment.assigned_doctor_id, duration_minutes and room are added via migration.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from peewee import BooleanField, CharField, ForeignKeyField, IntegerField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.user.user import User


class DayOfWeek(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    def get_label(self) -> str:
        return ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"][self.value]


class DoctorSchedule(ModelWithUser):
    """One availability block for a doctor on a recurring weekly basis.

    Example: Dr. Martin is available Monday 09:00–12:30 for 30-minute slots.
    The booking engine uses these blocks to compute free time slots.
    """

    doctor: User = ForeignKeyField(
        User, null=False, backref="schedule_blocks", on_delete="CASCADE", index=True
    )
    day_of_week: int = IntegerField(null=False)         # DayOfWeek enum value
    # Times stored as "HH:MM" strings for simplicity and timezone-independence
    start_time: str = CharField(max_length=5, null=False)   # e.g. "09:00"
    end_time: str = CharField(max_length=5, null=False)     # e.g. "12:30"
    slot_duration_minutes: int = IntegerField(null=False, default=20)
    # Optional room or cabinet identifier
    room: str = CharField(max_length=100, null=True)
    is_active: bool = BooleanField(default=True, null=False)

    def get_day_label(self) -> str:
        try:
            return DayOfWeek(self.day_of_week).get_label()
        except ValueError:
            return str(self.day_of_week)

    def get_slots(self, on_date: "datetime.date") -> list[datetime]:
        """Return all available start times for this block on a given date."""
        from datetime import date as date_type, time
        start_h, start_m = map(int, self.start_time.split(":"))
        end_h, end_m = map(int, self.end_time.split(":"))
        current = datetime(on_date.year, on_date.month, on_date.day, start_h, start_m)
        end = datetime(on_date.year, on_date.month, on_date.day, end_h, end_m)
        delta = timedelta(minutes=self.slot_duration_minutes)
        slots = []
        while current + delta <= end:
            slots.append(current)
            current += delta
        return slots

    class Meta:
        table_name = "gws_care_doctor_schedule"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class DoctorUnavailableDay(ModelWithUser):
    """Marks a date range as unavailable for a doctor (whole day or half day).

    Used to block holidays, sick leave or any ad-hoc absence so that the
    booking engine returns zero or partial slots for those days.
    """

    doctor: User = ForeignKeyField(
        User, null=False, backref="unavailable_days", on_delete="CASCADE", index=True
    )
    date: str = CharField(max_length=10, null=False)       # start date "YYYY-MM-DD"
    date_end: str = CharField(max_length=10, null=True)    # end date (inclusive); None = single day
    # "FULL" = whole day, "AM" = morning only, "PM" = afternoon only
    half_day: str = CharField(max_length=4, null=False, default="FULL")
    reason: str = CharField(max_length=200, null=True)

    class Meta:
        table_name = "gws_care_doctor_unavailable_day"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class DoctorScheduleService:
    """Manage doctor schedules and compute available time slots."""

    @classmethod
    def list_for_doctor(cls, doctor_id: str) -> list[DoctorSchedule]:
        return list(
            DoctorSchedule.select()
            .where(
                (DoctorSchedule.doctor == doctor_id)
                & (DoctorSchedule.is_active == True)  # noqa: E712
            )
            .order_by(DoctorSchedule.day_of_week, DoctorSchedule.start_time)
        )

    @classmethod
    def mark_unavailable(
        cls,
        doctor_id: str,
        date_from: str,
        date_to: str | None = None,
        reason: str | None = None,
        half_day: str = "FULL",
    ) -> None:
        """Block a date (or range) for a doctor."""
        DoctorUnavailableDay.create(
            doctor=doctor_id,
            date=date_from,
            date_end=date_to or None,
            half_day=half_day,
            reason=reason,
        )

    @classmethod
    def unmark_unavailable(cls, unavailable_day_id: str) -> None:
        """Remove a blocked date."""
        DoctorUnavailableDay.delete().where(
            DoctorUnavailableDay.id == unavailable_day_id
        ).execute()

    @classmethod
    def list_unavailable_for_doctor(cls, doctor_id: str) -> list[DoctorUnavailableDay]:
        return list(
            DoctorUnavailableDay.select()
            .where(DoctorUnavailableDay.doctor == doctor_id)
            .order_by(DoctorUnavailableDay.date)
        )

    @classmethod
    def available_slots(
        cls,
        doctor_id: str,
        on_date: "datetime.date",
    ) -> list[datetime]:
        """Return all available (unbooked) time slots for a doctor on a given date."""
        from gws_care.appointment.appointment import Appointment
        from gws_care.appointment.appointment_status import AppointmentStatus

        # Check unavailability records for this date
        date_str = on_date.strftime("%Y-%m-%d")
        unavail_records = list(
            DoctorUnavailableDay.select()
            .where(DoctorUnavailableDay.doctor == doctor_id)
        )
        am_blocked = False
        pm_blocked = False
        for rec in unavail_records:
            end = rec.date_end if rec.date_end else rec.date
            if rec.date <= date_str <= end:
                if rec.half_day == "FULL":
                    return []
                elif rec.half_day == "AM":
                    am_blocked = True
                elif rec.half_day == "PM":
                    pm_blocked = True

        blocks = [
            b for b in cls.list_for_doctor(doctor_id)
            if b.day_of_week == on_date.weekday()
        ]
        all_slots: list[datetime] = []
        for block in blocks:
            all_slots.extend(block.get_slots(on_date))

        # Apply half-day filtering
        if am_blocked:
            all_slots = [s for s in all_slots if s.hour >= 12]
        if pm_blocked:
            all_slots = [s for s in all_slots if s.hour < 12]

        # Fetch already-booked slots for this doctor/date
        booked = set()
        try:
            existing = list(
                Appointment.select()
                .where(
                    (Appointment.assigned_doctor_id == doctor_id)
                    & (Appointment.scheduled_at >= datetime(on_date.year, on_date.month, on_date.day, 0, 0))
                    & (Appointment.scheduled_at < datetime(on_date.year, on_date.month, on_date.day, 23, 59))
                    & (Appointment.status != AppointmentStatus.CANCELLED.value)
                )
            )
            for appt in existing:
                booked.add(appt.scheduled_at.replace(second=0, microsecond=0))
        except Exception as exc:
            print(f"[doctor_schedule] Failed to load booked slots for doctor={doctor_id} date={on_date}: {exc}")

        return [s for s in all_slots if s.replace(second=0, microsecond=0) not in booked]
