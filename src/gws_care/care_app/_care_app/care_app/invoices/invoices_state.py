"""State for the patient invoices list page."""

import reflex as rx
from pydantic import BaseModel
from gws_reflex_main import ReflexMainState


class InvoiceRowDTO(BaseModel):
    id: str = ""
    patient_id: str = ""
    patient_name: str = ""
    patient_number: str = ""
    invoice_number: str = ""
    invoice_date: str = ""
    status: str = ""
    status_label: str = ""
    status_color: str = ""
    total_ht: str = ""
    total_ttc: str = ""
    doctor_name: str = ""
    account_name: str = ""
    line_count: int = 0


class AccountFilterOption(BaseModel):
    id: str
    name: str


class InvoicesState(ReflexMainState):
    rows: list[InvoiceRowDTO] = []
    account_options: list[AccountFilterOption] = []
    is_loading: bool = False
    error_message: str = ""
    search_query: str = ""
    status_filter: str = "ALL"
    filter_account_id: str = ""
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
        await self._load_invoices()

    @rx.event
    async def set_status_filter(self, value: str):
        self.status_filter = value
        self.page = 1
        await self._load_invoices()

    @rx.event
    async def set_filter_account(self, value: str):
        self.filter_account_id = "" if value == "ALL" else value
        self.page = 1
        await self._load_invoices()

    @rx.event
    async def set_date_from(self, value: str):
        self.date_from = value
        self.page = 1
        await self._load_invoices()

    @rx.event
    async def set_date_to(self, value: str):
        self.date_to = value
        self.page = 1
        await self._load_invoices()

    @rx.event
    async def prev_page(self):
        if self.has_prev_page:
            self.page -= 1
            await self._load_invoices()

    @rx.event
    async def next_page(self):
        if self.has_next_page:
            self.page += 1
            await self._load_invoices()

    @rx.event
    async def clear_filters(self):
        self.search_query = ""
        self.status_filter = "ALL"
        self.filter_account_id = ""
        self.date_from = ""
        self.date_to = ""
        self.page = 1
        await self._load_invoices()

    @rx.event
    async def on_load(self):
        await self._load_account_options()
        await self._load_invoices()

    async def _load_account_options(self):
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                accounts = AccountService.list_accounts()
                self.account_options = [
                    AccountFilterOption(id=str(a.id), name=a.name) for a in accounts
                ]
        except Exception:
            self.account_options = []

    async def _load_invoices(self):
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from peewee import fn
                from gws_care.billing.patient_invoice import PatientInvoice, PatientInvoiceLine, PatientInvoiceStatus
                from gws_care.patient.patient import Patient
                from gws_care.account.account import Account

                base_q = (
                    PatientInvoice.select(PatientInvoice, Patient)
                    .join(Patient)
                )
                if self.status_filter != "ALL":
                    base_q = base_q.where(PatientInvoice.status == self.status_filter)
                if self.filter_account_id:
                    base_q = base_q.where(PatientInvoice.billing_account == self.filter_account_id)
                if self.search_query.strip():
                    s = self.search_query.strip()
                    base_q = base_q.where(
                        Patient.last_name.contains(s)
                        | Patient.first_name.contains(s)
                        | Patient.patient_number.contains(s)
                        | PatientInvoice.invoice_number.contains(s)
                    )
                if self.date_from:
                    from datetime import date as date_type
                    base_q = base_q.where(PatientInvoice.invoice_date >= date_type.fromisoformat(self.date_from))
                if self.date_to:
                    from datetime import date as date_type
                    base_q = base_q.where(PatientInvoice.invoice_date <= date_type.fromisoformat(self.date_to))

                self.total_count = base_q.count()
                self.page = max(1, min(self.page, self.total_pages))
                invoices = list(
                    base_q.order_by(PatientInvoice.invoice_date.desc())
                    .limit(self.page_size)
                    .offset((self.page - 1) * self.page_size)
                )
                # Pre-aggregate line counts
                inv_ids = [inv.id for inv in invoices]
                line_counts: dict[str, int] = {}
                if inv_ids:
                    for row in (
                        PatientInvoiceLine.select(
                            PatientInvoiceLine.invoice_id,
                            fn.COUNT(PatientInvoiceLine.id).alias("cnt"),
                        )
                        .where(PatientInvoiceLine.invoice.in_(inv_ids))
                        .group_by(PatientInvoiceLine.invoice_id)
                        .namedtuples()
                    ):
                        line_counts[str(row.invoice_id)] = row.cnt

                # Batch load doctor names and account names
                doctor_ids = {inv.issuing_doctor_id for inv in invoices if inv.issuing_doctor_id}
                doctor_names_map: dict[str, str] = {}
                if doctor_ids:
                    from gws_care.user.user import User
                    for u in User.select(User.id, User.first_name, User.last_name).where(User.id.in_(doctor_ids)):
                        doctor_names_map[str(u.id)] = f"{u.first_name} {u.last_name}".strip()
                acct_ids = {inv.billing_account_id for inv in invoices if inv.billing_account_id}
                acct_names_map: dict[str, str] = {}
                if acct_ids:
                    for a in Account.select(Account.id, Account.name).where(Account.id.in_(acct_ids)):
                        acct_names_map[str(a.id)] = a.name

                rows: list[InvoiceRowDTO] = []
                for inv in invoices:
                    try:
                        status_enum = PatientInvoiceStatus(inv.status)
                        status_label = status_enum.get_label()
                        status_color = status_enum.get_color()
                    except ValueError:
                        status_label = inv.status
                        status_color = "gray"
                    doctor_name = doctor_names_map.get(str(inv.issuing_doctor_id), "") if inv.issuing_doctor_id else ""
                    account_name = acct_names_map.get(str(inv.billing_account_id), "") if inv.billing_account_id else ""
                    rows.append(InvoiceRowDTO(
                        id=str(inv.id),
                        patient_id=str(inv.patient_id),
                        patient_name=inv.patient.get_full_name(),
                        patient_number=inv.patient.patient_number or "",
                        invoice_number=inv.invoice_number,
                        invoice_date=inv.invoice_date.isoformat() if inv.invoice_date else "",
                        status=inv.status,
                        status_label=status_label,
                        status_color=status_color,
                        total_ht=str(inv.total_ht),
                        total_ttc=str(inv.total_ttc),
                        doctor_name=doctor_name,
                        account_name=account_name,
                        line_count=line_counts.get(str(inv.id), 0),
                    ))
                self.rows = rows
        except Exception as exc:
            self.error_message = str(exc)
            print(f"[invoices] Erreur chargement: {exc}")
        finally:
            self.is_loading = False
