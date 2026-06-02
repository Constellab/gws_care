"""State management for the exam detail page."""

import re
import uuid
from typing import Any

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


def _auto_detect_status(value_str: str, ref_range: str, critical_low: str = "", critical_high: str = "") -> str | None:
    """Parse reference_range and return status for a numeric value.

    Levels (same as campaign workflow):
      critical_high | high | normal | low | critical_low
    Supported ref_range formats: '4.5–11.0', '4.5-11.0', '<200', '>40'.
    Returns None if value or range cannot be parsed numerically.
    """
    if not value_str.strip():
        return None
    try:
        val = float(value_str.replace(",", ".").strip())
    except ValueError:
        return None

    # Check critical thresholds first
    try:
        if critical_low and val < float(critical_low):
            return "critical"
        if critical_high and val > float(critical_high):
            return "critical"
    except (ValueError, TypeError):
        pass

    if not ref_range.strip():
        return None
    ref = ref_range.strip()
    # Range: X–Y  (en-dash, em-dash, or plain hyphen)
    m = re.match(r'^([0-9.]+)\s*[\u2013\u2014\-]\s*([0-9.]+)$', ref)
    if m:
        low, high = float(m.group(1)), float(m.group(2))
        if val < low:
            return "low"
        if val > high:
            return "high"
        return "normal"
    # Upper bound only: <X
    m = re.match(r'^<\s*([0-9.]+)$', ref)
    if m:
        return "high" if val > float(m.group(1)) else "normal"
    # Lower bound only: >X
    m = re.match(r'^>\s*([0-9.]+)$', ref)
    if m:
        return "low" if val < float(m.group(1)) else "normal"
    return None


class ExamDetailDTO(BaseModel):
    id: str
    exam_date: str
    exam_type: str
    exam_type_label: str
    status: str
    reason_for_visit: str | None = None
    medical_history: str | None = None
    weight: float | None = None
    height: float | None = None
    bmi: float | None = None
    blood_pressure: str | None = None
    heart_rate: float | None = None
    temperature: float | None = None
    conclusion: str | None = None
    patient_id: str
    patient_name: str
    requested_param_ids: list[str] = []
    consultation_id: str = ""   # non-empty when exam belongs to a Consultation
    prescribed_exam_ref_ids: list[str] = []  # follow-up exams prescribed by doctor


class ConsultationContextDTO(BaseModel):
    """Clinical context from the parent Consultation, shown read-only on exam detail."""

    id: str
    consultation_date: str
    reason_for_visit: str = ""
    medical_history: str = ""
    weight: float | None = None
    height: float | None = None
    bmi: float | None = None
    blood_pressure: str | None = None
    heart_rate: float | None = None
    temperature: float | None = None
    conclusion: str | None = None


class RequestedParamDTO(BaseModel):
    """A prescribed lab parameter displayed on the exam detail page."""

    id: str
    name: str
    unit: str = ""
    is_resulted: bool = False  # True if a lab_result row already exists for this param name




class AvailableParamOption(BaseModel):
    """One parameter available from the exam type referential."""

    id: str
    name: str
    unit: str = ""
    ref_range: str = ""
    critical_low: str = ""   # raw float string; empty = no threshold
    critical_high: str = ""  # raw float string; empty = no threshold


class FollowUpExamOption(BaseModel):
    """One exam type that the doctor can prescribe as a follow-up."""

    id: str
    name: str
    category_label: str = ""


class LabResultRowDTO(BaseModel):
    """One row in the lab results table."""

    id: str = ""
    parameter: str = ""
    unit: str = ""
    value: str = ""
    reference_range: str = ""
    status: str = "normal"  # normal | high | low | critical


class ExamResultDetailDTO(BaseModel):
    result_data: dict[str, Any] = {}
    image_paths: list[str] = []


class CertificateRowDTO(BaseModel):
    id: str
    issue_date: str
    conclusion: str
    is_fit_for_work: bool
    restrictions: str | None = None
    issued_by_name: str | None = None


class ExamFileRowDTO(BaseModel):
    id: str
    original_name: str
    stored_filename: str
    mime_type: str | None = None
    file_size: int | None = None
    file_size_label: str = ""  # human-readable size, computed at load time
    resource_download_url: str = ""  # browser-accessible gws_core download URL
    document_type: str = ""  # DocumentType enum value, empty means unset


class ExamDetailState(RoleState):
    """State for the exam detail / result-entry page."""

    exam: ExamDetailDTO | None = None
    consultation_context: ConsultationContextDTO | None = None
    result: ExamResultDetailDTO | None = None
    certificates: list[CertificateRowDTO] = []
    exam_files: list[ExamFileRowDTO] = []
    is_loading: bool = False
    error_message: str = ""
    is_edit_mode: bool = False

    # Medical sections form
    form_reason_for_visit: str = ""
    form_medical_history: str = ""
    form_weight: str = ""
    form_height: str = ""
    form_bmi: str = ""
    form_blood_pressure: str = ""
    form_heart_rate: str = ""
    form_temperature: str = ""
    form_conclusion: str = ""
    is_saving_sections: bool = False

    # Laboratory results
    lab_results: list[LabResultRowDTO] = []
    available_params: list[AvailableParamOption] = []
    requested_params: list[RequestedParamDTO] = []  # parameters prescribed by the doctor
    new_lab_selected_preset: str = ""
    new_lab_parameter: str = ""
    new_lab_unit: str = ""
    new_lab_value: str = ""
    new_lab_reference_range: str = ""

    # File upload on detail page
    is_uploading_file: bool = False

    # Prescribe follow-up exams (doctor selects ExamTypeRef items from the clinical exam form)
    prescribe_exam_options: list[FollowUpExamOption] = []
    prescribe_form_open: bool = False
    prescribe_selected_ids: list[str] = []  # toggled by doctor
    is_saving_prescription: bool = False
    is_submitting: bool = False  # True while submit_exam is running

    @rx.var
    def result_data_items(self) -> list[list[str]]:
        """Convert result_data dict to [[key, value], ...] list for rx.foreach."""
        if self.result is None:
            return []
        return [[str(k), str(v)] for k, v in self.result.result_data.items()]

    @rx.event
    async def on_load(self):
        await self._load_roles()
        await self._load_exam()
        self.is_edit_mode = False

    @rx.event
    def set_edit_mode(self, value: bool):
        self.is_edit_mode = value

    @rx.event
    async def notify_doctor_results_ready(self):
        """Explicitly notify the prescribing doctor that lab results are ready."""
        if not self.exam or not self.exam.requested_param_ids:
            yield rx.toast.error("Aucune analyse prescrite associée à cet examen.")
            return
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                from gws_care.notification.notification_service import NotificationService
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_care_role import UserCareRole
                exam_obj = Exam.get_or_none(Exam.id == self.exam_id_param)
                notified_ids: set[str] = set()
                msg = (
                    f"Résultats disponibles — {self.exam.patient_name} ({self.exam.exam_type_label})"
                )
                if exam_obj and exam_obj.created_by_id:
                    NotificationService.create_bell(
                        user_id=str(exam_obj.created_by_id),
                        message=msg,
                    )
                    notified_ids.add(str(exam_obj.created_by_id))
                for ur in UserCareRole.select().where(
                    UserCareRole.role == CareRole.MEDECIN_PSC.value
                ):
                    uid = str(ur.user_id)
                    if uid not in notified_ids:
                        NotificationService.create_bell(user_id=uid, message=msg)
            yield rx.toast.success("Médecin notifié.")
        except Exception as exc:
            yield rx.toast.error(f"Erreur lors de la notification : {exc}")

    @rx.event
    def go_back(self):
        if self.exam:
            return rx.redirect(f"/patient/{self.exam.patient_id}")
        return rx.redirect("/")

    @rx.event
    def set_form_reason_for_visit(self, value: str):
        self.form_reason_for_visit = value

    @rx.event
    def set_form_medical_history(self, value: str):
        self.form_medical_history = value

    @rx.event
    def set_form_weight(self, value: str):
        self.form_weight = value

    @rx.event
    def set_form_height(self, value: str):
        self.form_height = value

    @rx.event
    def set_form_bmi(self, value: str):
        self.form_bmi = value

    @rx.event
    def set_form_blood_pressure(self, value: str):
        self.form_blood_pressure = value

    @rx.event
    def set_form_heart_rate(self, value: str):
        self.form_heart_rate = value

    @rx.event
    def set_form_temperature(self, value: str):
        self.form_temperature = value

    @rx.event
    def set_form_conclusion(self, value: str):
        self.form_conclusion = value

    @rx.event
    def select_available_param(self, param_id: str):
        """Auto-fill parameter fields when a referential parameter is selected."""
        self.new_lab_selected_preset = param_id
        if not param_id:
            self.new_lab_parameter = ""
            self.new_lab_unit = ""
            self.new_lab_reference_range = ""
        else:
            for p in self.available_params:
                if p.id == param_id:
                    self.new_lab_parameter = p.name
                    self.new_lab_unit = p.unit
                    self.new_lab_reference_range = p.ref_range
                    break

    @rx.event
    def start_edit_lab_row(self, row_id: str):
        """No-op kept for compatibility — rows are now edited inline."""
        pass

    @rx.event
    def set_lab_row_value(self, row_id: str, value: str):
        """Update the value of a lab result row and auto-compute its status."""
        # Build a lookup of param name → critical thresholds from the referential
        crit_map: dict[str, tuple[str, str]] = {
            p.name: (p.critical_low, p.critical_high)
            for p in self.available_params
        }
        self.lab_results = [
            LabResultRowDTO(
                id=row.id,
                parameter=row.parameter,
                unit=row.unit,
                value=value if row.id == row_id else row.value,
                reference_range=row.reference_range,
                status=(
                    (_auto_detect_status(
                        value, row.reference_range,
                        *crit_map.get(row.parameter, ("", ""))
                    ) or "normal")
                    if row.id == row_id
                    else row.status
                ),
            )
            for row in self.lab_results
        ]

    @rx.event
    def set_new_lab_parameter(self, value: str):
        self.new_lab_parameter = value

    @rx.event
    def set_new_lab_unit(self, value: str):
        self.new_lab_unit = value

    @rx.event
    def set_new_lab_value(self, value: str):
        self.new_lab_value = value

    @rx.event
    def set_new_lab_reference_range(self, value: str):
        self.new_lab_reference_range = value

    @rx.event
    def add_lab_row(self):
        """Add a new row to lab results (parameter name is required). Status is auto-detected."""
        if not self.new_lab_parameter.strip():
            return
        # Look up critical thresholds for this param from the referential
        crit_low, crit_high = "", ""
        for p in self.available_params:
            if p.name == self.new_lab_parameter.strip():
                crit_low, crit_high = p.critical_low, p.critical_high
                break
        auto = _auto_detect_status(
            self.new_lab_value,
            self.new_lab_reference_range,
            crit_low,
            crit_high,
        )
        final_status = auto if auto is not None else "normal"
        self.lab_results = self.lab_results + [
            LabResultRowDTO(
                id=str(uuid.uuid4()),
                parameter=self.new_lab_parameter.strip(),
                unit=self.new_lab_unit.strip(),
                value=self.new_lab_value.strip(),
                reference_range=self.new_lab_reference_range.strip(),
                status=final_status,
            )
        ]
        self.new_lab_selected_preset = ""
        self.new_lab_parameter = ""
        self.new_lab_unit = ""
        self.new_lab_value = ""
        self.new_lab_reference_range = ""

    @rx.event
    def remove_lab_row(self, row_id: str):
        """Remove a lab result row by its id."""
        self.lab_results = [row for row in self.lab_results if row.id != row_id]

    @rx.event
    async def save_sections(self):
        """Save the medical sections of the exam."""
        self.is_saving_sections = True
        self.error_message = ""

        def _to_float(val: str) -> float | None:
            val = val.strip()
            if not val:
                return None
            try:
                return float(val)
            except ValueError:
                return None

        try:
            with await self.authenticate_user():
                from gws_care.exam.exam_dto import UpdateExamSectionsDTO
                from gws_care.exam.exam_service import ExamService

                dto = UpdateExamSectionsDTO(
                    reason_for_visit=self.form_reason_for_visit or None,
                    medical_history=self.form_medical_history or None,
                    weight=_to_float(self.form_weight),
                    height=_to_float(self.form_height),
                    bmi=_to_float(self.form_bmi),
                    blood_pressure=self.form_blood_pressure or None,
                    heart_rate=_to_float(self.form_heart_rate),
                    temperature=_to_float(self.form_temperature),
                    conclusion=self.form_conclusion or None,
                    lab_results=[row.dict() for row in self.lab_results],
                )
                ExamService.update_sections(self.exam_id_param, dto)
            # Refresh the local exam DTO
            if self.exam:
                self.exam = self.exam.copy(update={
                    "reason_for_visit": self.form_reason_for_visit or None,
                    "medical_history": self.form_medical_history or None,
                    "weight": _to_float(self.form_weight),
                    "height": _to_float(self.form_height),
                    "bmi": _to_float(self.form_bmi),
                    "blood_pressure": self.form_blood_pressure or None,
                    "heart_rate": _to_float(self.form_heart_rate),
                    "temperature": _to_float(self.form_temperature),
                    "conclusion": self.form_conclusion or None,
                })
            yield rx.toast.success("Sections saved.")
            # Refresh requested_params completion status after new lab results are saved
            self._refresh_requested_params_status()
            # Notify the prescribing doctor (exam creator) when lab results are submitted
            if self.exam and self.exam.requested_param_ids and self.lab_results:
                try:
                    with await self.authenticate_user():
                        from gws_care.exam.exam import Exam
                        from gws_care.notification.notification_service import NotificationService
                        from gws_care.role.care_role import CareRole
                        from gws_care.role.user_care_role import UserCareRole
                        exam_obj = Exam.get_or_none(Exam.id == self.exam_id_param)
                        notified_ids: set[str] = set()
                        # Notify exam creator if they have a doctor role
                        if exam_obj and exam_obj.created_by_id:
                            creator_role = UserCareRole.get_or_none(
                                (UserCareRole.user == exam_obj.created_by_id)
                            )
                            if creator_role:
                                NotificationService.create_bell(
                                    user_id=str(exam_obj.created_by_id),
                                    message=(
                                        f"Résultats disponibles \u2014 {self.exam.patient_name} ({self.exam.exam_type_label})"
                                    ),
                                )
                                notified_ids.add(str(exam_obj.created_by_id))
                        # Also notify all MEDECIN_PSC not yet notified
                        for ur in UserCareRole.select().where(
                            UserCareRole.role == CareRole.MEDECIN_PSC.value
                        ):
                            uid = str(ur.user_id)
                            if uid not in notified_ids:
                                NotificationService.create_bell(
                                    user_id=uid,
                                    message=(
                                        f"Résultats disponibles \u2014 {self.exam.patient_name} ({self.exam.exam_type_label})"
                                    ),
                                )
                except Exception as notify_exc:
                    print(f"[ExamDetailState] Doctor notification failed: {notify_exc}")
        except Exception as e:
            self.error_message = f"Error saving sections: {e}"
        finally:
            self.is_saving_sections = False

    # ── Prescribe follow-up exams ─────────────────────────────────────────────

    @rx.event
    async def open_prescribe_dialog(self):
        """Open the dialog for prescribing follow-up exams. Loads available exam types."""
        self.prescribe_form_open = True
        self.prescribe_selected_ids = list(self.exam.prescribed_exam_ref_ids) if self.exam else []
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                refs = list(
                    ExamTypeRef.select()
                    .where(ExamTypeRef.is_active == True)  # noqa: E712
                    .order_by(ExamTypeRef.category, ExamTypeRef.name)
                )
                self.prescribe_exam_options = [
                    FollowUpExamOption(
                        id=str(r.id),
                        name=r.name,
                        category_label=r.get_category_label(),
                    )
                    for r in refs
                ]
        except Exception as exc:
            self.error_message = str(exc)

    @rx.event
    def close_prescribe_dialog(self):
        self.prescribe_form_open = False

    @rx.event
    def toggle_prescribe_exam(self, ref_id: str):
        """Toggle an exam type in the prescription selection."""
        if ref_id in self.prescribe_selected_ids:
            self.prescribe_selected_ids = [x for x in self.prescribe_selected_ids if x != ref_id]
        else:
            self.prescribe_selected_ids = self.prescribe_selected_ids + [ref_id]

    @rx.event
    async def save_prescribed_exams(self):
        """Persist the prescribed follow-up exam list to the Exam record."""
        self.is_saving_prescription = True
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam_dto import UpdateExamSectionsDTO
                from gws_care.exam.exam_service import ExamService
                # Only update prescribed_exam_ref_ids; pass None for other fields to leave them unchanged
                dto = UpdateExamSectionsDTO(
                    prescribed_exam_ref_ids=list(self.prescribe_selected_ids),
                )
                ExamService.update_sections(self.exam_id_param, dto)
            if self.exam:
                self.exam = self.exam.copy(update={
                    "prescribed_exam_ref_ids": list(self.prescribe_selected_ids),
                })
            self.prescribe_form_open = False
            yield rx.toast.success("Ordonnances d'examens enregistrées.")
        except Exception as exc:
            self.error_message = str(exc)
            yield rx.toast.error(f"Erreur : {exc}")
        finally:
            self.is_saving_prescription = False

    @rx.event
    async def submit_exam(self):
        """Mark exam as PENDING (lab results to be entered). Keeps draft data intact."""
        if not self.exam:
            return
        self.is_submitting = True
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam_service import ExamService
                ExamService.set_pending(self.exam_id_param)
            if self.exam:
                self.exam = self.exam.copy(update={"status": "pending"})
            yield rx.toast.success("Examen soumis — en attente de résultats laboratoire.")
        except Exception as e:
            yield rx.toast.error(f"Erreur lors de la soumission : {e}")
        finally:
            self.is_submitting = False

    def _refresh_requested_params_status(self):
        """Update is_resulted flags on requested_params based on current lab_results."""
        if not self.requested_params:
            return
        resulted_names = {row.parameter.lower() for row in self.lab_results}
        self.requested_params = [
            RequestedParamDTO(
                id=p.id,
                name=p.name,
                unit=p.unit,
                is_resulted=p.name.lower() in resulted_names,
            )
            for p in self.requested_params
        ]

    async def _load_exam(self):
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return

        exam_id = self.exam_id_param
        if not exam_id:
            self.error_message = "No exam ID in URL"
            return

        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.certificate.medical_certificate import MedicalCertificate
                from gws_care.exam.exam_result_service import ExamResultService
                from gws_care.exam.exam_service import ExamService
                from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef

                exam = ExamService.get_exam(exam_id)
                patient = exam.patient

                # Resolve exam type label: prefer referential name when available
                from gws_care.exam_type_ref.exam_parameter import ExamParameter
                if exam.exam_type_ref_id:
                    ref = ExamTypeRef.get_or_none(ExamTypeRef.id == exam.exam_type_ref_id)
                    exam_type_label = ref.name if ref else exam.exam_type.get_label()
                    params = (
                        ExamParameter.select()
                        .where(ExamParameter.exam_type_ref == exam.exam_type_ref_id)
                        .order_by(ExamParameter.display_order)
                    )
                    self.available_params = [
                        AvailableParamOption(
                            id=str(p.id),
                            name=p.name,
                            unit=p.unit or "",
                            ref_range=(
                                f"{p.ref_low}\u2013{p.ref_high}"
                                if p.ref_low is not None and p.ref_high is not None
                                else (f">{p.ref_low}" if p.ref_low is not None else (f"<{p.ref_high}" if p.ref_high is not None else ""))
                            ),
                            critical_low=str(p.critical_low) if p.critical_low is not None else "",
                            critical_high=str(p.critical_high) if p.critical_high is not None else "",
                        )
                        for p in params
                    ]
                else:
                    exam_type_label = exam.exam_type.get_label()
                    self.available_params = []

                self.exam = ExamDetailDTO(
                    id=str(exam.id),
                    exam_date=exam.exam_date.isoformat(),
                    exam_type=exam.exam_type.value,
                    exam_type_label=exam_type_label,
                    status=exam.status.value,
                    reason_for_visit=exam.reason_for_visit,
                    medical_history=exam.medical_history,
                    weight=exam.weight,
                    height=exam.height,
                    bmi=exam.bmi,
                    blood_pressure=exam.blood_pressure,
                    heart_rate=exam.heart_rate,
                    temperature=exam.temperature,
                    conclusion=exam.conclusion,
                    patient_id=str(patient.id),
                    patient_name=f"{patient.first_name} {patient.last_name}",
                    requested_param_ids=exam.requested_param_ids or [],
                    consultation_id=exam.consultation_id or "",
                    prescribed_exam_ref_ids=exam.prescribed_exam_ref_ids or [],
                )

                # Load consultation context if this exam belongs to one
                if exam.consultation_id:
                    from gws_care.consultation.consultation import Consultation
                    consult = Consultation.get_or_none(Consultation.id == exam.consultation_id)
                    if consult:
                        self.consultation_context = ConsultationContextDTO(
                            id=str(consult.id),
                            consultation_date=consult.consultation_date.isoformat() if consult.consultation_date else "",
                            reason_for_visit=consult.reason_for_visit or "",
                            medical_history=consult.medical_history or "",
                            weight=consult.weight,
                            height=consult.height,
                            bmi=consult.bmi,
                            blood_pressure=consult.blood_pressure,
                            heart_rate=consult.heart_rate,
                            temperature=consult.temperature,
                            conclusion=consult.conclusion,
                        )
                    else:
                        self.consultation_context = None
                else:
                    self.consultation_context = None
                result = ExamResultService.get_result_for_exam(exam_id)
                if result:
                    self.result = ExamResultDetailDTO(
                        result_data=result.result_data or {},
                        image_paths=result.image_paths or [],
                    )
                else:
                    self.result = None

                self.form_reason_for_visit = exam.reason_for_visit or ""
                self.form_medical_history = exam.medical_history or ""
                self.form_weight = str(exam.weight) if exam.weight is not None else ""
                self.form_height = str(exam.height) if exam.height is not None else ""
                self.form_bmi = str(exam.bmi) if exam.bmi is not None else ""
                self.form_blood_pressure = exam.blood_pressure or ""
                self.form_heart_rate = str(exam.heart_rate) if exam.heart_rate is not None else ""
                self.form_temperature = str(exam.temperature) if exam.temperature is not None else ""
                self.form_conclusion = exam.conclusion or ""
                self.lab_results = [
                    LabResultRowDTO(
                        id=r.get("id") or str(uuid.uuid4()),
                        parameter=r.get("parameter", ""),
                        unit=r.get("unit", ""),
                        value=r.get("value", ""),
                        reference_range=r.get("reference_range", ""),
                        status=r.get("status", "normal"),
                    )
                    for r in (exam.lab_results or [])
                ]

                # Build requested_params from prescribed IDs and
                # pre-populate lab_results rows for any not yet filled
                req_ids: list[str] = exam.requested_param_ids or []
                if req_ids:
                    req_params = list(
                        ExamParameter.select()
                        .where(ExamParameter.id.in_(req_ids))
                        .order_by(ExamParameter.display_order)
                    )
                    resulted_names = {row.parameter.lower() for row in self.lab_results}
                    self.requested_params = [
                        RequestedParamDTO(
                            id=str(p.id),
                            name=p.name,
                            unit=p.unit or "",
                            is_resulted=p.name.lower() in resulted_names,
                        )
                        for p in req_params
                    ]
                    # Pre-populate empty rows for prescribed params not yet entered
                    for p in req_params:
                        if p.name.lower() not in resulted_names:
                            ref_range = (
                                f"{p.ref_low}\u2013{p.ref_high}"
                                if p.ref_low is not None and p.ref_high is not None
                                else (
                                    f">{p.ref_low}" if p.ref_low is not None
                                    else (f"<{p.ref_high}" if p.ref_high is not None else "")
                                )
                            )
                            self.lab_results = self.lab_results + [
                                LabResultRowDTO(
                                    id=str(uuid.uuid4()),
                                    parameter=p.name,
                                    unit=p.unit or "",
                                    value="",
                                    reference_range=ref_range,
                                    status="normal",
                                )
                            ]
                else:
                    self.requested_params = []

                certs = list(
                    MedicalCertificate.select()
                    .where(MedicalCertificate.exam == exam_id)
                    .order_by(MedicalCertificate.issue_date.desc())
                )
                self.certificates = [
                    CertificateRowDTO(
                        id=str(c.id),
                        issue_date=c.issue_date.isoformat(),
                        conclusion=c.conclusion,
                        is_fit_for_work=c.is_fit_for_work,
                        restrictions=c.restrictions,
                        issued_by_name=(
                            f"{c.issued_by.first_name} {c.issued_by.last_name}"
                            if c.issued_by_id
                            else None
                        ),
                    )
                    for c in certs
                ]

                from gws_care.exam.exam_file_service import ExamFileService
                files = ExamFileService.list_files_for_exam(exam_id)
                def _size_label(n: int | None) -> str:
                    if n is None:
                        return ""
                    if n >= 1_048_576:
                        return f"{n / 1_048_576:.1f} MB"
                    if n >= 1024:
                        return f"{n // 1024} KB"
                    return f"{n} B"

                self.exam_files = [
                    ExamFileRowDTO(
                        id=str(f.id),
                        original_name=f.original_name,
                        stored_filename=f.stored_filename or "",
                        mime_type=f.mime_type,
                        file_size=f.file_size,
                        file_size_label=_size_label(f.file_size),
                        resource_download_url=(
                            ExamFileService.get_resource_download_url(f.resource_id)
                            if f.resource_id
                            else ""
                        ),
                        document_type=f.document_type or "",
                    )
                    for f in files
                ]
        except Exception as e:
            self.error_message = f"Error loading exam: {e}"
        finally:
            self.is_loading = False

    # ── File upload on detail page ────────────────────────────────────────────

    @rx.event
    async def handle_file_upload(self, files: list[rx.UploadFile]):
        """Upload additional files, register each as a gws_core Resource, and attach to the exam."""
        import mimetypes

        exam_id = self.exam_id_param
        if not exam_id:
            yield rx.toast.error("No exam loaded.")
            return

        self.is_uploading_file = True
        yield

        try:
            from gws_care.exam.exam_file_service import ExamFileService

            # Read all bytes first (async) before entering the sync auth context
            uploads: list[tuple[str, bytes, str]] = []
            for uf in files:
                data = await uf.read()
                mime = mimetypes.guess_type(uf.filename or "")[0] or "application/octet-stream"
                uploads.append((uf.filename or "file", data, mime))

            # Auth context required by ResourceModel._before_insert (ModelWithUser)
            with await self.authenticate_user():
                for original_name, file_bytes, mime in uploads:
                    ExamFileService.create_file(
                        exam_id=exam_id,
                        original_name=original_name,
                        file_bytes=file_bytes,
                        mime_type=mime,
                    )

            await self._load_exam()
            yield rx.toast.success("File(s) attached.")
        except Exception as e:
            yield rx.toast.error(f"Upload failed: {e}")
        finally:
            self.is_uploading_file = False

    @rx.event
    async def set_file_document_type(self, file_id: str, document_type: str):
        """Update the document type of an attached file and re-tag the gws_core resource."""
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam_file_service import ExamFileService
                ExamFileService.update_document_type(file_id, document_type)
            # Update local state without full reload
            self.exam_files = [
                ExamFileRowDTO(**{**ef.dict(), "document_type": document_type})
                if ef.id == file_id
                else ef
                for ef in self.exam_files
            ]
        except Exception as e:
            self.error_message = f"Error updating document type: {e}"

    @rx.event
    async def delete_file(self, file_id: str):
        """Delete an attached file."""
        try:
            from gws_care.exam.exam_file_service import ExamFileService
            ExamFileService.delete_file(file_id)
            await self._load_exam()
        except Exception as e:
            self.error_message = f"Error deleting file: {e}"
