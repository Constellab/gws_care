"""Prebilling page — generate and manage pre-billings (US-190, US-191)."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class PrebillingRowVM(BaseModel):
    id: str
    account_name: str
    campaign_name: str
    status: str
    status_label: str
    status_color: str
    period_start: str
    period_end: str
    total_amount: float
    notes: str


class PrebillingCampaignOptionVM(BaseModel):
    id: str
    name: str


class PrebillingState(ReflexMainState):
    prebillings: list[PrebillingRowVM] = []
    is_loading: bool = False
    error: str = ""
    success: str = ""

    # Generate dialog
    gen_dialog_open: bool = False
    gen_campaign_id: str = ""
    gen_unit_price: str = "0"
    gen_error: str = ""
    is_generating: bool = False
    campaign_options: list[PrebillingCampaignOptionVM] = []

    @rx.event
    async def on_load(self):
        await self._load()

    @rx.event
    async def open_gen_dialog(self):
        self.gen_campaign_id = ""
        self.gen_unit_price = "0"
        self.gen_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.campaign.campaign_status import CampaignStatus
                campaigns = CampaignService.list_all_campaigns(status=CampaignStatus.TERRAIN_CLOTURE.value)
                self.campaign_options = [
                    PrebillingCampaignOptionVM(id=str(c.id), name=c.name)
                    for c in campaigns
                ]
        except Exception as e:
            self.gen_error = str(e)
        self.gen_dialog_open = True

    @rx.event
    def close_gen_dialog(self):
        self.gen_dialog_open = False

    @rx.event
    def set_gen_campaign(self, v: str):
        self.gen_campaign_id = v

    @rx.event
    def set_gen_unit_price(self, v: str):
        self.gen_unit_price = v

    @rx.event
    async def generate_prebilling(self):
        if not self.gen_campaign_id:
            self.gen_error = "Sélectionner une campagne."
            return
        self.is_generating = True
        self.gen_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.prebilling.prebilling_service import PrebillingService
                unit_price = float(self.gen_unit_price or "0")
                PrebillingService.generate_from_campaign(self.gen_campaign_id, unit_price)
            self.gen_dialog_open = False
            self.success = "Préfacturation générée."
            await self._load()
        except Exception as e:
            self.gen_error = str(e)
        finally:
            self.is_generating = False

    @rx.event
    async def validate_prebilling(self, prebilling_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.prebilling.prebilling_service import PrebillingService
                PrebillingService.validate(prebilling_id)
            self.success = "Préfacturation validée."
            await self._load()
        except Exception as e:
            self.error = str(e)

    @rx.event
    async def generate_invoice(self, prebilling_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.prebilling.prebilling_service import PrebillingService
                inv = PrebillingService.generate_invoice(prebilling_id)
            self.success = f"Facture générée : {inv.invoice_number}"
            await self._load()
        except Exception as e:
            self.error = str(e)

    @rx.event
    def dismiss_messages(self):
        self.error = ""
        self.success = ""

    async def _load(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        try:
            with await self.authenticate_user():
                from gws_care.prebilling.prebilling_service import PrebillingService, PrebillingStatus
                dtos = PrebillingService.list_all()
                self.prebillings = [
                    PrebillingRowVM(
                        id=d.id,
                        account_name=d.account_name,
                        campaign_name=d.campaign_name or "—",
                        status=d.status,
                        status_label=d.status_label,
                        status_color=d.status_color,
                        period_start=d.period_start or "",
                        period_end=d.period_end or "",
                        total_amount=d.total_amount,
                        notes=d.notes or "",
                    )
                    for d in dtos
                ]
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading = False
