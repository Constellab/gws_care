"""State for the consultation detail page (/consultation/[visit_id_param]).

New architecture: the consultation page is the single entry point for a medical visit.
All exam types are accessible as tabs within the same page. Motif and antécédents
are stored at the Visit (consultation) level, shared by all exams.
"""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class ExamTypeRefOption(BaseModel):
    id: str
    name: str
    category_label: str
    department: str = ""


class ExamParamOption(BaseModel):
    id: str
    name: str
    unit: str = ""
    value_type: str = "NUMERIC"
    is_required: bool = False
    is_selected: bool = False


class ConsultationDTO(BaseModel):
    id: str
    visit_number: str
    patient_name: str = ""
    patient_id: str = ""
    patient_gender: str = ""
    account_name: str = ""
    account_id: str = ""
    scheduled_at: str = ""
    status: str
    status_label: str
    cancellation_reason: str = ""
    reason_for_visit: str = ""
    medical_history: str = ""
    # True when this visit belongs to an occupational health campaign — in that
    # case results get transmitted to the "médecin du travail". False for a
    # standalone ("particulier") consultation, which has no work doctor.
    is_campaign: bool = False
    # Doctors assigned to this campaign visit (empty for "particulier")
    clinic_doctor_id: str = ""
    clinic_doctor_name: str = ""
    work_doctor_id: str = ""
    work_doctor_name: str = ""


class DoctorPickerOption(BaseModel):
    id: str
    label: str


class ExamRowDTO(BaseModel):
    id: str
    exam_date: str
    exam_type: str
    exam_type_label: str
    status: str
    status_label: str = ""


class ExamTabHeaderVM(BaseModel):
    """Lightweight data for one exam tab button."""
    exam_id: str
    exam_type_label: str
    status: str


class ExamActionOption(BaseModel):
    """One entry in the exam action dropdown (save / transmit to X)."""
    value: str
    label: str


class ExamParamRowVM(BaseModel):
    """One parameter row displayed inside an exam tab."""
    result_id: str = ""
    param_id: str
    param_name: str
    unit: str = ""
    value_type: str = "NUMERIC"
    is_computed: bool = False
    is_required: bool = False
    # Input binding values (all as strings)
    value_numeric: str = ""
    value_text: str = ""
    value_boolean: str = ""       # "true" | "false" | ""
    # Display after save
    status: str = "PENDING"
    status_color: str = "gray"
    ref_range_label: str = ""


class ExamAuditEntryVM(BaseModel):
    """One entry of the exam's action history (add/remove a test, modify a value…)."""
    action_label: str
    details: str = ""
    user_name: str = ""
    created_at: str = ""


class PrescriptionRowDTO(BaseModel):
    id: str
    prescription_date: str
    diagnosis: str = ""
    prescribed_by_name: str = ""
    drug_count: int = 0
    is_archived: bool = False


class CertificateRowDTO(BaseModel):
    id: str
    issue_date: str
    conclusion: str = ""
    is_fit_for_work: bool = True
    issued_by_name: str = ""


class DrugLineDTO(BaseModel):
    """One drug line in a prescription form."""
    name: str = ""
    dosage: str = ""
    frequency: str = ""
    duration: str = ""


def _status_color(status: str) -> str:
    return {
        "todo": "gray",
        "in_progress_results": "orange",
        "in_progress_interpretation": "blue",
        "done": "green",
    }.get(status, "gray")


class ConsultationDetailState(RoleState):
    """State for the /consultation/[visit_id_param] page."""

    consultation: ConsultationDTO | None = None
    exams: list[ExamRowDTO] = []
    prescriptions: list[PrescriptionRowDTO] = []
    certificates: list[CertificateRowDTO] = []

    is_loading: bool = True
    error_message: str = ""
    success_message: str = ""

    # ── Consultation-level motif / antécédents ────────────────────────────────
    form_reason: str = ""
    form_history: str = ""
    is_saving_info: bool = False

    # ── Tab navigation ────────────────────────────────────────────────────────
    # "informations" or an exam_id
    active_tab: str = "informations"
    exam_tab_headers: list[ExamTabHeaderVM] = []

    # ── Active exam tab — param results ──────────────────────────────────────
    active_exam_id: str = ""
    active_exam_type_ref_id: str = ""
    active_exam_status: str = ""
    active_exam_date: str = ""
    active_exam_params: list[ExamParamRowVM] = []
    # Tracks param_ids touched by the user since last load — reset on every load
    modified_param_ids: list[str] = []
    is_loading_params: bool = False
    is_saving_params: bool = False
    # Action dropdown — what happens when "Valider" is clicked
    exam_action: str = "save"
    # Action history (add/remove a test, modify a value…) — kept separate from interpretation
    active_exam_audit_log: list[ExamAuditEntryVM] = []
    # Transmission workflow
    active_exam_interpretation: str = ""
    active_exam_work_doctor_interpretation: str = ""
    is_saving_interpretation: bool = False
    is_transmitting: bool = False
    # Edit reason dialog (for re-saving already-recorded results)
    show_edit_reason_dialog: bool = False
    edit_reason: str = ""
    edit_reason_error: str = ""

    # Close dialog
    show_close_dialog: bool = False
    is_closing: bool = False

    # Cancel dialog
    show_cancel_dialog: bool = False
    cancel_reason: str = ""
    cancel_reason_error: str = ""
    is_cancelling: bool = False

    # Start consultation
    is_starting: bool = False

    # ── Doctor assignment dialogs (campaign visits only) ─────────────────────
    show_clinic_doctor_dialog: bool = False
    clinic_doctor_options: list[DoctorPickerOption] = []
    selected_clinic_doctor_id: str = ""
    is_saving_clinic_doctor: bool = False

    show_work_doctor_dialog: bool = False
    work_doctor_options: list[DoctorPickerOption] = []
    selected_work_doctor_id: str = ""
    is_saving_work_doctor: bool = False

    # ── New Exam dialog ───────────────────────────────────────────────────────
    show_new_exam_dialog: bool = False
    new_exam_type: str = ""
    new_exam_date: str = ""
    new_exam_error: str = ""
    new_exam_is_saving: bool = False
    new_exam_ref_options: list[ExamTypeRefOption] = []
    new_exam_params: list[ExamParamOption] = []
    new_exam_is_loading_types: bool = False

    @rx.var
    def new_exam_selected_param_count(self) -> int:
        return sum(1 for p in self.new_exam_params if p.is_selected)

    # ── Delete exam dialog ────────────────────────────────────────────────────
    show_delete_exam_dialog: bool = False
    delete_exam_reason: str = ""
    delete_exam_reason_error: str = ""
    is_deleting_exam: bool = False

    # ── Delete single param (test) dialog ────────────────────────────────────
    show_delete_param_dialog: bool = False
    delete_param_id: str = ""
    delete_param_name: str = ""
    delete_param_reason: str = ""
    delete_param_reason_error: str = ""
    is_deleting_param: bool = False

    # ── Add missed params dialog ──────────────────────────────────────────────
    show_add_param_dialog: bool = False
    add_param_options: list[ExamParamOption] = []
    is_saving_add_params: bool = False
    add_param_error: str = ""
    add_param_reason: str = ""
    add_param_reason_error: str = ""

    @rx.var
    def add_param_selected_count(self) -> int:
        return sum(1 for p in self.add_param_options if p.is_selected)

    # ── New Prescription dialog ───────────────────────────────────────────────
    show_new_prescription_dialog: bool = False
    presc_form_date: str = ""
    presc_form_diagnosis: str = ""
    presc_form_drugs: list[DrugLineDTO] = []
    presc_form_error: str = ""
    is_saving_prescription: bool = False

    # ── New Certificate dialog ────────────────────────────────────────────────
    show_new_certificate_dialog: bool = False
    cert_form_issue_date: str = ""
    cert_form_conclusion: str = ""
    cert_form_is_fit_for_work: bool = True
    cert_form_error: str = ""
    is_saving_certificate: bool = False

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(
            self.is_operator, self.is_doctor, self.is_account_admin, self.is_admin,
            self.is_patient_user,
        )
        if redirect:
            return redirect
        await self._load_consultation()
        # If URL has /exam/{exam_id_param}, switch directly to that exam tab
        exam_id_param = self.router.page.params.get("exam_id_param", "")
        if exam_id_param:
            self.active_tab = exam_id_param
            await self._load_exam_params(exam_id_param)

    @rx.event
    def go_back(self):
        return rx.call_script("window.history.back()")

    # ── Motif / antécédents ───────────────────────────────────────────────────

    @rx.event
    def set_form_reason(self, value: str):
        self.form_reason = value

    @rx.event
    def set_form_history(self, value: str):
        self.form_history = value

    @rx.event
    async def save_consultation_info(self):
        """Persist motif and antécédents to the Visit record."""
        if not self.consultation:
            return
        self.is_saving_info = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.visit import Visit
                visit = Visit.get_by_id(self.consultation.id)
                visit.reason_for_visit = self.form_reason or None
                visit.medical_history = self.form_history or None
                visit.save()
            self.consultation = ConsultationDTO(
                **{
                    **self.consultation.dict(),
                    "reason_for_visit": self.form_reason,
                    "medical_history": self.form_history,
                }
            )
            yield rx.toast.success("Informations enregistrées.")
        except Exception as e:
            self.error_message = f"Erreur : {e}"
        finally:
            self.is_saving_info = False

    # ── Tab navigation ────────────────────────────────────────────────────────

    @rx.event
    async def set_active_tab(self, tab_value: str):
        self.active_tab = tab_value
        if tab_value != "informations":
            await self._load_exam_params(tab_value)

    # ── Exam param results editing ────────────────────────────────────────────

    @rx.event
    def set_param_value(self, param_id: str, value: str):
        """Update the value of one parameter in the active exam."""
        updated = []
        for p in self.active_exam_params:
            if p.param_id == param_id:
                updated.append(ExamParamRowVM(**{**p.dict(), "value_numeric": value, "value_text": value}))
            else:
                updated.append(p)
        self.active_exam_params = updated

    @rx.event
    def set_param_numeric(self, param_id: str, value: str):
        self.active_exam_params = [
            ExamParamRowVM(**{**p.dict(), "value_numeric": value})
            if p.param_id == param_id else p
            for p in self.active_exam_params
        ]
        if param_id not in self.modified_param_ids:
            self.modified_param_ids = self.modified_param_ids + [param_id]

    @rx.event
    def set_param_text(self, param_id: str, value: str):
        self.active_exam_params = [
            ExamParamRowVM(**{**p.dict(), "value_text": value})
            if p.param_id == param_id else p
            for p in self.active_exam_params
        ]
        if param_id not in self.modified_param_ids:
            self.modified_param_ids = self.modified_param_ids + [param_id]

    @rx.event
    def set_param_boolean(self, param_id: str, value: str):
        self.active_exam_params = [
            ExamParamRowVM(**{**p.dict(), "value_boolean": value})
            if p.param_id == param_id else p
            for p in self.active_exam_params
        ]
        if param_id not in self.modified_param_ids:
            self.modified_param_ids = self.modified_param_ids + [param_id]

    @rx.var
    def exam_action_options(self) -> list[ExamActionOption]:
        """Available actions for the exam-action dropdown, filtered only by role
        and by whether this visit belongs to a campaign (médecin du travail) or
        is a standalone ("particulier") consultation. Not gated by exam status —
        each action validates its own preconditions (e.g. "Terminer" requires an
        interpretation) and reports a clear error if used too early.
        """
        options = [ExamActionOption(value="save", label="Enregistrer (sans transmettre)")]
        if self.is_doctor:
            options.append(ExamActionOption(value="transmit_lab", label="Transmettre au labo"))
        # Always available — the lab transmits results to the doctor for
        # interpretation, but the doctor may also want to re-route to another
        # doctor, so this isn't exclusive with "Transmettre au labo".
        options.append(ExamActionOption(value="transmit_doctor", label="Transmettre au médecin"))
        if self.is_doctor:
            # Campaign visits get BOTH options — transmitting to the médecin du
            # travail and simply closing the exam are two distinct, independent
            # choices, not one-or-the-other. "Particulier" only has "Terminer"
            # since there is no médecin du travail to notify.
            if self.consultation and self.consultation.is_campaign:
                options.append(ExamActionOption(
                    value="transmit_work_doctor", label="Transmettre au médecin du travail",
                ))
            options.append(ExamActionOption(value="finish_local", label="Terminer"))
        return options

    @rx.event
    def set_exam_action(self, value: str):
        self.exam_action = value

    @rx.event
    async def confirm_exam_action(self):
        """Dispatch the selected exam-action dropdown entry to its handler."""
        action = self.exam_action
        if action == "transmit_lab":
            async for ev in self.transmit_to_lab():
                yield ev
        elif action == "transmit_doctor":
            async for ev in self.transmit_to_doctor():
                yield ev
        elif action == "transmit_work_doctor":
            async for ev in self.transmit_to_work_doctor():
                yield ev
        elif action == "finish_local":
            async for ev in self.finish_exam_locally():
                yield ev
        else:
            async for ev in self.save_exam_params():
                yield ev

    @rx.event
    async def save_exam_params(self):
        """Save param values — opens reason dialog only when an already-saved result has changed."""
        if not self.active_exam_id:
            return
        # Nothing typed since last load — nothing to save
        if not self.modified_param_ids:
            yield rx.toast.info("Aucune modification en attente.")
            return
        # Require a reason only when at least one of the modified params already has a saved
        # result in DB (result_id != "").  A brand-new param (result_id == "") is a first save.
        modified_ids_set = set(self.modified_param_ids)
        has_modified_existing = any(
            p.result_id != "" and p.param_id in modified_ids_set
            for p in self.active_exam_params
        )
        if has_modified_existing:
            self.edit_reason = ""
            self.edit_reason_error = ""
            self.show_edit_reason_dialog = True
        else:
            await self._do_save_exam_params(reason=None)
            if not self.error_message:
                yield rx.toast.success("Résultats enregistrés.")

    @rx.event
    def set_edit_reason(self, value: str):
        self.edit_reason = value

    @rx.event
    def close_edit_reason_dialog(self):
        self.show_edit_reason_dialog = False

    @rx.event
    async def confirm_edit_save(self):
        """Validate reason then save param values."""
        reason = self.edit_reason.strip()
        if not reason:
            self.edit_reason_error = "Le motif de modification est obligatoire."
            return
        self.edit_reason_error = ""
        self.show_edit_reason_dialog = False
        await self._do_save_exam_params(reason=reason)
        if not self.error_message:
            yield rx.toast.success("Résultats modifiés.")

    async def _do_save_exam_params(self, reason: str | None):
        """Internal: persist parameter values + optionally log modification reason."""
        exam_id = self.active_exam_id
        if not exam_id:
            return
        self.is_saving_params = True
        self.error_message = ""
        try:
            patient_gender = self.consultation.patient_gender if self.consultation else None

            entries = []
            for p in self.active_exam_params:
                if p.is_computed:
                    continue
                entry: dict = {"parameter_id": p.param_id}
                if p.value_type == "NUMERIC":
                    raw = p.value_numeric.strip().replace(",", ".")
                    entry["value_numeric"] = float(raw) if raw else None
                elif p.value_type == "BOOLEAN":
                    entry["value_boolean"] = (p.value_boolean == "true") if p.value_boolean else None
                else:
                    entry["value_text"] = p.value_text or None
                entries.append(entry)

            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_parameter_result import ExamParameterResultService
                from gws_care.exam.exam_type import ExamStatus

                ExamParameterResultService.bulk_upsert_with_computed(
                    exam_id=exam_id,
                    exam_type_ref_id=self.active_exam_type_ref_id,
                    entries=entries,
                    patient_gender=patient_gender or None,
                )
                # Advance status from todo → in_progress_results on first save
                exam = Exam.get_by_id(exam_id)
                if exam.status == ExamStatus.TODO:
                    exam.status = ExamStatus.IN_PROGRESS_RESULTS
                    exam.save()
                # Log modification reason — only logged when re-saving already-recorded
                # results (reason is None for a brand-new value's first save)
                if reason:
                    from gws_care.exam.exam_audit_entry import ExamAuditAction
                    modified_ids = set(self.modified_param_ids)
                    modified_names = [
                        p.param_name for p in self.active_exam_params
                        if p.param_id in modified_ids
                    ]
                    body = f"{', '.join(modified_names)} : {reason}" if modified_names else reason
                    self._log_exam_audit(exam, ExamAuditAction.MODIFY_VALUE.value, body)

            await self._load_exam_params(exam_id)
            await self._refresh_exam_headers()
        except Exception as e:
            self.error_message = f"Erreur enregistrement : {e}"
        finally:
            self.is_saving_params = False

    # ── Exam transmission workflow ────────────────────────────────────────────

    @rx.event
    def set_active_exam_interpretation(self, value: str):
        self.active_exam_interpretation = value

    @rx.event
    def set_active_exam_work_doctor_interpretation(self, value: str):
        self.active_exam_work_doctor_interpretation = value

    @rx.event
    async def save_interpretation(self):
        """Save the doctor's interpretation text without changing the exam status.

        Used when the doctor wants to save a draft interpretation and come back
        later, rather than transmitting or closing the exam immediately.
        """
        exam_id = self.active_exam_id
        if not exam_id:
            return
        self.is_saving_interpretation = True
        self.error_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.exam.exam import Exam
                from gws_care.user.user import User
                exam = Exam.get_by_id(exam_id)
                exam.interpretation = self.active_exam_interpretation or None
                if self.active_exam_interpretation.strip():
                    exam.interpreted_by = User.get_by_id(str(auth_user.id))
                exam.save()
            yield rx.toast.success("Interprétation enregistrée.")
        except Exception as e:
            self.error_message = f"Erreur : {e}"
        finally:
            self.is_saving_interpretation = False

    @rx.event
    async def save_work_doctor_interpretation(self):
        """Save the médecin du travail's interpretation on the exam."""
        exam_id = self.active_exam_id
        if not exam_id:
            return
        self.is_saving_interpretation = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                exam = Exam.get_by_id(exam_id)
                exam.work_doctor_interpretation = self.active_exam_work_doctor_interpretation or None
                exam.save()
            yield rx.toast.success("Interprétation médecin du travail enregistrée.")
        except Exception as e:
            self.error_message = f"Erreur : {e}"
        finally:
            self.is_saving_interpretation = False

    @rx.event
    async def transmit_to_lab(self):
        """Doctor: delegate result entry to the lab and notify lab operators.

        Used when the doctor defines an exam that needs lab intervention instead
        of entering the results themselves.
        """
        exam_id = self.active_exam_id
        if not exam_id:
            return
        if self.modified_param_ids:
            await self._do_save_exam_params(reason=None)
        self.is_transmitting = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_audit_entry import ExamAuditAction
                from gws_care.notification.notification_service import NotificationService
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_care_role import UserCareRole

                exam = Exam.get_by_id(exam_id)
                exam_label = exam.exam_type.get_label()
                patient_name = self.consultation.patient_name if self.consultation else "le patient"
                message = f"Nouvel examen à réaliser pour {patient_name} — {exam_label}."
                lab_roles = list(
                    UserCareRole.select().where(UserCareRole.role == CareRole.OPERATEUR_LABO)
                )
                for role_entry in lab_roles:
                    NotificationService.create_bell(str(role_entry.user_id), message)

                self._log_exam_audit(
                    exam, ExamAuditAction.TRANSMIT_TO_LAB.value,
                    "Examen transmis au laboratoire pour saisie des résultats.",
                )

            await self._refresh_exam_headers()
            yield rx.toast.success("Résultats enregistrés et examen transmis au laboratoire.")
        except Exception as e:
            self.error_message = f"Erreur transmission : {e}"
        finally:
            self.is_transmitting = False

    @rx.event
    async def transmit_to_doctor(self):
        """Lab: mark exam results as complete and notify clinic doctors."""
        exam_id = self.active_exam_id
        if not exam_id:
            return
        if self.modified_param_ids:
            await self._do_save_exam_params(reason=None)
        self.is_transmitting = True
        self.error_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamStatus
                from gws_care.notification.notification_service import NotificationService
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_care_role import UserCareRole

                exam = Exam.get_by_id(exam_id)
                exam.status = ExamStatus.IN_PROGRESS_INTERPRETATION
                exam.save()

                # Bell notification to PSC clinic doctors
                exam_label = exam.exam_type.get_label()
                patient_name = self.consultation.patient_name if self.consultation else "le patient"
                message = (
                    f"Résultats disponibles pour {patient_name} — {exam_label}. "
                    "En attente d'interprétation."
                )
                doctor_roles = list(
                    UserCareRole.select()
                    .where(
                        (UserCareRole.role == CareRole.MEDECIN_PSC)
                        | (UserCareRole.role == CareRole.DOCTOR)
                    )
                )
                for role_entry in doctor_roles:
                    NotificationService.create_bell(str(role_entry.user_id), message)

            self.active_exam_status = "in_progress_interpretation"
            await self._refresh_exam_headers()
            yield rx.toast.success("Résultats enregistrés et transmis au médecin.")
        except Exception as e:
            self.error_message = f"Erreur transmission : {e}"
        finally:
            self.is_transmitting = False

    @rx.event
    async def transmit_to_work_doctor(self):
        """Clinic doctor: save interpretation and transmit to work doctor (account admins)."""
        exam_id = self.active_exam_id
        if not exam_id:
            return
        if not self.active_exam_interpretation.strip():
            self.error_message = "Veuillez renseigner l'interprétation avant de transmettre."
            return
        if self.modified_param_ids:
            await self._do_save_exam_params(reason=None)
        self.is_transmitting = True
        self.error_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamStatus
                from gws_care.notification.notification_service import NotificationService
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_care_role import UserCareRole
                from gws_care.user.user import User

                exam = Exam.get_by_id(exam_id)
                exam.status = ExamStatus.DONE
                exam.interpretation = self.active_exam_interpretation
                exam.interpreted_by = User.get_by_id(str(auth_user.id))
                exam.save()

                # Bell notification — to the specifically assigned médecin du
                # travail if one was set on this visit, else broadcast to every
                # user holding that role
                exam_label = exam.exam_type.get_label()
                patient_name = self.consultation.patient_name if self.consultation else "le patient"
                message = (
                    f"Résultats interprétés disponibles pour {patient_name} — {exam_label}."
                )
                if self.consultation and self.consultation.work_doctor_id:
                    NotificationService.create_bell(self.consultation.work_doctor_id, message)
                else:
                    work_doctor_roles = list(
                        UserCareRole.select()
                        .where(UserCareRole.role == CareRole.MEDECIN_ENTREPRISE)
                    )
                    for role_entry in work_doctor_roles:
                        NotificationService.create_bell(str(role_entry.user_id), message)

            self.active_exam_status = "done"
            await self._refresh_exam_headers()
            yield rx.toast.success("Résultats enregistrés et transmis au médecin du travail.")
        except Exception as e:
            self.error_message = f"Erreur transmission : {e}"
        finally:
            self.is_transmitting = False

    @rx.event
    async def finish_exam_locally(self):
        """Mark the exam as DONE with the doctor's interpretation (if any).

        Used for standalone ("particulier") consultations — there is no
        médecin du travail to transmit to, so the doctor closes the exam
        directly. Interpretation is optional: the exam is finalised even
        if the textarea is left blank.
        """
        exam_id = self.active_exam_id
        if not exam_id:
            return
        if self.modified_param_ids:
            await self._do_save_exam_params(reason=None)
        self.is_transmitting = True
        self.error_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamStatus
                from gws_care.user.user import User

                exam = Exam.get_by_id(exam_id)
                exam.status = ExamStatus.DONE
                exam.interpretation = self.active_exam_interpretation
                exam.interpreted_by = User.get_by_id(str(auth_user.id))
                exam.save()

            self.active_exam_status = "done"
            await self._refresh_exam_headers()
            yield rx.toast.success("Résultats enregistrés. Examen terminé.")
        except Exception as e:
            self.error_message = f"Erreur : {e}"
        finally:
            self.is_transmitting = False

    # ── Consultation lifecycle ────────────────────────────────────────────────

    @rx.event
    def open_close_dialog(self):
        self.show_close_dialog = True

    @rx.event
    def close_close_dialog(self):
        self.show_close_dialog = False

    @rx.event
    async def start_consultation(self):
        if not self.consultation:
            return
        self.is_starting = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.consultation_service import ConsultationService
                ConsultationService.mark_in_progress(visit_id=self.consultation.id)
            self.success_message = "Consultation démarrée."
            await self._load_consultation()
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_starting = False

    @rx.event
    async def confirm_close_consultation(self):
        if not self.consultation:
            return
        self.is_closing = True
        self.error_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.visit.consultation_service import ConsultationService
                ConsultationService.mark_done(
                    visit_id=self.consultation.id,
                    closed_by_user_id=str(auth_user.id),
                )
            self.show_close_dialog = False
            self.success_message = "Consultation clôturée."
            await self._load_consultation()
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_closing = False

    @rx.event
    def open_cancel_dialog(self):
        self.show_cancel_dialog = True
        self.cancel_reason = ""
        self.cancel_reason_error = ""

    @rx.event
    def close_cancel_dialog(self):
        self.show_cancel_dialog = False

    @rx.event
    def set_cancel_reason(self, value: str):
        self.cancel_reason = value

    @rx.event
    async def confirm_cancel_consultation(self):
        if not self.consultation:
            return
        reason = self.cancel_reason.strip()
        if not reason:
            self.cancel_reason_error = "Le motif d'annulation est obligatoire."
            return
        self.cancel_reason_error = ""
        self.is_cancelling = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.consultation_service import ConsultationService
                ConsultationService.cancel(visit_id=self.consultation.id, reason=reason)
            self.show_cancel_dialog = False
            self.success_message = "Consultation annulée."
            await self._load_consultation()
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_cancelling = False

    # ── Doctor assignment (campaign visits) ───────────────────────────────────

    @rx.event
    async def open_clinic_doctor_dialog(self):
        """Pick the PSC clinic doctor for this campaign visit."""
        if not self.consultation:
            return
        self.selected_clinic_doctor_id = self.consultation.clinic_doctor_id
        self.show_clinic_doctor_dialog = True
        try:
            with await self.authenticate_user():
                from gws_care.doctor.medical_doctor import MedicalDoctor
                doctors = list(
                    MedicalDoctor.select()
                    .where(MedicalDoctor.is_active == True)
                    .order_by(MedicalDoctor.last_name, MedicalDoctor.first_name)
                )
                self.clinic_doctor_options = [
                    DoctorPickerOption(id=str(d.id), label=d.get_full_name())
                    for d in doctors
                ]
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    def close_clinic_doctor_dialog(self):
        self.show_clinic_doctor_dialog = False

    @rx.event
    def set_selected_clinic_doctor(self, value: str):
        self.selected_clinic_doctor_id = "" if value == "__none__" else value

    @rx.event
    async def save_clinic_doctor(self):
        if not self.consultation:
            return
        self.is_saving_clinic_doctor = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.doctor.medical_doctor import MedicalDoctor
                from gws_care.visit.visit import Visit
                visit = Visit.get_by_id(self.consultation.id)
                visit.doctor_id = self.selected_clinic_doctor_id or None
                visit.save()
                doctor_name = ""
                if self.selected_clinic_doctor_id:
                    d = MedicalDoctor.get_by_id(self.selected_clinic_doctor_id)
                    doctor_name = d.get_full_name()
            self.consultation = ConsultationDTO(**{
                **self.consultation.dict(),
                "clinic_doctor_id": self.selected_clinic_doctor_id,
                "clinic_doctor_name": doctor_name,
            })
            self.show_clinic_doctor_dialog = False
            yield rx.toast.success("Médecin clinique assigné.")
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_saving_clinic_doctor = False

    @rx.event
    async def open_work_doctor_dialog(self):
        """Pick the médecin du travail (company doctor) for this campaign visit."""
        if not self.consultation:
            return
        self.selected_work_doctor_id = self.consultation.work_doctor_id
        self.show_work_doctor_dialog = True
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_care_role import UserCareRole
                rows = list(
                    UserCareRole.select(UserCareRole)
                    .where(UserCareRole.role == CareRole.MEDECIN_ENTREPRISE)
                )
                seen: set[str] = set()
                options: list[DoctorPickerOption] = []
                for r in rows:
                    uid = str(r.user_id)
                    if uid in seen:
                        continue
                    seen.add(uid)
                    u = r.user
                    options.append(DoctorPickerOption(id=uid, label=f"{u.first_name} {u.last_name}".strip()))
                self.work_doctor_options = options
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    def close_work_doctor_dialog(self):
        self.show_work_doctor_dialog = False

    @rx.event
    def set_selected_work_doctor(self, value: str):
        self.selected_work_doctor_id = "" if value == "__none__" else value

    @rx.event
    async def save_work_doctor(self):
        if not self.consultation:
            return
        self.is_saving_work_doctor = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.user.user import User
                from gws_care.visit.visit import Visit
                visit = Visit.get_by_id(self.consultation.id)
                visit.work_doctor_id = self.selected_work_doctor_id or None
                visit.save()
                doctor_name = ""
                if self.selected_work_doctor_id:
                    u = User.get_by_id(self.selected_work_doctor_id)
                    doctor_name = f"{u.first_name} {u.last_name}".strip()
            self.consultation = ConsultationDTO(**{
                **self.consultation.dict(),
                "work_doctor_id": self.selected_work_doctor_id,
                "work_doctor_name": doctor_name,
            })
            self.show_work_doctor_dialog = False
            yield rx.toast.success("Médecin du travail assigné.")
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_saving_work_doctor = False

    # ── Exam creation ─────────────────────────────────────────────────────────

    @rx.event
    async def open_new_exam_dialog(self):
        from datetime import date
        self.new_exam_type = ""
        self.new_exam_date = date.today().isoformat()
        self.new_exam_error = ""
        self.new_exam_is_saving = False
        self.new_exam_ref_options = []
        self.new_exam_params = []
        self.new_exam_is_loading_types = True
        self.show_new_exam_dialog = True
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                rows = ExamTypeRefService.list_all(active_only=True)
                self.new_exam_ref_options = [
                    ExamTypeRefOption(
                        id=r.id,
                        name=r.name,
                        category_label=r.category_label,
                        department=r.department or "",
                    )
                    for r in rows
                ]
        except Exception:
            self.new_exam_ref_options = []
        finally:
            self.new_exam_is_loading_types = False

    @rx.event
    def close_new_exam_dialog(self):
        self.show_new_exam_dialog = False

    @rx.event
    def set_new_exam_date(self, value: str):
        self.new_exam_date = value

    @rx.event
    async def select_new_exam_type_ref(self, ref_id: str):
        self.new_exam_type = ref_id
        self.new_exam_params = []
        if not ref_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                detail = ExamTypeRefService.get(ref_id)
                self.new_exam_params = [
                    ExamParamOption(
                        id=p.id,
                        name=p.name,
                        unit=p.unit or "",
                        value_type=p.value_type,
                        is_required=p.is_required,
                        is_selected=p.is_required,
                    )
                    for p in detail.parameters
                ]
        except Exception:
            pass

    @rx.event
    def toggle_new_exam_param(self, param_id: str):
        self.new_exam_params = [
            ExamParamOption(**{**p.dict(), "is_selected": not p.is_selected})
            if p.id == param_id else p
            for p in self.new_exam_params
        ]

    @rx.event
    def select_all_new_exam_params(self):
        self.new_exam_params = [
            ExamParamOption(**{**p.dict(), "is_selected": True})
            for p in self.new_exam_params
        ]

    @rx.event
    def clear_all_new_exam_params(self):
        self.new_exam_params = [
            ExamParamOption(**{**p.dict(), "is_selected": False})
            for p in self.new_exam_params
        ]

    @rx.event
    async def save_new_exam(self):
        if not self.consultation:
            return
        if not self.new_exam_type:
            self.new_exam_error = "Veuillez sélectionner un type d'examen."
            return
        if not self.new_exam_date:
            self.new_exam_error = "Veuillez sélectionner une date."
            return
        self.new_exam_error = ""
        self.new_exam_is_saving = True
        new_exam_id = ""
        try:
            with await self.authenticate_user():
                from datetime import date
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamStatus, ExamType

                exam = Exam()
                exam.patient_id = self.consultation.patient_id
                exam.visit_id = self.consultation.id
                exam.exam_date = date.fromisoformat(self.new_exam_date)
                exam.exam_type = ExamType.OTHER
                exam.exam_type_ref_id = self.new_exam_type
                exam.requested_param_ids = [p.id for p in self.new_exam_params if p.is_selected]
                exam.status = ExamStatus.TODO
                exam.save()
                new_exam_id = str(exam.id)
            self.show_new_exam_dialog = False
            # Reload consultation to pick up the new exam tab
            await self._load_consultation()
            # Switch to the new exam's tab
            if new_exam_id:
                self.active_tab = new_exam_id
                await self._load_exam_params(new_exam_id)
        except Exception as e:
            self.new_exam_error = str(e)
        finally:
            self.new_exam_is_saving = False

    # ── Delete exam ───────────────────────────────────────────────────────────

    @rx.event
    def open_delete_exam_dialog(self):
        self.show_delete_exam_dialog = True
        self.delete_exam_reason = ""
        self.delete_exam_reason_error = ""

    @rx.event
    def close_delete_exam_dialog(self):
        self.show_delete_exam_dialog = False

    @rx.event
    def set_delete_exam_reason(self, value: str):
        self.delete_exam_reason = value

    @rx.event
    async def confirm_delete_exam(self):
        """Soft-delete the active exam (CANCELLED) and log the reason."""
        exam_id = self.active_exam_id
        if not exam_id:
            return
        reason = self.delete_exam_reason.strip()
        if not reason:
            self.delete_exam_reason_error = "Le motif est obligatoire."
            return
        self.delete_exam_reason_error = ""
        self.is_deleting_exam = True
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamStatus
                exam = Exam.get_by_id(exam_id)
                exam.status = ExamStatus.CANCELLED
                exam.interpretation = f"[Annulé] {reason}"
                exam.save()
            self.show_delete_exam_dialog = False
            self.active_tab = "informations"
            await self._load_consultation()
            yield rx.toast.success("Examen supprimé.")
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_deleting_exam = False

    # ── Audit trail helpers ───────────────────────────────────────────────────
    # Unusual actions (add/remove a test, modify a value, transmit to lab) are
    # logged to the dedicated ExamAuditEntry table — kept separate from
    # Exam.interpretation, which stays reserved for the doctor's free-text
    # medical interpretation. created_by/created_at are auto-filled from the
    # authenticated user context (see ModelWithUser).

    @staticmethod
    def _log_exam_audit(exam, action: str, details: str) -> None:
        from gws_care.exam.exam_audit_entry import ExamAuditEntry
        ExamAuditEntry(exam=exam, action=action, details=details).save()

    # ── Add missed params to existing exam ────────────────────────────────────

    @staticmethod
    def _resolve_requested_param_ids(exam) -> list[str]:
        """Effective requested-param-id list for an exam.

        ``requested_param_ids`` is ``None`` when the exam was never customized,
        which implicitly means "show all active params of this exam type".
        Materialize that implicit list here before any add/remove mutation, so an
        explicit empty list (all tests removed) is never confused with "not yet
        customized" (which would otherwise make every test reappear on reload).
        """
        if exam.requested_param_ids is not None:
            return [str(i) for i in exam.requested_param_ids]
        from gws_care.exam_type_ref.exam_parameter import ExamParameter
        return [
            str(p.id) for p in ExamParameter.select()
            .where(
                (ExamParameter.exam_type_ref == exam.exam_type_ref_id)
                & (ExamParameter.is_active == True)
            )
        ]

    @rx.event
    async def open_add_param_dialog(self):
        """Load available params not yet in this exam's requested list."""
        exam_id = self.active_exam_id
        if not exam_id or not self.active_exam_type_ref_id:
            return
        self.add_param_options = []
        self.add_param_error = ""
        self.add_param_reason = ""
        self.add_param_reason_error = ""
        self.show_add_param_dialog = True
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                from gws_care.exam_type_ref.exam_parameter import ExamParameter
                exam = Exam.get_by_id(exam_id)
                already = set(self._resolve_requested_param_ids(exam))
                all_params = list(
                    ExamParameter.select()
                    .where(
                        (ExamParameter.exam_type_ref == self.active_exam_type_ref_id)
                        & (ExamParameter.is_active == True)
                    )
                    .order_by(ExamParameter.display_order)
                )
                available = [p for p in all_params if str(p.id) not in already]
                self.add_param_options = [
                    ExamParamOption(
                        id=str(p.id),
                        name=p.name,
                        unit=p.unit or "",
                        value_type=p.value_type,
                        is_required=bool(p.is_required),
                        is_selected=False,
                    )
                    for p in available
                ]
                if not self.add_param_options:
                    self.add_param_error = "Tous les tests de ce type d'examen sont déjà ajoutés."
        except Exception as e:
            self.add_param_error = str(e)

    @rx.event
    def close_add_param_dialog(self):
        self.show_add_param_dialog = False

    @rx.event
    def toggle_add_param(self, param_id: str):
        self.add_param_options = [
            ExamParamOption(**{**p.dict(), "is_selected": not p.is_selected})
            if p.id == param_id else p
            for p in self.add_param_options
        ]

    @rx.event
    def set_add_param_reason(self, value: str):
        self.add_param_reason = value

    @rx.event
    async def save_add_params(self):
        """Append selected params to exam.requested_param_ids then reload.

        A reason is mandatory — adding a test after exam creation is an unusual
        action (forgotten test, or a parameter needed to compute a constant) and
        must be traceable in the medical interpretation.
        """
        exam_id = self.active_exam_id
        if not exam_id:
            return
        selected_options = [p for p in self.add_param_options if p.is_selected]
        if not selected_options:
            self.add_param_error = "Sélectionnez au moins un test."
            return
        reason = self.add_param_reason.strip()
        if not reason:
            self.add_param_reason_error = "Le motif d'ajout est obligatoire."
            return
        self.add_param_reason_error = ""
        self.is_saving_add_params = True
        self.add_param_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_audit_entry import ExamAuditAction
                exam = Exam.get_by_id(exam_id)
                current = self._resolve_requested_param_ids(exam)
                selected_ids = [p.id for p in selected_options]
                exam.requested_param_ids = current + selected_ids
                exam.save()
                names = ", ".join(p.name for p in selected_options)
                self._log_exam_audit(exam, ExamAuditAction.ADD_TEST.value, f"{names} : {reason}")
            self.show_add_param_dialog = False
            await self._load_exam_params(exam_id)
            yield rx.toast.success("Tests ajoutés.")
        except Exception as e:
            self.add_param_error = str(e)
        finally:
            self.is_saving_add_params = False

    # ── Delete single param (test) ────────────────────────────────────────────

    @rx.event
    def open_delete_param_dialog(self, param_id: str, param_name: str):
        self.delete_param_id = param_id
        self.delete_param_name = param_name
        self.delete_param_reason = ""
        self.delete_param_reason_error = ""
        self.is_deleting_param = False
        self.show_delete_param_dialog = True

    @rx.event
    def close_delete_param_dialog(self):
        self.show_delete_param_dialog = False

    @rx.event
    def set_delete_param_reason(self, value: str):
        self.delete_param_reason = value

    @rx.event
    async def confirm_delete_param(self):
        """Remove a single test (param) from the exam and delete its result if any.

        A reason is mandatory — removing a test is an unusual action and must be
        traceable in the medical interpretation.
        """
        exam_id = self.active_exam_id
        param_id = self.delete_param_id
        param_name = self.delete_param_name
        if not exam_id or not param_id:
            return
        reason = self.delete_param_reason.strip()
        if not reason:
            self.delete_param_reason_error = "Le motif de suppression est obligatoire."
            return
        self.delete_param_reason_error = ""
        self.is_deleting_param = True
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_audit_entry import ExamAuditAction
                from gws_care.exam.exam_parameter_result import ExamParameterResult

                exam = Exam.get_by_id(exam_id)
                current = self._resolve_requested_param_ids(exam)
                exam.requested_param_ids = [i for i in current if str(i) != param_id]
                exam.save()
                self._log_exam_audit(exam, ExamAuditAction.REMOVE_TEST.value, f"{param_name} : {reason}")
                # Delete the saved result if it exists
                ExamParameterResult.delete().where(
                    (ExamParameterResult.exam == exam_id)
                    & (ExamParameterResult.parameter == param_id)
                ).execute()

            self.show_delete_param_dialog = False
            await self._load_exam_params(exam_id)
            await self._refresh_exam_headers()
            yield rx.toast.success(f"Test « {param_name} » supprimé.")
        except Exception as e:
            self.error_message = f"Erreur suppression test : {e}"
        finally:
            self.is_deleting_param = False

    # ── Prescription creation ─────────────────────────────────────────────────

    @rx.event
    def open_new_prescription_dialog(self):
        from datetime import date
        self.presc_form_date = date.today().isoformat()
        self.presc_form_diagnosis = ""
        self.presc_form_drugs = [DrugLineDTO()]
        self.presc_form_error = ""
        self.is_saving_prescription = False
        self.show_new_prescription_dialog = True

    @rx.event
    def close_new_prescription_dialog(self):
        self.show_new_prescription_dialog = False

    @rx.event
    def set_presc_form_date(self, value: str):
        self.presc_form_date = value

    @rx.event
    def set_presc_form_diagnosis(self, value: str):
        self.presc_form_diagnosis = value

    @rx.event
    def presc_add_drug(self):
        self.presc_form_drugs = self.presc_form_drugs + [DrugLineDTO()]

    @rx.event
    def presc_remove_drug(self, index: int):
        drugs = [DrugLineDTO(**d.dict()) for d in self.presc_form_drugs]
        if 0 <= index < len(drugs):
            drugs.pop(index)
        self.presc_form_drugs = drugs

    @rx.event
    def presc_set_drug_name(self, index: int, value: str):
        drugs = [DrugLineDTO(**d.dict()) for d in self.presc_form_drugs]
        if 0 <= index < len(drugs):
            drugs[index].name = value
        self.presc_form_drugs = drugs

    @rx.event
    def presc_set_drug_dosage(self, index: int, value: str):
        drugs = [DrugLineDTO(**d.dict()) for d in self.presc_form_drugs]
        if 0 <= index < len(drugs):
            drugs[index].dosage = value
        self.presc_form_drugs = drugs

    @rx.event
    def presc_set_drug_frequency(self, index: int, value: str):
        drugs = [DrugLineDTO(**d.dict()) for d in self.presc_form_drugs]
        if 0 <= index < len(drugs):
            drugs[index].frequency = value
        self.presc_form_drugs = drugs

    @rx.event
    def presc_set_drug_duration(self, index: int, value: str):
        drugs = [DrugLineDTO(**d.dict()) for d in self.presc_form_drugs]
        if 0 <= index < len(drugs):
            drugs[index].duration = value
        self.presc_form_drugs = drugs

    @rx.event
    async def save_new_prescription(self):
        if not self.consultation:
            return
        if not self.presc_form_date:
            self.presc_form_error = "La date est obligatoire."
            return
        self.presc_form_error = ""
        self.is_saving_prescription = True
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.prescription.prescription import (
                    DrugLineDTO as ServiceDrugLineDTO,
                    Prescription,
                    PrescriptionService,
                    SavePrescriptionDTO,
                )
                from gws_care.user.user import User

                doctor = User.get_by_id(str(auth_user.id))
                dto = SavePrescriptionDTO(
                    patient_id=self.consultation.patient_id,
                    prescription_date=self.presc_form_date,
                    drugs=[
                        ServiceDrugLineDTO(
                            name=d.name,
                            dosage=d.dosage,
                            frequency=d.frequency,
                            duration=d.duration,
                        )
                        for d in self.presc_form_drugs
                        if d.name.strip()
                    ],
                    diagnosis=self.presc_form_diagnosis,
                )
                prescription = PrescriptionService.create(dto, doctor)
                presc_obj = Prescription.get_by_id(str(prescription.id))
                presc_obj.visit_id = self.consultation.id
                presc_obj.save()
                presc_id = str(prescription.id)
            self.show_new_prescription_dialog = False
            return rx.redirect(f"/prescription/{presc_id}")
        except Exception as e:
            self.presc_form_error = str(e)
        finally:
            self.is_saving_prescription = False

    # ── Certificate creation ──────────────────────────────────────────────────

    @rx.event
    def open_new_certificate_dialog(self):
        from datetime import date
        self.cert_form_issue_date = date.today().isoformat()
        self.cert_form_conclusion = ""
        self.cert_form_is_fit_for_work = True
        self.cert_form_error = ""
        self.is_saving_certificate = False
        self.show_new_certificate_dialog = True

    @rx.event
    def close_new_certificate_dialog(self):
        self.show_new_certificate_dialog = False

    @rx.event
    def set_cert_form_issue_date(self, value: str):
        self.cert_form_issue_date = value

    @rx.event
    def set_cert_form_conclusion(self, value: str):
        self.cert_form_conclusion = value

    @rx.event
    def set_cert_form_is_fit_for_work(self, value: bool):
        self.cert_form_is_fit_for_work = value

    @rx.event
    async def save_new_certificate(self):
        if not self.consultation:
            return
        if not self.cert_form_conclusion.strip():
            self.cert_form_error = "La conclusion est requise."
            return
        self.cert_form_error = ""
        self.is_saving_certificate = True
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.certificate.medical_certificate import (
                    MedicalCertificate,
                    MedicalCertificateService,
                    SaveMedicalCertificateDTO,
                )
                from gws_care.user.user import User

                doctor = User.get_by_id(str(auth_user.id))
                dto = SaveMedicalCertificateDTO(
                    patient_id=self.consultation.patient_id,
                    exam_id=None,
                    issue_date=self.cert_form_issue_date,
                    conclusion=self.cert_form_conclusion,
                    is_fit_for_work=self.cert_form_is_fit_for_work,
                )
                cert = MedicalCertificateService.create_certificate(dto, doctor)
                cert_obj = MedicalCertificate.get_by_id(str(cert.id))
                cert_obj.visit_id = self.consultation.id
                cert_obj.save()
            self.show_new_certificate_dialog = False
            self.success_message = "Certificat émis avec succès."
            await self._load_consultation()
        except Exception as e:
            self.cert_form_error = str(e)
        finally:
            self.is_saving_certificate = False

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _load_consultation(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        self.error_message = ""
        # Reset all exam-related state immediately so navigating from one
        # consultation to another never leaks a previous patient's data while
        # the new visit is loading from the DB.
        self.active_tab = "informations"
        self.exam_tab_headers = []
        self.exams = []
        self.prescriptions = []
        self.certificates = []
        self.active_exam_id = ""
        self.active_exam_type_ref_id = ""
        self.active_exam_status = ""
        self.active_exam_date = ""
        self.active_exam_params = []
        self.active_exam_audit_log = []
        self.active_exam_interpretation = ""
        self.active_exam_work_doctor_interpretation = ""
        self.modified_param_ids = []
        self.exam_action = "save"
        try:
            visit_id = self.router.page.params.get("visit_id_param", "")
            if not visit_id:
                self.consultation = None
                return

            with await self.authenticate_user():
                from gws_care.certificate.medical_certificate import MedicalCertificate
                from gws_care.exam.exam import Exam
                from gws_care.prescription.prescription import Prescription
                from gws_care.visit.campaign_visit_service import CampaignVisitService

                visit = CampaignVisitService.get_visit(visit_id)

                if self.is_patient_user:
                    if not self._linked_patient_id or str(visit.patient_id) != str(self._linked_patient_id):
                        self.consultation = None
                        self.error_message = "Access denied."
                        return

                account_name = ""
                if visit.billing_account_id:
                    try:
                        account_name = visit.billing_account.name
                    except Exception:
                        pass
                elif visit.patient_id:
                    # Fall back to the patient's own default billing account
                    # when none was set specifically on this visit
                    try:
                        if visit.patient.billing_account_id:
                            account_name = visit.patient.billing_account.name
                    except Exception:
                        pass

                patient_gender = ""
                try:
                    patient_gender = getattr(visit.patient, "gender", "") or ""
                except Exception:
                    pass

                clinic_doctor_name = ""
                if visit.doctor_id:
                    try:
                        clinic_doctor_name = visit.doctor.get_full_name()
                    except Exception:
                        pass
                work_doctor_name = ""
                if visit.work_doctor_id:
                    try:
                        wd = visit.work_doctor
                        work_doctor_name = f"{wd.first_name} {wd.last_name}".strip()
                    except Exception:
                        pass

                self.consultation = ConsultationDTO(
                    id=str(visit.id),
                    visit_number=visit.visit_number,
                    patient_name=visit.patient.get_full_name() if visit.patient_id else "",
                    patient_id=str(visit.patient_id) if visit.patient_id else "",
                    patient_gender=patient_gender,
                    account_name=account_name,
                    account_id=str(visit.billing_account_id) if visit.billing_account_id else "",
                    scheduled_at=visit.scheduled_at.isoformat() if visit.scheduled_at else "",
                    status=visit.consultation_visit_status.value if visit.consultation_visit_status else "",
                    status_label=visit.consultation_visit_status.get_label() if visit.consultation_visit_status else "",
                    cancellation_reason=getattr(visit, "cancellation_reason", None) or "",
                    reason_for_visit=getattr(visit, "reason_for_visit", None) or "",
                    medical_history=getattr(visit, "medical_history", None) or "",
                    is_campaign=bool(visit.campaign_id),
                    clinic_doctor_id=str(visit.doctor_id) if visit.doctor_id else "",
                    clinic_doctor_name=clinic_doctor_name,
                    work_doctor_id=str(visit.work_doctor_id) if visit.work_doctor_id else "",
                    work_doctor_name=work_doctor_name,
                )

                # Populate motif/history form fields
                self.form_reason = self.consultation.reason_for_visit
                self.form_history = self.consultation.medical_history

                # Linked exams → tab headers (creation order, exclude cancelled)
                from gws_care.exam.exam_type import ExamStatus
                exams = list(
                    Exam.select()
                    .where(
                        (Exam.visit == visit.id)
                        & (Exam.status != ExamStatus.CANCELLED)
                    )
                    .order_by(Exam.created_at.asc())
                )

                def _exam_label(e) -> str:
                    ref_id = getattr(e, "exam_type_ref_id", None) or ""
                    if ref_id:
                        try:
                            from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                            ref = ExamTypeRef.get_or_none(ExamTypeRef.id == ref_id)
                            if ref:
                                return ref.name
                        except Exception:
                            pass
                    return e.exam_type.get_label() if hasattr(e.exam_type, "get_label") else e.exam_type.value

                self.exams = [
                    ExamRowDTO(
                        id=str(e.id),
                        exam_date=e.exam_date.isoformat(),
                        exam_type=e.exam_type.value,
                        exam_type_label=_exam_label(e),
                        status=e.status.value,
                        status_label=e.status.get_label() if hasattr(e.status, "get_label") else e.status.value,
                    )
                    for e in exams
                ]
                self.exam_tab_headers = [
                    ExamTabHeaderVM(
                        exam_id=str(e.id),
                        exam_type_label=_exam_label(e),
                        status=e.status.value,
                    )
                    for e in exams
                ]

                # Linked prescriptions
                prescriptions = list(
                    Prescription.select()
                    .where(Prescription.visit == visit.id)
                    .order_by(Prescription.prescription_date.desc())
                )
                self.prescriptions = [
                    PrescriptionRowDTO(
                        id=str(p.id),
                        prescription_date=p.prescription_date.isoformat() if p.prescription_date else "",
                        diagnosis=p.diagnosis or "",
                        prescribed_by_name=(
                            f"{p.prescribed_by.first_name} {p.prescribed_by.last_name}"
                            if p.prescribed_by_id else ""
                        ),
                        drug_count=len(p.drugs) if p.drugs else 0,
                        is_archived=bool(p.is_archived),
                    )
                    for p in prescriptions
                ]

                # Linked certificates
                certificates = list(
                    MedicalCertificate.select()
                    .where(MedicalCertificate.visit == visit.id)
                    .order_by(MedicalCertificate.issue_date.desc())
                )
                self.certificates = [
                    CertificateRowDTO(
                        id=str(c.id),
                        issue_date=c.issue_date.isoformat() if c.issue_date else "",
                        conclusion=c.conclusion or "",
                        is_fit_for_work=bool(c.is_fit_for_work),
                        issued_by_name=(
                            f"{c.issued_by.first_name} {c.issued_by.last_name}"
                            if c.issued_by_id else ""
                        ),
                    )
                    for c in certificates
                ]

        except Exception as e:
            self.error_message = f"Consultation introuvable : {e}"
            self.consultation = None
        finally:
            self.is_loading = False

    async def _refresh_exam_headers(self):
        """Refresh only the exam tab header statuses without full reload."""
        if not self.consultation:
            return
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam

                from gws_care.exam.exam_type import ExamStatus
                exams = list(
                    Exam.select()
                    .where(
                        (Exam.visit == self.consultation.id)
                        & (Exam.status != ExamStatus.CANCELLED)
                    )
                    .order_by(Exam.created_at.asc())
                )

                def _exam_label(e) -> str:
                    ref_id = getattr(e, "exam_type_ref_id", None) or ""
                    if ref_id:
                        try:
                            from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                            ref = ExamTypeRef.get_or_none(ExamTypeRef.id == ref_id)
                            if ref:
                                return ref.name
                        except Exception:
                            pass
                    return e.exam_type.get_label() if hasattr(e.exam_type, "get_label") else e.exam_type.value

                self.exam_tab_headers = [
                    ExamTabHeaderVM(
                        exam_id=str(e.id),
                        exam_type_label=_exam_label(e),
                        status=e.status.value,
                    )
                    for e in exams
                ]
        except Exception:
            pass

    async def _load_exam_params(self, exam_id: str):
        """Load ExamParameterResult rows for the given exam."""
        if not exam_id:
            return
        self.is_loading_params = True
        self.active_exam_params = []
        self.active_exam_audit_log = []
        self.modified_param_ids = []
        self.exam_action = "save"
        self.active_exam_id = exam_id
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_parameter_result import ExamParameterResult
                from gws_care.exam_type_ref.exam_parameter import ExamParameter

                from gws_care.exam.exam_type import ExamStatus as _ExamStatus
                exam = Exam.get_by_id(exam_id)
                self.active_exam_date = exam.exam_date.isoformat()
                self.active_exam_interpretation = exam.interpretation or ""
                self.active_exam_work_doctor_interpretation = getattr(exam, "work_doctor_interpretation", None) or ""
                exam_type_ref_id = str(exam.exam_type_ref_id) if exam.exam_type_ref_id else ""
                self.active_exam_type_ref_id = exam_type_ref_id

                if not exam_type_ref_id:
                    self.active_exam_status = exam.status.value
                    self.active_exam_params = []
                    return

                # None = never customized -> show all active params (default).
                # [] = explicitly emptied (all tests removed one by one) -> show none.
                requested_ids_raw = exam.requested_param_ids

                all_params = list(
                    ExamParameter.select()
                    .where(
                        (ExamParameter.exam_type_ref == exam_type_ref_id)
                        & (ExamParameter.is_active == True)
                    )
                    .order_by(ExamParameter.display_order)
                )

                if requested_ids_raw is not None:
                    requested_ids = set(str(i) for i in requested_ids_raw)
                    all_params = [p for p in all_params if str(p.id) in requested_ids]

                existing = {
                    str(r.parameter_id): r
                    for r in ExamParameterResult.select()
                    .where(ExamParameterResult.exam == exam_id)
                }

                # Auto-fix: if results already exist in DB but status is still TODO,
                # advance status so the UI reflects reality
                if exam.status == _ExamStatus.TODO and existing:
                    exam.status = _ExamStatus.IN_PROGRESS_RESULTS
                    exam.save()

                self.active_exam_status = exam.status.value

                def _ref_label(param) -> str:
                    rl = param.ref_low
                    rh = param.ref_high
                    if rl is not None and rh is not None:
                        return f"{rl} – {rh}"
                    if rl is not None:
                        return f"≥ {rl}"
                    if rh is not None:
                        return f"≤ {rh}"
                    return ""

                def _status_color_from_status(s: str) -> str:
                    return {
                        "NORMAL": "green", "NEGATIVE": "green",
                        "LOW": "orange", "HIGH": "orange",
                        "CRITICAL_LOW": "red", "CRITICAL_HIGH": "red",
                        "POSITIVE": "red",
                    }.get(s, "gray")

                rows = []
                for param in all_params:
                    result = existing.get(str(param.id))
                    status = result.status if result else "PENDING"
                    rows.append(ExamParamRowVM(
                        result_id=str(result.id) if result else "",
                        param_id=str(param.id),
                        param_name=param.name,
                        unit=param.unit or "",
                        value_type=param.value_type,
                        is_computed=bool(param.is_computed),
                        is_required=bool(param.is_required),
                        value_numeric=(
                            str(result.value_numeric)
                            if result and result.value_numeric is not None else ""
                        ),
                        value_text=result.value_text or "" if result else "",
                        value_boolean=(
                            "true" if (result and result.value_boolean is True)
                            else ("false" if (result and result.value_boolean is False) else "")
                        ),
                        status=status,
                        status_color=_status_color_from_status(status),
                        ref_range_label=_ref_label(param),
                    ))

                self.active_exam_params = rows

                # Action history (add/remove a test, modify a value…)
                from gws_care.exam.exam_audit_entry import ExamAuditAction, ExamAuditEntry
                audit_rows = list(
                    ExamAuditEntry.select()
                    .where(ExamAuditEntry.exam == exam_id)
                    .order_by(ExamAuditEntry.created_at.desc())
                )
                audit_log = []
                for entry in audit_rows:
                    try:
                        user_name = f"{entry.created_by.first_name} {entry.created_by.last_name}".strip()
                    except Exception:
                        user_name = ""
                    audit_log.append(ExamAuditEntryVM(
                        action_label=ExamAuditAction(entry.action).get_label(),
                        details=entry.details or "",
                        user_name=user_name or "Utilisateur",
                        created_at=entry.created_at.strftime("%d/%m/%Y %H:%M"),
                    ))
                self.active_exam_audit_log = audit_log

        except Exception as e:
            self.error_message = f"Erreur chargement paramètres : {e}"
        finally:
            self.is_loading_params = False
