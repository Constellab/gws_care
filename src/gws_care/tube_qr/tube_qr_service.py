"""Service layer for TubeQR (US-081, US-091, US-092)."""

import uuid
from datetime import datetime

from gws_care.campaign.campaign import Campaign
from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
from gws_care.patient.patient import Patient
from gws_care.tube_qr.tube_qr import TubeQR, TubeQRStatus


class TubeQRService:
    """Generate and manage lab tube QR codes for a campaign."""

    @classmethod
    def generate_tubes(cls, campaign_id: str, count: int) -> list[TubeQR]:
        """Generate `count` blank tubes for a campaign."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        tubes = []
        for i in range(count):
            tube = TubeQR()
            tube.campaign = campaign
            tube.qr_code = str(uuid.uuid4())
            # Short alphanumeric ID for printing (6 uppercase chars)
            tube.short_id = tube.qr_code.replace("-", "")[:6].upper()
            tube.status = TubeQRStatus.BLANK.value
            tube.save()
            tubes.append(tube)
        return tubes

    @classmethod
    def get_by_qr_code(cls, qr_code: str) -> TubeQR:
        """Resolve a scanned QR code to its TubeQR row."""
        try:
            return TubeQR.get(TubeQR.qr_code == qr_code)
        except TubeQR.DoesNotExist:
            raise ValueError(f"QR code inconnu : {qr_code}")

    @classmethod
    def associate_tube(
        cls,
        qr_code: str,
        patient_id: str,
        exam_type_ref_id: str,
        sample_type: str | None = None,
    ) -> TubeQR:
        """Associate a blank tube to a patient + exam type (US-091)."""
        tube = cls.get_by_qr_code(qr_code)
        if tube.status != TubeQRStatus.BLANK.value:
            raise ValueError(f"Ce tube est déjà utilisé (statut: {tube.status}).")
        tube.patient = Patient.get_by_id_and_check(patient_id)
        tube.exam_type_ref = ExamTypeRef.get_by_id_and_check(exam_type_ref_id)
        tube.sample_type = sample_type
        tube.status = TubeQRStatus.ASSOCIATED.value
        tube.associated_at = datetime.now()
        tube.save()
        return tube

    @classmethod
    def mark_collected(cls, qr_code: str) -> TubeQR:
        """Mark a tube as physically collected (sample taken)."""
        tube = cls.get_by_qr_code(qr_code)
        if tube.status != TubeQRStatus.ASSOCIATED.value:
            raise ValueError("Le tube doit être associé avant d'être marqué prélevé.")
        tube.status = TubeQRStatus.COLLECTED.value
        tube.collected_at = datetime.now()
        tube.save()
        return tube

    @classmethod
    def cancel_tube(cls, qr_code: str, reason: str, cancelled_by_id: str | None = None) -> TubeQR:
        """Cancel a tube association (US-091 — requires reason and audit)."""
        if not reason or not reason.strip():
            raise ValueError("Un motif d'annulation est obligatoire.")
        tube = cls.get_by_qr_code(qr_code)
        tube.status = TubeQRStatus.CANCELLED.value
        tube.cancelled_reason = reason
        tube.cancelled_by_id = cancelled_by_id
        tube.save()
        return tube

    @classmethod
    def list_for_campaign(cls, campaign_id: str) -> list[TubeQR]:
        return list(
            TubeQR.select()
            .where(TubeQR.campaign == campaign_id)
            .order_by(TubeQR.created_at)
        )

    @classmethod
    def count_by_status(cls, campaign_id: str) -> dict[str, int]:
        counts: dict[str, int] = {s.value: 0 for s in TubeQRStatus}
        for tube in TubeQR.select().where(TubeQR.campaign == campaign_id):
            counts[tube.status] = counts.get(tube.status, 0) + 1
        return counts
