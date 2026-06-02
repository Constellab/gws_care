"""Doctor PSC queue — interpretation and validation (US-120, US-121, US-122, US-123)."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class DossierRowDTO(BaseModel):
    campaign_patient_id: str
    patient_id: str
    patient_number: str
    patient_name: str
    campaign_id: str
    campaign_name: str
    account_name: str
    medical_status: str
    medical_status_label: str
    medical_status_color: str
    psc_notes: str
    psc_validated_at: str


class IndependentExamRowDTO(BaseModel):
    """Standalone (non-campaign) exam prescribed by a doctor and awaiting review."""
    exam_id: str
    patient_id: str
    patient_number: str
    patient_name: str
    exam_date: str
    exam_type_label: str
    has_lab_results: bool
    is_draft: bool = False  # True when exam status is DRAFT (appointment-based, not yet submitted)
    from_appointment: bool = False  # True when created via go_to_or_create_exam


class ClinicConsultationRowDTO(BaseModel):
    """A clinical consultation (CLINIC_VISIT / PREVENTIVE) shown in Dossiers Médicaux."""
    consultation_id: str
    patient_id: str
    patient_number: str
    patient_name: str
    consultation_date: str
    reason_for_visit: str
    encounter_type_label: str
    nb_exams: int


class DoctorPscState(ReflexMainState):
    dossiers: list[DossierRowDTO] = []
    independent_exams: list[IndependentExamRowDTO] = []
    clinic_consultations: list[ClinicConsultationRowDTO] = []
    dossiers_truncated: bool = False  # True when result capped at 500
    is_loading: bool = False
    error: str = ""
    success: str = ""
    filter_campaign_id: str = ""
    filter_status: str = "ALL"

    # Interpretation dialog
    interp_dialog_open: bool = False
    interp_campaign_id: str = ""
    interp_patient_id: str = ""
    interp_patient_name: str = ""
    interp_notes: str = ""
    interp_current_status: str = ""   # to check if already PSC_INTERPRETED
    is_saving: bool = False
    campaigns_for_filter: list[list[str]] = []  # [[id, name], ...]

    @rx.event
    async def on_load(self):
        await self._load()
        await self._load_campaigns()

    @rx.event
    async def set_filter_status(self, v: str):
        self.filter_status = v
        await self._load()

    @rx.event
    async def set_filter_campaign(self, v: str):
        self.filter_campaign_id = "" if v == "__all__" else v
        await self._load()

    @rx.event
    def open_interp_dialog(
        self, campaign_id: str, patient_id: str, patient_name: str, current_notes: str, current_status: str = ""
    ):
        self.interp_campaign_id = campaign_id
        self.interp_patient_id = patient_id
        self.interp_patient_name = patient_name
        self.interp_notes = current_notes
        self.interp_current_status = current_status
        self.interp_dialog_open = True

    @rx.event
    def close_interp_dialog(self):
        self.interp_dialog_open = False

    @rx.event
    def set_interp_notes(self, v: str):
        self.interp_notes = v

    @rx.event
    async def save_notes_only(self):
        """Save PSC notes as draft WITHOUT changing workflow status."""
        self.is_saving = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.save_psc_notes_draft(
                    self.interp_campaign_id, self.interp_patient_id, self.interp_notes
                )
            self.success = "Notes enregistrées."
            await self._load()
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving = False

    @rx.event
    async def save_interpretation(self):
        """Save notes AND set status to PSC_INTERPRETED, then close dialog."""
        self.is_saving = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.add_psc_interpretation(
                    self.interp_campaign_id, self.interp_patient_id, self.interp_notes
                )
            self.interp_dialog_open = False
            self.success = "Interprétation enregistrée et transmise à l’entreprise."
            await self._load()
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving = False

    @rx.event
    async def validate_patient(self, campaign_id: str, patient_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.validate_psc_patient(campaign_id, patient_id)
            self.success = "Dossier validé PSC."
            await self._load()
        except Exception as e:
            self.error = str(e)

    @rx.event
    async def validate_campaign(self, campaign_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.validate_psc_campaign(campaign_id)
            self.success = "Campagne validée PSC."
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
        self.error = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.campaign.campaign_patient import CampaignPatient, MedicalRecordStatus
                from gws_care.campaign.campaign import Campaign
                from gws_care.patient.patient import Patient
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService

                current_user_id = str(auth_user.id)
                roles = [r.value for r in UserRoleService.get_roles_for_user(current_user_id)]
                is_admin = any(r in {"SUPER_ADMIN_PSC", "ADMIN_PSC", "DIRECTEUR_PSC"} for r in roles)

                query = (
                    CampaignPatient.select(CampaignPatient, Campaign, Patient)
                    .join(Campaign)
                    .switch(CampaignPatient)
                    .join(Patient)
                )
                if self.filter_status and self.filter_status not in ("ALL", ""):
                    query = query.where(CampaignPatient.medical_status == self.filter_status)
                else:
                    query = query.where(
                        CampaignPatient.medical_status.in_([
                            MedicalRecordStatus.LAB_ENTERED.value,
                            MedicalRecordStatus.LAB_VALIDATED.value,
                            MedicalRecordStatus.PSC_INTERPRETED.value,
                        ])
                    )
                if self.filter_campaign_id:
                    query = query.where(CampaignPatient.campaign == self.filter_campaign_id)

                # Row-level isolation: non-admin PSC doctors only see campaigns
                # where they are the assigned PSC doctor
                if not is_admin:
                    from gws_care.user.user import User as UserModel
                    query = query.where(Campaign.psc_doctor == current_user_id)

                rows = []
                cp_list = list(query.order_by(CampaignPatient.medical_status, Patient.last_name).limit(500))
                cp_account_ids = [cp.campaign.account_id for cp in cp_list if cp.campaign.account_id]
                cp_account_names: dict[str, str] = {}
                if cp_account_ids:
                    from gws_care.account.account import Account
                    for ac in Account.select(Account.id, Account.name).where(Account.id.in_(cp_account_ids)):
                        cp_account_names[str(ac.id)] = ac.name
                for cp in cp_list:
                    try:
                        ms = MedicalRecordStatus(cp.medical_status)
                    except ValueError:
                        ms = MedicalRecordStatus.PENDING
                    rows.append(DossierRowDTO(
                        campaign_patient_id=str(cp.id),
                        patient_id=str(cp.patient.id),
                        patient_number=cp.patient.patient_number,
                        patient_name=f"{cp.patient.last_name} {cp.patient.first_name}",
                        campaign_id=str(cp.campaign.id),
                        campaign_name=cp.campaign.name,
                        account_name=cp_account_names.get(str(cp.campaign.account_id), "") if cp.campaign.account_id else "",
                        medical_status=cp.medical_status,
                        medical_status_label=ms.get_label(),
                        medical_status_color=ms.get_color(),
                        psc_notes=cp.psc_notes or "",
                        psc_validated_at=cp.psc_validated_at.isoformat() if cp.psc_validated_at else "",
                    ))
                self.dossiers = rows
                self.dossiers_truncated = len(rows) >= 500
                # Load standalone (non-campaign) exams prescribed by a doctor
                from gws_care.exam.exam import Exam
                from gws_care.patient.patient import Patient as PatientModel
                ind_rows = []
                try:
                    ind_query = (
                        Exam.select(Exam, PatientModel)
                        .join(PatientModel)
                        .where(
                            # Include: exams with prescribed lab params OR created from an appointment
                            (
                                Exam.requested_param_ids.is_null(False) |
                                Exam.reason_for_visit.like("APPT:%")
                            ),
                            Exam.consultation_id.is_null(True),
                            (Exam.reason_for_visit.is_null(True) | Exam.reason_for_visit.not_like("CAMP:%")),
                        )
                        .order_by(Exam.exam_date.desc())
                    )
                    # Non-admin doctors only see exams they ordered
                    if not is_admin:
                        ind_query = ind_query.where(Exam.created_by == current_user_id)
                    for exam in ind_query.limit(200):
                        try:
                            pat = exam.patient
                            from_appt = bool(exam.reason_for_visit and exam.reason_for_visit.startswith("APPT:"))
                            has_params = bool(exam.requested_param_ids)
                            # Skip exams with neither params nor appointment tag
                            if not from_appt and not has_params:
                                continue
                            ind_rows.append(IndependentExamRowDTO(
                                exam_id=str(exam.id),
                                patient_id=str(pat.id),
                                patient_number=pat.patient_number or "",
                                patient_name=f"{pat.last_name} {pat.first_name}",
                                exam_date=exam.exam_date.isoformat() if exam.exam_date else "",
                                exam_type_label=exam.exam_type.get_label() if hasattr(exam.exam_type, "get_label") else str(exam.exam_type),
                                has_lab_results=bool(exam.lab_results),
                                is_draft=exam.status.value == "draft" if hasattr(exam.status, "value") else str(exam.status).lower() == "draft",
                                from_appointment=from_appt,
                            ))
                        except Exception as exc:
                            continue
                except Exception as exc:
                    pass
                self.independent_exams = ind_rows

                # Load clinical consultations (CLINIC_VISIT / PREVENTIVE — not campaign)
                from gws_care.consultation.consultation import Consultation
                consult_rows = []
                try:
                    cq = (
                        Consultation.select(Consultation, PatientModel)
                        .join(PatientModel, on=(Consultation.patient == PatientModel.id))
                        .where(Consultation.encounter_type != "CAMPAIGN_EXAM")
                        .order_by(Consultation.consultation_date.desc())
                    )
                    if not is_admin:
                        cq = cq.where(Consultation.created_by == current_user_id)
                    for c in cq.limit(200):
                        try:
                            pat = c.patient
                            nb_ex = Exam.select().where(Exam.consultation_id == str(c.id)).count()
                            consult_rows.append(ClinicConsultationRowDTO(
                                consultation_id=str(c.id),
                                patient_id=str(pat.id),
                                patient_number=pat.patient_number or "",
                                patient_name=f"{pat.last_name} {pat.first_name}",
                                consultation_date=c.consultation_date.isoformat() if c.consultation_date else "",
                                reason_for_visit=c.reason_for_visit or "",
                                encounter_type_label=c.get_encounter_type_label(),
                                nb_exams=nb_ex,
                            ))
                        except Exception:
                            continue
                except Exception:
                    pass
                self.clinic_consultations = consult_rows
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading = False

    async def _load_campaigns(self):
        """Load distinct campaigns that have dossiers in the PSC queue."""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign import Campaign
                from gws_care.campaign.campaign_patient import CampaignPatient, MedicalRecordStatus
                campaign_ids = set(
                    cp.campaign_id
                    for cp in CampaignPatient.select(CampaignPatient.campaign)
                    .where(CampaignPatient.medical_status.in_([
                        MedicalRecordStatus.LAB_ENTERED.value,
                        MedicalRecordStatus.LAB_VALIDATED.value,
                        MedicalRecordStatus.PSC_INTERPRETED.value,
                        MedicalRecordStatus.PSC_VALIDATED.value,
                    ]))
                )
                campaigns = list(Campaign.select().where(Campaign.id.in_(campaign_ids)))
                self.campaigns_for_filter = [[str(c.id), c.name] for c in campaigns]
        except Exception as exc:
            self.campaigns_for_filter = []
