"""State for the doctor's assigned-exams page.

Shows all campaign exam types where the logged-in doctor is the assigned doctor,
grouped by campaign, with a patient count and a link to review results.
"""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class AssignedExamRowDTO(BaseModel):
    campaign_id: str
    campaign_name: str
    campaign_number: str
    campaign_status: str
    campaign_status_label: str
    exam_type_id: str
    exam_type_name: str
    exam_category: str
    patient_count: int = 0


class DoctorAssignedExamsState(ReflexMainState):
    rows: list[AssignedExamRowDTO] = []
    is_loading: bool = False
    error: str = ""
    doctor_name: str = ""

    @rx.event
    async def on_load(self):
        self.is_loading = True
        self.error = ""
        try:
            with await self.authenticate_user() as auth_user:
                self._load_rows(str(auth_user.id))
        except Exception as exc:
            self.error = str(exc)
        finally:
            self.is_loading = False

    def _load_rows(self, user_id: str) -> None:
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.campaign.campaign import Campaign
        from gws_care.campaign.campaign_patient import CampaignPatient
        from gws_care.doctor.medical_doctor import MedicalDoctor
        from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef

        # Find this doctor's MedicalDoctor record via user_id
        doctor = MedicalDoctor.get_or_none(MedicalDoctor.user_id == user_id)
        if doctor is None:
            self.rows = []
            self.doctor_name = ""
            return

        self.doctor_name = doctor.get_full_name()
        doctor_id = str(doctor.id)

        # Find all CampaignExam records assigned to this doctor (materialise to list)
        assigned = list(
            CampaignExam.select(CampaignExam, Campaign, ExamTypeRef)
            .join(Campaign, on=(CampaignExam.campaign == Campaign.id))
            .switch(CampaignExam)
            .join(ExamTypeRef, on=(CampaignExam.exam_type_ref == ExamTypeRef.id))
            .where(CampaignExam.assigned_doctor_id == doctor_id)
            .order_by(Campaign.name, ExamTypeRef.name)
        )

        # Count patients per campaign (one query per unique campaign)
        patient_counts: dict[str, int] = {}
        for row in assigned:
            cid = str(row.campaign_id)
            if cid not in patient_counts:
                patient_counts[cid] = (
                    CampaignPatient.select()
                    .where(CampaignPatient.campaign == cid)
                    .count()
                )

        _status_labels = {
            "draft": "Brouillon",
            "validated": "Validé",
            "in_progress": "En cours",
            "completed": "Terminé",
            "archived": "Archivé",
        }

        result = []
        for row in assigned:
            cid = str(row.campaign_id)
            status = (
                row.campaign.status.value
                if hasattr(row.campaign.status, "value")
                else str(row.campaign.status)
            )
            result.append(
                AssignedExamRowDTO(
                    campaign_id=cid,
                    campaign_name=row.campaign.name,
                    campaign_number=row.campaign.campaign_number,
                    campaign_status=status,
                    campaign_status_label=_status_labels.get(status, status),
                    exam_type_id=str(row.exam_type_ref_id),
                    exam_type_name=row.exam_type_ref.name,
                    exam_category=row.exam_type_ref.category or "",
                    patient_count=patient_counts.get(cid, 0),
                )
            )
        self.rows = result
