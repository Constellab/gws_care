"""State for the consultation detail page (/consultation/[visit_id_param])."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class ConsultationDTO(BaseModel):
    id: str
    visit_number: str
    patient_name: str = ""
    patient_id: str = ""
    account_name: str = ""
    account_id: str = ""
    scheduled_at: str = ""
    status: str
    status_label: str


class ExamRowDTO(BaseModel):
    id: str
    exam_date: str
    exam_type: str
    exam_type_label: str
    status: str
    status_label: str = ""


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


class ConsultationDetailState(RoleState):
    """State for the /consultation/[visit_id_param] page."""

    consultation: ConsultationDTO | None = None
    exams: list[ExamRowDTO] = []
    prescriptions: list[PrescriptionRowDTO] = []
    certificates: list[CertificateRowDTO] = []

    is_loading: bool = True
    error_message: str = ""
    success_message: str = ""

    # Close dialog
    show_close_dialog: bool = False
    is_closing: bool = False

    # ── New Exam dialog ───────────────────────────────────────────────────────
    show_new_exam_dialog: bool = False
    new_exam_type: str = ""
    new_exam_date: str = ""
    new_exam_error: str = ""
    new_exam_is_saving: bool = False

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

    @rx.event
    def go_back(self):
        if self.is_patient_user:
            return rx.redirect("/my-consultations")
        if self.consultation and self.consultation.patient_id:
            return rx.redirect(f"/patient/{self.consultation.patient_id}")
        return rx.redirect("/consultations")

    @rx.event
    def open_close_dialog(self):
        self.show_close_dialog = True

    @rx.event
    def close_close_dialog(self):
        self.show_close_dialog = False

    @rx.event
    async def confirm_close_consultation(self):
        if not self.consultation:
            return
        self.is_closing = True
        self.error_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.visit.consultation_service import ConsultationService

                visit = ConsultationService.mark_done(
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
    async def cancel_consultation(self):
        if not self.consultation:
            return
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.consultation_service import ConsultationService

                ConsultationService.cancel(visit_id=self.consultation.id)

            self.success_message = "Consultation annulée."
            await self._load_consultation()
        except Exception as e:
            self.error_message = str(e)

    # ── Exam creation events ──────────────────────────────────────────────────

    @rx.event
    def open_new_exam_dialog(self):
        from datetime import date
        self.new_exam_type = ""
        self.new_exam_date = date.today().isoformat()
        self.new_exam_error = ""
        self.new_exam_is_saving = False
        self.show_new_exam_dialog = True

    @rx.event
    def close_new_exam_dialog(self):
        self.show_new_exam_dialog = False

    @rx.event
    def set_new_exam_type(self, value: str):
        self.new_exam_type = value

    @rx.event
    def set_new_exam_date(self, value: str):
        self.new_exam_date = value

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
        try:
            with await self.authenticate_user():
                from datetime import date

                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamStatus, ExamType

                exam = Exam()
                exam.patient_id = self.consultation.patient_id
                exam.visit_id = self.consultation.id
                exam.exam_date = date.fromisoformat(self.new_exam_date)
                exam.exam_type = ExamType(self.new_exam_type)
                exam.status = ExamStatus.DRAFT
                exam.save()
                exam_id = str(exam.id)
            self.show_new_exam_dialog = False
            return rx.redirect(f"/exam/{exam_id}")
        except Exception as e:
            self.new_exam_error = str(e)
        finally:
            self.new_exam_is_saving = False

    # ── Prescription creation events ──────────────────────────────────────────

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
        drugs = list(self.presc_form_drugs)
        if len(drugs) > 1:
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
                )
                from gws_care.prescription.prescription import (
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
                # Link to consultation visit
                from gws_care.prescription.prescription import Prescription
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

    # ── Certificate creation events ───────────────────────────────────────────

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
                # Link to consultation visit
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

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _load_consultation(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        self.error_message = ""
        try:
            visit_id = self.router.page.params.get("visit_id_param", "")
            if not visit_id:
                self.consultation = None
                return

            with await self.authenticate_user():
                from gws_care.certificate.medical_certificate import MedicalCertificate
                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type import ExamType
                from gws_care.prescription.prescription import Prescription
                from gws_care.visit.campaign_visit_service import CampaignVisitService

                visit = CampaignVisitService.get_visit(visit_id)

                # Patient security: patients may only view their own consultation
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

                self.consultation = ConsultationDTO(
                    id=str(visit.id),
                    visit_number=visit.visit_number,
                    patient_name=visit.patient.get_full_name() if visit.patient_id else "",
                    patient_id=str(visit.patient_id) if visit.patient_id else "",
                    account_name=account_name,
                    account_id=str(visit.billing_account_id) if visit.billing_account_id else "",
                    scheduled_at=visit.scheduled_at.isoformat() if visit.scheduled_at else "",
                    status=visit.consultation_visit_status.value if visit.consultation_visit_status else "",
                    status_label=visit.consultation_visit_status.get_label() if visit.consultation_visit_status else "",
                )

                # Linked exams
                exams = list(
                    Exam.select()
                    .where(Exam.visit == visit.id)
                    .order_by(Exam.exam_date.desc())
                )
                self.exams = [
                    ExamRowDTO(
                        id=str(e.id),
                        exam_date=e.exam_date.isoformat(),
                        exam_type=e.exam_type.value,
                        exam_type_label=e.exam_type.get_label() if hasattr(e.exam_type, "get_label") else e.exam_type.value,
                        status=e.status.value,
                        status_label=e.status.get_label() if hasattr(e.status, "get_label") else e.status.value,
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
                            if p.prescribed_by_id
                            else ""
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
                            if c.issued_by_id
                            else ""
                        ),
                    )
                    for c in certificates
                ]

        except Exception as e:
            self.error_message = f"Consultation introuvable : {e}"
            self.consultation = None
        finally:
            self.is_loading = False
