"""State for the campaign patient exam results entry page.

Route: /campaign-patient/[cp_campaign_id]/[cp_patient_id]

Workflow:
  1. Page loads → shows all exam types of the campaign as sections
  2. User clicks a section → active_params populated with that section's parameters
  3. User enters values → set_param_value updates active_params in real time
  4. User clicks "Enregistrer" → save_active_section persists to Exam.lab_results (JSON)
  5. All sections saved → user clicks "Transmettre au médecin PSC"
     → CampaignPatient.medical_status = LAB_ENTERED
"""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class ExamParamEntry(BaseModel):
    """One parameter row in the result entry form."""

    param_id: str
    name: str
    unit: str
    ref_range: str       # "4.0 – 10.0" or "" if not defined
    critical_range: str  # "2.0 / 15.0" or "" if not defined
    is_required: bool
    value_type: str      # NUMERIC | TEXT | CHOICE | FILE
    value: str = ""
    # Raw float strings for colour-coding (empty = threshold not defined)
    ref_low_raw: str = ""
    ref_high_raw: str = ""
    critical_low_raw: str = ""
    critical_high_raw: str = ""
    # Computed status: "" | "normal" | "low" | "high" | "critical_low" | "critical_high"
    value_status: str = ""
    # Whether this param is included in the saved results (default True = all selected)
    is_selected: bool = True


def _compute_param_status(
    value: str,
    ref_low: str,
    ref_high: str,
    critical_low: str,
    critical_high: str,
) -> str:
    """Compute colour-coding status for a numeric parameter value."""
    if not value.strip():
        return ""
    try:
        v = float(value.replace(",", "."))
        cl = float(critical_low) if critical_low != "" else None
        ch = float(critical_high) if critical_high != "" else None
        rl = float(ref_low) if ref_low != "" else None
        rh = float(ref_high) if ref_high != "" else None
        if cl is not None and v < cl:
            return "critical_low"
        if ch is not None and v > ch:
            return "critical_high"
        if rl is not None and v < rl:
            return "low"
        if rh is not None and v > rh:
            return "high"
        if rl is not None or rh is not None:
            return "normal"
        return ""
    except Exception as exc:
        return ""


class SectionFileVM(BaseModel):
    """A file attached to a saved exam section."""

    file_id: str
    name: str
    size_label: str
    download_url: str
    mime_type: str = ""


class ExamSectionVM(BaseModel):
    """One exam type card in the results entry page."""

    exam_type_ref_id: str
    name: str
    category_label: str
    param_count: int = 0
    is_saved: bool = False
    is_transmitted: bool = False   # True once results have been sent to the doctor
    saved_exam_id: str = ""
    allows_attachment: bool = True


class CampaignPatientExamsState(ReflexMainState):
    """State for per-patient exam result entry within a campaign."""

    # Context
    campaign_name: str = ""
    patient_name: str = ""
    patient_number: str = ""
    medical_status: str = "PENDING"

    # All exam type sections of the campaign
    sections: list[ExamSectionVM] = []

    # Currently active section
    active_section_id: str = ""
    active_section_name: str = ""
    active_section_is_saved: bool = False
    active_section_is_transmitted: bool = False   # True if section was already transmitted
    active_params: list[ExamParamEntry] = []

    # UI state
    is_loading: bool = False
    is_saving: bool = False
    error: str = ""
    success: str = ""

    # File attachments for the active section
    section_attached_files: list[SectionFileVM] = []
    is_uploading_file: bool = False

    # Track whether any section has been saved (to gate the global transmit button)
    has_saved_sections: bool = False

    # PSC doctor interpretation
    psc_notes: str = ""
    # Enterprise doctor interpretation
    enterprise_notes: str = ""
    enterprise_patient_message: str = ""

    # Role of the current viewer (set on load)
    viewer_is_psc: bool = False
    viewer_is_enterprise: bool = False

    # ── Load ──────────────────────────────────────────────────────────────

    @rx.event
    async def on_load(self):
        await self._load()

    # ── Navigation ────────────────────────────────────────────────────────

    @rx.event
    def go_back(self):
        return rx.redirect(f"/campaign/{self.cp_campaign_id}")

    # ── Section selection ─────────────────────────────────────────────────

    @rx.event
    async def set_active_section(self, section_id: str):
        """Switch to a different exam type section."""
        if section_id == self.active_section_id:
            return
        self.active_section_id = section_id
        sec = next((s for s in self.sections if s.exam_type_ref_id == section_id), None)
        self.active_section_name = sec.name if sec else ""
        self.active_section_is_saved = sec.is_saved if sec else False
        self.active_section_is_transmitted = sec.is_transmitted if sec else False
        await self._load_active_params(section_id)
        await self._load_section_files()

    # ── Value entry ───────────────────────────────────────────────────────

    @rx.event
    def set_param_value(self, param_id: str, value: str):
        """Update the value of one parameter in the active section."""
        updated = []
        for p in self.active_params:
            if p.param_id == param_id:
                status = (
                    _compute_param_status(
                        value, p.ref_low_raw, p.ref_high_raw,
                        p.critical_low_raw, p.critical_high_raw,
                    )
                    if p.value_type == "NUMERIC"
                    else ""
                )
                updated.append(ExamParamEntry(**{**p.dict(), "value": value, "value_status": status}))
            else:
                updated.append(p)
        self.active_params = updated

    @rx.event
    def toggle_param_selection(self, param_id: str):
        """Toggle whether a parameter is included in the saved results."""
        self.active_params = [
            ExamParamEntry(**{**p.model_dump(), "is_selected": not p.is_selected})
            if p.param_id == param_id else p
            for p in self.active_params
        ]

    @rx.event
    def select_all_params(self):
        """Mark all parameters as selected."""
        self.active_params = [
            ExamParamEntry(**{**p.model_dump(), "is_selected": True})
            for p in self.active_params
        ]

    @rx.event
    def deselect_all_params(self):
        """Mark all non-required parameters as deselected."""
        self.active_params = [
            ExamParamEntry(**{**p.model_dump(), "is_selected": p.is_required})
            for p in self.active_params
        ]

    # ── Save section ──────────────────────────────────────────────────────

    @rx.event
    async def save_active_section(self):
        """Persist the active section's results as an Exam record (lab_results JSON)."""
        section_id = self.active_section_id
        section_name = self.active_section_name
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id

        if not section_id or not campaign_id or not patient_id:
            return

        self.is_saving = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from datetime import date

                from gws_care.campaign.campaign import Campaign
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamStatus, ExamType
                from gws_care.patient.patient import Patient

                lab_results = [
                    {
                        "parameter": p.name,
                        "value": p.value,
                        "unit": p.unit,
                        "reference_range": p.ref_range,
                        "status": _compute_param_status(
                            p.value, p.ref_low_raw, p.ref_high_raw,
                            p.critical_low_raw, p.critical_high_raw,
                        ) if p.value_type == "NUMERIC" else ("normal" if p.value else ""),
                    }
                    for p in self.active_params
                    if p.is_selected   # only save params that are selected
                ]

                # Marker in reason_for_visit to identify this exam uniquely
                marker = f"CAMP:{campaign_id}|REF:{section_id}"

                existing = Exam.get_or_none(
                    (Exam.patient == patient_id)
                    & Exam.reason_for_visit.startswith(marker)
                )

                if existing:
                    existing.lab_results = lab_results
                    existing.save()
                    exam_id = str(existing.id)
                else:
                    patient = Patient.get_by_id_and_check(patient_id)
                    campaign = Campaign.get_by_id_and_check(campaign_id)
                    e = Exam()
                    e.patient = patient
                    e.billing_account_id = campaign.account_id
                    e.exam_date = date.today()
                    e.exam_type = ExamType.OTHER
                    e.exam_type_ref_id = section_id   # link to ExamTypeRef for label resolution
                    e.status = ExamStatus.DRAFT
                    e.reason_for_visit = f"{marker}|{section_name}"
                    e.lab_results = lab_results
                    e.save()
                    exam_id = str(e.id)

                # Update section status
                self.sections = [
                    ExamSectionVM(
                        **{**s.dict(), "is_saved": True, "saved_exam_id": exam_id}
                    )
                    if s.exam_type_ref_id == section_id
                    else s
                    for s in self.sections
                ]
                self.active_section_is_saved = True
                self.has_saved_sections = True
                self.success = f'Résultats "{section_name}" enregistrés ✓'
                await self._load_section_files()
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving = False

    # ── Internal helpers ─────────────────────────────────────────────────

    def _mark_campaign_exams_pending(
        self, campaign_id: str, patient_id: str, marker_prefix: str
    ) -> None:
        """Set matching DRAFT campaign exams to PENDING status."""
        from gws_care.exam.exam import Exam
        from gws_care.exam.exam_type import ExamStatus
        for exam in list(
            Exam.select().where(
                Exam.patient == patient_id,
                Exam.reason_for_visit % f"CAMP:{campaign_id}|%",
            )
        ):
            rv = exam.reason_for_visit or ""
            if rv.startswith(marker_prefix) and exam.status == ExamStatus.DRAFT:
                exam.status = ExamStatus.PENDING
                exam.save()

    # ── Transmit section ─────────────────────────────────────────────────

    @rx.event
    async def transmit_section(self, section_id: str):
        """Mark a specific section's exam as submitted — transitions patient to LAB_ENTERED."""
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id
        self.is_saving = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService

                # Move this section's draft exam to PENDING
                marker = f"CAMP:{campaign_id}|REF:{section_id}"
                self._mark_campaign_exams_pending(campaign_id, patient_id, marker)

                # Mark campaign patient as LAB_ENTERED if not already further along
                CampaignService.mark_lab_entered(campaign_id, patient_id)

            self.medical_status = "LAB_ENTERED"
            # Mark this section as transmitted in local state
            self.sections = [
                ExamSectionVM(**{**s.dict(), "is_transmitted": True})
                if s.exam_type_ref_id == section_id
                else s
                for s in self.sections
            ]
            if self.active_section_id == section_id:
                self.active_section_is_transmitted = True
            sec = next((s for s in self.sections if s.exam_type_ref_id == section_id), None)
            section_name = sec.name if sec else "cet examen"
            self.success = f'Résultats "{section_name}" transmis au médecin PSC.'
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving = False

    # ── Transmit to doctor ───────────────────────────────────────────────

    @rx.event
    async def transmit_to_doctor(self):
        """Mark patient results as submitted — transitions to LAB_ENTERED."""
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id
        self.is_saving = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamStatus

                # Move all draft campaign exams for this patient to PENDING
                marker_prefix = f"CAMP:{campaign_id}|"
                self._mark_campaign_exams_pending(campaign_id, patient_id, marker_prefix)

            self.medical_status = "LAB_ENTERED"
            self.success = "Résultats transmis au médecin PSC. Le dossier passe en « Résultats saisis »."

            # Notification au médecin PSC
            try:
                with await self.authenticate_user():
                    from gws_care.campaign.campaign import Campaign
                    from gws_care.notification.notification_service import NotificationService
                    camp = Campaign.get_by_id(campaign_id)
                    if camp and camp.psc_doctor_id:
                        try:
                            psc_user = camp.psc_doctor
                            patient_lbl = self.patient_name
                            camp_lbl = self.campaign_name
                            NotificationService._dispatch(
                                "EMAIL",
                                to_email=getattr(psc_user, "email", None),
                                to_phone=None,
                                to_name=f"{getattr(psc_user, 'first_name', '')} {getattr(psc_user, 'last_name', '')}".strip(),
                                subject=f"[Care] Résultats disponibles – {patient_lbl}",
                                body=(
                                    f"Bonjour,\n\n"
                                    f"Les résultats de laboratoire du patient {patient_lbl} "
                                    f"(campagne : {camp_lbl}) ont été saisis et sont disponibles pour interprétation.\n\n"
                                    f"Connectez-vous sur la plateforme PSC Care pour accéder au dossier.\n\n"
                                    f"Cordialement,\nPSC Care"
                                ),
                            )
                        except Exception as exc:
                            pass  # notification non bloquante
            except Exception as exc:
                pass
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving = False

    # ── File attachments ──────────────────────────────────────────────────

    @rx.event
    async def handle_section_file_upload(self, files: list[rx.UploadFile]):
        """Upload files and attach them to the active section's saved exam."""
        import mimetypes

        sec = next((s for s in self.sections if s.exam_type_ref_id == self.active_section_id), None)
        if not sec or not sec.saved_exam_id:
            yield rx.toast.error("Enregistrez d'abord les résultats avant d'ajouter des documents.")
            return

        self.is_uploading_file = True
        yield

        try:
            uploads: list[tuple[str, bytes, str]] = []
            for uf in files:
                data = await uf.read()
                mime = mimetypes.guess_type(uf.filename or "")[0] or "application/octet-stream"
                uploads.append((uf.filename or "fichier", data, mime))

            with await self.authenticate_user():
                from gws_care.exam.exam_file_service import ExamFileService
                for original_name, file_bytes, mime in uploads:
                    ExamFileService.create_file(
                        exam_id=sec.saved_exam_id,
                        original_name=original_name,
                        file_bytes=file_bytes,
                        mime_type=mime,
                    )

            await self._load_section_files()
            yield rx.toast.success(f"{len(uploads)} document(s) joint(s).")
        except Exception as e:
            yield rx.toast.error(f"Erreur d'upload : {e}")
        finally:
            self.is_uploading_file = False

    @rx.event
    async def delete_section_file(self, file_id: str):
        """Delete an attached file from the active section."""
        try:
            from gws_care.exam.exam_file_service import ExamFileService
            ExamFileService.delete_file(file_id)
            await self._load_section_files()
        except Exception as e:
            self.error = str(e)

    async def _load_section_files(self):
        """Load attached files for the currently active (saved) section."""
        sec = next((s for s in self.sections if s.exam_type_ref_id == self.active_section_id), None)
        if not sec or not sec.saved_exam_id:
            self.section_attached_files = []
            return
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam_file_service import ExamFileService
                files = ExamFileService.list_files_for_exam(sec.saved_exam_id)
                result = []
                for f in files:
                    size_kb = (f.file_size or 0) / 1024
                    size_label = f"{size_kb:.0f} Ko" if size_kb < 1024 else f"{size_kb/1024:.1f} Mo"
                    dl_url = ExamFileService.get_resource_download_url(f.resource_id) if f.resource_id else ""
                    result.append(SectionFileVM(
                        file_id=str(f.id),
                        name=f.original_name or "fichier",
                        size_label=size_label,
                        download_url=dl_url,
                        mime_type=f.mime_type or "",
                    ))
                self.section_attached_files = result
        except Exception as exc:
            self.section_attached_files = []

    @rx.event
    def dismiss_messages(self):
        self.error = ""
        self.success = ""

    # ── PSC doctor interpretation ─────────────────────────────────────────

    @rx.event
    def set_psc_notes(self, value: str):
        self.psc_notes = value

    @rx.event
    async def validate_and_send_to_enterprise(self):
        """PSC doctor: save interpretation + validate + notify enterprise doctor."""
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id
        self.is_saving = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.add_psc_interpretation(campaign_id, patient_id, self.psc_notes)
                CampaignService.validate_psc_patient(campaign_id, patient_id)
            self.medical_status = "PSC_VALIDATED"
            self.success = "Interprétation PSC validée. Dossier transmis au médecin entreprise."

            # Notify enterprise doctor
            try:
                with await self.authenticate_user():
                    from gws_care.campaign.campaign import Campaign
                    from gws_care.notification.notification_service import NotificationService
                    camp = Campaign.get_by_id(campaign_id)
                    if camp and camp.enterprise_doctor_id:
                        doc = camp.enterprise_doctor
                        NotificationService._dispatch(
                            "EMAIL",
                            to_email=getattr(doc, "email", None),
                            to_phone=None,
                            to_name=f"{getattr(doc, 'first_name', '')} {getattr(doc, 'last_name', '')}".strip(),
                            subject=f"[Care] Dossier validé PSC – {self.patient_name}",
                            body=(
                                f"Bonjour,\n\nLe dossier du patient {self.patient_name} "
                                f"a été validé par le médecin PSC dans la campagne « {self.campaign_name} ».\n"
                                "Vous pouvez maintenant ajouter votre interprétation.\n\nCordialement,\nConstellab Care"
                            ),
                        )
            except Exception as exc:
                pass
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving = False

    # ── Enterprise doctor interpretation ──────────────────────────────────

    @rx.event
    def set_enterprise_notes(self, value: str):
        self.enterprise_notes = value
        self.enterprise_patient_message = value

    @rx.event
    async def validate_enterprise(self):
        """Enterprise doctor: save interpretation + validate."""
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id
        if not self.enterprise_notes.strip():
            self.error = "L'interprétation est obligatoire avant validation."
            return
        self.is_saving = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.add_enterprise_interpretation(
                    campaign_id, patient_id,
                    self.enterprise_notes,
                    self.enterprise_notes,
                )
                CampaignService.validate_enterprise_patient(campaign_id, patient_id)
            self.medical_status = "ENTERPRISE_VALIDATED"
            self.success = "Interprétation entreprise validée."
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving = False

    # ── Internals ─────────────────────────────────────────────────────────

    async def _load(self):
        if not await self.check_authentication():
            return
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id
        if not campaign_id or not patient_id:
            self.error = "Paramètres manquants dans l'URL."
            return
        self.is_loading = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign import Campaign
                from gws_care.campaign.campaign_exam import CampaignExam
                from gws_care.campaign.campaign_patient import CampaignPatient
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamStatus
                from gws_care.exam_type_ref.exam_parameter import ExamParameter
                from gws_care.patient.patient import Patient

                campaign = Campaign.get_by_id_and_check(campaign_id)
                self.campaign_name = campaign.name

                patient = Patient.get_by_id_and_check(patient_id)
                self.patient_name = f"{patient.last_name} {patient.first_name}"
                self.patient_number = patient.patient_number

                cp = CampaignPatient.get_or_none(
                    (CampaignPatient.campaign == campaign_id)
                    & (CampaignPatient.patient == patient_id)
                )
                self.medical_status = cp.medical_status if cp else "PENDING"
                self.psc_notes = (cp.psc_notes or "") if cp else ""
                self.enterprise_notes = (cp.enterprise_notes or "") if cp else ""
                self.enterprise_patient_message = (cp.enterprise_notes or "") if cp else ""

                # Detect viewer role
                from gws_care.role.user_role_service import UserRoleService
                from gws_care.role.care_role import CareRole as _CareRole
                with await self.authenticate_user() as auth_user:
                    roles = UserRoleService.get_roles_for_user(str(auth_user.id))
                    role_vals = [r.value for r in roles]
                self.viewer_is_psc = (
                    _CareRole.MEDECIN_PSC.value in role_vals
                    or _CareRole.SUPER_ADMIN_PSC.value in role_vals
                    or _CareRole.ADMIN_PSC.value in role_vals
                    or _CareRole.DIRECTEUR_PSC.value in role_vals
                    or len(role_vals) == 0  # no role → show all (dev mode)
                )
                self.viewer_is_enterprise = (
                    _CareRole.MEDECIN_ENTREPRISE.value in role_vals
                    or _CareRole.SUPER_ADMIN_PSC.value in role_vals
                    or _CareRole.ADMIN_PSC.value in role_vals
                    or _CareRole.DIRECTEUR_PSC.value in role_vals
                    or len(role_vals) == 0
                )

                # Index existing saved exams {marker → (exam_id, is_transmitted)}
                # is_transmitted = exam.status == PENDING (was submitted)
                marker_prefix = f"CAMP:{campaign_id}|"
                existing_map: dict[str, tuple[str, bool]] = {}
                for exam in Exam.select().where(Exam.patient == patient_id):
                    rv = exam.reason_for_visit or ""
                    if rv.startswith(marker_prefix):
                        is_tx = exam.status == ExamStatus.PENDING
                        existing_map[rv] = (str(exam.id), is_tx)

                from peewee import fn

                campaign_exams = list(
                    CampaignExam.select()
                    .where(CampaignExam.campaign == campaign_id)
                    .order_by(CampaignExam.id)
                )

                # Pre-aggregate ExamParameter counts by ref_id (one GROUP BY query)
                ce_ref_ids = [str(ce.exam_type_ref_id) for ce in campaign_exams]
                param_counts: dict[str, int] = {}
                if ce_ref_ids:
                    for row in (
                        ExamParameter.select(
                            ExamParameter.exam_type_ref,
                            fn.COUNT(ExamParameter.id).alias("cnt"),
                        )
                        .where(ExamParameter.exam_type_ref.in_(ce_ref_ids))
                        .group_by(ExamParameter.exam_type_ref)
                        .namedtuples()
                    ):
                        param_counts[str(row.exam_type_ref)] = row.cnt

                sections: list[ExamSectionVM] = []
                for ce in campaign_exams:
                    ref = ce.exam_type_ref
                    ref_id = str(ref.id)
                    marker = f"CAMP:{campaign_id}|REF:{ref_id}"
                    saved_exam_id = ""
                    is_saved = False
                    is_transmitted = False
                    for rv_key, (eid, is_tx) in existing_map.items():
                        if rv_key.startswith(marker):
                            saved_exam_id = eid
                            is_saved = True
                            is_transmitted = is_tx
                            break
                    sections.append(
                        ExamSectionVM(
                            exam_type_ref_id=ref_id,
                            name=ref.name,
                            category_label=ref.get_category_label(),
                            param_count=param_counts.get(ref_id, 0),
                            is_saved=is_saved,
                            is_transmitted=is_transmitted,
                            saved_exam_id=saved_exam_id,
                            allows_attachment=ref.allows_attachment,
                        )
                    )

                self.sections = sections
                self.has_saved_sections = any(s.is_saved for s in sections)
                if sections:
                    first = sections[0]
                    self.active_section_id = first.exam_type_ref_id
                    self.active_section_name = first.name
                    self.active_section_is_saved = first.is_saved
                    self.active_section_is_transmitted = first.is_transmitted
                    await self._load_active_params(first.exam_type_ref_id)
                    await self._load_section_files()
        except Exception as e:
            self.error = f"Erreur de chargement : {e}"
        finally:
            self.is_loading = False

    async def _load_active_params(self, section_id: str):
        """Load params (with already-saved values if any) for a given section."""
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                from gws_care.exam_type_ref.exam_parameter import ExamParameter

                # Load existing saved values and track which params were saved
                marker = f"CAMP:{campaign_id}|REF:{section_id}"
                saved_values: dict[str, str] = {}  # param_name → value
                saved_param_names: set[str] = set()  # names that were explicitly saved
                existing = Exam.get_or_none(
                    (Exam.patient == patient_id)
                    & Exam.reason_for_visit.startswith(marker)
                )
                has_existing = existing is not None
                if existing and existing.lab_results:
                    for row in existing.lab_results:
                        name = row.get("parameter", "")
                        saved_values[name] = str(row.get("value", ""))
                        saved_param_names.add(name)

                params = list(
                    ExamParameter.select()
                    .where(ExamParameter.exam_type_ref == section_id)
                    .order_by(ExamParameter.display_order)
                )
                entries: list[ExamParamEntry] = []
                for p in params:
                    r_lo = str(p.ref_low) if p.ref_low is not None else ""
                    r_hi = str(p.ref_high) if p.ref_high is not None else ""
                    if r_lo and r_hi:
                        ref_range = f"{r_lo} – {r_hi}"
                    elif r_lo:
                        ref_range = f"≥ {r_lo}"
                    elif r_hi:
                        ref_range = f"≤ {r_hi}"
                    else:
                        ref_range = ""

                    c_lo = str(p.critical_low) if p.critical_low is not None else ""
                    c_hi = str(p.critical_high) if p.critical_high is not None else ""
                    crit_range = (
                        f"{c_lo or '—'} / {c_hi or '—'}" if (c_lo or c_hi) else ""
                    )

                    entries.append(
                        ExamParamEntry(
                            param_id=str(p.id),
                            name=p.name,
                            unit=p.unit or "",
                            ref_range=ref_range,
                            critical_range=crit_range,
                            ref_low_raw=r_lo,
                            ref_high_raw=r_hi,
                            critical_low_raw=c_lo,
                            critical_high_raw=c_hi,
                            is_required=p.is_required,
                            value_type=p.value_type,
                            value=saved_values.get(p.name, ""),
                            # If a previous save exists, restore selection state:
                            # selected if was in saved results OR if no save exists yet (first load)
                            is_selected=(not has_existing) or (p.name in saved_param_names) or p.is_required,
                            value_status=(
                                _compute_param_status(
                                    saved_values.get(p.name, ""),
                                    r_lo, r_hi, c_lo, c_hi,
                                )
                                if p.value_type == "NUMERIC"
                                else ""
                            ),
                        )
                    )
                self.active_params = entries
        except Exception as exc:
            self.active_params = []
