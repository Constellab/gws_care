"""Service layer for CorrectionRequest (US-200, US-201)."""

from datetime import datetime

from gws_care.correction.correction_request import CorrectionRequest, CorrectionStatus
from gws_care.user.user import User


class CorrectionService:
    """Manage post-validation correction requests."""

    @classmethod
    def submit_request(
        cls,
        field_name: str,
        old_value: str | None,
        new_value: str | None,
        reason: str,
        patient_id: str | None = None,
        campaign_id: str | None = None,
        exam_id: str | None = None,
    ) -> CorrectionRequest:
        if not reason or not reason.strip():
            raise ValueError("Le motif de correction est obligatoire.")
        cr = CorrectionRequest()
        cr.field_name = field_name
        cr.old_value = old_value
        cr.new_value = new_value
        cr.reason = reason
        cr.status = CorrectionStatus.PENDING.value
        if patient_id:
            cr.patient_id = patient_id
        if campaign_id:
            cr.campaign_id = campaign_id
        if exam_id:
            cr.exam_id = exam_id
        cr.save()
        return cr

    @classmethod
    def accept(cls, correction_id: str, reviewer_id: str | None = None) -> CorrectionRequest:
        cr = CorrectionRequest.get_by_id_and_check(correction_id)
        if cr.status != CorrectionStatus.PENDING.value:
            raise ValueError("Seule une demande en attente peut être acceptée.")
        cr.status = CorrectionStatus.ACCEPTED.value
        cr.review_date = datetime.now()
        if reviewer_id:
            cr.reviewed_by_id = reviewer_id
        cr.save()
        return cr

    @classmethod
    def refuse(cls, correction_id: str, reason: str, reviewer_id: str | None = None) -> CorrectionRequest:
        if not reason or not reason.strip():
            raise ValueError("Le motif de refus est obligatoire.")
        cr = CorrectionRequest.get_by_id_and_check(correction_id)
        if cr.status != CorrectionStatus.PENDING.value:
            raise ValueError("Seule une demande en attente peut être refusée.")
        cr.status = CorrectionStatus.REFUSED.value
        cr.review_reason = reason
        cr.review_date = datetime.now()
        if reviewer_id:
            cr.reviewed_by_id = reviewer_id
        cr.save()
        return cr

    @classmethod
    def mark_applied(cls, correction_id: str) -> CorrectionRequest:
        cr = CorrectionRequest.get_by_id_and_check(correction_id)
        if cr.status != CorrectionStatus.ACCEPTED.value:
            raise ValueError("Seule une demande acceptée peut être marquée appliquée.")
        cr.status = CorrectionStatus.APPLIED.value
        cr.save()
        return cr

    @classmethod
    def list_all(cls, status: str | None = None, limit: int = 500) -> list[CorrectionRequest]:
        query = CorrectionRequest.select().order_by(CorrectionRequest.created_at.desc())
        if status:
            query = query.where(CorrectionRequest.status == status)
        return list(query.limit(limit))

    @classmethod
    def list_for_exam(cls, exam_id: str) -> list[CorrectionRequest]:
        return list(
            CorrectionRequest.select()
            .where(CorrectionRequest.exam == exam_id)
            .order_by(CorrectionRequest.created_at.desc())
        )
