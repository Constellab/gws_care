"""State for the doctor's assigned-exams page.

Shows all campaign exam types where doctors are assigned, expanded to
per-patient rows. Supports filtering by doctor, status, and text search.
"""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class AssignedDoctorOption(BaseModel):
    """Doctor entry for the filter dropdown."""
    id: str       # MedicalDoctor.id (string)
    name: str


class AssignedExamRowDTO(BaseModel):
    """One row in the assigned-exams table — one patient × one exam type."""

    # Assigned doctor
    assigned_doctor_id: str = ""
    assigned_doctor_name: str = ""

    # Source context
    source_type: str = "campaign"          # "campaign" | "individual"
    campaign_id: str = ""
    campaign_name: str = ""
    campaign_number: str = ""
    campaign_status: str = ""
    campaign_status_label: str = ""

    # Exam type
    exam_type_id: str = ""
    exam_type_name: str = ""
    exam_category: str = ""

    # Patient
    patient_id: str = ""
    patient_name: str = ""
    patient_number: str = ""

    # Current medical status of this patient in this campaign
    medical_status: str = "PENDING"
    medical_status_label: str = "En attente"
    medical_status_color: str = "gray"

    # Deep-link to the exam entry page
    action_url: str = ""
    can_act: bool = True


class DoctorAssignedExamsState(ReflexMainState):
    rows: list[AssignedExamRowDTO] = []
    available_doctors: list[AssignedDoctorOption] = []
    is_loading: bool = False
    error: str = ""

    # The logged-in user's own doctor ID (empty if not a doctor)
    my_doctor_id: str = ""

    # Filters
    filter_doctor_id: str = "__all__"
    filter_status: str = "__all__"
    filter_search: str = ""

    @rx.var
    def filtered_rows(self) -> list[AssignedExamRowDTO]:
        result = self.rows
        if self.filter_doctor_id != "__all__":
            result = [r for r in result if r.assigned_doctor_id == self.filter_doctor_id]
        if self.filter_status != "__all__":
            result = [r for r in result if r.medical_status == self.filter_status]
        if self.filter_search.strip():
            q = self.filter_search.strip().lower()
            result = [
                r for r in result
                if q in r.patient_name.lower()
                or q in r.patient_number.lower()
                or q in r.exam_type_name.lower()
                or q in r.campaign_name.lower()
                or q in r.assigned_doctor_name.lower()
            ]
        return result

    @rx.event
    def set_filter_doctor_id(self, value: str):
        self.filter_doctor_id = value

    @rx.event
    def set_filter_status(self, value: str):
        self.filter_status = value

    @rx.event
    def set_filter_search(self, value: str):
        self.filter_search = value

    @rx.event
    async def on_load(self):
        self.is_loading = True
        self.error = ""
        try:
            with await self.authenticate_user() as auth_user:
                self._load_rows(auth_user.id)
        except Exception as exc:
            self.error = str(exc)
        finally:
            self.is_loading = False

    def _load_rows(self, auth_user_id) -> None:
        from gws_care.campaign.campaign import Campaign
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.campaign.campaign_patient import CampaignPatient, MedicalRecordStatus
        from gws_care.doctor.medical_doctor import MedicalDoctor
        from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
        from gws_care.patient.patient import Patient

        # Detect whether the logged-in user is a doctor (for default filter)
        me = MedicalDoctor.get_or_none(
            (MedicalDoctor.user == auth_user_id)
            & (MedicalDoctor.is_active == True)
            & (MedicalDoctor.is_archived == False)
        )
        self.my_doctor_id = str(me.id) if me else ""

        # Load ALL CampaignExam records that have an assigned doctor
        assigned_ces = list(
            CampaignExam.select(CampaignExam, Campaign, ExamTypeRef)
            .join(Campaign, on=(CampaignExam.campaign == Campaign.id))
            .switch(CampaignExam)
            .join(ExamTypeRef, on=(CampaignExam.exam_type_ref == ExamTypeRef.id))
            .where(CampaignExam.assigned_doctor_id.is_null(False))
            .order_by(Campaign.name, ExamTypeRef.name)
        )

        # Build unique doctor list for the filter dropdown
        doctor_map: dict[str, str] = {}  # id → name
        for ce in assigned_ces:
            did = ce.assigned_doctor_id or ""
            dname = ce.assigned_doctor_name or did
            if did and did not in doctor_map:
                doctor_map[did] = dname
        self.available_doctors = [
            AssignedDoctorOption(id=did, name=dname)
            for did, dname in sorted(doctor_map.items(), key=lambda x: x[1])
        ]

        # If logged-in user is a doctor and filter not yet set → default to self
        if self.filter_doctor_id == "__all__" and self.my_doctor_id:
            self.filter_doctor_id = self.my_doctor_id

        # Preload campaign patients keyed by campaign_id
        campaign_ids = list({str(ce.campaign_id) for ce in assigned_ces})
        campaign_patients: dict[str, list] = {}
        for cid in campaign_ids:
            cp_list = list(
                CampaignPatient.select(CampaignPatient, Patient)
                .join(Patient, on=(CampaignPatient.patient == Patient.id))
                .where(CampaignPatient.campaign == cid)
            )
            campaign_patients[cid] = cp_list

        _status_labels = {
            "draft": "Brouillon", "validated": "Validée",
            "terrain_exam": "Terrain", "sample_analysis": "Analyse",
            "lab_done": "Labo terminé", "closed": "Clôturée",
            "archived": "Archivée",
        }

        result: list[AssignedExamRowDTO] = []
        for ce in assigned_ces:
            cid = str(ce.campaign_id)
            camp = ce.campaign
            camp_status = (
                camp.status.value if hasattr(camp.status, "value") else str(camp.status)
            )
            camp_status_label = _status_labels.get(camp_status, camp_status)
            doc_id = ce.assigned_doctor_id or ""
            doc_name = ce.assigned_doctor_name or ""

            for cp in campaign_patients.get(cid, []):
                patient = cp.patient
                ms = cp.medical_status or MedicalRecordStatus.PENDING.value
                try:
                    msr = MedicalRecordStatus(ms)
                    ms_label = msr.get_label()
                    ms_color = msr.get_color()
                except Exception:
                    ms_label = ms
                    ms_color = "gray"

                result.append(AssignedExamRowDTO(
                    assigned_doctor_id=doc_id,
                    assigned_doctor_name=doc_name,
                    source_type="campaign",
                    campaign_id=cid,
                    campaign_name=camp.name,
                    campaign_number=camp.campaign_number,
                    campaign_status=camp_status,
                    campaign_status_label=camp_status_label,
                    exam_type_id=str(ce.exam_type_ref_id),
                    exam_type_name=ce.exam_type_ref.name,
                    exam_category=(
                        ce.exam_type_ref.get_category_label()
                        if hasattr(ce.exam_type_ref, "get_category_label")
                        else (ce.exam_type_ref.category or "")
                    ),
                    patient_id=str(patient.id),
                    patient_name=patient.get_full_name(),
                    patient_number=patient.patient_number,
                    medical_status=ms,
                    medical_status_label=ms_label,
                    medical_status_color=ms_color,
                    action_url=f"/campaign-patient/{cid}/{patient.id}",
                    can_act=camp_status in ("terrain_exam", "sample_analysis", "lab_done"),
                ))

        # Sort: actionable first, then by doctor name → campaign → patient
        result.sort(key=lambda r: (
            0 if r.can_act else 1,
            r.assigned_doctor_name,
            r.campaign_name,
            r.patient_name,
        ))
        self.rows = result
