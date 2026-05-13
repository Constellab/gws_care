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
    conclusion: str | None = None
    patient_id: str
    patient_name: str


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


class ExamDetailState(RoleState):
    """State for the exam detail / result-entry page."""

    exam: ExamDetailDTO | None = None
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
    new_lab_selected_preset: str = ""
    new_lab_parameter: str = ""
    new_lab_unit: str = ""
    new_lab_value: str = ""
    new_lab_reference_range: str = ""
    new_lab_status: str = "normal"

    # File upload on detail page
    is_uploading_file: bool = False

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
    def add_lab_row(self):
        """Add a new row to lab results (parameter name is required)."""
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
        except Exception as e:
            self.error_message = f"Error saving sections: {e}"
        finally:
            self.is_saving_sections = False

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
                self.exam = ExamDetailDTO(
                    id=str(exam.id),
                    exam_date=exam.exam_date.isoformat(),
                    exam_type=exam.exam_type.value,
                    exam_type_label=exam.exam_type.get_label(),
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
