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
    address_complement: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None
    phone: str | None = None
    email: str | None = None
    # Medical / identity fields
    social_security_number: str | None = None
    sex: str | None = None
    nationality: str | None = None
    phone_country: str | None = None
    weight: float | None = None
    height: float | None = None
    qr_code: str | None = None
    account_id: str = ""
    account_name: str = ""
    # Referent doctor (médecin traitant) — from PatientDoctor where is_referent=True
    primary_physician_id: str = ""
    primary_physician_full_name: str = ""
    primary_physician_specialization: str = ""
    primary_physician_phone: str = ""
    primary_physician_email: str = ""
    # Archive status
    is_archived: bool = False
    archived_reason: str | None = None
    archived_at: str | None = None


class ExamRowDTO(BaseModel):
    """Lightweight exam row for the patient detail exam list."""

    id: str
    exam_date: str
    exam_type_label: str
    status: str
    visit_id: str = ""


class PatientVisitRowDTO(BaseModel):
    """Lightweight visit row for the patient detail visits list."""

    id: str
    visit_number: str
    visit_type: str = "campaign"    # "campaign" or "consultation"
    campaign_name: str = ""
    campaign_id: str = ""
    scheduled_at: str = ""
    campaign_visit_status: str = ""  # kept for backward compat; also used as generic status
    status_label: str = ""
    appointment_mode: str = ""
    doctor_name: str = ""


class AccountForVisitDTO(BaseModel):
    """Account option for the create-visit form select."""

    id: str
    name: str


class PrescriptionRowDTO(BaseModel):
    """Lightweight prescription row for the patient detail prescriptions tab."""

    id: str
    prescription_date: str
    drug_count: int = 0
    diagnosis: str = ""
    prescribed_by_name: str = ""
    is_archived: bool = False


class DrugLineDTO(BaseModel):
    """One drug line in the prescription form."""

    name: str = ""
    dosage: str = ""
    dosage_unit: str = "mg"
    frequency: str = ""
    frequency_unit: str = "fois/jour"
    duration: str = ""
    duration_unit: str = "jours"


class CertificateRowDTO(BaseModel):
    """Lightweight certificate row for the patient detail certificates tab."""

    id: str
    issue_date: str
    certificate_type: str = "APTITUDE"
    certificate_type_label: str = ""
    conclusion: str = ""
    is_fit_for_work: bool = True
    issued_by_name: str = ""
    is_archived: bool = False


class ExamHistoryItemDTO(BaseModel):
    """One exam line inside a consultation history card."""
    exam_type_label: str
    status: str
    has_abnormal: bool = False


class ConsultationHistoryDTO(BaseModel):
    """One consultation card in the patient history timeline."""
    id: str
    visit_number: str
    scheduled_at: str
    status: str
    reason_for_visit: str = ""
    medical_history: str = ""
    exams: list[ExamHistoryItemDTO] = []
    prescription_count: int = 0
    certificate_count: int = 0
    has_abnormal_results: bool = False


class PatientDetailState(ReflexMainState):
    """State for the patient detail page."""

    patient: PatientDetailDTO | None = None
    exams: list[ExamRowDTO] = []
    exam_type_options: list[str] = []
    patient_visits: list[PatientVisitRowDTO] = []
    consultation_history: list[ConsultationHistoryDTO] = []
    latest_medical_history: str = ""
    is_loading: bool = False
    error_message: str = ""
    show_id_card: bool = False

    # Create standalone visit dialog
    show_create_visit_dialog: bool = False
    create_visit_scheduled_at: str = ""
    create_visit_account_id: str = ""
    create_visit_error: str = ""
    patient_accounts: list[AccountForVisitDTO] = []

    # ── Prescriptions ─────────────────────────────────────────────────────────
    prescriptions: list[PrescriptionRowDTO] = []
    show_prescription_dialog: bool = False
    prescription_form_date: str = ""
    prescription_form_diagnosis: str = ""
    prescription_form_instructions: str = ""
    prescription_form_drugs: list[DrugLineDTO] = []
    prescription_form_error: str = ""
    is_saving_prescription: bool = False
    # Prescription sort / filter
    presc_sort_column: str = "prescription_date"
    presc_sort_ascending: bool = False
    presc_filter_from: str = ""
    presc_filter_to: str = ""
    presc_show_archived: bool = False

    # ── Certificates ──────────────────────────────────────────────────────────
    certificates: list[CertificateRowDTO] = []
    show_certificate_dialog: bool = False
    cert_form_type: str = "APTITUDE"
    cert_form_date: str = ""
    cert_form_conclusion: str = ""
    cert_form_is_fit_for_work: bool = True
    cert_form_restrictions: str = ""
    # Work stoppage
    cert_form_start_date: str = ""
    cert_form_end_date: str = ""
    cert_form_return_date: str = ""
    # Pre-employment / periodic sub-type
    cert_form_visit_subtype: str = ""
    # Work accident
    cert_form_accident_date: str = ""
    cert_form_body_part: str = ""
    # SIR
    cert_form_exposure_type: str = ""
    # Vaccination
    cert_form_vaccine_name: str = ""
    cert_form_vaccine_lot: str = ""
    cert_form_next_booster: str = ""
    cert_form_error: str = ""
    is_saving_certificate: bool = False
    # Certificate sort / filter
    cert_sort_column: str = "issue_date"
    cert_sort_ascending: bool = False
    cert_filter_from: str = ""
    cert_filter_to: str = ""
    cert_show_archived: bool = False

    # ── Visit sort / filter state ──────────────────────────────
    visit_sort_column: str = "scheduled_at"
    visit_sort_ascending: bool = False
    visit_filter_from: str = ""
    visit_filter_to: str = ""
    visit_filter_mode: str = ""
    visit_filter_doctor: str = ""
    visit_filter_status: str = ""
    visit_doctor_options: list[str] = []

    # ── Archive / delete dialogs ───────────────────────────────
    show_archive_dialog: bool = False
    archive_reason: str = ""
    archive_error: str = ""
    is_archiving: bool = False

    show_delete_dialog: bool = False
    delete_reason: str = ""
    delete_error: str = ""
    is_deleting: bool = False

    @rx.event
    async def set_visit_sort(self, column: str):
        if self.visit_sort_column == column:
            self.visit_sort_ascending = not self.visit_sort_ascending
        else:
            self.visit_sort_column = column
            self.visit_sort_ascending = True

    @rx.event
    def set_visit_filter_from(self, value: str):
        self.visit_filter_from = value

    @rx.event
    def set_visit_filter_to(self, value: str):
        self.visit_filter_to = value

    @rx.event
    def set_visit_filter_mode(self, value: str):
        self.visit_filter_mode = "" if value == "ALL" else value

    @rx.event
    def set_visit_filter_doctor(self, value: str):
        self.visit_filter_doctor = "" if value == "ALL" else value

    @rx.event
    def set_visit_filter_status(self, value: str):
        self.visit_filter_status = "" if value == "ALL" else value

    @rx.var
    def sorted_visits(self) -> list[PatientVisitRowDTO]:
        col = self.visit_sort_column
        return sorted(
            self.patient_visits,
            key=lambda v: (getattr(v, col) or "").lower(),
            reverse=not self.visit_sort_ascending,
        )

    @rx.var
    def filtered_sorted_visits(self) -> list[PatientVisitRowDTO]:
        rows = self.patient_visits
        if self.visit_filter_from:
            rows = [v for v in rows if v.scheduled_at >= self.visit_filter_from]
        if self.visit_filter_to:
            rows = [v for v in rows if v.scheduled_at <= self.visit_filter_to]
        if self.visit_filter_mode:
            rows = [v for v in rows if v.appointment_mode == self.visit_filter_mode]
        if self.visit_filter_doctor:
            rows = [v for v in rows if v.doctor_name == self.visit_filter_doctor]
        if self.visit_filter_status:
            rows = [v for v in rows if v.campaign_visit_status == self.visit_filter_status]
        col = self.visit_sort_column
        return sorted(
            rows,
            key=lambda v: (getattr(v, col) or "").lower(),
            reverse=not self.visit_sort_ascending,
        )

    exam_sort_column: str = "exam_date"
    exam_sort_ascending: bool = False
    exam_filter_from: str = ""
    exam_filter_to: str = ""
    exam_filter_type: str = ""
    exam_filter_status: str = ""

    @rx.event
    async def set_exam_sort(self, column: str):
        if self.exam_sort_column == column:
            self.exam_sort_ascending = not self.exam_sort_ascending
        else:
            self.exam_sort_column = column
            self.exam_sort_ascending = True

    @rx.event
    def set_exam_filter_from(self, value: str):
        self.exam_filter_from = value

    @rx.event
    def set_exam_filter_to(self, value: str):
        self.exam_filter_to = value

    @rx.event
    def set_exam_filter_type(self, value: str):
        self.exam_filter_type = "" if value == "ALL" else value

    @rx.event
    def set_exam_filter_status(self, value: str):
        self.exam_filter_status = "" if value == "ALL" else value

    @rx.var
    def patient_bmi(self) -> float | None:
        """Auto-calculate patient BMI from stored weight and height."""
        if self.patient is None:
            return None
        try:
            w = self.patient.weight
            h = self.patient.height
            if w and h:
                h_m = float(h) / 100.0
                return round(float(w) / (h_m * h_m), 1)
        except Exception:
            pass
        return None

    @rx.var
    def patient_bmi_category(self) -> str:
        bmi = self.patient_bmi
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
    def filtered_sorted_exams(self) -> list[ExamRowDTO]:
        rows = self.exams
        if self.exam_filter_from:
            rows = [e for e in rows if e.exam_date >= self.exam_filter_from]
        if self.exam_filter_to:
            rows = [e for e in rows if e.exam_date <= self.exam_filter_to]
        if self.exam_filter_type:
            rows = [e for e in rows if e.exam_type_label == self.exam_filter_type]
        if self.exam_filter_status:
            rows = [e for e in rows if e.status == self.exam_filter_status]
        col = self.exam_sort_column
        return sorted(
            rows,
            key=lambda e: (getattr(e, col) or "").lower(),
            reverse=not self.exam_sort_ascending,
        )

    @rx.var
    def sorted_exams(self) -> list[ExamRowDTO]:
        col = self.exam_sort_column
        return sorted(
            self.exams,
            key=lambda e: (getattr(e, col) or "").lower(),
            reverse=not self.exam_sort_ascending,
        )

    @rx.event
    def set_presc_sort(self, column: str):
        if self.presc_sort_column == column:
            self.presc_sort_ascending = not self.presc_sort_ascending
        else:
            self.presc_sort_column = column
            self.presc_sort_ascending = True

    @rx.event
    def set_presc_filter_from(self, value: str):
        self.presc_filter_from = value

    @rx.event
    def set_presc_filter_to(self, value: str):
        self.presc_filter_to = value

    @rx.event
    def toggle_presc_show_archived(self):
        self.presc_show_archived = not self.presc_show_archived

    @rx.var
    def filtered_sorted_prescriptions(self) -> list[PrescriptionRowDTO]:
        rows = self.prescriptions
        if not self.presc_show_archived:
            rows = [r for r in rows if not r.is_archived]
        if self.presc_filter_from:
            rows = [r for r in rows if r.prescription_date >= self.presc_filter_from]
        if self.presc_filter_to:
            rows = [r for r in rows if r.prescription_date <= self.presc_filter_to]
        col = self.presc_sort_column
        return sorted(
            rows,
            key=lambda r: str(getattr(r, col) or "").lower(),
            reverse=not self.presc_sort_ascending,
        )

    @rx.event
    def set_cert_sort(self, column: str):
        if self.cert_sort_column == column:
            self.cert_sort_ascending = not self.cert_sort_ascending
        else:
            self.cert_sort_column = column
            self.cert_sort_ascending = True

    @rx.event
    def set_cert_filter_from(self, value: str):
        self.cert_filter_from = value

    @rx.event
    def set_cert_filter_to(self, value: str):
        self.cert_filter_to = value

    @rx.event
    def toggle_cert_show_archived(self):
        self.cert_show_archived = not self.cert_show_archived

    @rx.var
    def filtered_sorted_certificates(self) -> list[CertificateRowDTO]:
        rows = self.certificates
        if not self.cert_show_archived:
            rows = [r for r in rows if not r.is_archived]
        if self.cert_filter_from:
            rows = [r for r in rows if r.issue_date >= self.cert_filter_from]
        if self.cert_filter_to:
            rows = [r for r in rows if r.issue_date <= self.cert_filter_to]
        col = self.cert_sort_column
        return sorted(
            rows,
            key=lambda r: str(getattr(r, col) or "").lower(),
            reverse=not self.cert_sort_ascending,
        )


    @rx.event
    async def on_load(self):
        """Load patient data, exam list and tab states when the page is mounted."""
        await self._load_patient()
        patient_id = self.patient_id_param
        if patient_id:
            from .patient_doctor_tab_state import PatientDoctorTabState
            from .patient_account_tab_state import PatientAccountTabState
            from .patient_campaign_tab_state import PatientCampaignTabState
            yield PatientDoctorTabState.load(patient_id)
            yield PatientAccountTabState.load(patient_id)
            yield PatientCampaignTabState.load(patient_id)

    @rx.event
    def go_back(self):
        return rx.call_script("window.history.back()")

    @rx.event
    def open_id_card(self):
        """Open the patient ID card dialog."""
        self.show_id_card = True

    @rx.event
    def close_id_card(self):
        """Close the patient ID card dialog."""
        self.show_id_card = False

    # ── Prescription events ───────────────────────────────────────────────────

    @rx.event
    def open_prescription_dialog(self):
        from datetime import date
        self.prescription_form_date = date.today().isoformat()
        self.prescription_form_diagnosis = ""
        self.prescription_form_instructions = ""
        self.prescription_form_drugs = [DrugLineDTO()]
        self.prescription_form_error = ""
        self.show_prescription_dialog = True

    @rx.event
    def close_prescription_dialog(self):
        self.show_prescription_dialog = False

    @rx.event
    def set_prescription_form_date(self, value: str):
        self.prescription_form_date = value

    @rx.event
    def set_prescription_form_diagnosis(self, value: str):
        self.prescription_form_diagnosis = value

    @rx.event
    def set_prescription_form_instructions(self, value: str):
        self.prescription_form_instructions = value

    @rx.event
    def prescription_add_drug(self):
        self.prescription_form_drugs = self.prescription_form_drugs + [DrugLineDTO()]

    @rx.event
    def prescription_remove_drug(self, index: int):
        drugs = list(self.prescription_form_drugs)
        if len(drugs) > 1:
            drugs.pop(index)
        self.prescription_form_drugs = drugs

    @rx.event
    def prescription_set_drug_name(self, index: int, value: str):
        drugs = [DrugLineDTO(**d.dict()) for d in self.prescription_form_drugs]
        if 0 <= index < len(drugs):
            drugs[index].name = value
        self.prescription_form_drugs = drugs

    @rx.event
    def prescription_set_drug_dosage(self, index: int, value: str):
        drugs = [DrugLineDTO(**d.dict()) for d in self.prescription_form_drugs]
        if 0 <= index < len(drugs):
            drugs[index].dosage = value
        self.prescription_form_drugs = drugs

    @rx.event
    def prescription_set_drug_frequency(self, index: int, value: str):
        drugs = [DrugLineDTO(**d.dict()) for d in self.prescription_form_drugs]
        if 0 <= index < len(drugs):
            drugs[index].frequency = value
        self.prescription_form_drugs = drugs

    @rx.event
    def prescription_set_drug_duration(self, index: int, value: str):
        drugs = [DrugLineDTO(**d.dict()) for d in self.prescription_form_drugs]
        if 0 <= index < len(drugs):
            drugs[index].duration = value
        self.prescription_form_drugs = drugs

    @rx.event
    def prescription_set_drug_dosage_unit(self, index: int, value: str):
        drugs = [DrugLineDTO(**d.dict()) for d in self.prescription_form_drugs]
        if 0 <= index < len(drugs):
            drugs[index].dosage_unit = value
        self.prescription_form_drugs = drugs

    @rx.event
    def prescription_set_drug_frequency_unit(self, index: int, value: str):
        drugs = [DrugLineDTO(**d.dict()) for d in self.prescription_form_drugs]
        if 0 <= index < len(drugs):
            drugs[index].frequency_unit = value
        self.prescription_form_drugs = drugs

    @rx.event
    def prescription_set_drug_duration_unit(self, index: int, value: str):
        drugs = [DrugLineDTO(**d.dict()) for d in self.prescription_form_drugs]
        if 0 <= index < len(drugs):
            drugs[index].duration_unit = value
        self.prescription_form_drugs = drugs

    @rx.event
    async def save_prescription(self):
        if not self.patient:
            return
        if not self.prescription_form_date:
            self.prescription_form_error = "La date est obligatoire."
            return
        self.prescription_form_error = ""
        self.is_saving_prescription = True
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.prescription.prescription import (
                    DrugLineDTO as ServiceDrugLineDTO,
                )
                from gws_care.prescription.prescription import (
                    PrescriptionService,
                    SavePrescriptionDTO,
                )
                from gws_care.user.user import User
                doctor = User.get_by_id(str(auth_user.id))
                dto = SavePrescriptionDTO(
                    patient_id=self.patient.id,
                    prescription_date=self.prescription_form_date,
                    drugs=[
                        ServiceDrugLineDTO(
                            name=d.name,
                            dosage=d.dosage,
                            frequency=d.frequency,
                            duration=d.duration,
                        )
                        for d in self.prescription_form_drugs
                        if d.name.strip()
                    ],
                    instructions=self.prescription_form_instructions,
                    diagnosis=self.prescription_form_diagnosis,
                )
                PrescriptionService.create(dto, doctor)
            self.show_prescription_dialog = False
            await self._load_prescriptions()
        except Exception as e:
            self.prescription_form_error = str(e)
        finally:
            self.is_saving_prescription = False

    @rx.event
    async def download_prescription_pdf(self, prescription_id: str):
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_prescription_pdf
                pdf_bytes = generate_prescription_pdf(prescription_id)
            return rx.download(data=pdf_bytes, filename=f"ordonnance_{prescription_id[:8]}.pdf")
        except Exception as e:
            self.error_message = f"Erreur génération PDF : {e}"

    @rx.event
    async def delete_prescription(self, prescription_id: str):
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.prescription.prescription import PrescriptionService
                PrescriptionService.delete(prescription_id)
            await self._load_prescriptions()
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def download_id_card_pdf(self):
        """Generate and download the patient ID card as a PDF."""
        if not self.patient:
            return
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_patient_id_card_pdf
                pdf_bytes = generate_patient_id_card_pdf(self.patient.id)
            filename = f"carte_patient_{self.patient.patient_number}.pdf"
            return rx.download(data=pdf_bytes, filename=filename)
        except Exception as e:
            self.error_message = f"PDF generation error: {e}"

    @rx.event
    def go_to_exam(self, exam_id: str):
        """Navigate to the exam detail page."""
        return rx.redirect(f"/exam/{exam_id}")

    @rx.event
    def go_to_exam_or_consultation(self, exam_id: str, visit_id: str):
        """Navigate directly to the exam tab inside the consultation page."""
        if visit_id and exam_id:
            return rx.redirect(f"/consultation/{visit_id}/exam/{exam_id}")
        if visit_id:
            return rx.redirect(f"/consultation/{visit_id}")
        return rx.redirect(f"/exam/{exam_id}")

    @rx.event
    def go_to_prescription(self, prescription_id: str):
        """Navigate to the prescription detail page."""
        return rx.redirect(f"/prescription/{prescription_id}")

    @rx.event
    def go_to_certificate(self, certificate_id: str):
        """Navigate to the certificate detail page."""
        return rx.redirect(f"/certificate/{certificate_id}")

    @rx.event
    def go_to_visit(self, visit_id: str):
        """Navigate to the visit detail page."""
        return rx.redirect(f"/visit/{visit_id}")

    @rx.event
    def go_to_consultation_visit(self, visit_id: str):
        """Navigate to the consultation detail page."""
        return rx.redirect(f"/consultation/{visit_id}")

    @rx.event
    def go_to_campaign(self, campaign_id: str):
        """Navigate to the campaign detail page."""
        return rx.redirect(f"/campaign/{campaign_id}")

    @rx.event
    def go_to_visits(self):
        """Navigate to the visits page."""
        return rx.redirect("/visits")

    # ── Standalone visit creation ─────────────────────────────────────────────

    @rx.event
    def open_book_appointment_for_patient(self):
        """Open the appointment booking wizard pre-filled with this patient."""
        if not self.patient or not self.patient.id:
            return
        from ..appointment_list.appointment_form_state import AppointmentFormState
        label = f"{self.patient.last_name} {self.patient.first_name}"
        return AppointmentFormState.open_create_dialog(
            self.patient.id, label, self.patient.account_id or ""
        )

    @rx.event
    def open_create_visit_dialog(self):
        self.show_create_visit_dialog = True
        self.create_visit_scheduled_at = ""
        self.create_visit_error = ""
        # Auto-select when the patient has exactly one linked account
        if len(self.patient_accounts) == 1:
            self.create_visit_account_id = self.patient_accounts[0].id
        else:
            self.create_visit_account_id = ""

    @rx.event
    def close_create_visit_dialog(self):
        self.show_create_visit_dialog = False

    @rx.event
    def set_create_visit_scheduled_at(self, value: str):
        self.create_visit_scheduled_at = value

    @rx.event
    def set_create_visit_account_id(self, value: str):
        self.create_visit_account_id = "" if value == "none" else value

    @rx.event
    async def save_create_visit(self):
        if not self.patient:
            return
        if not self.create_visit_scheduled_at:
            self.create_visit_error = "Veuillez sélectionner une date et une heure."
            return
        self.create_visit_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.campaign_visit_service import CampaignVisitService
                from gws_care.visit.visit_dto import SaveStandaloneVisitDTO
                dto = SaveStandaloneVisitDTO(
                    patient_id=self.patient.id,
                    billing_account_id=self.create_visit_account_id or None,
                    scheduled_at=self.create_visit_scheduled_at,
                )
                _visit, program = CampaignVisitService.create_visit_with_default_campaign(
                    patient_id=dto.patient_id,
                    scheduled_at_str=dto.scheduled_at,
                    billing_account_id=dto.billing_account_id,
                )
            self.show_create_visit_dialog = False
            return rx.redirect(f"/campaign/{program.id}")
        except Exception as e:
            self.create_visit_error = str(e)

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
                from gws_care.exam.exam_service import ExamService
                from gws_care.patient.patient_service import PatientService
                from gws_care.visit.campaign_visit_service import CampaignVisitService
                p = PatientService.get_patient(patient_id)
                # Resolve referent doctor from PatientDoctor table
                physician_id = ""
                physician_full_name = ""
                physician_specialization = ""
                physician_phone = ""
                physician_email = ""
                try:
                    from gws_care.patient.patient_doctor_service import PatientDoctorService
                    referent = PatientDoctorService.get_referent(patient_id)
                    if referent:
                        physician_id = str(referent.id)
                        physician_full_name = referent.get_full_name()
                        physician_specialization = referent.specialization or ""
                        physician_phone = referent.phone or ""
                        physician_email = referent.email or ""
                except Exception:
                    pass

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
                    address_complement=p.address_complement if hasattr(p, "address_complement") else None,
                    postal_code=p.postal_code,
                    city=p.city,
                    country=p.country if hasattr(p, "country") else None,
                    phone=p.phone,
                    email=p.email,
                    social_security_number=p.social_security_number,
                    sex=p.sex,
                    nationality=p.nationality,
                    phone_country=p.phone_country,
                    weight=float(p.weight) if p.weight is not None else None,
                    height=float(p.height) if p.height is not None else None,
                    qr_code=p.qr_code,
                    primary_physician_id=physician_id,
                    primary_physician_full_name=physician_full_name,
                    primary_physician_specialization=physician_specialization,
                    primary_physician_phone=physician_phone,
                    primary_physician_email=physician_email,
                    is_archived=bool(getattr(p, "is_archived", False)),
                    archived_reason=getattr(p, "archived_reason", None) or None,
                    archived_at=getattr(p, "archived_at", None) or None,
                )
                exams = ExamService.list_exams_for_patient(patient_id)

                # Resolve exam type ref labels in one pass
                _ref_label_cache: dict[str, str] = {}
                def _exam_label(e) -> str:
                    ref_id = str(getattr(e, "exam_type_ref_id", None) or "")
                    if ref_id:
                        if ref_id not in _ref_label_cache:
                            try:
                                from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                                ref = ExamTypeRef.get_or_none(ExamTypeRef.id == ref_id)
                                _ref_label_cache[ref_id] = ref.name if ref else ""
                            except Exception:
                                _ref_label_cache[ref_id] = ""
                        if _ref_label_cache[ref_id]:
                            return _ref_label_cache[ref_id]
                    return e.exam_type.get_label()

                self.exams = [
                    ExamRowDTO(
                        id=str(e.id),
                        exam_date=e.exam_date.isoformat(),
                        exam_type_label=_exam_label(e),
                        status=e.status.value,
                        visit_id=str(e.visit_id) if getattr(e, "visit_id", None) else "",
                    )
                    for e in exams
                ]
                # Build exam type filter options from exams present for this patient
                seen: set[str] = set()
                options: list[str] = []
                for e in exams:
                    lbl = e.exam_type.get_label()
                    if lbl not in seen:
                        seen.add(lbl)
                        options.append(lbl)
                self.exam_type_options = sorted(options)
                from gws_care.visit.visit_type import VisitType
                visits = CampaignVisitService.list_for_patient(patient_id)
                campaign_rows = [
                    PatientVisitRowDTO(
                        id=str(v.id),
                        visit_number=v.visit_number,
                        visit_type="campaign",
                        campaign_name=v.campaign.name if v.campaign_id else "",
                        campaign_id=str(v.campaign_id) if v.campaign_id else "",
                        scheduled_at=v.scheduled_at.isoformat() if v.scheduled_at else "",
                        campaign_visit_status=v.campaign_visit_status.value,
                        status_label=v.campaign_visit_status.get_label(),
                        appointment_mode=v.appointment_mode.value if v.appointment_mode else "",
                        doctor_name=v.doctor.get_full_name() if v.doctor_id else "",
                    )
                    for v in visits
                    if v.visit_type == VisitType.CAMPAIGN
                ]
                from gws_care.visit.consultation_service import ConsultationService
                consultations = ConsultationService.list_for_patient(patient_id)
                consultation_rows = []
                for cv in consultations:
                    cvs = cv.consultation_visit_status
                    consultation_rows.append(PatientVisitRowDTO(
                        id=str(cv.id),
                        visit_number=cv.visit_number,
                        visit_type="consultation",
                        campaign_name="",
                        campaign_id="",
                        scheduled_at=cv.scheduled_at.isoformat() if cv.scheduled_at else "",
                        campaign_visit_status=cvs.value if cvs else "",
                        status_label=cvs.get_label() if cvs else "",
                        appointment_mode=cv.appointment_mode.value if cv.appointment_mode else "",
                        doctor_name=cv.doctor.get_full_name() if cv.doctor_id else "",
                    ))
                all_rows = campaign_rows + consultation_rows
                all_rows.sort(key=lambda r: r.scheduled_at or "", reverse=True)
                self.patient_visits = all_rows
                seen_doctors: set[str] = set()
                doctor_options: list[str] = []
                for v in list(visits) + list(consultations):
                    name = v.doctor.get_full_name() if v.doctor_id else ""
                    if name and name not in seen_doctors:
                        seen_doctors.add(name)
                        doctor_options.append(name)
                self.visit_doctor_options = sorted(doctor_options)

                # ── Consultation history timeline ─────────────────────────────
                # Group already-loaded exams by visit_id
                exams_by_visit: dict[str, list] = {}
                for e in exams:
                    vid = str(e.visit_id) if getattr(e, "visit_id", None) else ""
                    if vid:
                        exams_by_visit.setdefault(vid, []).append(e)

                # Batch: find exam IDs with at least one abnormal parameter result
                abnormal_exam_ids: set[str] = set()
                try:
                    from gws_care.exam.exam_parameter_result import ExamParameterResult
                    for r in ExamParameterResult.select(ExamParameterResult.exam).where(
                        ExamParameterResult.status << [
                            "HIGH", "LOW", "CRITICAL_HIGH", "CRITICAL_LOW", "POSITIVE"
                        ]
                    ).distinct():
                        abnormal_exam_ids.add(str(r.exam_id))
                except Exception:
                    pass

                # Prescription and certificate counts per visit
                presc_counts: dict[str, int] = {}
                cert_counts: dict[str, int] = {}
                try:
                    from gws_care.certificate.medical_certificate import MedicalCertificate
                    from gws_care.prescription.prescription import Prescription
                    for p in Prescription.select(Prescription.id, Prescription.visit).where(
                        Prescription.patient == patient_id
                    ):
                        if p.visit_id:
                            vid = str(p.visit_id)
                            presc_counts[vid] = presc_counts.get(vid, 0) + 1
                    for c in MedicalCertificate.select(MedicalCertificate.id, MedicalCertificate.visit).where(
                        MedicalCertificate.patient == patient_id
                    ):
                        if c.visit_id:
                            vid = str(c.visit_id)
                            cert_counts[vid] = cert_counts.get(vid, 0) + 1
                except Exception:
                    pass

                history_items: list[ConsultationHistoryDTO] = []
                from datetime import datetime as _datetime
                for cv in sorted(
                    list(consultations),
                    key=lambda v: v.scheduled_at or _datetime.min,
                    reverse=True,
                ):
                    vid = str(cv.id)
                    cv_exams = exams_by_visit.get(vid, [])
                    exam_items = []
                    has_abnormal = False
                    for e in cv_exams:
                        e_abnormal = str(e.id) in abnormal_exam_ids
                        if e_abnormal:
                            has_abnormal = True
                        # Try to get label from exam_type_ref
                        label = e.exam_type.get_label()
                        if getattr(e, "exam_type_ref_id", None):
                            try:
                                from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                                ref = ExamTypeRef.get_or_none(ExamTypeRef.id == e.exam_type_ref_id)
                                if ref:
                                    label = ref.name
                            except Exception:
                                pass
                        exam_items.append(ExamHistoryItemDTO(
                            exam_type_label=label,
                            status=e.status.value,
                            has_abnormal=e_abnormal,
                        ))
                    prescription_count = presc_counts.get(vid, 0)
                    certificate_count = cert_counts.get(vid, 0)
                    # Skip empty visits — created (e.g. via "+ Nouvel examen") but
                    # abandoned before any exam/prescription/certificate was added
                    if not exam_items and not prescription_count and not certificate_count:
                        continue
                    cvs = cv.consultation_visit_status
                    history_items.append(ConsultationHistoryDTO(
                        id=vid,
                        visit_number=cv.visit_number,
                        scheduled_at=cv.scheduled_at.isoformat() if cv.scheduled_at else "",
                        status=cvs.value if cvs else "",
                        reason_for_visit=getattr(cv, "reason_for_visit", None) or "",
                        medical_history=getattr(cv, "medical_history", None) or "",
                        exams=exam_items,
                        prescription_count=prescription_count,
                        certificate_count=certificate_count,
                        has_abnormal_results=has_abnormal,
                    ))
                self.consultation_history = history_items
                # Store the most recent non-empty medical history for quick reference
                self.latest_medical_history = next(
                    (h.medical_history for h in history_items if h.medical_history), ""
                )

                from gws_care.patient.patient_account import PatientAccount
                links = list(PatientAccount.select().where(PatientAccount.patient == patient_id))
                self.patient_accounts = [
                    AccountForVisitDTO(id=str(link.account_id), name=link.account.name)
                    for link in links
                ]
                if links:
                    self.patient.account_name = links[0].account.name
                    self.patient.account_id = str(links[0].account_id)
                else:
                    self.patient.account_name = ""
                    self.patient.account_id = ""
            await self._load_prescriptions()
            await self._load_certificates()
        except Exception as e:
            self.error_message = f"Error loading patient: {e}"
        finally:
            self.is_loading = False

    async def _load_prescriptions(self):
        """Load the prescriptions list for the current patient."""
        patient_id = self.patient_id_param
        if not patient_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.prescription.prescription import PrescriptionService
                rows = PrescriptionService.list_for_patient(patient_id, include_archived=True)
                self.prescriptions = [
                    PrescriptionRowDTO(
                        id=str(r.id),
                        prescription_date=r.prescription_date.isoformat(),
                        drug_count=len(r.drugs),
                        diagnosis=r.diagnosis or "",
                        prescribed_by_name=r.to_row_dto().prescribed_by_name,
                        is_archived=bool(r.is_archived),
                    )
                    for r in rows
                ]
        except Exception as e:
            self.error_message = f"Error loading prescriptions: {e}"

    async def _reload_visits(self):
        """Reload only the visits list for the current patient."""
        patient_id = self.patient_id_param
        if not patient_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.visit.campaign_visit_service import CampaignVisitService
                from gws_care.visit.consultation_service import ConsultationService
                from gws_care.visit.visit_type import VisitType
                visits = CampaignVisitService.list_for_patient(patient_id)
                campaign_rows = [
                    PatientVisitRowDTO(
                        id=str(v.id),
                        visit_number=v.visit_number,
                        visit_type="campaign",
                        campaign_name=v.campaign.name if v.campaign_id else "",
                        campaign_id=str(v.campaign_id) if v.campaign_id else "",
                        scheduled_at=v.scheduled_at.isoformat() if v.scheduled_at else "",
                        campaign_visit_status=v.campaign_visit_status.value,
                        status_label=v.campaign_visit_status.get_label(),
                        appointment_mode=v.appointment_mode.value if v.appointment_mode else "",
                        doctor_name=v.doctor.get_full_name() if v.doctor_id else "",
                    )
                    for v in visits
                    if v.visit_type == VisitType.CAMPAIGN
                ]
                consultations = ConsultationService.list_for_patient(patient_id)
                consultation_rows = []
                for cv in consultations:
                    cvs = cv.consultation_visit_status
                    consultation_rows.append(PatientVisitRowDTO(
                        id=str(cv.id),
                        visit_number=cv.visit_number,
                        visit_type="consultation",
                        campaign_name="",
                        campaign_id="",
                        scheduled_at=cv.scheduled_at.isoformat() if cv.scheduled_at else "",
                        campaign_visit_status=cvs.value if cvs else "",
                        status_label=cvs.get_label() if cvs else "",
                        appointment_mode=cv.appointment_mode.value if cv.appointment_mode else "",
                        doctor_name=cv.doctor.get_full_name() if cv.doctor_id else "",
                    ))
                all_rows = campaign_rows + consultation_rows
                all_rows.sort(key=lambda r: r.scheduled_at or "", reverse=True)
                self.patient_visits = all_rows
                seen_doctors: set[str] = set()
                doctor_options: list[str] = []
                for v in list(visits) + list(consultations):
                    name = v.doctor.get_full_name() if v.doctor_id else ""
                    if name and name not in seen_doctors:
                        seen_doctors.add(name)
                        doctor_options.append(name)
                self.visit_doctor_options = sorted(doctor_options)
        except Exception:
            pass

    # ── Certificate event handlers ────────────────────────────────────────────

    @rx.event
    def open_certificate_dialog(self):
        """Open the new certificate dialog with a fresh form."""
        self.cert_form_type = "APTITUDE"
        self.cert_form_date = ""
        self.cert_form_conclusion = ""
        self.cert_form_is_fit_for_work = True
        self.cert_form_restrictions = ""
        self.cert_form_start_date = ""
        self.cert_form_end_date = ""
        self.cert_form_return_date = ""
        self.cert_form_visit_subtype = ""
        self.cert_form_accident_date = ""
        self.cert_form_body_part = ""
        self.cert_form_exposure_type = ""
        self.cert_form_vaccine_name = ""
        self.cert_form_vaccine_lot = ""
        self.cert_form_next_booster = ""
        self.cert_form_error = ""
        self.is_saving_certificate = False
        self.show_certificate_dialog = True

    @rx.event
    def close_certificate_dialog(self):
        self.show_certificate_dialog = False

    @rx.event
    def set_cert_form_type(self, value: str):
        self.cert_form_type = value

    @rx.event
    def set_cert_form_date(self, value: str):
        self.cert_form_date = value

    @rx.event
    def set_cert_form_conclusion(self, value: str):
        self.cert_form_conclusion = value

    @rx.event
    def set_cert_form_is_fit_for_work(self, value: bool):
        self.cert_form_is_fit_for_work = value

    @rx.event
    def set_cert_form_restrictions(self, value: str):
        self.cert_form_restrictions = value

    @rx.event
    def set_cert_form_start_date(self, value: str):
        self.cert_form_start_date = value

    @rx.event
    def set_cert_form_end_date(self, value: str):
        self.cert_form_end_date = value

    @rx.event
    def set_cert_form_return_date(self, value: str):
        self.cert_form_return_date = value

    @rx.event
    def set_cert_form_visit_subtype(self, value: str):
        self.cert_form_visit_subtype = value

    @rx.event
    def set_cert_form_accident_date(self, value: str):
        self.cert_form_accident_date = value

    @rx.event
    def set_cert_form_body_part(self, value: str):
        self.cert_form_body_part = value

    @rx.event
    def set_cert_form_exposure_type(self, value: str):
        self.cert_form_exposure_type = value

    @rx.event
    def set_cert_form_vaccine_name(self, value: str):
        self.cert_form_vaccine_name = value

    @rx.event
    def set_cert_form_vaccine_lot(self, value: str):
        self.cert_form_vaccine_lot = value

    @rx.event
    def set_cert_form_next_booster(self, value: str):
        self.cert_form_next_booster = value

    @rx.event
    async def save_certificate(self):
        """Validate and persist a new medical certificate."""
        if not self.cert_form_date:
            self.cert_form_error = "La date d'émission est requise."
            return
        if not self.cert_form_conclusion.strip():
            self.cert_form_error = "La conclusion médicale est requise."
            return
        self.cert_form_error = ""
        self.is_saving_certificate = True
        try:
            with await self.authenticate_user() as user:
                from datetime import date

                from gws_care.certificate.medical_certificate import (
                    MedicalCertificateService,
                    SaveMedicalCertificateDTO,
                )
                dto = SaveMedicalCertificateDTO(
                    patient_id=self.patient_id_param,
                    issue_date=date.fromisoformat(self.cert_form_date),
                    conclusion=self.cert_form_conclusion.strip(),
                    is_fit_for_work=self.cert_form_is_fit_for_work,
                    restrictions=self.cert_form_restrictions.strip() or None,
                    certificate_type=self.cert_form_type,
                    start_date=self.cert_form_start_date or None,
                    end_date=self.cert_form_end_date or None,
                    return_date=self.cert_form_return_date or None,
                    visit_subtype=self.cert_form_visit_subtype.strip() or None,
                    accident_date=self.cert_form_accident_date or None,
                    body_part=self.cert_form_body_part.strip() or None,
                    exposure_type=self.cert_form_exposure_type.strip() or None,
                    vaccine_name=self.cert_form_vaccine_name.strip() or None,
                    vaccine_lot=self.cert_form_vaccine_lot.strip() or None,
                    next_booster=self.cert_form_next_booster or None,
                )
                MedicalCertificateService.create_certificate(dto, issued_by=user)
            self.show_certificate_dialog = False
            await self._load_certificates()
        except Exception as e:
            self.cert_form_error = f"Erreur : {e}"
        finally:
            self.is_saving_certificate = False

    @rx.event
    async def download_certificate_pdf(self, certificate_id: str):
        """Generate and stream the certificate PDF to the browser."""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_certificate_pdf
                pdf_bytes = generate_certificate_pdf(certificate_id)
            import base64
            b64 = base64.b64encode(pdf_bytes).decode()
            yield rx.call_script(
                f"const a=document.createElement('a');a.href='data:application/pdf;base64,{b64}';"
                f"a.download='certificat_{certificate_id[:8]}.pdf';a.click();"
            )
        except Exception as e:
            self.error_message = f"PDF error: {e}"

    @rx.event
    async def delete_certificate(self, certificate_id: str):
        """Delete a medical certificate."""
        try:
            with await self.authenticate_user():
                from gws_care.certificate.medical_certificate import MedicalCertificateService
                MedicalCertificateService.delete(certificate_id)
            await self._load_certificates()
        except Exception as e:
            self.error_message = f"Delete error: {e}"

    async def _load_certificates(self):
        """Load the certificates list for the current patient."""
        patient_id = self.patient_id_param
        if not patient_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.certificate.medical_certificate import (
                    CERTIFICATE_TYPES,
                    MedicalCertificateService,
                )
                rows = MedicalCertificateService.list_for_patient(patient_id, include_archived=True)
                issued_by_cache: dict = {}

                def _get_issued_by(cert) -> str:
                    if not cert.issued_by_id:
                        return ""
                    uid = str(cert.issued_by_id)
                    if uid not in issued_by_cache:
                        try:
                            from gws_care.user.user import User
                            u = User.get_by_id(uid)
                            issued_by_cache[uid] = f"Dr. {u.first_name} {u.last_name}"
                        except Exception:
                            issued_by_cache[uid] = ""
                    return issued_by_cache[uid]

                self.certificates = [
                    CertificateRowDTO(
                        id=str(c.id),
                        issue_date=c.issue_date.isoformat() if c.issue_date else "",
                        certificate_type=c.certificate_type or "APTITUDE",
                        certificate_type_label=CERTIFICATE_TYPES.get(
                            c.certificate_type or "APTITUDE", c.certificate_type or ""
                        ),
                        conclusion=c.conclusion or "",
                        is_fit_for_work=c.is_fit_for_work,
                        issued_by_name=_get_issued_by(c),
                        is_archived=bool(c.is_archived),
                    )
                    for c in rows
                ]
        except Exception as e:
            self.error_message = f"Error loading certificates: {e}"

    # ── Archive events ─────────────────────────────────────────────────────────

    @rx.event
    def open_archive_dialog(self):
        self.show_archive_dialog = True
        self.archive_reason = ""
        self.archive_error = ""

    @rx.event
    def close_archive_dialog(self):
        self.show_archive_dialog = False

    @rx.event
    def set_archive_reason(self, value: str):
        self.archive_reason = value

    @rx.event(background=True)
    async def confirm_archive(self):
        async with self:
            if not self.archive_reason.strip():
                self.archive_error = "Veuillez saisir un motif d'archivage"
                return
            self.is_archiving = True
            self.archive_error = ""
            patient_id = self.patient_id_param
            reason = self.archive_reason.strip()
            _main = await self.get_state(ReflexMainState)
        try:
            with await _main.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                PatientService.archive_patient(patient_id, reason)
            async with self:
                self.show_archive_dialog = False
            yield rx.toast.success("Patient archivé")
            from ..patient_list.patient_list_state import PatientListState
            yield PatientListState.on_load
            yield PatientDetailState.on_load()
        except Exception as e:
            async with self:
                self.archive_error = str(e)
        finally:
            async with self:
                self.is_archiving = False

    # ── Delete events ──────────────────────────────────────────────────────────

    @rx.event
    def open_delete_dialog(self):
        self.show_delete_dialog = True
        self.delete_reason = ""
        self.delete_error = ""

    @rx.event
    def close_delete_dialog(self):
        self.show_delete_dialog = False

    @rx.event
    def set_delete_reason(self, value: str):
        self.delete_reason = value

    @rx.event(background=True)
    async def confirm_delete(self):
        async with self:
            if not self.delete_reason.strip():
                self.delete_error = "Veuillez saisir un motif de suppression"
                return
            self.is_deleting = True
            self.delete_error = ""
            patient_id = self.patient_id_param
            reason = self.delete_reason.strip()
            _main = await self.get_state(ReflexMainState)
        try:
            with await _main.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                PatientService.delete_patient(patient_id, reason)
            yield rx.toast.success("Patient supprimé définitivement")
            from ..patient_list.patient_list_state import PatientListState
            yield PatientListState.on_load
            yield rx.redirect("/")
        except Exception as e:
            async with self:
                self.delete_error = str(e)
        finally:
            async with self:
                self.is_deleting = False
