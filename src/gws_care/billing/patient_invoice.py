"""PatientInvoice — billing document for private clinic consultations.

Distinct from Prebilling (which is tied to company campaigns).
PatientInvoice covers individual patient billing for clinic visits.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from peewee import (
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    ForeignKeyField,
    IntegerField,
    TextField,
)

from gws_care.account.account import Account
from gws_care.billing.price_list import PriceList
from gws_care.consultation.consultation import Consultation
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
from gws_care.patient.patient import Patient
from gws_care.user.user import User


class PatientInvoiceStatus(str, Enum):
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


class PatientInvoice(ModelWithUser):
    """A billing document for one patient's clinic visit.

    Lines are stored in PatientInvoiceLine.
    totals are denormalised and recomputed by the service on each line change.
    """

    patient: Patient = ForeignKeyField(
        Patient, null=False, backref="invoices", on_delete="RESTRICT", index=True
    )
    consultation: Consultation = ForeignKeyField(
        Consultation, null=True, backref="invoices", on_delete="SET NULL"
    )
    # Optional billing account (for employer-reimbursed invoices)
    billing_account: Account = ForeignKeyField(
        Account, null=True, backref="patient_invoices", on_delete="SET NULL"
    )
    issuing_doctor: User = ForeignKeyField(
        User, null=True, backref="+", on_delete="SET NULL"
    )
    invoice_number: str = CharField(max_length=50, null=False, unique=True)
    invoice_date: date = DateField(null=False)
    status: str = CharField(
        max_length=20, null=False, default=PatientInvoiceStatus.DRAFT.value
    )
    total_ht: Decimal = DecimalField(max_digits=10, decimal_places=2, null=False, default=Decimal("0"))
    total_vat: Decimal = DecimalField(max_digits=10, decimal_places=2, null=False, default=Decimal("0"))
    total_ttc: Decimal = DecimalField(max_digits=10, decimal_places=2, null=False, default=Decimal("0"))
    paid_at: datetime = DateTimeField(null=True)
    notes: str | None = TextField(null=True)

    class Meta:
        table_name = "gws_care_patient_invoice"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class PatientInvoiceLine(ModelWithUser):
    """One line on a PatientInvoice — one exam act at one price."""

    invoice: PatientInvoice = ForeignKeyField(
        PatientInvoice, null=False, backref="lines", on_delete="CASCADE", index=True
    )
    exam_type_ref: ExamTypeRef = ForeignKeyField(
        ExamTypeRef, null=True, backref="+", on_delete="SET NULL"
    )
    description: str = CharField(max_length=300, null=False)
    quantity: int = IntegerField(null=False, default=1)
    unit_price_ht: Decimal = DecimalField(max_digits=10, decimal_places=2, null=False)
    vat_rate: Decimal = DecimalField(max_digits=5, decimal_places=2, null=False, default=Decimal("0"))
    line_total_ht: Decimal = DecimalField(max_digits=10, decimal_places=2, null=False)
    line_total_ttc: Decimal = DecimalField(max_digits=10, decimal_places=2, null=False)

    class Meta:
        table_name = "gws_care_patient_invoice_line"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


