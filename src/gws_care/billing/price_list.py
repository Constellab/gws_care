"""PriceList — tariff per exam type for private clinic billing.

Admins define a price per ExamTypeRef with optional validity dates.
The service resolves the active price at a given date.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from peewee import BooleanField, CharField, DateField, DecimalField, ForeignKeyField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef


class PriceList(ModelWithUser):
    """One tariff entry: price_ht for one exam type, with optional validity window.

    Multiple entries for the same exam_type_ref are supported — the service
    picks the one whose validity window contains the requested date.
    If no end_date is set, the entry is valid indefinitely.
    """

    exam_type_ref: ExamTypeRef = ForeignKeyField(
        ExamTypeRef, null=False, backref="prices", on_delete="CASCADE", index=True
    )
    # Tarif hors taxe (HT) in euros
    price_ht: Decimal = DecimalField(max_digits=10, decimal_places=2, null=False)
    # VAT rate as a percentage (e.g. 20.0 for 20%)
    vat_rate: Decimal = DecimalField(max_digits=5, decimal_places=2, null=False, default=Decimal("0"))
    # Description optionnelle (ex: "Tarif Secteur 1", "Tarif mutuelles")
    label: str = CharField(max_length=200, null=True)
    # Optional validity window — None means "no start/end constraint"
    effective_from: date = DateField(null=True)
    effective_to: date = DateField(null=True)
    is_active: bool = BooleanField(default=True, null=False)

    @property
    def price_ttc(self) -> Decimal:
        return self.price_ht * (1 + self.vat_rate / 100)

    class Meta:
        table_name = "gws_care_price_list"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class PriceListService:
    """Resolve active prices and manage the tariff schedule."""

    @classmethod
    def get_active_price(
        cls,
        exam_type_ref_id: str,
        on_date: date | None = None,
    ) -> PriceList | None:
        """Return the active PriceList entry for this exam type on a given date.

        If on_date is None, today is used.
        Returns None when no active tariff is configured.
        """
        check_date = on_date or date.today()
        query = (
            PriceList.select()
            .where(
                (PriceList.exam_type_ref == exam_type_ref_id)
                & (PriceList.is_active == True)  # noqa: E712
                & (
                    (PriceList.effective_from.is_null(True))
                    | (PriceList.effective_from <= check_date)
                )
                & (
                    (PriceList.effective_to.is_null(True))
                    | (PriceList.effective_to >= check_date)
                )
            )
            .order_by(PriceList.effective_from.desc())
        )
        return query.first()

    @classmethod
    def list_all(cls) -> list[PriceList]:
        return list(
            PriceList.select(PriceList, ExamTypeRef)
            .join(ExamTypeRef)
            .order_by(ExamTypeRef.name)
        )
