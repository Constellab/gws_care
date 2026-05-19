"""Prebilling and Invoice models (US-190, US-191)."""

from datetime import date
from enum import Enum

from peewee import CharField, DateField, DoubleField, ForeignKeyField, IntegerField, TextField

from gws_care.account.account import Account
from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
from gws_core import Model


class PrebillingStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    INVOICED = "INVOICED"

    def get_label(self) -> str:
        return {"DRAFT": "Brouillon", "VALIDATED": "Validée", "INVOICED": "Facturée"}[self.value]

    def get_color(self) -> str:
        return {"DRAFT": "gray", "VALIDATED": "blue", "INVOICED": "green"}[self.value]


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    SENT = "SENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

    def get_label(self) -> str:
        return {
            "DRAFT": "Brouillon",
            "VALIDATED": "Validée",
            "SENT": "Envoyée",
            "PAID": "Payée",
            "CANCELLED": "Annulée",
        }[self.value]

    def get_color(self) -> str:
        return {
            "DRAFT": "gray",
            "VALIDATED": "blue",
            "SENT": "indigo",
            "PAID": "green",
            "CANCELLED": "red",
        }[self.value]


class Prebilling(ModelWithUser):
    """Pre-billing document grouping services for an account (US-190)."""

    account: Account = ForeignKeyField(
        Account, null=False, backref="prebillings", on_delete="RESTRICT"
    )
    campaign: Campaign = ForeignKeyField(
        Campaign, null=True, backref="prebillings", on_delete="SET NULL"
    )
    period_start: date = DateField(null=True)
    period_end: date = DateField(null=True)
    status: str = CharField(max_length=20, default=PrebillingStatus.DRAFT.value, null=False)
    total_amount: float = DoubleField(default=0.0, null=False)
    notes: str = TextField(null=True)

    class Meta:
        table_name = "gws_care_prebilling"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class PrebillingLine(Model):
    """One line item in a pre-billing document."""

    prebilling: Prebilling = ForeignKeyField(
        Prebilling, null=False, backref="lines", on_delete="CASCADE"
    )
    description: str = CharField(max_length=500, null=False)
    exam_type_ref: ExamTypeRef = ForeignKeyField(
        ExamTypeRef, null=True, backref="+", on_delete="SET NULL"
    )
    quantity: int = IntegerField(default=0, null=False)
    unit_price: float = DoubleField(default=0.0, null=False)
    total_price: float = DoubleField(default=0.0, null=False)

    class Meta:
        table_name = "gws_care_prebilling_line"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class Invoice(ModelWithUser):
    """Definitive invoice generated from a validated pre-billing (US-191)."""

    prebilling: Prebilling = ForeignKeyField(
        Prebilling, null=True, backref="invoices", on_delete="SET NULL"
    )
    account: Account = ForeignKeyField(
        Account, null=False, backref="invoices", on_delete="RESTRICT"
    )
    invoice_number: str = CharField(max_length=100, unique=True, null=True)
    status: str = CharField(max_length=20, default=InvoiceStatus.DRAFT.value, null=False)
    issue_date: date = DateField(null=True)
    total_amount: float = DoubleField(default=0.0, null=False)
    notes: str = TextField(null=True)

    class Meta:
        table_name = "gws_care_invoice"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
