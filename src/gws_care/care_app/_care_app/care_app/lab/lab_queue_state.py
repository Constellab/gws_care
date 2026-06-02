"""State for the lab queue page — exams with pending lab analyses."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class LabQueueRowDTO(BaseModel):
    """One row in the lab queue list."""

    source: str  # "consultation" | "campaign" | "appointment"
    patient_id: str
    patient_name: str
    exam_date: str
    exam_type_label: str
    param_count: int       # total requested parameters
    pending_count: int     # parameters still missing a value
    param_names: str       # comma-joined list of parameter names (truncated for display)

    # Consultation-specific (empty for campaign rows)
    exam_id: str = ""

    # Campaign-specific (empty for consultation rows)
    campaign_id: str = ""
    campaign_name: str = ""

    # Appointment-specific
    appointment_id: str = ""
    doctor_name: str = ""


class LabQueueState(RoleState):
    """Lab queue: exams that have prescribed lab tests awaiting results."""

    rows: list[LabQueueRowDTO] = []
    is_loading: bool = False
    error_message: str = ""
    status_filter: str = "pending"  # "all" | "pending" | "done"

    @rx.var
    def filtered_rows(self) -> list[LabQueueRowDTO]:
        """Filter rows by status."""
        if self.status_filter == "all":
            return self.rows
        if self.status_filter == "done":
            return [r for r in self.rows if r.pending_count == 0]
        # "pending" = at least one result missing
        return [r for r in self.rows if r.pending_count > 0]

    @rx.event
    def set_status_filter(self, value: str | list[str]):
        self.status_filter = value if isinstance(value, str) else (value[0] if value else "pending")

    @rx.event
    async def on_load(self):
        await self._load_roles()
        await self._load_queue()

    @rx.event
    async def refresh(self):
        await self._load_queue()

    async def _load_queue(self):
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                rows: list[LabQueueRowDTO] = []

                from peewee import fn
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamStatus
                from gws_care.exam_type_ref.exam_parameter import ExamParameter
                from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                from gws_care.patient.patient import Patient

                # ── 1. Consultation exams with prescribed lab parameters ────────
                exams_list = list(
                    Exam.select(Exam, Patient)
                    .join(Patient)
                    .where(
                        Exam.status == ExamStatus.DRAFT,
                        Exam.requested_param_ids.is_null(False),
                    )
                    .order_by(Exam.exam_date.desc())
                )

                # Bulk-fetch all ExamParameters and ExamTypeRefs needed (2 queries)
                all_param_ids: list[str] = list({
                    pid
                    for exam in exams_list
                    for pid in (exam.requested_param_ids or [])
                })
                all_exam_ref_ids: list[str] = list({
                    str(exam.exam_type_ref_id)
                    for exam in exams_list
                    if exam.exam_type_ref_id
                })
                params_by_id: dict[str, object] = {}
                if all_param_ids:
                    for p in ExamParameter.select().where(ExamParameter.id.in_(all_param_ids)):
                        params_by_id[str(p.id)] = p
                exam_ref_by_id: dict[str, object] = {}
                if all_exam_ref_ids:
                    for r in ExamTypeRef.select().where(ExamTypeRef.id.in_(all_exam_ref_ids)):
                        exam_ref_by_id[str(r.id)] = r

                for exam in exams_list:
                    param_ids: list[str] = exam.requested_param_ids or []
                    if not param_ids:
                        continue

                    params = sorted(
                        [params_by_id[pid] for pid in param_ids if pid in params_by_id],
                        key=lambda p: p.display_order or 0,
                    )
                    param_names_list = [p.name for p in params]
                    display_names = ", ".join(param_names_list[:5])
                    if len(param_names_list) > 5:
                        display_names += f" (+{len(param_names_list) - 5})"

                    existing_results = exam.lab_results or []
                    resulted_lower = {
                        r.get("parameter", "").lower()
                        for r in existing_results
                        if r.get("value", "").strip()
                    }
                    pending_count = sum(1 for n in param_names_list if n.lower() not in resulted_lower)

                    ref = exam_ref_by_id.get(str(exam.exam_type_ref_id)) if exam.exam_type_ref_id else None
                    exam_type_label = ref.name if ref else exam.exam_type.get_label()

                    patient = exam.patient
                    rows.append(
                        LabQueueRowDTO(
                            source="consultation",
                            exam_id=str(exam.id),
                            patient_id=str(patient.id),
                            patient_name=f"{patient.first_name} {patient.last_name}",
                            exam_date=exam.exam_date.isoformat(),
                            exam_type_label=exam_type_label,
                            param_count=len(param_ids),
                            pending_count=pending_count,
                            param_names=display_names,
                        )
                    )

                # ── 2. Campaign patients PRESENT but awaiting lab entry ─────────
                from gws_care.campaign.campaign import Campaign
                from gws_care.campaign.campaign_exam import CampaignExam
                from gws_care.campaign.campaign_patient import (
                    CampaignPatient,
                    MedicalRecordStatus,
                    PresenceStatus,
                )

                pending_cp_list = list(
                    CampaignPatient.select(CampaignPatient, Patient, Campaign)
                    .join(Patient)
                    .switch(CampaignPatient)
                    .join(Campaign)
                    .where(
                        CampaignPatient.presence_status == PresenceStatus.PRESENT.value,
                        CampaignPatient.medical_status == MedicalRecordStatus.PENDING.value,
                    )
                    .order_by(Campaign.start_date.desc())
                )

                # Pre-fetch all CampaignExams for all involved campaigns (1 query)
                cp_campaign_ids = list({str(cp.campaign_id) for cp in pending_cp_list})
                camp_exams_by_campaign: dict[str, list] = {}
                if cp_campaign_ids:
                    for ce in (
                        CampaignExam.select(CampaignExam, ExamTypeRef)
                        .join(ExamTypeRef)
                        .where(CampaignExam.campaign.in_(cp_campaign_ids))
                    ):
                        camp_exams_by_campaign.setdefault(str(ce.campaign_id), []).append(ce)

                # Pre-fetch all ExamParameters for all involved ref_ids (1 query)
                all_ref_ids = list({
                    str(ce.exam_type_ref_id)
                    for ces in camp_exams_by_campaign.values()
                    for ce in ces
                })
                params_by_ref: dict[str, list[str]] = {}
                if all_ref_ids:
                    for p in (
                        ExamParameter.select()
                        .where(ExamParameter.exam_type_ref.in_(all_ref_ids))
                        .order_by(ExamParameter.display_order)
                    ):
                        params_by_ref.setdefault(str(p.exam_type_ref_id), []).append(p.name)

                for cp in pending_cp_list:
                    campaign = cp.campaign
                    patient = cp.patient
                    campaign_exams = camp_exams_by_campaign.get(str(campaign.id), [])

                    all_params: list[str] = []
                    exam_type_names: list[str] = []
                    for ce in campaign_exams:
                        exam_type_names.append(ce.exam_type_ref.name)
                        all_params.extend(params_by_ref.get(str(ce.exam_type_ref_id), []))

                    if not all_params:
                        continue

                    display_names = ", ".join(all_params[:5])
                    if len(all_params) > 5:
                        display_names += f" (+{len(all_params) - 5})"

                    exam_type_label = ", ".join(exam_type_names) if exam_type_names else "Bilan campagne"
                    exam_date = campaign.start_date.isoformat() if campaign.start_date else "—"

                    rows.append(
                        LabQueueRowDTO(
                            source="campaign",
                            campaign_id=str(campaign.id),
                            campaign_name=campaign.name,
                            patient_id=str(patient.id),
                            patient_name=f"{patient.first_name} {patient.last_name}",
                            exam_date=exam_date,
                            exam_type_label=exam_type_label,
                            param_count=len(all_params),
                            pending_count=len(all_params),
                            param_names=display_names,
                        )
                    )

                # ── 3. Appointments with scheduled lab parameters ───────────
                from gws_care.appointment.appointment import Appointment
                from gws_care.appointment.appointment_status import AppointmentStatus

                pending_appts_list = list(
                    Appointment.select(Appointment, Patient)
                    .join(Patient)
                    .where(
                        Appointment.status == AppointmentStatus.SCHEDULED,
                        Appointment.exam_type_ref_id.is_null(False),
                    )
                    .order_by(Appointment.scheduled_at.asc())
                )

                # Bulk-fetch ExamTypeRefs and ExamParameters for all appt ref_ids (2 queries)
                appt_ref_ids = list({
                    str(appt.exam_type_ref_id)
                    for appt in pending_appts_list
                    if appt.exam_type_ref_id
                })
                appt_ref_lookup: dict[str, object] = {}
                appt_params_by_ref: dict[str, list] = {}
                if appt_ref_ids:
                    for r in ExamTypeRef.select().where(ExamTypeRef.id.in_(appt_ref_ids)):
                        appt_ref_lookup[str(r.id)] = r
                    for p in (
                        ExamParameter.select()
                        .where(ExamParameter.exam_type_ref.in_(appt_ref_ids))
                        .order_by(ExamParameter.display_order)
                    ):
                        appt_params_by_ref.setdefault(str(p.exam_type_ref_id), []).append(p)

                for appt in pending_appts_list:
                    patient = appt.patient
                    ref_id_str = str(appt.exam_type_ref_id) if appt.exam_type_ref_id else ""
                    ref = appt_ref_lookup.get(ref_id_str)
                    appt_label = ref.name if ref else appt.exam_type.get_label()
                    appt_params = appt_params_by_ref.get(ref_id_str, [])

                    if not appt_params:
                        continue

                    appt_param_names = [p.name for p in appt_params]
                    appt_display = ", ".join(appt_param_names[:5])
                    if len(appt_param_names) > 5:
                        appt_display += f" (+{len(appt_param_names) - 5})"

                    rows.append(
                        LabQueueRowDTO(
                            source="appointment",
                            appointment_id=str(appt.id),
                            patient_id=str(patient.id),
                            patient_name=f"{patient.first_name} {patient.last_name}",
                            exam_date=appt.scheduled_at.isoformat() if appt.scheduled_at else "",
                            exam_type_label=appt_label,
                            param_count=len(appt_params),
                            pending_count=len(appt_params),
                            param_names=appt_display,
                            doctor_name=appt.assigned_doctor_name or "",
                        )
                    )

                self.rows = rows
        except Exception as exc:
            self.error_message = f"Erreur lors du chargement: {exc}"
        finally:
            self.is_loading = False
