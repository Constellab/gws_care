"""State for the consultations list page — all private (non-campaign) consultations."""

import reflex as rx
from pydantic import BaseModel
from gws_reflex_main import ReflexMainState


class ConsultationListRowDTO(BaseModel):
    """One row in the consultations list table."""

    id: str
    patient_id: str
    patient_name: str
    patient_number: str
    consultation_date: str
    reason_for_visit: str
    exam_count: int
    has_conclusion: bool
    # "patient" | "enterprise"
    consultation_type: str = "patient"
    billing_account_name: str = ""


class ConsultationListState(ReflexMainState):
    """Consultations list page state."""

    rows: list[ConsultationListRowDTO] = []
    is_loading: bool = False
    error_message: str = ""
    search_query: str = ""
    active_tab: str = "tous"  # "tous" | "patient" | "enterprise"
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

    @rx.var
    def filtered_rows(self) -> list[ConsultationListRowDTO]:
        return self.rows

    @rx.event
    async def set_tab(self, tab: str):
        self.active_tab = tab
        self.page = 1
        await self.on_load()

    @rx.event
    async def set_search(self, value: str):
        """Update search and reload — debounce handled in component via rx.debounce_input."""
        self.search_query = value
        self.page = 1
        await self.on_load()

    @rx.event
    async def execute_search(self):
        """Trigger a server-side reload — kept for backward compatibility."""
        await self.on_load()

    @rx.event
    async def clear_search(self):
        self.search_query = ""
        self.page = 1
        await self.on_load()

    @rx.event
    async def prev_page(self):
        if self.has_prev_page:
            self.page -= 1
            await self.on_load()

    @rx.event
    async def next_page(self):
        if self.has_next_page:
            self.page += 1
            await self.on_load()

    @rx.event
    async def on_load(self):
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.consultation.consultation import Consultation
                from gws_care.exam.exam import Exam
                from gws_care.patient.patient import Patient
                from peewee import fn
                # Push type filter to SQL
                sql_type = self.active_tab if self.active_tab != "tous" else None
                search = self.search_query.strip()
                # Build base query with optional type + search filters
                base_q = Consultation.select(Consultation, Patient).join(Patient)
                if sql_type == "patient":
                    base_q = base_q.where(Consultation.billing_account.is_null(True))
                elif sql_type == "enterprise":
                    base_q = base_q.where(Consultation.billing_account.is_null(False))
                if search:
                    base_q = base_q.where(
                        Patient.last_name.contains(search)
                        | Patient.first_name.contains(search)
                        | Patient.patient_number.contains(search)
                        | Consultation.reason_for_visit.contains(search)
                    )
                # Count total for pagination header
                self.total_count = base_q.count()
                consultations = list(
                    base_q.order_by(Consultation.consultation_date.desc())
                    .limit(self.page_size)
                    .offset((self.page - 1) * self.page_size)
                )
                # Pre-compute exam counts in ONE query (avoids N+1)
                c_ids = [c.id for c in consultations]
                exam_counts: dict[str, int] = {}
                if c_ids:
                    for row in (
                        Exam.select(Exam.consultation_id, fn.COUNT(Exam.id).alias("cnt"))
                        .where(Exam.consultation_id.in_(c_ids))
                        .group_by(Exam.consultation_id)
                        .namedtuples()
                    ):
                        exam_counts[str(row.consultation_id)] = row.cnt
                # Preload billing account names (avoids N+1)
                acct_ids_set = {
                    str(c.billing_account_id) for c in consultations
                    if getattr(c, "billing_account_id", None)
                }
                billing_acct_names: dict[str, str] = {}
                if acct_ids_set:
                    from gws_care.account.account import Account
                    for a in Account.select(Account.id, Account.name).where(Account.id.in_(acct_ids_set)):
                        billing_acct_names[str(a.id)] = a.name
                rows: list[ConsultationListRowDTO] = []
                for c in consultations:
                    patient = c.patient
                    exam_count = exam_counts.get(str(c.id), 0)
                    has_account = bool(getattr(c, "billing_account_id", None))
                    consultation_type = "enterprise" if has_account else "patient"
                    billing_account_name = billing_acct_names.get(str(c.billing_account_id), "") if has_account else ""
                    rows.append(ConsultationListRowDTO(
                        id=str(c.id),
                        patient_id=str(patient.id),
                        patient_name=patient.get_full_name(),
                        patient_number=patient.patient_number,
                        consultation_date=c.consultation_date.strftime("%d/%m/%Y") if c.consultation_date else "",
                        reason_for_visit=c.reason_for_visit or "",
                        exam_count=exam_count,
                        has_conclusion=bool(c.conclusion),
                        consultation_type=consultation_type,
                        billing_account_name=billing_account_name,
                    ))
                self.rows = rows
        except Exception as exc:
            self.rows = []
            self.error_message = f"Erreur chargement consultations : {exc}"
            print(f"[consultation_list] {exc}")
        finally:
            self.is_loading = False
