"""State management for the campaign detail page."""

from datetime import date

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class CampaignDetailDTO(BaseModel):
    id: str
    name: str
    account_id: str
    account_name: str
    status: str
    status_label: str
    status_color: str
    start_date: str
    end_date: str
    location: str
    psc_doctor_name: str
    enterprise_doctor_name: str
    requires_medical_review: bool
    notes: str
    patient_count: int
    present_count: int
    absent_count: int


class CampaignPatientRowDTO(BaseModel):
    cp_id: str
    patient_id: str
    patient_number: str
    first_name: str
    last_name: str
    presence_status: str
    presence_label: str
    presence_color: str
    medical_status: str
    medical_status_label: str
    medical_status_color: str
    phone: str
    psc_notes: str
    enterprise_notes: str
    patient_message: str


class CampaignExamTypeDTO(BaseModel):
    id: str
    exam_type_ref_id: str
    exam_type_name: str
    category: str
    category_label: str


class PatientSearchOptionDTO(BaseModel):
    id: str
    label: str  # "DUPONT Jean (PAT-XXXX)"


class ExamTypeOptionDTO(BaseModel):
    id: str
    name: str
    category_label: str


class CampaignDetailState(ReflexMainState):
    campaign: CampaignDetailDTO | None = None
    patients: list[CampaignPatientRowDTO] = []
    exam_types: list[CampaignExamTypeDTO] = []
    is_loading: bool = False
    error: str = ""
    success: str = ""

    # Workflow action dialog (refuse reason)
    refuse_dialog_open: bool = False
    refuse_reason: str = ""
    refuse_error: str = ""

    # Add patient dialog
    add_patient_dialog_open: bool = False
    patient_search: str = ""
    patient_options: list[PatientSearchOptionDTO] = []
    # Multi-select : liste des IDs patients cochés
    selected_patient_ids: list[str] = []
    is_adding_patient: bool = False

    # Add exam type dialog
    add_exam_type_dialog_open: bool = False
    exam_type_options: list[ExamTypeOptionDTO] = []
    selected_exam_type_id: str = ""
    is_adding_exam_type: bool = False

    # PSC interpretation dialog
    psc_dialog_open: bool = False
    psc_dialog_patient_id: str = ""
    psc_dialog_patient_name: str = ""
    psc_notes_input: str = ""

    # Enterprise interpretation dialog
    enterprise_dialog_open: bool = False
    enterprise_dialog_patient_id: str = ""
    enterprise_dialog_patient_name: str = ""
    enterprise_notes_input: str = ""
    patient_message_input: str = ""

    # Edit campaign fields
    edit_dialog_open: bool = False
    edit_name: str = ""
    edit_start: str = ""
    edit_end: str = ""
    edit_location: str = ""
    edit_notes: str = ""
    edit_requires_medical_review: bool = False
    edit_psc_doctor_id: str = ""
    edit_enterprise_doctor_id: str = ""
    edit_psc_doctor_options: list[PatientSearchOptionDTO] = []  # reusing id/label shape
    edit_enterprise_doctor_options: list[PatientSearchOptionDTO] = []
    is_saving_edit: bool = False
    edit_error: str = ""

    # Confirm retrait patient
    confirm_remove_patient_open: bool = False
    confirm_remove_patient_id: str = ""
    confirm_remove_patient_name: str = ""

    # Confirm retrait type d'examen
    confirm_remove_exam_type_open: bool = False
    confirm_remove_exam_type_id: str = ""
    confirm_remove_exam_type_name: str = ""

    @rx.event
    async def on_load(self):
        await self._load_campaign()

    @rx.event
    def go_back(self):
        if self.campaign:
            return rx.redirect(f"/account/{self.campaign.account_id}")
        return rx.redirect("/campaigns")

    # ── Workflow actions ──────────────────────────────────────────────────

    @rx.event
    async def submit_campaign(self):
        await self._do_workflow_action("submit")

    @rx.event
    async def validate_ops(self):
        await self._do_workflow_action("validate_ops")

    @rx.event
    async def open_refuse_dialog(self):
        self.refuse_reason = ""
        self.refuse_error = ""
        self.refuse_dialog_open = True

    @rx.event
    def set_refuse_reason(self, v: str):
        self.refuse_reason = v

    @rx.event
    async def confirm_refuse_medical(self):
        if not self.refuse_reason.strip():
            self.refuse_error = "Le motif est obligatoire."
            return
        self.refuse_dialog_open = False
        await self._do_workflow_action("refuse_medical", reason=self.refuse_reason)

    @rx.event
    async def validate_medical(self):
        await self._do_workflow_action("validate_medical")

    @rx.event
    async def ready_for_convocations(self):
        await self._do_workflow_action("ready_for_convocations")

    @rx.event
    async def send_convocations(self):
        await self._do_workflow_action("send_convocations")

    @rx.event
    async def start_terrain(self):
        await self._do_workflow_action("start_terrain")

    @rx.event
    async def close_terrain(self):
        await self._do_workflow_action("close_terrain")

    @rx.event
    async def start_lab(self):
        await self._do_workflow_action("start_lab")

    @rx.event
    async def validate_lab_campaign(self):
        await self._do_workflow_action("validate_lab_campaign")

    @rx.event
    async def validate_psc_campaign(self):
        await self._do_workflow_action("validate_psc_campaign")

    @rx.event
    async def publish_campaign(self):
        await self._do_workflow_action("publish_campaign")

    @rx.event
    async def publish_to_patients(self):
        await self._do_workflow_action("publish_to_patients")

    @rx.event
    async def archive_campaign(self):
        await self._do_workflow_action("archive")

    # ── Presence tracking ───────────────────────────────────────────────

    @rx.event
    async def set_presence(self, patient_id: str, status: str):
        if not self.campaign:
            return
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.set_presence(self.campaign.id, patient_id, status)
            await self._load_patients()
        except Exception as e:
            self.error = str(e)

    # ── Validate lab for patient ─────────────────────────────────────────

    @rx.event
    async def validate_lab_patient(self, patient_id: str):
        if not self.campaign:
            return
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.validate_lab_patient(self.campaign.id, patient_id)
            await self._load_patients()
        except Exception as e:
            self.error = str(e)

    # ── PSC interpretation dialog ────────────────────────────────────────

    @rx.event
    def open_psc_dialog(self, patient_id: str, patient_name: str, current_notes: str):
        self.psc_dialog_patient_id = patient_id
        self.psc_dialog_patient_name = patient_name
        self.psc_notes_input = current_notes
        self.psc_dialog_open = True

    @rx.event
    def close_psc_dialog(self):
        self.psc_dialog_open = False

    @rx.event
    def set_psc_notes(self, v: str):
        self.psc_notes_input = v

    @rx.event
    async def save_psc_interpretation(self):
        if not self.campaign:
            return
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.add_psc_interpretation(
                    self.campaign.id, self.psc_dialog_patient_id, self.psc_notes_input
                )
            self.psc_dialog_open = False
            await self._load_patients()
        except Exception as e:
            self.error = str(e)

    @rx.event
    async def validate_psc_patient(self, patient_id: str):
        if not self.campaign:
            return
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.validate_psc_patient(self.campaign.id, patient_id)
            await self._load_patients()
        except Exception as e:
            self.error = str(e)

    # ── Enterprise interpretation dialog ─────────────────────────────────

    @rx.event
    def open_enterprise_dialog(
        self, patient_id: str, patient_name: str, current_notes: str, current_message: str
    ):
        self.enterprise_dialog_patient_id = patient_id
        self.enterprise_dialog_patient_name = patient_name
        self.enterprise_notes_input = current_notes
        self.patient_message_input = current_message
        self.enterprise_dialog_open = True

    @rx.event
    def close_enterprise_dialog(self):
        self.enterprise_dialog_open = False

    @rx.event
    def set_enterprise_notes(self, v: str):
        self.enterprise_notes_input = v

    @rx.event
    def set_patient_message(self, v: str):
        self.patient_message_input = v

    @rx.event
    async def save_enterprise_interpretation(self):
        if not self.campaign:
            return
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.add_enterprise_interpretation(
                    self.campaign.id,
                    self.enterprise_dialog_patient_id,
                    self.enterprise_notes_input,
                    self.patient_message_input,
                )
            self.enterprise_dialog_open = False
            await self._load_patients()
        except Exception as e:
            self.error = str(e)

    @rx.event
    async def validate_enterprise_patient(self, patient_id: str):
        if not self.campaign:
            return
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.validate_enterprise_patient(self.campaign.id, patient_id)
            await self._load_patients()
        except Exception as e:
            self.error = str(e)

    @rx.event
    async def publish_patient_results(self, patient_id: str):
        if not self.campaign:
            return
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.publish_patient_results(self.campaign.id, patient_id)
            await self._load_patients()
        except Exception as e:
            self.error = str(e)

    # ── Add patient dialog ───────────────────────────────────────────────

    @rx.event
    async def open_add_patient_dialog(self):
        self.patient_search = ""
        self.selected_patient_ids = []
        self.add_patient_dialog_open = True
        # Charger TOUS les patients affiliés au compte dès l'ouverture
        await self._load_patient_options("")

    @rx.event
    def close_add_patient_dialog(self):
        self.add_patient_dialog_open = False

    @rx.event
    async def search_patients(self, query: str):
        self.patient_search = query
        await self._load_patient_options(query)

    async def _load_patient_options(self, query: str):
        """Charge les patients du compte affilié, filtrés par query si fourni."""
        if not self.campaign:
            self.patient_options = []
            return
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_patient import CampaignPatient
                from gws_care.patient.patient import Patient
                from gws_care.patient_account.patient_account import PatientAccount, PatientAccountStatus

                # Patients déjà dans la campagne (à exclure)
                already_in = set(
                    str(cp.patient_id)
                    for cp in CampaignPatient.select(CampaignPatient.patient).where(
                        CampaignPatient.campaign == self.campaign.id
                    )
                )

                # Mécanisme 1 : Patient.billing_account FK directe
                ids_fk = set(
                    str(p.id)
                    for p in Patient.select(Patient.id)
                    .where(Patient.billing_account == self.campaign.account_id)
                )

                # Mécanisme 2 : PatientAccount M2M actif
                ids_m2m = set(
                    str(pa.patient_id)
                    for pa in PatientAccount.select(PatientAccount.patient).where(
                        (PatientAccount.account == self.campaign.account_id)
                        & (PatientAccount.status == PatientAccountStatus.ACTIVE.value)
                    )
                )

                # Mécanisme 3 : patients liés par company_id via existing patients
                ids_company: set[str] = set()
                try:
                    from gws_care.patient.patient import Patient as _Patient
                    from gws_care.company.company_service import CompanyService
                    from gws_care.company.company import Company
                    from gws_care.account.account import Account as _Account
                    # a) via patients déjà liés à ce compte avec un company_id
                    company_id = CompanyService.get_company_id_for_account(self.campaign.account_id)
                    # b) fallback : trouver une Company dont le nom correspond au compte
                    if not company_id:
                        acct = _Account.get_or_none(_Account.id == self.campaign.account_id)
                        if acct:
                            comp = Company.get_or_none(Company.name == acct.name)
                            if comp:
                                company_id = str(comp.id)
                    if company_id:
                        ids_company = set(
                            str(p.id)
                            for p in _Patient.select(_Patient.id)
                            .where(_Patient.company_id == company_id)
                        )
                except Exception:
                    pass

                candidate_ids = (ids_fk | ids_m2m | ids_company) - already_in

                if not candidate_ids:
                    self.patient_options = []
                    return

                base_q = Patient.select().where(Patient.id.in_(list(candidate_ids)))
                if query and len(query) >= 2:
                    base_q = base_q.where(
                        Patient.last_name.contains(query)
                        | Patient.first_name.contains(query)
                        | Patient.patient_number.contains(query)
                    )
                base_q = base_q.order_by(Patient.last_name, Patient.first_name).limit(50)

                self.patient_options = [
                    PatientSearchOptionDTO(
                        id=str(p.id),
                        label=f"{p.last_name} {p.first_name} ({p.patient_number})",
                    )
                    for p in base_q
                ]
        except Exception:
            self.patient_options = []

    @rx.event
    def toggle_patient_selection(self, patient_id: str):
        """Ajouter/retirer un patient de la sélection."""
        if patient_id in self.selected_patient_ids:
            self.selected_patient_ids = [p for p in self.selected_patient_ids if p != patient_id]
        else:
            self.selected_patient_ids = self.selected_patient_ids + [patient_id]

    @rx.event
    async def confirm_add_patient(self):
        if not self.selected_patient_ids or not self.campaign:
            return
        self.is_adding_patient = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                for pid in self.selected_patient_ids:
                    try:
                        CampaignService.add_patient(self.campaign.id, pid)
                    except Exception:
                        pass
            self.add_patient_dialog_open = False
            await self._load_campaign()
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_adding_patient = False

    @rx.event
    def open_confirm_remove_patient(self, patient_id: str, patient_name: str):
        self.confirm_remove_patient_id = patient_id
        self.confirm_remove_patient_name = patient_name
        self.confirm_remove_patient_open = True

    @rx.event
    def dismiss_confirm_remove_patient(self):
        self.confirm_remove_patient_open = False
        self.confirm_remove_patient_id = ""
        self.confirm_remove_patient_name = ""

    @rx.event
    async def confirmed_remove_patient(self):
        patient_id = self.confirm_remove_patient_id
        self.confirm_remove_patient_open = False
        self.confirm_remove_patient_id = ""
        self.confirm_remove_patient_name = ""
        if not self.campaign:
            return
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.remove_patient(self.campaign.id, patient_id)
            await self._load_patients()
        except Exception as e:
            self.error = str(e)

    @rx.event
    async def remove_patient(self, patient_id: str):
        """Kept for backward compat — prefer confirmed_remove_patient."""
        if not self.campaign:
            return
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.remove_patient(self.campaign.id, patient_id)
            await self._load_patients()
        except Exception as e:
            self.error = str(e)

    # ── Add exam type dialog ─────────────────────────────────────────────

    @rx.event
    async def open_add_exam_type_dialog(self):
        self.selected_exam_type_id = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                refs = ExamTypeRefService.list_all(active_only=True)
                self.exam_type_options = [
                    ExamTypeOptionDTO(
                        id=r.id, name=r.name, category_label=r.category_label
                    )
                    for r in refs
                ]
        except Exception:
            self.exam_type_options = []
        self.add_exam_type_dialog_open = True

    @rx.event
    def close_add_exam_type_dialog(self):
        self.add_exam_type_dialog_open = False

    @rx.event
    def set_selected_exam_type(self, v: str):
        self.selected_exam_type_id = v

    @rx.event
    async def confirm_add_exam_type(self):
        if not self.selected_exam_type_id or not self.campaign:
            return
        self.is_adding_exam_type = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_exam import CampaignExam
                if CampaignExam.select().where(
                    (CampaignExam.campaign == self.campaign.id)
                    & (CampaignExam.exam_type_ref == self.selected_exam_type_id)
                ).exists():
                    raise ValueError("Ce type d'examen est déjà configuré pour cette campagne.")
                ce = CampaignExam()
                ce.campaign_id = self.campaign.id
                ce.exam_type_ref_id = self.selected_exam_type_id
                ce.save()
            self.add_exam_type_dialog_open = False
            await self._load_exam_types()
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_adding_exam_type = False

    @rx.event
    def open_confirm_remove_exam_type(self, exam_id: str, exam_name: str):
        self.confirm_remove_exam_type_id = exam_id
        self.confirm_remove_exam_type_name = exam_name
        self.confirm_remove_exam_type_open = True

    @rx.event
    def dismiss_confirm_remove_exam_type(self):
        self.confirm_remove_exam_type_open = False
        self.confirm_remove_exam_type_id = ""
        self.confirm_remove_exam_type_name = ""

    @rx.event
    async def confirmed_remove_exam_type(self):
        exam_id = self.confirm_remove_exam_type_id
        self.confirm_remove_exam_type_open = False
        self.confirm_remove_exam_type_id = ""
        self.confirm_remove_exam_type_name = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_exam import CampaignExam
                CampaignExam.delete().where(CampaignExam.id == exam_id).execute()
            await self._load_exam_types()
        except Exception as e:
            self.error = str(e)

    @rx.event
    async def remove_exam_type(self, campaign_exam_id: str):
        """Kept for backward compat — prefer confirmed_remove_exam_type."""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_exam import CampaignExam
                CampaignExam.delete().where(CampaignExam.id == campaign_exam_id).execute()
            await self._load_exam_types()
        except Exception as e:
            self.error = str(e)

    # ── Edit campaign ────────────────────────────────────────────────────

    @rx.event
    async def open_edit_dialog(self):
        if not self.campaign:
            return
        self.edit_name = self.campaign.name
        self.edit_start = self.campaign.start_date
        self.edit_end = self.campaign.end_date
        self.edit_location = self.campaign.location
        self.edit_notes = self.campaign.notes
        self.edit_requires_medical_review = self.campaign.requires_medical_review
        self.edit_psc_doctor_id = ""
        self.edit_enterprise_doctor_id = ""
        self.edit_error = ""
        self.edit_dialog_open = True
        # Load doctor options
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_care_role import UserCareRole
                from gws_care.user.user import User

                psc = list(
                    UserCareRole.select(UserCareRole, User).join(User)
                    .where(UserCareRole.role == CareRole.MEDECIN_PSC.value)
                    .order_by(User.last_name)
                )
                self.edit_psc_doctor_options = [
                    PatientSearchOptionDTO(id=str(r.user.id), label=f"{r.user.last_name} {r.user.first_name}")
                    for r in psc
                ]
                ent = list(
                    UserCareRole.select(UserCareRole, User).join(User)
                    .where(UserCareRole.role == CareRole.MEDECIN_ENTREPRISE.value)
                    .order_by(User.last_name)
                )
                self.edit_enterprise_doctor_options = [
                    PatientSearchOptionDTO(id=str(r.user.id), label=f"{r.user.last_name} {r.user.first_name}")
                    for r in ent
                ]
        except Exception:
            pass

    @rx.event
    def close_edit_dialog(self):
        self.edit_dialog_open = False

    @rx.event
    def set_edit_name(self, v: str):
        self.edit_name = v

    @rx.event
    def set_edit_start(self, v: str):
        self.edit_start = v

    @rx.event
    def set_edit_end(self, v: str):
        self.edit_end = v

    @rx.event
    def set_edit_location(self, v: str):
        self.edit_location = v

    @rx.event
    def set_edit_notes(self, v: str):
        self.edit_notes = v

    @rx.event
    def set_edit_requires_medical_review(self, v: bool):
        self.edit_requires_medical_review = v

    @rx.event
    def set_edit_psc_doctor(self, v: str):
        self.edit_psc_doctor_id = v

    @rx.event
    def set_edit_enterprise_doctor(self, v: str):
        self.edit_enterprise_doctor_id = v

    @rx.event
    async def save_edit(self):
        if not self.campaign:
            return
        self.is_saving_edit = True
        self.edit_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                start = date.fromisoformat(self.edit_start) if self.edit_start else None
                end = date.fromisoformat(self.edit_end) if self.edit_end else None
                CampaignService.update_campaign(
                    campaign_id=self.campaign.id,
                    name=self.edit_name,
                    start_date=start,
                    end_date=end,
                    location=self.edit_location,
                    requires_medical_review=self.edit_requires_medical_review,
                    notes=self.edit_notes,
                    psc_doctor_id=self.edit_psc_doctor_id or None,
                    enterprise_doctor_id=self.edit_enterprise_doctor_id or None,
                )
            self.edit_dialog_open = False
            await self._load_campaign()
        except Exception as e:
            self.edit_error = str(e)
        finally:
            self.is_saving_edit = False

    # ── Clear messages ───────────────────────────────────────────────────

    @rx.event
    def dismiss_error(self):
        self.error = ""

    @rx.event
    def dismiss_success(self):
        self.success = ""

    # ── CSV Export ───────────────────────────────────────────────────────

    @rx.event
    async def export_patients_csv(self):
        """Generate and download a CSV of all enrolled patients with their status."""
        import io
        import csv

        if not self.campaign:
            return

        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";")
        writer.writerow([
            "N° Dossier", "Nom", "Prénom", "Téléphone",
            "Présence", "Statut médical", "Notes PSC", "Notes Entreprise", "Message patient",
        ])
        for p in self.patients:
            writer.writerow([
                p.patient_number,
                p.last_name,
                p.first_name,
                p.phone,
                p.presence_label,
                p.medical_status_label,
                p.psc_notes,
                p.enterprise_notes,
                p.patient_message,
            ])

        csv_bytes = buffer.getvalue().encode("utf-8-sig")
        filename = f"campagne_{self.campaign.name.replace(' ', '_')}_patients.csv"
        return rx.download(data=csv_bytes, filename=filename)

    # ── Internal loaders ─────────────────────────────────────────────────

    async def _do_workflow_action(self, action: str, **kwargs):
        if not self.campaign:
            return
        self.is_loading = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                fn = getattr(CampaignService, action)
                fn(self.campaign.id, **kwargs)

                # Notifications automatiques après envoi convocations
                if action == "send_convocations":
                    try:
                        from gws_care.campaign.campaign_patient import CampaignPatient
                        from gws_care.patient.patient import Patient
                        from gws_care.notification.notification_service import NotificationService
                        camp_name = self.campaign.name
                        start = self.campaign.start_date or ""
                        location = self.campaign.location or "à définir"
                        for cp in CampaignPatient.select(CampaignPatient, Patient).join(Patient).where(
                            CampaignPatient.campaign == self.campaign.id
                        ):
                            pat = cp.patient
                            if pat.email:
                                try:
                                    NotificationService._dispatch(
                                        "EMAIL",
                                        to_email=pat.email,
                                        to_phone=pat.phone,
                                        to_name=f"{pat.last_name} {pat.first_name}",
                                        subject=f"[Care] Convocation – {camp_name}",
                                        body=(
                                            f"Bonjour {pat.first_name} {pat.last_name},\n\n"
                                            f"Vous êtes convoqué(e) à la campagne de santé « {camp_name} ».\n"
                                            f"Date : {start}\n"
                                            f"Lieu : {location}\n\n"
                                            f"Merci de vous présenter muni(e) de votre convocation.\n\n"
                                            f"Cordialement,\nPSC Care"
                                        ),
                                    )
                                except Exception:
                                    pass
                    except Exception:
                        pass  # notifications non bloquantes

            await self._load_campaign()
            self.success = "Statut mis à jour avec succès."
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading = False

    async def _load_campaign(self):
        if not await self.check_authentication():
            return
        campaign_id = self.campaign_id_param
        if not campaign_id:
            self.error = "Identifiant campagne manquant dans l'URL."
            return
        self.is_loading = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_patient import CampaignPatient, PresenceStatus
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.campaign.campaign_status import CampaignStatus
                c = CampaignService.get_campaign(campaign_id)
                total = CampaignPatient.select().where(CampaignPatient.campaign == campaign_id).count()
                present = CampaignPatient.select().where(
                    (CampaignPatient.campaign == campaign_id)
                    & (CampaignPatient.presence_status == PresenceStatus.PRESENT.value)
                ).count()
                absent = CampaignPatient.select().where(
                    (CampaignPatient.campaign == campaign_id)
                    & (CampaignPatient.presence_status == PresenceStatus.ABSENT.value)
                ).count()
                try:
                    status_e = CampaignStatus(c.status)
                except ValueError:
                    status_e = CampaignStatus.DRAFT
                psc_name = ""
                if c.psc_doctor_id:
                    try:
                        psc_name = f"{c.psc_doctor.first_name} {c.psc_doctor.last_name}"
                    except Exception:
                        pass
                ent_name = ""
                if c.enterprise_doctor_id:
                    try:
                        ent_name = f"{c.enterprise_doctor.first_name} {c.enterprise_doctor.last_name}"
                    except Exception:
                        pass
                self.campaign = CampaignDetailDTO(
                    id=str(c.id),
                    name=c.name,
                    account_id=str(c.account_id),
                    account_name=c.account.name if c.account_id else "",
                    status=c.status,
                    status_label=status_e.get_label(),
                    status_color=status_e.get_color(),
                    start_date=c.start_date.isoformat() if c.start_date else "",
                    end_date=c.end_date.isoformat() if c.end_date else "",
                    location=c.location or "",
                    psc_doctor_name=psc_name,
                    enterprise_doctor_name=ent_name,
                    requires_medical_review=c.requires_medical_review,
                    notes=c.notes or "",
                    patient_count=total,
                    present_count=present,
                    absent_count=absent,
                )
            await self._load_patients()
            await self._load_exam_types()
        except Exception as e:
            self.error = f"Erreur de chargement : {e}"
        finally:
            self.is_loading = False

    async def _load_patients(self):
        if not self.campaign:
            return
        with await self.authenticate_user():
            from gws_care.campaign.campaign_patient import CampaignPatient, MedicalRecordStatus, PresenceStatus
            from gws_care.patient.patient import Patient
            rows = (
                CampaignPatient.select(CampaignPatient, Patient)
                .join(Patient)
                .where(CampaignPatient.campaign == self.campaign.id)
                .order_by(Patient.last_name)
            )
            result = []
            for cp in rows:
                try:
                    ps = PresenceStatus(cp.presence_status)
                except ValueError:
                    ps = PresenceStatus.PENDING
                try:
                    ms = MedicalRecordStatus(cp.medical_status)
                except ValueError:
                    ms = MedicalRecordStatus.PENDING
                result.append(CampaignPatientRowDTO(
                    cp_id=str(cp.id),
                    patient_id=str(cp.patient.id),
                    patient_number=cp.patient.patient_number,
                    first_name=cp.patient.first_name,
                    last_name=cp.patient.last_name,
                    presence_status=cp.presence_status,
                    presence_label=ps.get_label(),
                    presence_color=ps.get_color(),
                    medical_status=cp.medical_status,
                    medical_status_label=ms.get_label(),
                    medical_status_color=ms.get_color(),
                    phone=cp.patient.phone or "",
                    psc_notes=cp.psc_notes or "",
                    enterprise_notes=cp.enterprise_notes or "",
                    patient_message=cp.patient_message or "",
                ))
            self.patients = result

    async def _load_exam_types(self):
        if not self.campaign:
            return
        with await self.authenticate_user():
            from gws_care.campaign.campaign_exam import CampaignExam
            from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
            rows = (
                CampaignExam.select(CampaignExam, ExamTypeRef)
                .join(ExamTypeRef)
                .where(CampaignExam.campaign == self.campaign.id)
            )
            self.exam_types = [
                CampaignExamTypeDTO(
                    id=str(ce.id),
                    exam_type_ref_id=str(ce.exam_type_ref.id),
                    exam_type_name=ce.exam_type_ref.name,
                    category=ce.exam_type_ref.category,
                    category_label=ce.exam_type_ref.get_category_label(),
                )
                for ce in rows
            ]
