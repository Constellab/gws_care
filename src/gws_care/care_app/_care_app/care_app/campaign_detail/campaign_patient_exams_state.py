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


class AddParamOption(BaseModel):
    """A parameter option shown in the 'add missed test' dialog."""

    id: str
    name: str
    unit: str = ""
    value_type: str = "NUMERIC"
    is_selected: bool = False


class ExamParamEntry(BaseModel):
    """One parameter row in the result entry form."""

    param_id: str
    name: str
    unit: str
    ref_range: str  # "4.0 – 10.0" or "" if not defined
    critical_range: str  # "2.0 / 15.0" or "" if not defined
    is_required: bool
    value_type: str  # NUMERIC | TEXT | BOOLEAN
    value: str = ""
    # Raw float strings for colour-coding (empty = threshold not defined)
    ref_low_raw: str = ""
    ref_high_raw: str = ""
    critical_low_raw: str = ""
    critical_high_raw: str = ""
    # Computed status: "" | "normal" | "low" | "high" | "critical_low" | "critical_high"
    value_status: str = ""
    # Interpretation labels from ExamParameter (empty = not defined)
    label_normal: str = ""
    label_low: str = ""
    label_high: str = ""
    label_critical_low: str = ""
    label_critical_high: str = ""
    # Whether this param is included in the saved results (default True = all selected)
    is_selected: bool = True
    # Computed parameter support
    is_computed: bool = False
    formula: str = ""
    code: str = ""


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


def _recompute_params(params: list[ExamParamEntry]) -> list[ExamParamEntry]:
    """Re-evaluate all computed parameters from current non-computed NUMERIC values."""
    from gws_care.exam_type_ref.exam_formula_engine import ExamFormulaEngine

    context: dict[str, float] = {}
    for p in params:
        if not p.is_computed and p.code and p.value.strip() and p.value_type == "NUMERIC":
            try:
                context[p.code] = float(p.value.replace(",", "."))
            except ValueError:
                pass
    result = []
    for p in params:
        if p.is_computed and p.formula:
            try:
                computed = ExamFormulaEngine.evaluate(p.formula, context)
                val_str = f"{computed:.4g}"
                status = _compute_param_status(
                    val_str, p.ref_low_raw, p.ref_high_raw, p.critical_low_raw, p.critical_high_raw
                )
                result.append(
                    ExamParamEntry(**{**p.model_dump(), "value": val_str, "value_status": status})
                )
            except Exception:
                result.append(p)
        else:
            result.append(p)
    return result


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
    is_transmitted: bool = False  # True once results have been sent to the doctor
    transmission_target: str = ""  # "LABO" | "PSC" | "TRAVAIL" — in-memory only
    saved_exam_id: str = ""
    allows_attachment: bool = True
    requires_lab_validation: bool = True  # False = on-site exam, results entered directly


class CampaignPatientExamsState(ReflexMainState):
    """State for per-patient exam result entry within a campaign."""

    # Context
    campaign_name: str = ""
    patient_name: str = ""
    patient_number: str = ""
    medical_status: str = "PENDING"

    # All exam type sections of the campaign
    sections: list[ExamSectionVM] = []

    # Currently active section id (name / saved / transmitted are computed vars)
    active_section_id: str = ""
    active_params: list[ExamParamEntry] = []

    # UI state
    is_loading: bool = False
    is_saving: bool = False
    error: str = ""
    success: str = ""

    # Section action dropdown selection
    section_action: str = "save"  # "save" | "labo" | "psc" | "travail"
    _pending_section_action: str = ""  # action queued while motif dialog is open
    visit_status: str = "pending"  # CampaignVisitStatus of the patient's visit
    visit_id: str = ""  # Visit ID for linking to the visit detail / doctor interpretation page

    # True while the user has clicked "Modifier" to unlock an already-transmitted section
    is_editing_section: bool = False

    # Modification motif dialog
    show_motif_dialog: bool = False
    modification_motif: str = ""

    # Ordered list of patient IDs in the same campaign (for prev/next navigation)
    patient_nav_ids: list[str] = []

    # File attachments for the active section
    section_attached_files: list[SectionFileVM] = []
    is_uploading_file: bool = False

    # Add missed param dialog
    show_add_param_dialog: bool = False
    add_param_options: list[AddParamOption] = []
    add_param_error: str = ""
    is_saving_add_params: bool = False

    # ── Computed vars (always in sync with self.sections) ─────────────────

    @rx.var
    def active_section_name(self) -> str:
        sec = next((s for s in self.sections if s.exam_type_ref_id == self.active_section_id), None)
        return sec.name if sec else ""

    @rx.var
    def active_section_is_saved(self) -> bool:
        sec = next((s for s in self.sections if s.exam_type_ref_id == self.active_section_id), None)
        return sec.is_saved if sec else False

    @rx.var
    def active_section_is_transmitted(self) -> bool:
        sec = next((s for s in self.sections if s.exam_type_ref_id == self.active_section_id), None)
        return sec.is_transmitted if sec else False

    @rx.var
    def has_saved_sections(self) -> bool:
        return any(s.is_saved for s in self.sections)

    @rx.var
    def has_any_value_filled(self) -> bool:
        """True when at least one non-computed active param has a non-empty value."""
        return any(p.value.strip() != "" and not p.is_computed for p in self.active_params)

    @rx.var
    def can_save_section(self) -> bool:
        """True when at least one value is filled (partial save allowed)."""
        if not self.active_params:
            return True
        return any(p.value.strip() != "" and not p.is_computed for p in self.active_params)

    @rx.var
    def can_execute_section_action(self) -> bool:
        """Valider enabled: labo action needs no values; all others need at least one."""
        if self.section_action == "labo":
            return True
        return self.can_save_section

    @rx.var
    def can_validate_section(self) -> bool:
        """True when all required params have a value (full validation)."""
        if not self.active_params:
            return True
        required = [p for p in self.active_params if p.is_required and not p.is_computed]
        if not required:
            return self.can_save_section
        return all(p.value.strip() != "" for p in required)

    @rx.var
    def all_sections_saved(self) -> bool:
        """True when every section has been saved (required before global transfer)."""
        return len(self.sections) > 0 and all(s.is_saved for s in self.sections)

    @rx.var
    def active_section_transmission_target(self) -> str:
        """Transmission target of the currently active section (in-memory)."""
        sec = next((s for s in self.sections if s.exam_type_ref_id == self.active_section_id), None)
        return sec.transmission_target if sec else ""

    @rx.var
    def all_sections_transmitted(self) -> bool:
        """True when every section has been transmitted to a doctor."""
        return len(self.sections) > 0 and all(s.is_transmitted for s in self.sections)

    @rx.var
    def patient_is_on_terrain(self) -> bool:
        """True when patient presence has been declared (visit not pending)."""
        return self.visit_status != "pending"

    @rx.var
    def add_param_selected_count(self) -> int:
        return sum(1 for p in self.add_param_options if p.is_selected)

    # ── Patient navigation ────────────────────────────────────────────────

    @rx.var
    def patient_nav_index(self) -> int:
        try:
            return self.patient_nav_ids.index(self.cp_patient_id)
        except ValueError:
            return -1

    @rx.var
    def prev_patient_id(self) -> str:
        try:
            idx = self.patient_nav_ids.index(self.cp_patient_id)
        except ValueError:
            return ""
        return self.patient_nav_ids[idx - 1] if idx > 0 else ""

    @rx.var
    def next_patient_id(self) -> str:
        try:
            idx = self.patient_nav_ids.index(self.cp_patient_id)
        except ValueError:
            return ""
        total = len(self.patient_nav_ids)
        return self.patient_nav_ids[idx + 1] if idx < total - 1 else ""

    @rx.var
    def patient_nav_label(self) -> str:
        try:
            idx = self.patient_nav_ids.index(self.cp_patient_id)
        except ValueError:
            return ""
        return str(idx + 1) + " / " + str(len(self.patient_nav_ids))

    # Treating doctor transmission flag
    treating_doctor_transmitted: bool = False

    # Operator notes entered during the terrain phase
    terrain_notes: str = ""
    is_saving_notes: bool = False

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

    @rx.event
    def go_to_prev_patient(self):
        nxt = self.prev_patient_id
        if nxt:
            return rx.redirect("/campaign-patient/" + self.cp_campaign_id + "/" + nxt)

    @rx.event
    def go_to_next_patient(self):
        nxt = self.next_patient_id
        if nxt:
            return rx.redirect("/campaign-patient/" + self.cp_campaign_id + "/" + nxt)

    @rx.event
    def go_to_visit_detail(self):
        """Navigate to the visit detail page (doctor interpretation / main page)."""
        if self.visit_id:
            return rx.redirect(f"/visit/{self.visit_id}")

    # ── Terrain notes ─────────────────────────────────────────────────────

    @rx.event
    def set_terrain_notes(self, value: str):
        self.terrain_notes = value

    @rx.event
    async def save_terrain_notes(self):
        """Persist terrain notes to CampaignPatient on blur."""
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id
        self.is_saving_notes = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_patient import CampaignPatient

                cp = CampaignPatient.get_or_none(
                    (CampaignPatient.campaign == campaign_id)
                    & (CampaignPatient.patient == patient_id)
                )
                if cp:
                    cp.terrain_notes = self.terrain_notes
                    cp.save()
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving_notes = False

    # ── Section selection ─────────────────────────────────────────────────

    @rx.event
    async def set_active_section(self, section_id: str):
        """Switch to a different exam type section."""
        if section_id == self.active_section_id:
            return
        self.active_section_id = section_id
        self.is_editing_section = False
        await self._load_active_params(section_id)
        await self._load_section_files()

    # ── Value entry ───────────────────────────────────────────────────────

    @rx.event
    def set_param_value(self, param_id: str, value: str):
        """Update the value of one parameter and re-evaluate computed params."""
        updated = []
        for p in self.active_params:
            if p.param_id == param_id:
                status = (
                    _compute_param_status(
                        value,
                        p.ref_low_raw,
                        p.ref_high_raw,
                        p.critical_low_raw,
                        p.critical_high_raw,
                    )
                    if p.value_type == "NUMERIC"
                    else ""
                )
                updated.append(
                    ExamParamEntry(**{**p.dict(), "value": value, "value_status": status})
                )
            else:
                updated.append(p)
        # Recompute any formula-based parameters
        self.active_params = _recompute_params(updated)

    @rx.event
    def toggle_param_selection(self, param_id: str):
        """Toggle whether a parameter is included in the saved results."""
        self.active_params = [
            ExamParamEntry(**{**p.model_dump(), "is_selected": not p.is_selected})
            if p.param_id == param_id
            else p
            for p in self.active_params
        ]

    @rx.event
    def select_all_params(self):
        """Mark all parameters as selected."""
        self.active_params = [
            ExamParamEntry(**{**p.model_dump(), "is_selected": True}) for p in self.active_params
        ]

    @rx.event
    def deselect_all_params(self):
        """Mark all non-required parameters as deselected."""
        self.active_params = [
            ExamParamEntry(**{**p.model_dump(), "is_selected": p.is_required})
            for p in self.active_params
        ]

    # ── Motif dialog (modification reason) ───────────────────────────────

    @rx.event
    def open_motif_dialog(self):
        self.modification_motif = ""
        self._pending_section_action = ""
        self.show_motif_dialog = True

    @rx.event
    def close_motif_dialog(self):
        self.show_motif_dialog = False
        self._pending_section_action = ""

    @rx.event
    def enter_edit_mode(self):
        """Unlock the form for an already-transmitted section (requires re-transmit after editing)."""
        self.is_editing_section = True

    @rx.var
    def active_section_is_readonly(self) -> bool:
        """True when the active section is transmitted AND the user hasn't clicked Modifier yet."""
        return self.active_section_is_transmitted and not self.is_editing_section

    @rx.event
    def set_modification_motif(self, value: str):
        self.modification_motif = value

    @rx.event
    async def confirm_modification(self):
        """Save with motif, then execute any pending transmission action."""
        self.show_motif_dialog = False
        pending = self._pending_section_action
        self._pending_section_action = ""
        await self._do_save_section(motif=self.modification_motif)
        if self.error:
            return
        self.is_editing_section = False
        if pending and pending != "save":
            await self._do_transmit_action(pending)

    # ── Section action (4-option dropdown) ────────────────────────────────

    @rx.event
    def set_section_action(self, value: str):
        self.section_action = value

    @rx.event
    async def execute_section_action(self):
        """Save the active section and optionally transmit based on section_action."""
        action = self.section_action

        # Already saved → require modification motif before proceeding
        if self.active_section_is_saved:
            self._pending_section_action = action
            self.modification_motif = ""
            self.show_motif_dialog = True
            return

        # Labo transmission: no values required, skip save
        if action == "labo":
            await self._do_transmit_action(action)
            return

        # All other actions: save first (at least one value required), then transmit
        await self._do_save_section(motif="")
        if self.error or action == "save":
            return
        await self._do_transmit_action(action)

    async def _do_transmit_action(self, action: str):
        """Transmit the active section based on the given action string."""
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id
        section_id = self.active_section_id
        if not campaign_id or not patient_id or not section_id:
            return

        self.is_saving = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamStatus

                if action in ("labo", "psc"):
                    CampaignService.mark_lab_entered(campaign_id, patient_id)
                    target = "LABO" if action == "labo" else "PSC"
                    new_status = "LAB_ENTERED"
                elif action == "travail":
                    CampaignService.validate_psc_patient(campaign_id, patient_id)
                    target = "TRAVAIL"
                    new_status = "PSC_VALIDATED"
                else:
                    return

                marker = f"CAMP:{campaign_id}|REF:{section_id}"
                for exam in Exam.select().where(Exam.patient == patient_id):
                    rv = exam.reason_for_visit or ""
                    if rv.startswith(marker):
                        exam.status = ExamStatus.IN_PROGRESS_INTERPRETATION
                        exam.save()
                        break

            self.medical_status = new_status
            self.sections = [
                ExamSectionVM(
                    **{
                        **s.dict(),
                        "is_transmitted": True,
                        "transmission_target": target,
                    }
                )
                if s.exam_type_ref_id == section_id
                else s
                for s in self.sections
            ]
            target_labels = {
                "LABO": "au labo",
                "PSC": "au médecin PSC",
                "TRAVAIL": "au médecin de travail",
            }
            sec = next((s for s in self.sections if s.exam_type_ref_id == section_id), None)
            sec_name = sec.name if sec else "l'examen"
            self.success = f'Résultats "{sec_name}" transmis {target_labels.get(target, "")} ✓'
            self.is_editing_section = False

        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving = False

    # ── Validate lab results ──────────────────────────────────────────────

    @rx.event
    async def validate_lab(self):
        """Advance medical_status from LAB_ENTERED to LAB_VALIDATED."""
        await self._do_validate_lab()

    @rx.event
    async def validate_lab_and_next(self):
        """Validate lab results then navigate to the next patient."""
        await self._do_validate_lab()
        if self.error:
            return
        nxt = self.next_patient_id
        if nxt:
            return rx.redirect("/campaign-patient/" + self.cp_campaign_id + "/" + nxt)

    async def _do_validate_lab(self):
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id
        self.is_saving = True
        self.error = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.campaign.campaign_patient import CampaignPatient, MedicalRecordStatus
                from gws_care.visit.campaign_visit_service import CampaignVisitService
                from gws_care.visit.visit import Visit

                cp = CampaignPatient.get_or_none(
                    (CampaignPatient.campaign == campaign_id)
                    & (CampaignPatient.patient == patient_id)
                )
                if cp:
                    cp.medical_status = MedicalRecordStatus.LAB_VALIDATED.value
                    cp.save()

                visit = Visit.get_or_none(
                    (Visit.campaign == campaign_id) & (Visit.patient == patient_id)
                )
                if visit:
                    try:
                        CampaignVisitService.validate_lab(visit.id, auth_user)
                    except Exception:
                        pass
            self.medical_status = "LAB_VALIDATED"
            self.success = "Résultats de laboratoire validés ✓"
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving = False

    # ── Save section ──────────────────────────────────────────────────────

    @rx.event
    async def save_section_partial(self):
        """Enregistrer: partial save — any filled values, no required-field check."""
        await self._do_save_section(motif="")

    @rx.event
    async def save_active_section(self):
        """Valider: full save — all required fields should be filled."""
        await self._do_save_section(motif="")

    async def save_active_section_with_motif(self, motif: str):
        """Save with a modification reason (called from motif dialog)."""
        await self._do_save_section(motif=motif)

    async def _do_save_section(self, motif: str = ""):
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
                            p.value,
                            p.ref_low_raw,
                            p.ref_high_raw,
                            p.critical_low_raw,
                            p.critical_high_raw,
                        )
                        if p.value_type == "NUMERIC"
                        else ("normal" if p.value else ""),
                    }
                    for p in self.active_params
                    if p.is_selected  # only save params that are selected
                ]

                # Marker in reason_for_visit to identify this exam uniquely
                marker = f"CAMP:{campaign_id}|REF:{section_id}"

                existing = Exam.get_or_none(
                    (Exam.patient == patient_id) & Exam.reason_for_visit.startswith(marker)
                )

                if existing:
                    existing.lab_results = lab_results
                    if motif:
                        from gws_care.exam.exam_audit_entry import ExamAuditEntry

                        ExamAuditEntry.create(
                            exam=existing,
                            action="MODIFICATION",
                            details=motif,
                        )
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
                    e.exam_type_ref_id = section_id  # link to ExamTypeRef for label resolution
                    e.status = ExamStatus.IN_PROGRESS_RESULTS
                    e.reason_for_visit = f"{marker}|{section_name}"
                    e.lab_results = lab_results
                    e.save()
                    exam_id = str(e.id)

                # Update section status
                self.sections = [
                    ExamSectionVM(**{**s.dict(), "is_saved": True, "saved_exam_id": exam_id})
                    if s.exam_type_ref_id == section_id
                    else s
                    for s in self.sections
                ]
                suffix = f" (motif : {motif})" if motif else ""
                self.success = f'Résultats "{section_name}" enregistrés ✓{suffix}'
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
            if rv.startswith(marker_prefix) and exam.status == ExamStatus.IN_PROGRESS_RESULTS:
                exam.status = ExamStatus.IN_PROGRESS_INTERPRETATION
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
            sec = next((s for s in self.sections if s.exam_type_ref_id == section_id), None)
            section_name = sec.name if sec else "cet examen"
            self.success = f'Résultats "{section_name}" transférés au médecin PSC.'
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
                # Persist LAB_ENTERED status to DB
                CampaignService.mark_lab_entered(campaign_id, patient_id)

            self.medical_status = "LAB_ENTERED"
            # Mark every section as transmitted in local state
            self.sections = [
                ExamSectionVM(**{**s.dict(), "is_transmitted": True}) for s in self.sections
            ]
            self.success = (
                "Résultats transmis au médecin PSC. Le dossier passe en « Résultats saisis »."
            )

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
                    size_label = (
                        f"{size_kb:.0f} Ko" if size_kb < 1024 else f"{size_kb / 1024:.1f} Mo"
                    )
                    dl_url = (
                        ExamFileService.get_resource_download_url(f.resource_id)
                        if f.resource_id
                        else ""
                    )
                    result.append(
                        SectionFileVM(
                            file_id=str(f.id),
                            name=f.original_name or "fichier",
                            size_label=size_label,
                            download_url=dl_url,
                            mime_type=f.mime_type or "",
                        )
                    )
                self.section_attached_files = result
        except Exception as exc:
            self.section_attached_files = []

    @rx.event
    def dismiss_messages(self):
        self.error = ""
        self.success = ""

    # ── Add missed param ──────────────────────────────────────────────────────

    @rx.event
    async def open_add_param_dialog(self):
        """Load params not yet selected for the active section."""
        section_id = self.active_section_id
        campaign_id = self.cp_campaign_id
        self.add_param_options = []
        self.add_param_error = ""
        self.show_add_param_dialog = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_exam import CampaignExam
                from gws_care.exam_type_ref.exam_parameter import ExamParameter

                ce = CampaignExam.get_or_none(
                    (CampaignExam.campaign == campaign_id)
                    & (CampaignExam.exam_type_ref == section_id)
                )
                already: set[str] = set()
                if ce and ce.selected_param_ids:
                    already = {str(pid) for pid in ce.selected_param_ids}

                all_params = list(
                    ExamParameter.select()
                    .where(ExamParameter.exam_type_ref == section_id)
                    .order_by(ExamParameter.display_order)
                )
                available = [p for p in all_params if str(p.id) not in already]
                self.add_param_options = [
                    AddParamOption(
                        id=str(p.id),
                        name=p.name,
                        unit=p.unit or "",
                        value_type=p.value_type,
                        is_selected=False,
                    )
                    for p in available
                ]
                if not self.add_param_options:
                    self.add_param_error = "Tous les tests de cet examen sont déjà ajoutés."
        except Exception as e:
            self.add_param_error = str(e)

    @rx.event
    def close_add_param_dialog(self):
        self.show_add_param_dialog = False
        self.add_param_options = []
        self.add_param_error = ""

    @rx.event
    def toggle_add_param_option(self, param_id: str):
        self.add_param_options = [
            AddParamOption(**{**p.dict(), "is_selected": not p.is_selected})
            if p.id == param_id
            else p
            for p in self.add_param_options
        ]

    @rx.event
    async def save_add_params(self):
        """Append selected params to CampaignExam.selected_param_ids and reload."""
        section_id = self.active_section_id
        campaign_id = self.cp_campaign_id
        selected = [p for p in self.add_param_options if p.is_selected]
        if not selected:
            self.add_param_error = "Sélectionnez au moins un test."
            return
        self.is_saving_add_params = True
        self.add_param_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_exam import CampaignExam

                ce = CampaignExam.get_or_none(
                    (CampaignExam.campaign == campaign_id)
                    & (CampaignExam.exam_type_ref == section_id)
                )
                if ce:
                    current = list(ce.selected_param_ids or [])
                    current += [p.id for p in selected]
                    ce.selected_param_ids = current
                    ce.save()
            self.show_add_param_dialog = False
            self.add_param_options = []
            await self._load_active_params(section_id)
        except Exception as e:
            self.add_param_error = str(e)
        finally:
            self.is_saving_add_params = False

    # ── PSC doctor interpretation ─────────────────────────────────────────

    @rx.event
    def set_psc_notes(self, value: str):
        self.psc_notes = value

    @rx.event
    async def validate_and_send_to_enterprise(self):
        """PSC doctor: save interpretation + validate + notify enterprise doctor."""
        await self._do_validate_psc()

    @rx.event
    async def validate_psc_and_next(self):
        """PSC doctor: validate + notify enterprise + navigate to next patient."""
        await self._do_validate_psc()
        if self.error:
            return
        nxt = self.next_patient_id
        if nxt:
            return rx.redirect("/campaign-patient/" + self.cp_campaign_id + "/" + nxt)

    async def _do_validate_psc(self):
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

    # ── Transmit to treating doctor ───────────────────────────────────────────

    @rx.event
    async def transmit_to_treating_doctor(self):
        """Record transmission to the patient's treating doctor."""
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id
        self.is_saving = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService

                CampaignService.transmit_to_treating_doctor(campaign_id, patient_id)
            self.treating_doctor_transmitted = True
            self.medical_status = "TRANSMITTED_TREATING_DOCTOR"
            self.success = "Résultats transmis au médecin traitant."
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving = False

    # ── Finish / close record ─────────────────────────────────────────────────

    @rx.event
    async def finish_record(self):
        """Close the patient dossier (PUBLISHED)."""
        campaign_id = self.cp_campaign_id
        patient_id = self.cp_patient_id
        self.is_saving = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService

                CampaignService.finish_patient_record(campaign_id, patient_id)
            self.medical_status = "PUBLISHED"
            self.success = "Dossier patient clôturé."
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
                    campaign_id,
                    patient_id,
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
        # Use router.page.params (consistent with other states; avoids stale-state issues)
        campaign_id = self.router.page.params.get("cp_campaign_id", "") or self.cp_campaign_id
        patient_id = self.router.page.params.get("cp_patient_id", "") or self.cp_patient_id
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
                # Normalize to the exact ID format used in FK columns in the DB
                campaign_id = str(campaign.id)

                patient = Patient.get_by_id_and_check(patient_id)
                self.patient_name = f"{patient.last_name} {patient.first_name}"
                self.patient_number = patient.patient_number
                patient_id = str(patient.id)

                # Load ordered patient list for navigation
                all_cps = list(
                    CampaignPatient.select(CampaignPatient.patient_id)
                    .join(Patient, on=(CampaignPatient.patient == Patient.id))
                    .where(CampaignPatient.campaign == campaign_id)
                    .order_by(Patient.last_name, Patient.first_name)
                )
                self.patient_nav_ids = [str(cp.patient_id) for cp in all_cps]

                cp = CampaignPatient.get_or_none(
                    (CampaignPatient.campaign == campaign_id)
                    & (CampaignPatient.patient == patient_id)
                )
                self.medical_status = cp.medical_status if cp else "PENDING"
                self.terrain_notes = (cp.terrain_notes or "") if cp else ""
                self.psc_notes = (cp.psc_notes or "") if cp else ""
                self.enterprise_notes = (cp.enterprise_notes or "") if cp else ""
                self.enterprise_patient_message = (cp.enterprise_notes or "") if cp else ""
                self.treating_doctor_transmitted = (
                    bool(cp.treating_doctor_transmitted_at) if cp else False
                )

                # Load visit status (determines whether entry form is unlocked)
                from gws_care.visit.visit import Visit

                visit = Visit.get_or_none(
                    (Visit.campaign == campaign_id) & (Visit.patient == patient_id)
                )
                if visit:
                    vs = visit.campaign_visit_status
                    self.visit_status = vs.value if hasattr(vs, "value") else str(vs)
                    self.visit_id = str(visit.id)
                else:
                    self.visit_status = "pending"
                    self.visit_id = ""

                # Detect viewer role
                from gws_care.role.care_role import CareRole as _CareRole
                from gws_care.role.user_role_service import UserRoleService

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
                        is_tx = exam.status == ExamStatus.IN_PROGRESS_INTERPRETATION
                        existing_map[rv] = (str(exam.id), is_tx)

                from peewee import fn

                campaign_exams = list(
                    CampaignExam.select()
                    .where(CampaignExam.campaign == campaign_id)
                    .order_by(CampaignExam.created_at)
                )

                # Fallback: if no CampaignExam entries exist the campaign was configured
                # via the old CampaignExamType system.  Find or create ExamTypeRef entries
                # (matching by name, then by substring, then creating one if needed) and
                # auto-create CampaignExam records so the results page works immediately.
                if not campaign_exams:
                    from gws_care.campaign.campaign_exam_type import CampaignExamType as _OldCET
                    from gws_care.exam_type_ref.exam_type_ref import (
                        ExamCategory as _EC,
                    )
                    from gws_care.exam_type_ref.exam_type_ref import (
                        ExamTypeRef as _ETR,
                    )

                    # ExamType.value → ExamCategory.value
                    _ET_TO_CAT = {
                        "biology": _EC.BIOLOGY.value,
                        "hematology": _EC.BIOLOGY.value,
                        "hormones": _EC.BIOLOGY.value,
                        "bacteriology": _EC.BIOLOGY.value,
                        "parasitology": _EC.BIOLOGY.value,
                        "immunology": _EC.BIOLOGY.value,
                        "hepatic_markers": _EC.BIOLOGY.value,
                        "clinical": _EC.CLINICAL.value,
                        "radiology": _EC.IMAGING.value,
                        "ophthalmology": _EC.ORL.value,
                        "orl": _EC.ORL.value,
                        "ecg": _EC.ECG.value,
                    }
                    old_types = list(_OldCET.select().where(_OldCET.campaign == campaign_id))
                    for old_cet in old_types:
                        try:
                            old_name = old_cet.exam_type.name.strip()
                            # 1) exact, 2) case-insensitive, 3) substring LIKE
                            ref = (
                                _ETR.get_or_none(_ETR.name == old_name)
                                or _ETR.get_or_none(fn.LOWER(_ETR.name) == old_name.lower())
                                or _ETR.get_or_none(_ETR.name.contains(old_name))
                            )
                            if ref is None:
                                # Create a placeholder ExamTypeRef so results can be entered.
                                old_cat_val = getattr(old_cet.exam_type.category, "value", "other")
                                ref = _ETR.create(
                                    name=old_name,
                                    category=_ET_TO_CAT.get(old_cat_val, _EC.OTHER.value),
                                    allows_attachment=True,
                                    requires_lab_validation=False,
                                    is_active=True,
                                )
                            if not CampaignExam.get_or_none(
                                (CampaignExam.campaign == campaign_id)
                                & (CampaignExam.exam_type_ref == ref.id)
                            ):
                                CampaignExam.create(campaign=campaign, exam_type_ref=ref)
                        except Exception:
                            pass
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
                section_errors: list[str] = []
                for ce in campaign_exams:
                    try:
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
                                requires_lab_validation=ref.requires_lab_validation,
                            )
                        )
                    except Exception as sec_err:
                        section_errors.append(str(sec_err))
                if section_errors and not sections:
                    self.error = f"Erreur chargement examens : {section_errors[0]}"

                self.sections = sections
                if sections:
                    first = sections[0]
                    self.active_section_id = first.exam_type_ref_id
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
                    (Exam.patient == patient_id) & Exam.reason_for_visit.startswith(marker)
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

                # Filter by campaign-level param selection if set
                from gws_care.campaign.campaign_exam import CampaignExam
                ce = CampaignExam.get_or_none(
                    (CampaignExam.campaign == campaign_id)
                    & (CampaignExam.exam_type_ref == section_id)
                )
                allowed_ids: set | None = None
                if ce and ce.selected_param_ids:
                    allowed_ids = set(str(pid) for pid in ce.selected_param_ids)
                if allowed_ids is not None:
                    params = [p for p in params if str(p.id) in allowed_ids or p.is_required]
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
                    crit_range = f"{c_lo or '—'} / {c_hi or '—'}" if (c_lo or c_hi) else ""

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
                            is_selected=(not has_existing)
                            or (p.name in saved_param_names)
                            or p.is_required,
                            value_status=(
                                _compute_param_status(
                                    saved_values.get(p.name, ""),
                                    r_lo,
                                    r_hi,
                                    c_lo,
                                    c_hi,
                                )
                                if p.value_type == "NUMERIC"
                                else ""
                            ),
                            is_computed=bool(p.is_computed),
                            formula=p.formula or "",
                            code=p.code or "",
                            label_normal=p.label_normal or "",
                            label_low=p.label_low or "",
                            label_high=p.label_high or "",
                            label_critical_low=p.label_critical_low or "",
                            label_critical_high=p.label_critical_high or "",
                        )
                    )
                # Initial pass: compute formula-based params from saved non-computed values
                self.active_params = _recompute_params(entries)
        except Exception as exc:
            self.active_params = []
