"""State management for the patient detail page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class PatientDetailDTO(BaseModel):
    """Full patient details DTO for the detail page."""

    id: str
    patient_number: str
    last_name: str
    first_name: str
    birth_name: str | None = None
    date_of_birth: str
    gender: str
    photo: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    phone: str | None = None
    email: str | None = None
    primary_physician_name: str | None = None
    primary_physician_phone: str | None = None
    qr_token: str | None = None


class ExamRowDTO(BaseModel):
    """Lightweight exam row for the patient detail exam list."""

    id: str
    exam_date: str
    exam_type_label: str
    status: str
    link_url: str = ""   # /exam/{id} for standalone, /campaign-patient/{c}/{p} for campaign


class AppointmentRowDTO(BaseModel):
    """Lightweight appointment row for the patient detail appointments list."""

    id: str
    scheduled_at: str
    exam_type_label: str
    status: str
    account_name: str | None = None
    campaign_name: str = ""  # non-empty when this row comes from a campaign enrollment


class ConsultationExamDTO(BaseModel):
    """Lightweight exam row inside a consultation card."""

    exam_id: str
    exam_type_label: str
    status: str
    has_lab_results: bool = False


class ConsultationRowDTO(BaseModel):
    """One consultation visit shown on the patient detail page."""

    id: str
    consultation_date: str
    reason_for_visit: str = ""
    exam_count: int = 0
    exams: list[ConsultationExamDTO] = []


class CampaignEnrollmentDTO(BaseModel):
    """Lightweight campaign participation row for the patient detail page."""

    campaign_id: str
    campaign_name: str
    status: str
    status_label: str
    start_date: str
    account_name: str
    exams: list[ExamRowDTO] = []


class PatientDetailState(ReflexMainState):
    """State for the patient detail page."""

    patient: PatientDetailDTO | None = None
    exams: list[ExamRowDTO] = []
    consultations: list[ConsultationRowDTO] = []
    appointments: list[AppointmentRowDTO] = []
    campaign_enrollments: list[CampaignEnrollmentDTO] = []
    is_loading: bool = False
    error_message: str = ""

    @rx.event
    async def on_load(self):
        """Load patient data and exam list when the page is mounted."""
        await self._load_patient()

    @rx.event
    def go_back(self):
        """Navigate back to the patient list."""
        return rx.redirect("/")

    @rx.event
    def go_to_exam(self, exam_id: str):
        """Navigate to the exam detail page."""
        return rx.redirect(f"/exam/{exam_id}")

    @rx.event
    async def go_to_appointments(self):
        """Navigate to the appointments page, pre-filtered for this patient."""
        from ..appointment_list.appointment_list_state import AppointmentListState
        patient_name = (
            f"{self.patient.first_name} {self.patient.last_name}"
            if self.patient else ""
        )
        yield AppointmentListState.set_patient_context(self.patient_id_param, patient_name)
        yield rx.redirect("/appointments")

    @rx.event
    async def delete_exam(self, exam_id: str):
        """Delete a standalone exam and reload the patient."""
        if not exam_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam_service import ExamService
                ExamService.delete_exam(exam_id)
            yield PatientDetailState.on_load()
        except Exception as exc:
            yield rx.toast.error(f"Erreur lors de la suppression : {exc}")

    @rx.event
    async def download_exam_history(self):
        """Generate and download the patient's exam history as CSV."""
        if not self.patient:
            return
        try:
            with await self.authenticate_user():
                from gws_care.export.csv_export_service import generate_exam_history_csv
                csv_bytes = generate_exam_history_csv(self.patient.id)

            filename = f"exam_history_{self.patient.patient_number}.csv"
            return rx.download(data=csv_bytes, filename=filename)
        except Exception as e:
            self.error_message = f"Export error: {e}"

    async def _load_patient(self):
        """Internal: fetch patient and their exams from DB using URL param."""
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return

        patient_id = self.patient_id_param
        if not patient_id:
            self.error_message = "No patient ID in URL"
            return

        self.is_loading = True
        self.error_message = ""

        try:
            with await self.authenticate_user():
                from gws_care.appointment.appointment_service import AppointmentService
                from gws_care.exam.exam_service import ExamService
                from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                from gws_care.patient.patient_service import PatientService

                # Build a label lookup dict for all active ExamTypeRef entries
                ref_labels: dict[str, str] = {
                    str(r.id): r.name
                    for r in ExamTypeRef.select(ExamTypeRef.id, ExamTypeRef.name)
                }

                p = PatientService.get_patient(patient_id)
                self.patient = PatientDetailDTO(
                    id=str(p.id),
                    patient_number=p.patient_number,
                    last_name=p.last_name,
                    first_name=p.first_name,
                    birth_name=p.birth_name,
                    date_of_birth=p.date_of_birth.isoformat(),
                    gender=p.gender,
                    photo=p.photo,
                    address=p.address,
                    postal_code=p.postal_code,
                    city=p.city,
                    phone=p.phone,
                    email=p.email,
                    primary_physician_name=p.primary_physician_name,
                    primary_physician_phone=p.primary_physician_phone,
                    qr_token=p.qr_token,
                )

                # ── Load campaign memberships — enrollments built after exam processing ──
                from peewee import JOIN
                from gws_care.campaign.campaign import Campaign
                from gws_care.campaign.campaign_patient import CampaignPatient, MedicalRecordStatus
                from gws_care.account.account import Account
                cp_rows = list(
                    CampaignPatient.select(CampaignPatient, Campaign, Account)
                    .join(Campaign)
                    .join(Account, JOIN.LEFT_OUTER, on=(Campaign.account == Account.id))
                    .switch(CampaignPatient)
                    .where(CampaignPatient.patient == patient_id)
                    .order_by(Campaign.start_date.desc())
                )

                # ── Consultations (visits with grouped exams) ─────────────────────────
                from gws_care.consultation.consultation_service import ConsultationService
                from gws_care.exam.exam import Exam as ExamModel
                consult_rows: list[ConsultationRowDTO] = []
                try:
                    consults = list(ConsultationService.list_for_patient(patient_id))
                    # Pre-fetch all exams for all consultations in one query (avoids N+1)
                    consult_ids = [str(c.id) for c in consults]
                    exams_by_consult: dict[str, list] = {}
                    if consult_ids:
                        for ex in (
                            ExamModel.select()
                            .where(ExamModel.consultation_id.in_(consult_ids))
                            .order_by(ExamModel.exam_date.asc())
                        ):
                            exams_by_consult.setdefault(str(ex.consultation_id), []).append(ex)
                    for consult in consults:
                        linked_exams = exams_by_consult.get(str(consult.id), [])
                        exam_dtos = []
                        for ex in linked_exams:
                            lbl = (
                                ref_labels.get(str(ex.exam_type_ref_id), ex.exam_type.get_label())
                                if ex.exam_type_ref_id
                                else ex.exam_type.get_label()
                            )
                            exam_dtos.append(ConsultationExamDTO(
                                exam_id=str(ex.id),
                                exam_type_label=lbl,
                                status=ex.status.value,
                                has_lab_results=bool(ex.lab_results),
                            ))
                        consult_rows.append(ConsultationRowDTO(
                            id=str(consult.id),
                            consultation_date=consult.consultation_date.isoformat(),
                            reason_for_visit=consult.reason_for_visit or "",
                            exam_count=len(exam_dtos),
                            exams=exam_dtos,
                        ))
                except Exception as exc:
                    self.error_message = f"Erreur lors du chargement des consultations : {exc}"
                self.consultations = consult_rows

                # ── Exams: separate into campaign groups and standalone ─────────────────
                exams_loaded = ExamService.list_exams_for_patient(patient_id)
                consultation_exam_ids: set[str] = {
                    ex_dto.exam_id
                    for cr in consult_rows
                    for ex_dto in cr.exams
                }
                existing_camp_sections: set[tuple[str, str]] = set()
                exam_rows_standalone: list[ExamRowDTO] = []
                exam_rows_by_campaign: dict[str, list[ExamRowDTO]] = {}

                for e in exams_loaded:
                    if str(e.id) in consultation_exam_ids:
                        continue
                    rv = e.reason_for_visit or ""
                    if rv.startswith("CAMP:"):
                        try:
                            parts = rv.split("|")
                            c_id = parts[0][5:]
                            s_id = parts[1][4:]
                            existing_camp_sections.add((c_id, s_id))
                            label = ref_labels.get(s_id, e.exam_type.get_label())
                            exam_rows_by_campaign.setdefault(c_id, []).append(ExamRowDTO(
                                id=str(e.id),
                                exam_date=e.exam_date.isoformat(),
                                exam_type_label=label,
                                status=e.status.value,
                                link_url=f"/campaign-patient/{c_id}/{patient_id}",
                            ))
                        except Exception as exc:
                            exam_rows_standalone.append(ExamRowDTO(
                                id=str(e.id),
                                exam_date=e.exam_date.isoformat() if e.exam_date else "",
                                exam_type_label=e.exam_type.get_label(),
                                status=e.status.value,
                                link_url=f"/exam/{e.id}",
                            ))
                            print(f"[patient_detail] Fallback exam row: {exc}")
                    else:
                        label = (
                            ref_labels.get(str(e.exam_type_ref_id), e.exam_type.get_label())
                            if e.exam_type_ref_id
                            else e.exam_type.get_label()
                        )
                        exam_rows_standalone.append(ExamRowDTO(
                            id=str(e.id),
                            exam_date=e.exam_date.isoformat(),
                            exam_type_label=label,
                            status=e.status.value,
                            link_url=f"/exam/{e.id}",
                        ))

                # Pre-fetch all CampaignExams (used for pending rows + appointment inference)
                from gws_care.campaign.campaign_exam import CampaignExam
                all_patient_campaign_ids = list({str(cp.campaign_id) for cp in cp_rows})
                camp_exams_by_c: dict[str, list] = {}
                if all_patient_campaign_ids:
                    for ce in (
                        CampaignExam.select(CampaignExam, ExamTypeRef)
                        .join(ExamTypeRef)
                        .where(CampaignExam.campaign.in_(all_patient_campaign_ids))
                    ):
                        camp_exams_by_c.setdefault(str(ce.campaign_id), []).append(ce)

                # Pending rows for campaign exam types not yet entered
                for cp in cp_rows:
                    c_id = str(cp.campaign_id)
                    for ce in camp_exams_by_c.get(c_id, []):
                        s_id = str(ce.exam_type_ref_id)
                        if (c_id, s_id) not in existing_camp_sections:
                            exam_rows_by_campaign.setdefault(c_id, []).append(ExamRowDTO(
                                id="",
                                exam_date="",
                                exam_type_label=ce.exam_type_ref.name,
                                status="PENDING_ENTRY",
                                link_url=f"/campaign-patient/{c_id}/{patient_id}",
                            ))
                            existing_camp_sections.add((c_id, s_id))

                self.exams = exam_rows_standalone

                # ── Campaign enrollments (built after exam processing to include exams) ──
                campaign_enrollments = []
                for cp in cp_rows:
                    try:
                        ms = MedicalRecordStatus(cp.medical_status)
                        ms_label = ms.get_label()
                    except ValueError:
                        ms_label = cp.medical_status
                    try:
                        acct_name = cp.campaign.account.name if cp.campaign.account_id else ""
                    except Exception:
                        acct_name = ""
                    c_id = str(cp.campaign_id)
                    campaign_enrollments.append(CampaignEnrollmentDTO(
                        campaign_id=c_id,
                        campaign_name=cp.campaign.name,
                        status=cp.medical_status,
                        status_label=ms_label,
                        start_date=cp.campaign.start_date.isoformat() if cp.campaign.start_date else "",
                        account_name=acct_name,
                        exams=exam_rows_by_campaign.get(c_id, []),
                    ))
                self.campaign_enrollments = campaign_enrollments

                # ── Appointments (real + inferred from campaigns) ─────────────────────
                appointments = AppointmentService.list_for_patient(patient_id)
                # Batch-load billing account names (avoids N+1)
                appt_acct_ids = {str(a.billing_account_id) for a in appointments if a.billing_account_id}
                appt_acct_names: dict[str, str] = {}
                if appt_acct_ids:
                    from gws_care.account.account import Account as _Account
                    for ac in _Account.select(_Account.id, _Account.name).where(_Account.id.in_(appt_acct_ids)):
                        appt_acct_names[str(ac.id)] = ac.name
                appt_rows: list[AppointmentRowDTO] = [
                    AppointmentRowDTO(
                        id=str(a.id),
                        scheduled_at=a.scheduled_at.isoformat(),
                        exam_type_label=(
                            ref_labels.get(str(a.exam_type_ref_id), a.exam_type.get_label())
                            if a.exam_type_ref_id
                            else a.exam_type.get_label()
                        ),
                        status=a.status.value,
                        account_name=appt_acct_names.get(str(a.billing_account_id)) if a.billing_account_id else None,
                    )
                    for a in appointments
                ]
                for cp in cp_rows:
                    c_id = str(cp.campaign_id)
                    campaign_obj = cp.campaign
                    campaign_start = (
                        campaign_obj.start_date.isoformat() if campaign_obj.start_date else ""
                    )
                    for ce in camp_exams_by_c.get(c_id, []):
                        appt_rows.append(AppointmentRowDTO(
                            id="",
                            scheduled_at=campaign_start + "T00:00:00" if campaign_start else "",
                            exam_type_label=ce.exam_type_ref.name,
                            status="campaign",
                            campaign_name=campaign_obj.name,
                        ))
                self.appointments = appt_rows
        except Exception as e:
            self.error_message = f"Error loading patient: {e}"
        finally:
            self.is_loading = False
