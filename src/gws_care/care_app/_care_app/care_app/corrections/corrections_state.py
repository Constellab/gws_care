"""State for the correction requests page."""

import reflex as rx
from pydantic import BaseModel
from gws_reflex_main import ReflexMainState


class CorrectionRowDTO(BaseModel):
    id: str = ""
    patient_id: str = ""
    patient_name: str = ""
    patient_number: str = ""
    field_name: str = ""
    old_value: str = ""
    new_value: str = ""
    reason: str = ""
    status: str = ""
    status_label: str = ""
    status_color: str = ""
    requested_by_name: str = ""
    reviewed_by_name: str = ""
    review_date: str = ""
    review_reason: str = ""
    created_at: str = ""
    exam_id: str = ""
    campaign_name: str = ""


class CorrectionsState(ReflexMainState):
    rows: list[CorrectionRowDTO] = []
    is_loading: bool = False
    error_message: str = ""
    search_query: str = ""
    status_filter: str = "PENDING"
    # Pagination
    page: int = 1
    page_size: int = 50
    total_count: int = 0
    # Review dialog
    review_dialog_open: bool = False
    review_correction_id: str = ""
    review_decision: str = "ACCEPTED"
    review_reason_text: str = ""

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
        await self.on_load()  # type: ignore[misc]

    @rx.event
    async def set_status_filter(self, value: str):
        self.status_filter = value
        self.page = 1
        await self.on_load()  # type: ignore[misc]

    @rx.event
    async def prev_page(self):
        if self.has_prev_page:
            self.page -= 1
            await self.on_load()  # type: ignore[misc]

    @rx.event
    async def next_page(self):
        if self.has_next_page:
            self.page += 1
            await self.on_load()  # type: ignore[misc]

    @rx.event
    def open_review_dialog(self, correction_id: str):
        self.review_correction_id = correction_id
        self.review_decision = "ACCEPTED"
        self.review_reason_text = ""
        self.review_dialog_open = True

    @rx.event
    def close_review_dialog(self):
        self.review_dialog_open = False

    @rx.event
    def set_review_decision(self, v: str):
        self.review_decision = v

    @rx.event
    def set_review_reason(self, v: str):
        self.review_reason_text = v

    @rx.event
    async def submit_review(self):
        if not self.review_correction_id:
            return
        try:
            with await self.authenticate_user() as auth_user:
                from datetime import datetime
                from gws_care.correction.correction_request import CorrectionRequest
                cr = CorrectionRequest.get_by_id(self.review_correction_id)
                cr.status = self.review_decision
                cr.reviewed_by_id = str(auth_user.id)
                cr.review_date = datetime.utcnow()
                cr.review_reason = self.review_reason_text or None
                cr.save()
            self.review_dialog_open = False
            await self.on_load()  # type: ignore[misc]
        except Exception as exc:
            self.error_message = str(exc)
            print(f"[corrections] Erreur review: {exc}")

    @rx.event
    async def on_load(self):
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.correction.correction_request import CorrectionRequest, CorrectionStatus
                from gws_care.patient.patient import Patient

                query = (
                    CorrectionRequest.select(CorrectionRequest, Patient)
                    .join(Patient, on=(CorrectionRequest.patient == Patient.id), join_type="LEFT OUTER")
                    .order_by(CorrectionRequest.created_at.desc())
                )
                if self.status_filter != "ALL":
                    query = query.where(CorrectionRequest.status == self.status_filter)
                if self.search_query.strip():
                    term = f"%{self.search_query.strip()}%"
                    query = query.where(
                        (Patient.last_name ** term)
                        | (Patient.first_name ** term)
                        | (Patient.patient_number ** term)
                        | (CorrectionRequest.field_name ** term)
                        | (CorrectionRequest.reason ** term)
                    )
                self.total_count = query.count()
                self.page = max(1, min(self.page, self.total_pages))
                corrections = list(
                    query.limit(self.page_size).offset((self.page - 1) * self.page_size)
                )
                # Preload user display names (created_by + reviewed_by) in one query (avoids N+1)
                user_ids_needed = (
                    {c.created_by_id for c in corrections if c.created_by_id}
                    | {c.reviewed_by_id for c in corrections if c.reviewed_by_id}
                )
                user_display: dict[str, str] = {}
                if user_ids_needed:
                    from gws_care.user.user import User
                    for u in User.select(User.id, User.first_name, User.last_name, User.email).where(User.id.in_(user_ids_needed)):
                        user_display[str(u.id)] = f"{u.first_name} {u.last_name}".strip() or u.email
                # Preload campaign names in one query (avoids N+1)
                campaign_ids_needed = {c.campaign_id for c in corrections if c.campaign_id}
                campaign_names_map: dict[str, str] = {}
                if campaign_ids_needed:
                    from gws_care.campaign.campaign import Campaign
                    for camp in Campaign.select(Campaign.id, Campaign.name).where(Campaign.id.in_(campaign_ids_needed)):
                        campaign_names_map[str(camp.id)] = camp.name
                rows: list[CorrectionRowDTO] = []
                for cr in corrections:
                    try:
                        st = CorrectionStatus(cr.status)
                        status_label = st.get_label()
                        status_color = st.get_color()
                    except ValueError:
                        status_label = cr.status
                        status_color = "gray"
                    requested_by_name = user_display.get(str(cr.created_by_id), "") if cr.created_by_id else ""
                    reviewed_by_name = user_display.get(str(cr.reviewed_by_id), "") if cr.reviewed_by_id else ""
                    # Patient
                    patient_name = ""
                    patient_number = ""
                    patient_id = ""
                    try:
                        if cr.patient_id:
                            patient_id = str(cr.patient_id)
                            patient_name = cr.patient.get_full_name()
                            patient_number = cr.patient.patient_number or ""
                    except Exception as exc:
                        print(f"[corrections] patient for {cr.id}: {exc}")
                    campaign_name = campaign_names_map.get(str(cr.campaign_id), "") if cr.campaign_id else ""
                    rows.append(CorrectionRowDTO(
                        id=str(cr.id),
                        patient_id=patient_id,
                        patient_name=patient_name,
                        patient_number=patient_number,
                        field_name=cr.field_name,
                        old_value=cr.old_value or "",
                        new_value=cr.new_value or "",
                        reason=cr.reason or "",
                        status=cr.status,
                        status_label=status_label,
                        status_color=status_color,
                        requested_by_name=requested_by_name,
                        reviewed_by_name=reviewed_by_name,
                        review_date=cr.review_date.isoformat() if cr.review_date else "",
                        review_reason=cr.review_reason or "",
                        created_at=cr.created_at.isoformat() if cr.created_at else "",
                        exam_id=str(cr.exam_id) if cr.exam_id else "",
                        campaign_name=campaign_name,
                    ))
                self.rows = rows
        except Exception as exc:
            self.error_message = str(exc)
            print(f"[corrections] Erreur chargement: {exc}")
        finally:
            self.is_loading = False
