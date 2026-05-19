"""Service layer for Prebilling and Invoice (US-190, US-191)."""

import uuid
from datetime import date

from gws_care.account.account import Account
from gws_care.campaign.campaign import Campaign
from gws_care.campaign.campaign_patient import CampaignPatient
from gws_care.prebilling.prebilling import (
    Invoice,
    InvoiceStatus,
    Prebilling,
    PrebillingLine,
    PrebillingStatus,
)


class PrebillingDTO:
    def __init__(self, pb: Prebilling):
        try:
            status_enum = PrebillingStatus(pb.status)
        except ValueError:
            status_enum = PrebillingStatus.DRAFT
        self.id = str(pb.id)
        self.account_id = str(pb.account_id)
        self.account_name = pb.account.name if pb.account_id else ""
        self.campaign_id = str(pb.campaign_id) if pb.campaign_id else None
        self.campaign_name = pb.campaign.name if pb.campaign_id else None
        self.period_start = pb.period_start.isoformat() if pb.period_start else None
        self.period_end = pb.period_end.isoformat() if pb.period_end else None
        self.status = pb.status
        self.status_label = status_enum.get_label()
        self.status_color = status_enum.get_color()
        self.total_amount = pb.total_amount
        self.notes = pb.notes
        self.lines = []


class PrebillingService:
    """Manage pre-billing lifecycle."""

    @classmethod
    def list_for_account(cls, account_id: str) -> list["PrebillingDTO"]:
        rows = (
            Prebilling.select()
            .where(Prebilling.account == account_id)
            .order_by(Prebilling.created_at.desc())
        )
        return [PrebillingDTO(pb) for pb in rows]

    @classmethod
    def list_all(cls) -> list["PrebillingDTO"]:
        rows = Prebilling.select().order_by(Prebilling.created_at.desc())
        return [PrebillingDTO(pb) for pb in rows]

    @classmethod
    def generate_from_campaign(cls, campaign_id: str, unit_price_per_exam: float = 0.0) -> Prebilling:
        """Generate a draft pre-billing from a campaign's present patients."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        present = CampaignPatient.select().where(
            (CampaignPatient.campaign == campaign_id)
            & (CampaignPatient.presence_status == "PRESENT")
        ).count()

        pb = Prebilling()
        pb.account = campaign.account
        pb.campaign = campaign
        pb.period_start = campaign.start_date
        pb.period_end = campaign.end_date
        pb.status = PrebillingStatus.DRAFT.value
        pb.total_amount = present * unit_price_per_exam
        pb.save()

        if present > 0:
            line = PrebillingLine()
            line.prebilling = pb
            line.description = f"Examens réalisés — campaign {campaign.name}"
            line.quantity = present
            line.unit_price = unit_price_per_exam
            line.total_price = present * unit_price_per_exam
            line.save()

        return pb

    @classmethod
    def validate(cls, prebilling_id: str) -> Prebilling:
        pb = Prebilling.get_by_id_and_check(prebilling_id)
        if pb.status != PrebillingStatus.DRAFT.value:
            raise ValueError("Seul un brouillon peut être validé.")
        pb.status = PrebillingStatus.VALIDATED.value
        pb.save()
        return pb

    @classmethod
    def generate_invoice(cls, prebilling_id: str) -> Invoice:
        pb = Prebilling.get_by_id_and_check(prebilling_id)
        if pb.status != PrebillingStatus.VALIDATED.value:
            raise ValueError("La préfacturation doit être validée avant de générer une facture.")

        # Generate unique invoice number
        short = str(uuid.uuid4())[:8].upper()
        invoice_number = f"FAC-{date.today().strftime('%Y%m')}-{short}"

        inv = Invoice()
        inv.prebilling = pb
        inv.account = pb.account
        inv.invoice_number = invoice_number
        inv.status = InvoiceStatus.VALIDATED.value
        inv.issue_date = date.today()
        inv.total_amount = pb.total_amount
        inv.save()

        pb.status = PrebillingStatus.INVOICED.value
        pb.save()
        return inv
