"""State management for the exam detail page."""

import uuid
from typing import Any

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


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
    interpretation: str | None = None
    interpreted_by_name: str = ""
    patient_id: str
    patient_name: str
    visit_id: str = ""


# ── Predefined laboratory parameters ────────────────────────────────────────

PREDEFINED_LAB_PARAMS: list[dict] = [
    # Complete Blood Count (CBC)
    {"name": "WBC", "unit": "10³/μL", "reference_range": "4.5–11.0"},
    {"name": "RBC", "unit": "10⁶/μL", "reference_range": "4.5–5.5"},
    {"name": "Hemoglobin", "unit": "g/dL", "reference_range": "12.0–17.5"},
    {"name": "Hematocrit", "unit": "%", "reference_range": "36–50"},
    {"name": "MCV", "unit": "fL", "reference_range": "80–100"},
    {"name": "MCH", "unit": "pg", "reference_range": "27–33"},
    {"name": "MCHC", "unit": "g/dL", "reference_range": "32–36"},
    {"name": "Platelets", "unit": "10³/μL", "reference_range": "150–400"},
    # Basic Metabolic Panel
    {"name": "Glucose", "unit": "mg/dL", "reference_range": "70–100"},
    {"name": "BUN", "unit": "mg/dL", "reference_range": "7–20"},
    {"name": "Creatinine", "unit": "mg/dL", "reference_range": "0.6–1.2"},
    {"name": "eGFR", "unit": "mL/min/1.73m²", "reference_range": ">60"},
    {"name": "Sodium", "unit": "mmol/L", "reference_range": "136–145"},
    {"name": "Potassium", "unit": "mmol/L", "reference_range": "3.5–5.1"},
    {"name": "Chloride", "unit": "mmol/L", "reference_range": "98–107"},
    {"name": "Bicarbonate", "unit": "mmol/L", "reference_range": "22–29"},
    {"name": "Calcium", "unit": "mg/dL", "reference_range": "8.5–10.5"},
    # Liver Function Tests (LFT)
    {"name": "ALT", "unit": "U/L", "reference_range": "7–56"},
    {"name": "AST", "unit": "U/L", "reference_range": "10–40"},
    {"name": "ALP", "unit": "U/L", "reference_range": "44–147"},
    {"name": "GGT", "unit": "U/L", "reference_range": "9–48"},
    {"name": "Total Bilirubin", "unit": "mg/dL", "reference_range": "0.1–1.2"},
    {"name": "Direct Bilirubin", "unit": "mg/dL", "reference_range": "0.0–0.3"},
    {"name": "Total Protein", "unit": "g/dL", "reference_range": "6.3–8.2"},
    {"name": "Albumin", "unit": "g/dL", "reference_range": "3.5–5.0"},
    # Lipid Panel
    {"name": "Total Cholesterol", "unit": "mg/dL", "reference_range": "<200"},
    {"name": "LDL", "unit": "mg/dL", "reference_range": "<100"},
    {"name": "HDL", "unit": "mg/dL", "reference_range": ">40"},
    {"name": "Triglycerides", "unit": "mg/dL", "reference_range": "<150"},
    # Diabetes
    {"name": "HbA1c", "unit": "%", "reference_range": "<5.7"},
    {"name": "Fasting Glucose", "unit": "mmol/L", "reference_range": "3.9–5.6"},
    {"name": "Insulin", "unit": "μIU/mL", "reference_range": "2.6–24.9"},
    # Thyroid
    {"name": "TSH", "unit": "μIU/mL", "reference_range": "0.4–4.0"},
    {"name": "fT4", "unit": "ng/dL", "reference_range": "0.8–1.8"},
    {"name": "fT3", "unit": "pg/mL", "reference_range": "2.3–4.2"},
    # Inflammation
    {"name": "CRP", "unit": "mg/L", "reference_range": "<5.0"},
    {"name": "ESR", "unit": "mm/hr", "reference_range": "0–20"},
    {"name": "Ferritin", "unit": "ng/mL", "reference_range": "12–300"},
    # Coagulation
    {"name": "PT", "unit": "seconds", "reference_range": "11–13"},
    {"name": "INR", "unit": "—", "reference_range": "0.8–1.2"},
    {"name": "aPTT", "unit": "seconds", "reference_range": "25–35"},
    # Iron & Vitamins
    {"name": "Iron", "unit": "μg/dL", "reference_range": "60–170"},
    {"name": "Transferrin", "unit": "mg/dL", "reference_range": "200–380"},
    {"name": "Saturation (%)", "unit": "%", "reference_range": "20–50"},
    {"name": "Vitamin B12", "unit": "pg/mL", "reference_range": "200–900"},
    {"name": "Folate", "unit": "ng/mL", "reference_range": "2.7–17.0"},
    {"name": "Vitamin D", "unit": "ng/mL", "reference_range": "30–100"},
    # Hormones
    {"name": "Testosterone", "unit": "ng/dL", "reference_range": "300–1000"},
    {"name": "FSH", "unit": "mIU/mL", "reference_range": "1.5–12.4"},
    {"name": "LH", "unit": "mIU/mL", "reference_range": "1.7–8.6"},
    {"name": "Estradiol", "unit": "pg/mL", "reference_range": "15–350"},
    {"name": "Prolactin", "unit": "ng/mL", "reference_range": "2–18"},
    # Urinalysis
    {"name": "Glucose (urine)", "unit": "mg/dL", "reference_range": "Negative"},
    {"name": "Protein (urine)", "unit": "mg/dL", "reference_range": "Negative"},
    {"name": "Blood (urine)", "unit": "", "reference_range": "Negative"},
    {"name": "pH (urine)", "unit": "", "reference_range": "4.5–8.0"},
    {"name": "Creatinine (urine)", "unit": "mg/dL", "reference_range": "20–320"},
    # Radiology — chest X-ray
    {"name": "ICT", "unit": "ratio", "reference_range": "<0.50"},
    {"name": "Silhouette médiastinale", "unit": "", "reference_range": "Normale"},
    {"name": "Parenchyme pulmonaire", "unit": "", "reference_range": "Normal"},
    {"name": "Plèvres", "unit": "", "reference_range": "Libres"},
    # Spirometry / EFR
    {"name": "CVF (FVC)", "unit": "L", "reference_range": ">80% pred."},
    {"name": "VEMS (FEV1)", "unit": "L", "reference_range": ">80% pred."},
    {"name": "VEMS/CVF (Tiffeneau)", "unit": "%", "reference_range": ">70%"},
    {"name": "DEP (PEF)", "unit": "L/min", "reference_range": ">80% pred."},
    {"name": "DEM 25-75%", "unit": "L/s", "reference_range": ">60% pred."},
    # ECG
    {"name": "Rythme", "unit": "", "reference_range": "Sinusal"},
    {"name": "FC (bpm)", "unit": "bpm", "reference_range": "60–100"},
    {"name": "PR", "unit": "ms", "reference_range": "120–200"},
    {"name": "QRS", "unit": "ms", "reference_range": "<120"},
    {"name": "QTc", "unit": "ms", "reference_range": "<440"},
    {"name": "Axe électrique", "unit": "°", "reference_range": "-30 à +90"},
    # Ophthalmology
    {"name": "AV OD (sc)", "unit": "/10", "reference_range": "10/10"},
    {"name": "AV OG (sc)", "unit": "/10", "reference_range": "10/10"},
    {"name": "AV ODG (ac)", "unit": "/10", "reference_range": "10/10"},
    {"name": "Tonus OD", "unit": "mmHg", "reference_range": "10–21"},
    {"name": "Tonus OG", "unit": "mmHg", "reference_range": "10–21"},
    {"name": "Vision couleurs", "unit": "", "reference_range": "Normale"},
    {"name": "Champ visuel", "unit": "", "reference_range": "Normal"},
    # ORL / Audiometry
    {"name": "Seuil OD 500Hz", "unit": "dB", "reference_range": "≤25"},
    {"name": "Seuil OD 1kHz", "unit": "dB", "reference_range": "≤25"},
    {"name": "Seuil OD 2kHz", "unit": "dB", "reference_range": "≤25"},
    {"name": "Seuil OD 4kHz", "unit": "dB", "reference_range": "≤25"},
    {"name": "Seuil OD 8kHz", "unit": "dB", "reference_range": "≤25"},
    {"name": "Seuil OG 500Hz", "unit": "dB", "reference_range": "≤25"},
    {"name": "Seuil OG 1kHz", "unit": "dB", "reference_range": "≤25"},
    {"name": "Seuil OG 2kHz", "unit": "dB", "reference_range": "≤25"},
    {"name": "Seuil OG 4kHz", "unit": "dB", "reference_range": "≤25"},
    {"name": "Seuil OG 8kHz", "unit": "dB", "reference_range": "≤25"},
]

_PREDEFINED_LAB_PARAMS_DICT: dict[str, dict] = {p["name"]: p for p in PREDEFINED_LAB_PARAMS}


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


def _resolve_exam_type_label(exam) -> str:
    """Return the referential name if set, otherwise fall back to the enum label."""
    ref_id = getattr(exam, "exam_type_ref_id", None) or ""
    if ref_id:
        try:
            from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
            ref = ExamTypeRef.get_or_none(ExamTypeRef.id == ref_id)
            if ref:
                return ref.name
        except Exception:
            pass
    return exam.exam_type.get_label()


class ExamDetailState(RoleState):
    """State for the exam detail / result-entry page."""

    exam: ExamDetailDTO | None = None
    result: ExamResultDetailDTO | None = None
    certificates: list[CertificateRowDTO] = []
    exam_files: list[ExamFileRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # Medical sections form
    form_reason_for_visit: str = ""
    form_medical_history: str = ""
    form_weight: str = ""
    form_height: str = ""
    form_bmi: str = ""
    form_blood_pressure: str = ""
    form_heart_rate: str = ""
    form_temperature: str = ""
    form_interpretation: str = ""
    is_saving_reason: bool = False
    is_saving_physical: bool = False
    is_saving_lab: bool = False
    is_submitting_review: bool = False
    is_submitting_interpretation: bool = False

    # Laboratory results
    lab_results: list[LabResultRowDTO] = []
    new_lab_selected_preset: str = ""
    new_lab_parameter: str = ""
    new_lab_unit: str = ""
    new_lab_value: str = ""
    new_lab_reference_range: str = ""
    new_lab_status: str = "normal"

    # File upload on detail page
    is_uploading_file: bool = False

    # File delete confirmation dialog
    file_delete_confirm_open: bool = False
    file_to_delete_id: str = ""

    # Delete exam dialog
    delete_exam_confirm_open: bool = False
    delete_exam_comment: str = ""
    is_deleting_exam: bool = False

    # Delete lab result row dialog
    delete_lab_confirm_open: bool = False
    delete_lab_row_id: str = ""
    delete_lab_comment: str = ""

    # Tab navigation
    active_tab: str = "informations"

    # File preview dialog
    preview_dialog_open: bool = False
    selected_file_id: str = ""
    selected_file_name: str = ""
    selected_file_type: str = ""   # image | pdf | table | other | ""
    selected_file_preview_url: str = ""
    # Plotly data stored as {"figure": <dict>, "name": <str>} so it can be
    # accessed via dict subscript in the component — rx.plotly rejects direct
    # dict|None vars but accepts dict["key"] subscript vars without type checking.
    selected_file_data: dict | None = None
    is_loading_preview: bool = False
    preview_error: str = ""
    # Table preview (CSV / Excel)
    table_preview_columns: list[str] = []
    table_preview_rows: list[list[str]] = []
    table_preview_total_rows: int = 0
    # Plot-from-prompt
    plot_prompt: str = ""
    plot_chart: dict | None = None   # {"figure": dict, "name": str}
    is_generating_plot: bool = False
    plot_generation_error: str = ""

    @rx.var
    def computed_bmi(self) -> float | None:
        """Auto-calculate BMI from form_weight and form_height."""
        try:
            w = float(self.form_weight)
            h = float(self.form_height) / 100.0
            if w > 0 and h > 0:
                return round(w / (h * h), 1)
        except (ValueError, TypeError, ZeroDivisionError):
            pass
        return None

    @rx.var
    def bmi_category(self) -> str:
        bmi = self.computed_bmi
        if bmi is None:
            return ""
        if bmi < 18.5:
            return "underweight"
        if bmi < 25.0:
            return "normal"
        if bmi < 30.0:
            return "overweight"
        return "obese"

    @rx.var
    def is_sections_editable(self) -> bool:
        """True for all statuses except DONE — forms stay editable until interpretation is complete."""
        if self.exam is None:
            return False
        return self.exam.status != "done"

    @rx.var
    def is_results_editable(self) -> bool:
        """True whenever an exam is loaded — editing remains allowed after Done."""
        return self.exam is not None

    @rx.var
    def exam_status_index(self) -> int:
        """Map exam status to a 0-based workflow step index."""
        if self.exam is None:
            return 0
        if self.exam.status == "in_progress_results":
            return 1
        if self.exam.status == "in_progress_interpretation":
            return 2
        if self.exam.status == "done":
            return 3
        return 0  # todo

    @rx.var
    def missing_sections_for_review(self) -> list[str]:
        """List of section names that are still empty, blocking submit-for-review."""
        if self.exam is None:
            return ["All sections"]
        missing: list[str] = []
        if not self.exam.reason_for_visit:
            missing.append("Reason for visit")
        if not self.exam.medical_history:
            missing.append("Medical history")
        has_physical = bool(
            self.exam.weight or self.exam.height or self.exam.bmi
            or self.exam.blood_pressure or self.exam.heart_rate or self.exam.temperature
        )
        if not has_physical:
            missing.append("Physical examination")
        if not self.lab_results and not self.exam_files:
            missing.append("Laboratory results or Medical documents (at least one required)")
        return missing

    @rx.var
    def result_data_items(self) -> list[list[str]]:
        """Convert result_data dict to [[key, value], ...] list for rx.foreach."""
        if self.result is None:
            return []
        return [[str(k), str(v)] for k, v in self.result.result_data.items()]

    @rx.event
    async def on_load(self):
        # Clear stale state immediately so no previous error/exam flashes on screen
        self.exam = None
        self.error_message = ""
        self.is_loading = True
        yield
        await self._load_roles()
        await self._load_exam()
        if self.exam:
            status = self.exam.status
            if status == "in_progress_results":
                self.active_tab = "results"
            elif status in ("in_progress_interpretation", "done"):
                self.active_tab = "interpretation"
            else:
                self.active_tab = "informations"
        # Reset preview state so a previously viewed file doesn't linger
        self.preview_dialog_open = False
        self.selected_file_id = ""
        self.selected_file_name = ""
        self.selected_file_type = ""
        self.selected_file_preview_url = ""
        self.selected_file_data = None
        self.is_loading_preview = False
        self.preview_error = ""
        self.table_preview_columns = []
        self.table_preview_rows = []
        self.table_preview_total_rows = 0
        self.plot_prompt = ""
        self.plot_chart = None
        self.is_generating_plot = False
        self.plot_generation_error = ""

    @rx.event
    async def save_informations(self):
        """Save Informations. First save advances TODO→IN_PROGRESS_RESULTS and opens Results tab.
        Subsequent saves (re-edits, including after the exam is Done) just persist
        without changing status or tab."""
        if self.exam is None:
            return
        await self._persist_reason_and_history()
        await self._persist_physical()
        if self.exam.status == "todo":
            with await self.authenticate_user() as auth_user:
                from gws_care.exam.exam_service import ExamService
                from gws_care.user.user import User
                user = User.get_by_id(str(auth_user.id))
                ExamService.set_in_progress_results(self.exam_id_param, user=user)
            self.exam = self.exam.copy(update={"status": "in_progress_results"})
            self.active_tab = "results"
        yield rx.toast.success("Informations saved.")

    @rx.event
    def go_back(self):
        return rx.call_script("window.history.back()")

    @rx.event
    def set_active_tab(self, value: str):
        self.active_tab = value

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
    def set_form_interpretation(self, value: str):
        self.form_interpretation = value

    @rx.event
    def select_predefined_param(self, preset_name: str):
        """Auto-fill parameter fields when a predefined parameter is selected."""
        self.new_lab_selected_preset = preset_name
        if preset_name == "CUSTOM":
            self.new_lab_parameter = ""
            self.new_lab_unit = ""
            self.new_lab_reference_range = ""
        else:
            p = _PREDEFINED_LAB_PARAMS_DICT.get(preset_name)
            if p:
                self.new_lab_parameter = p["name"]
                self.new_lab_unit = p["unit"]
                self.new_lab_reference_range = p["reference_range"]

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
    def set_new_lab_status(self, value: str):
        self.new_lab_status = value

    @rx.event
    async def add_lab_row(self):
        """Add a new row to lab results and persist immediately."""
        if not self.new_lab_parameter.strip():
            return
        self.lab_results = self.lab_results + [
            LabResultRowDTO(
                id=str(uuid.uuid4()),
                parameter=self.new_lab_parameter.strip(),
                unit=self.new_lab_unit.strip(),
                value=self.new_lab_value.strip(),
                reference_range=self.new_lab_reference_range.strip(),
                status=self.new_lab_status or "normal",
            )
        ]
        self.new_lab_selected_preset = ""
        self.new_lab_parameter = ""
        self.new_lab_unit = ""
        self.new_lab_value = ""
        self.new_lab_reference_range = ""
        self.new_lab_status = "normal"
        await self._persist_lab_results()

    @rx.event
    async def remove_lab_row(self, row_id: str):
        """Remove a lab result row and persist immediately."""
        self.lab_results = [row for row in self.lab_results if row.id != row_id]
        await self._persist_lab_results()

    @rx.event
    async def submit_for_review(self):
        """Transition exam IN_PROGRESS_RESULTS→IN_PROGRESS_INTERPRETATION."""
        if self.exam is None or self.exam.status != "in_progress_results":
            return
        self.is_submitting_review = True
        self.error_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.exam.exam_service import ExamService
                from gws_care.user.user import User
                user = User.get_by_id(str(auth_user.id))
                ExamService.set_in_progress_interpretation(self.exam.id, user=user)
            self.exam = self.exam.copy(update={"status": "in_progress_interpretation"})
            self.active_tab = "interpretation"
            yield rx.toast.success("Exam submitted for review.")
        except Exception as e:
            self.error_message = f"Error: {e}"
        finally:
            self.is_submitting_review = False

    @rx.event
    async def submit_interpretation(self):
        """Save doctor's interpretation and transition exam to DONE."""
        if self.exam is None or self.exam.status != "in_progress_interpretation":
            return
        if not self.form_interpretation.strip():
            self.error_message = "Please enter the medical interpretation before submitting."
            return
        self.is_submitting_interpretation = True
        self.error_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.exam.exam_dto import InterpretExamDTO
                from gws_care.exam.exam_service import ExamService
                from gws_care.user.user import User
                doctor = User.get_by_id(str(auth_user.id))
                dto = InterpretExamDTO(interpretation=self.form_interpretation.strip())
                exam = ExamService.interpret_exam(self.exam.id, dto, doctor)
                interpreted_by_name = f"{doctor.first_name} {doctor.last_name}"
            self.exam = self.exam.copy(update={
                "status": "done",
                "interpretation": self.form_interpretation.strip(),
                "interpreted_by_name": interpreted_by_name,
            })
            yield rx.toast.success("Interpretation submitted. Exam is now locked.")
        except Exception as e:
            self.error_message = f"Error: {e}"
        finally:
            self.is_submitting_interpretation = False

    @rx.event
    async def save_reason_and_history(self):
        """Save Reason for visit + Medical history (called from frontend button if exposed)."""
        await self._persist_reason_and_history()

    @rx.event
    async def save_physical(self):
        """Save Physical examination fields (called from frontend button if exposed)."""
        await self._persist_physical()

    @rx.event
    async def save_lab_results(self):
        """Save Laboratory results (called from frontend button if exposed)."""
        await self._persist_lab_results()

    async def _persist_reason_and_history(self):
        if self.exam is None:
            return
        self.is_saving_reason = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam_service import ExamService
                ExamService.update_reason_and_history(
                    self.exam_id_param,
                    self.form_reason_for_visit or None,
                    self.form_medical_history or None,
                )
            self.exam = self.exam.copy(update={
                "reason_for_visit": self.form_reason_for_visit or None,
                "medical_history": self.form_medical_history or None,
            })
        except Exception as e:
            self.error_message = f"Error: {e}"
        finally:
            self.is_saving_reason = False

    async def _persist_physical(self):
        if self.exam is None:
            return
        self.is_saving_physical = True
        self.error_message = ""

        def _f(val: str) -> float | None:
            v = val.strip()
            if not v:
                return None
            try:
                return float(v)
            except ValueError:
                return None

        try:
            bmi_to_save = self.computed_bmi if self.computed_bmi is not None else _f(self.form_bmi)
            with await self.authenticate_user():
                from gws_care.exam.exam_service import ExamService
                from gws_care.patient.patient import Patient
                ExamService.update_physical(
                    self.exam_id_param,
                    weight=_f(self.form_weight),
                    height=_f(self.form_height),
                    bmi=bmi_to_save,
                    blood_pressure=self.form_blood_pressure or None,
                    heart_rate=_f(self.form_heart_rate),
                    temperature=_f(self.form_temperature),
                )
                if self.exam and (self.form_weight or self.form_height):
                    try:
                        patient = Patient.get_by_id(str(self.exam.patient_id))
                        if _f(self.form_weight):
                            patient.weight = _f(self.form_weight)
                        if _f(self.form_height):
                            patient.height = _f(self.form_height)
                        patient.save()
                    except Exception:
                        pass
            self.exam = self.exam.copy(update={
                "weight": _f(self.form_weight),
                "height": _f(self.form_height),
                "bmi": bmi_to_save,
                "blood_pressure": self.form_blood_pressure or None,
                "heart_rate": _f(self.form_heart_rate),
                "temperature": _f(self.form_temperature),
            })
        except Exception as e:
            self.error_message = f"Error: {e}"
        finally:
            self.is_saving_physical = False

    async def _persist_lab_results(self):
        if self.exam is None:
            return
        self.is_saving_lab = True
        self.error_message = ""
        rows_payload = [
            {
                "id": row.id,
                "parameter": row.parameter,
                "unit": row.unit,
                "value": row.value,
                "reference_range": row.reference_range,
                "status": row.status,
            }
            for row in self.lab_results
        ]
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam_service import ExamService
                ExamService.update_lab_results(self.exam_id_param, rows_payload)
        except Exception as e:
            self.error_message = f"Error saving lab results: {e}"
        finally:
            self.is_saving_lab = False

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

                exam = ExamService.get_exam(exam_id)
                patient = exam.patient
                interpreted_by_name = ""
                if exam.interpreted_by_id:
                    try:
                        from gws_care.user.user import User as UserModel
                        u = UserModel.get_by_id(str(exam.interpreted_by_id))
                        interpreted_by_name = f"{u.first_name} {u.last_name}"
                    except Exception:
                        pass
                self.exam = ExamDetailDTO(
                    id=str(exam.id),
                    exam_date=exam.exam_date.isoformat(),
                    exam_type=exam.exam_type.value,
                    exam_type_label=_resolve_exam_type_label(exam),
                    status=exam.status.value,
                    reason_for_visit=exam.reason_for_visit,
                    medical_history=exam.medical_history,
                    weight=exam.weight,
                    height=exam.height,
                    bmi=exam.bmi,
                    blood_pressure=exam.blood_pressure,
                    heart_rate=exam.heart_rate,
                    temperature=exam.temperature,
                    interpretation=exam.interpretation,
                    interpreted_by_name=interpreted_by_name,
                    patient_id=str(patient.id),
                    patient_name=f"{patient.first_name} {patient.last_name}",
                    visit_id=str(exam.visit_id) if exam.visit_id else "",
                )
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
                self.form_interpretation = exam.interpretation or ""
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
    def confirm_delete_file(self, file_id: str):
        """Open the delete confirmation dialog for a file."""
        self.file_to_delete_id = file_id
        self.file_delete_confirm_open = True

    @rx.event
    def close_delete_file_confirm(self):
        """Close the delete confirmation dialog without deleting."""
        self.file_delete_confirm_open = False
        self.file_to_delete_id = ""

    @rx.event
    async def delete_file_confirmed(self):
        """Delete the file after user confirmation."""
        file_id = self.file_to_delete_id
        self.file_delete_confirm_open = False
        self.file_to_delete_id = ""
        if not file_id:
            return
        try:
            from gws_care.exam.exam_file_service import ExamFileService
            ExamFileService.delete_file(file_id)
            await self._load_exam()
        except Exception as e:
            self.error_message = f"Error deleting file: {e}"

    @rx.event
    async def delete_file(self, file_id: str):
        """Delete an attached file."""
        try:
            from gws_care.exam.exam_file_service import ExamFileService
            ExamFileService.delete_file(file_id)
            await self._load_exam()
        except Exception as e:
            self.error_message = f"Error deleting file: {e}"

    # ── Delete exam ───────────────────────────────────────────────────────────

    @rx.event
    def open_delete_exam_dialog(self):
        """Open the delete exam confirmation dialog."""
        self.delete_exam_comment = ""
        self.delete_exam_confirm_open = True

    @rx.event
    def close_delete_exam_dialog(self):
        """Close the delete exam dialog without deleting."""
        self.delete_exam_confirm_open = False
        self.delete_exam_comment = ""

    @rx.event
    def set_delete_exam_comment(self, value: str):
        self.delete_exam_comment = value

    @rx.event
    async def confirm_delete_exam(self):
        """Delete the exam after user confirms with a mandatory comment."""
        if not self.delete_exam_comment.strip():
            self.error_message = "Un commentaire est obligatoire pour supprimer un examen."
            return
        if not self.exam:
            return
        self.is_deleting_exam = True
        self.delete_exam_confirm_open = False
        exam_id = self.exam.id
        try:
            with await self.authenticate_user():
                from gws_care.exam.exam import Exam
                exam_obj = Exam.get_by_id(exam_id)
                exam_obj.is_active = False
                exam_obj.save()
            yield rx.toast.success("Examen supprimé.")
            yield rx.redirect("/")
        except Exception as e:
            self.error_message = f"Erreur suppression examen : {e}"
        finally:
            self.is_deleting_exam = False

    # ── Delete lab result row ─────────────────────────────────────────────────

    @rx.event
    def open_delete_lab_row_dialog(self, row_id: str):
        """Open the delete lab result row confirmation dialog."""
        self.delete_lab_row_id = row_id
        self.delete_lab_comment = ""
        self.delete_lab_confirm_open = True

    @rx.event
    def close_delete_lab_row_dialog(self):
        """Close the delete lab row dialog without deleting."""
        self.delete_lab_confirm_open = False
        self.delete_lab_row_id = ""
        self.delete_lab_comment = ""

    @rx.event
    def set_delete_lab_comment(self, value: str):
        self.delete_lab_comment = value

    @rx.event
    async def confirm_delete_lab_row(self):
        """Remove the lab result row after user confirms with a mandatory comment."""
        if not self.delete_lab_comment.strip():
            self.error_message = "Un commentaire est obligatoire pour supprimer un résultat."
            return
        row_id = self.delete_lab_row_id
        self.delete_lab_confirm_open = False
        self.delete_lab_row_id = ""
        self.delete_lab_comment = ""
        self.lab_results = [row for row in self.lab_results if row.id != row_id]
        await self._persist_lab_results()

    # ── Phase 8 — Certificate PDF download ───────────────────────────────────

    @rx.event
    async def download_certificate_pdf(self, certificate_id: str):
        """Generate and download a medical certificate PDF."""
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_certificate_pdf
                pdf_bytes = generate_certificate_pdf(certificate_id)
            return rx.download(data=pdf_bytes, filename=f"certificat_{certificate_id[:8]}.pdf")
        except Exception as e:
            self.error_message = f"Erreur génération PDF : {e}"

    # ── File preview dialog ───────────────────────────────────────────────────────

    @rx.event
    def open_preview_dialog(self, file_id: str):
        """Open the preview dialog and start loading the file."""
        self.preview_dialog_open = True
        self.selected_file_id = file_id
        self.selected_file_name = ""
        self.selected_file_type = ""
        self.selected_file_preview_url = ""
        self.selected_file_data = None
        self.is_loading_preview = True
        self.preview_error = ""
        self.table_preview_columns = []
        self.table_preview_rows = []
        self.table_preview_total_rows = 0
        self.plot_prompt = ""
        self.plot_chart = None
        self.is_generating_plot = False
        self.plot_generation_error = ""
        return ExamDetailState.select_file_for_preview(file_id)

    @rx.event
    def close_preview_dialog(self):
        self.preview_dialog_open = False

    @rx.event
    def set_plot_prompt(self, value: str):
        self.plot_prompt = value

    @rx.event(background=True)
    async def generate_plot_from_prompt(self):
        """Generate a Plotly chart from the user's text prompt using stored table data."""
        async with self:
            if not self.table_preview_columns:
                self.plot_generation_error = "No table data loaded."
                return
            self.is_generating_plot = True
            self.plot_generation_error = ""
            prompt = self.plot_prompt.strip()
            file_id = self.selected_file_id
            file_name = self.selected_file_name
            columns = list(self.table_preview_columns)

        try:
            from gws_care.exam.exam_file import ExamFile

            file_rec = ExamFile.get_by_id(file_id)
            import os
            ext = os.path.splitext(file_rec.original_name or "")[1].lower()
            is_excel = ext in {".xlsx", ".xls"}
            figure_dict = ExamDetailState._prompt_to_plotly(file_rec, is_excel, prompt, columns)
            async with self:
                if figure_dict:
                    self.plot_chart = {"figure": figure_dict, "name": file_name}
                    self.plot_generation_error = ""
                else:
                    self.plot_generation_error = f"Could not generate chart. Available columns: {', '.join(columns)}"
        except Exception as e:
            async with self:
                self.plot_generation_error = str(e)
        finally:
            async with self:
                self.is_generating_plot = False

    @staticmethod
    def _prompt_to_plotly(file_rec, is_excel: bool, prompt: str, columns: list[str]) -> dict | None:
        """Parse prompt and generate a plotly chart from the file data."""
        try:
            import os
            from json import loads

            import pandas as pd
            import plotly.express as px
            from gws_core.impl.file.file import File
            from gws_core.resource.resource_model import ResourceModel

            if not file_rec.resource_id:
                return None
            rm = ResourceModel.get_by_id_and_check(file_rec.resource_id)
            resource = rm.get_resource()
            if not isinstance(resource, File):
                return None
            path = resource.path
            if not path or not os.path.exists(path):
                return None

            df = pd.read_excel(path) if is_excel else pd.read_csv(path)
            if df.empty:
                return None

            prompt_lower = prompt.lower()
            chart_type = "scatter"
            if any(k in prompt_lower for k in ["bar", "barre", "histogram", "histogramme", "count"]):
                chart_type = "bar"
            elif any(k in prompt_lower for k in ["line", "ligne", "courbe", "trend", "tendance", "time", "temps"]):
                chart_type = "line"
            elif any(k in prompt_lower for k in ["pie", "camembert", "donut"]):
                chart_type = "pie"
            elif any(k in prompt_lower for k in ["box", "boite", "whisker"]):
                chart_type = "box"

            mentioned_cols: list[str] = [col for col in df.columns if col.lower() in prompt_lower]
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

            if len(mentioned_cols) >= 2:
                x_col, y_col = mentioned_cols[0], mentioned_cols[1]
            elif len(mentioned_cols) == 1:
                x_col = mentioned_cols[0]
                candidates = [c for c in numeric_cols if c != x_col]
                y_col = candidates[0] if candidates else x_col
            elif len(numeric_cols) >= 2:
                x_col, y_col = numeric_cols[0], numeric_cols[1]
            elif len(numeric_cols) == 1:
                x_col = df.columns[0] if df.columns[0] != numeric_cols[0] else None
                y_col = numeric_cols[0]
            else:
                x_col = df.columns[0]
                y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

            title = file_rec.original_name or "Data"
            if chart_type == "pie":
                fig = px.pie(df, names=x_col, values=y_col if y_col != x_col else None, title=title)
            elif chart_type == "bar":
                fig = px.bar(df, x=x_col, y=y_col, title=title) if x_col else px.bar(df, y=y_col, title=title)
            elif chart_type == "line":
                fig = px.line(df, x=x_col, y=y_col, title=title) if x_col else px.line(df, y=y_col, title=title)
            elif chart_type == "box":
                fig = px.box(df, y=y_col, title=title)
            else:
                fig = px.scatter(df, x=x_col, y=y_col, title=title) if x_col else px.scatter(df, y=y_col, title=title)

            return loads(fig.to_json())
        except Exception:
            return None

    @rx.event(background=True)
    async def select_file_for_preview(self, file_id: str):
        """Load and prepare a file for preview."""
        async with self:
            self.selected_file_id = file_id
            self.is_loading_preview = True
            self.preview_error = ""
            self.selected_file_data = None
            self.selected_file_preview_url = ""
            self.selected_file_type = ""
            self.selected_file_name = ""
            self.table_preview_columns = []
            self.table_preview_rows = []
            self.table_preview_total_rows = 0

        try:
            import os
            from json import loads

            from gws_care.exam.exam_file import ExamFile
            from gws_care.exam.exam_file_service import ExamFileService

            file_rec = ExamFile.get_by_id(file_id)
            name = file_rec.original_name or ""
            ext = os.path.splitext(name)[1].lower()
            mime = (file_rec.mime_type or "").lower()

            async with self:
                self.selected_file_name = name

            is_image = mime.startswith("image/") or ext in {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".gif"}
            is_pdf = "pdf" in mime or ext == ".pdf"
            is_csv = ext == ".csv" or "text/csv" in mime or (ext == ".txt" and not is_pdf)
            is_excel = ext in {".xlsx", ".xls"} or "spreadsheet" in mime or "excel" in mime

            if is_image:
                url = ExamFileService.get_resource_download_url(file_rec.resource_id) if file_rec.resource_id else ""
                async with self:
                    self.selected_file_type = "image"
                    self.selected_file_preview_url = url

            elif is_pdf:
                url = ExamFileService.get_resource_download_url(file_rec.resource_id) if file_rec.resource_id else ""
                async with self:
                    self.selected_file_type = "pdf"
                    self.selected_file_preview_url = url

            elif is_csv or is_excel:
                table_cols, table_rows, total_rows = self._file_to_table(file_rec, is_excel)
                async with self:
                    self.selected_file_type = "table"
                    self.table_preview_columns = table_cols
                    self.table_preview_rows = table_rows
                    self.table_preview_total_rows = total_rows

            else:
                url = ExamFileService.get_resource_download_url(file_rec.resource_id) if file_rec.resource_id else ""
                async with self:
                    self.selected_file_type = "other"
                    self.selected_file_preview_url = url

        except Exception as e:
            async with self:
                self.preview_error = str(e)
        finally:
            async with self:
                self.is_loading_preview = False

    _TABLE_PREVIEW_MAX_ROWS = 50

    @staticmethod
    def _file_to_table(file_rec, is_excel: bool) -> tuple[list[str], list[list[str]], int]:
        """Parse a CSV/Excel file resource into (columns, rows, total_rows) for table preview."""
        try:
            import os

            import pandas as pd
            from gws_core.impl.file.file import File
            from gws_core.resource.resource_model import ResourceModel

            if not file_rec.resource_id:
                return [], [], 0
            rm = ResourceModel.get_by_id_and_check(file_rec.resource_id)
            resource = rm.get_resource()
            if not isinstance(resource, File):
                return [], [], 0
            path = resource.path
            if not path or not os.path.exists(path):
                return [], [], 0

            df = pd.read_excel(path) if is_excel else pd.read_csv(path)
            if df.empty:
                return [], [], 0

            total = len(df)
            cols = [str(c) for c in df.columns.tolist()]
            preview = df.head(ExamDetailState._TABLE_PREVIEW_MAX_ROWS)
            rows = [[str(v) if v is not None else "" for v in row] for row in preview.values.tolist()]
            return cols, rows, total
        except Exception:
            return [], [], 0

