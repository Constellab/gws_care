"""State for the prescriptions list page."""

import reflex as rx
from pydantic import BaseModel
from gws_reflex_main import ReflexMainState


class PrescriptionRowDTO(BaseModel):
    id: str = ""
    patient_id: str = ""
    patient_name: str = ""
    patient_number: str = ""
    doctor_name: str = ""
    prescription_type: str = ""
    type_label: str = ""
    issued_at: str = ""
    valid_until: str = ""
    is_renewable: bool = False
    line_count: int = 0
    consultation_id: str = ""


class PrescriptionsState(ReflexMainState):
    rows: list[PrescriptionRowDTO] = []
    is_loading: bool = False
    error_message: str = ""
    search_query: str = ""
    type_filter: str = "ALL"
    date_from: str = ""
    date_to: str = ""
    # Pagination
    page: int = 1
    page_size: int = 50
    total_count: int = 0

    @rx.var
    def total_pages(self) -> int:
        return max(1, (self.total_count + self.page_size - 1) // self.page_size)

    @rx.var
    def has_prev_page(self) -> bool:
        return self.page > 1

    @rx.var
    def has_next_page(self) -> bool:
        return self.page < self.total_pages

    @rx.event
    async def set_search(self, value: str):
        self.search_query = value
        self.page = 1
        await self._load_prescriptions()

    @rx.event
    async def set_type_filter(self, value: str):
        self.type_filter = value
        self.page = 1
        await self._load_prescriptions()

    @rx.event
    async def set_date_from(self, value: str):
        self.date_from = value
        self.page = 1
        await self._load_prescriptions()

    @rx.event
    async def set_date_to(self, value: str):
        self.date_to = value
        self.page = 1
        await self._load_prescriptions()

    @rx.event
    async def prev_page(self):
        if self.has_prev_page:
            self.page -= 1
            await self._load_prescriptions()

    @rx.event
    async def next_page(self):
        if self.has_next_page:
            self.page += 1
            await self._load_prescriptions()

    @rx.event
    async def clear_filters(self):
        self.search_query = ""
        self.type_filter = "ALL"
        self.date_from = ""
        self.date_to = ""
        self.page = 1
        await self._load_prescriptions()

    @rx.event
    async def on_load(self):
        await self._load_prescriptions()

    async def _load_prescriptions(self):
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from peewee import fn
                from gws_care.prescription.prescription import Prescription, PrescriptionLine, PrescriptionType
                from gws_care.patient.patient import Patient
                from gws_care.user.user import User

                base_q = (
                    Prescription.select(Prescription, Patient, User)
                    .join(Patient)
                    .switch(Prescription)
                    .join(User, on=(Prescription.prescribing_doctor == User.id))
                )
                if self.type_filter != "ALL":
                    base_q = base_q.where(Prescription.prescription_type == self.type_filter)
                if self.search_query.strip():
                    s = self.search_query.strip()
                    base_q = base_q.where(
                        Patient.last_name.contains(s)
                        | Patient.first_name.contains(s)
                        | Patient.patient_number.contains(s)
                        | User.last_name.contains(s)
                        | User.first_name.contains(s)
                    )
                if self.date_from:
                    from datetime import date as date_type
                    base_q = base_q.where(Prescription.issued_at >= date_type.fromisoformat(self.date_from))
                if self.date_to:
                    from datetime import date as date_type
                    base_q = base_q.where(Prescription.issued_at <= date_type.fromisoformat(self.date_to))

                self.total_count = base_q.count()
                self.page = max(1, min(self.page, self.total_pages))
                prescriptions = list(
                    base_q.order_by(Prescription.issued_at.desc())
                    .limit(self.page_size)
                    .offset((self.page - 1) * self.page_size)
                )
                # Pre-aggregate line counts (avoid N+1)
                pids = [p.id for p in prescriptions]
                line_counts: dict[str, int] = {}
                if pids:
                    for row in (
                        PrescriptionLine.select(
                            PrescriptionLine.prescription_id,
                            fn.COUNT(PrescriptionLine.id).alias("cnt"),
                        )
                        .where(PrescriptionLine.prescription.in_(pids))
                        .group_by(PrescriptionLine.prescription_id)
                        .namedtuples()
                    ):
                        line_counts[str(row.prescription_id)] = row.cnt

                rows: list[PrescriptionRowDTO] = []
                for p in prescriptions:
                    try:
                        type_label = PrescriptionType(p.prescription_type).get_label()
                    except ValueError:
                        type_label = p.prescription_type
                    rows.append(PrescriptionRowDTO(
                        id=str(p.id),
                        patient_id=str(p.patient_id),
                        patient_name=p.patient.get_full_name(),
                        patient_number=p.patient.patient_number or "",
                        doctor_name=f"{p.prescribing_doctor.first_name} {p.prescribing_doctor.last_name}".strip(),
                        prescription_type=p.prescription_type,
                        type_label=type_label,
                        issued_at=p.issued_at.isoformat() if p.issued_at else "",
                        valid_until=p.valid_until.isoformat() if p.valid_until else "",
                        is_renewable=bool(p.is_renewable),
                        line_count=line_counts.get(str(p.id), 0),
                        consultation_id=str(p.consultation_id) if p.consultation_id else "",
                    ))
                self.rows = rows
        except Exception as exc:
            self.error_message = str(exc)
            print(f"[prescriptions] Erreur chargement: {exc}")
        finally:
            self.is_loading = False
