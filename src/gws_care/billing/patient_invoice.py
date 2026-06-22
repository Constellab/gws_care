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


class PatientInvoiceService:
    """Create, manage and query patient invoices."""

    _INVOICE_COUNTER_TABLE = "gws_care_patient_invoice"

    @classmethod
    def create_from_consultation(
        cls,
        patient_id: str,
        consultation_id: str,
        issuing_doctor_id: str | None,
        invoice_date: date | None = None,
        billing_account_id: str | None = None,
    ) -> PatientInvoice:
        """Create a DRAFT invoice for a consultation, auto-adding lines from exam types."""
        from gws_care.exam.exam import Exam
        from gws_care.billing.price_list import PriceListService

        check_date = invoice_date or date.today()
        number = cls._next_invoice_number(check_date)

        invoice = PatientInvoice.create(
            patient_id=patient_id,
            consultation_id=consultation_id,
            billing_account_id=billing_account_id,
            issuing_doctor_id=issuing_doctor_id,
            invoice_number=number,
            invoice_date=check_date,
            status=PatientInvoiceStatus.DRAFT.value,
            total_ht=Decimal("0"),
            total_vat=Decimal("0"),
            total_ttc=Decimal("0"),
        )

        # Auto-add one line per exam in the consultation
        exams = list(Exam.select().where(Exam.consultation_id == str(consultation_id)))
        # Pre-fetch all ExamTypeRef names in one query (avoids N+1)
        ref_ids = [e.exam_type_ref_id for e in exams if e.exam_type_ref_id]
        from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
        ref_names: dict[str, str] = {}
        if ref_ids:
            for r in ExamTypeRef.select(ExamTypeRef.id, ExamTypeRef.name).where(ExamTypeRef.id.in_(ref_ids)):
                ref_names[str(r.id)] = r.name
        for exam in exams:
            if not exam.exam_type_ref_id:
                continue
            price_entry = PriceListService.get_active_price(exam.exam_type_ref_id, check_date)
            price_ht = price_entry.price_ht if price_entry else Decimal("0")
            vat_rate = price_entry.vat_rate if price_entry else Decimal("0")
            line_total_ht = price_ht
            line_total_ttc = price_ht * (1 + vat_rate / 100)
            description = ref_names.get(str(exam.exam_type_ref_id), "Examen")
            PatientInvoiceLine.create(
                invoice=invoice,
                exam_type_ref_id=exam.exam_type_ref_id,
                description=description,
                quantity=1,
                unit_price_ht=price_ht,
                vat_rate=vat_rate,
                line_total_ht=line_total_ht,
                line_total_ttc=line_total_ttc,
            )

        cls._recompute_totals(invoice)
        return invoice

    @classmethod
    def validate(cls, invoice_id: str) -> PatientInvoice:
        invoice = PatientInvoice.get_by_id(invoice_id)
        if invoice.status != PatientInvoiceStatus.DRAFT.value:
            raise ValueError("Seul un brouillon peut être validé.")
        invoice.status = PatientInvoiceStatus.VALIDATED.value
        invoice.save()
        return invoice

    @classmethod
    def mark_paid(cls, invoice_id: str) -> PatientInvoice:
        invoice = PatientInvoice.get_by_id(invoice_id)
        invoice.status = PatientInvoiceStatus.PAID.value
        invoice.paid_at = datetime.now()
        invoice.save()
        return invoice

    @classmethod
    def list_for_patient(cls, patient_id: str) -> list[PatientInvoice]:
        return list(
            PatientInvoice.select()
            .where(PatientInvoice.patient == patient_id)
            .order_by(PatientInvoice.invoice_date.desc())
        )

    @classmethod
    def _recompute_totals(cls, invoice: PatientInvoice) -> None:
        lines = list(PatientInvoiceLine.select().where(PatientInvoiceLine.invoice == invoice.id))
        total_ht = sum(l.line_total_ht for l in lines)
        total_ttc = sum(l.line_total_ttc for l in lines)
        invoice.total_ht = total_ht
        invoice.total_vat = total_ttc - total_ht
        invoice.total_ttc = total_ttc
        invoice.save()

    @classmethod
    def _next_invoice_number(cls, on_date: date) -> str:
        """Generate a sequential invoice number: FACT-YYYY-NNNN."""
        year = on_date.year
        from peewee import fn
        count = (
            PatientInvoice.select()
            .where(fn.YEAR(PatientInvoice.invoice_date) == year)
            .count()
        ) + 1
        return f"FACT-{year}-{count:04d}"
