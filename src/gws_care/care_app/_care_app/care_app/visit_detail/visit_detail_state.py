"""State for the visit detail page (7.3)."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class ExamResultRowDTO(BaseModel):
    exam_id: str = ""          # empty when the Exam record hasn't been created yet
    exam_type_model_id: str = ""  # ExamTypeModel PK — always populated for campaign exams
    exam_type_name: str
    exam_type_code: str
    status: str = ""
    result_data: dict = {}
    primary_value: str = ""
    edit_value: str = ""  # draft value while editing
    appreciation: str = ""
    appreciation_label: str = ""
    appreciation_override: bool = False


class VisitDetailDTO(BaseModel):
    id: str
    visit_number: str
    patient_name: str = ""
    patient_id: str = ""
    campaign_name: str = ""
    program_id: str = ""
    status: str
    status_label: str
    # Lab validation
    lab_validated_by: str = ""
    lab_validated_at: str = ""
    # Clinic
    doctor_clinic_validated_by: str = ""
    doctor_clinic_validated_at: str = ""
    doctor_clinic_interpretation: str = ""
    # Company
    doctor_company_validated_by: str = ""
    doctor_company_validated_at: str = ""
    doctor_company_interpretation: str = ""
    doctor_company_message: str = ""


class VisitCertificateRowDTO(BaseModel):
    id: str
    issue_date: str
    conclusion: str
    is_fit_for_work: bool
    issued_by_name: str = ""
    restrictions: str = ""


_APPRECIATION_LABELS = {
    "critical_low": "Critique bas",
    "low": "Bas",
    "normal": "Normal",
    "high": "Haut",
    "critical_high": "Critique haut",
}


class CampaignVisitDetailState(RoleState):
    """State for the /visit/[id] page."""

    visit: VisitDetailDTO | None = None
    exam_results: list[ExamResultRowDTO] = []
    is_loading: bool = True
    error_message: str = ""
    success_message: str = ""

    # Editable interpretation fields (for doctors)
    clinic_interpretation: str = ""
    company_interpretation: str = ""
    company_message: str = ""
    is_saving_interpretation: bool = False
    is_saving_exam: bool = False

    # Certificates
    certificates: list[VisitCertificateRowDTO] = []
    cert_dialog_open: bool = False
    cert_form_issue_date: str = ""
    cert_form_conclusion: str = ""
    cert_form_is_fit_for_work: bool = True
    cert_form_restrictions: str = ""
    is_issuing_certificate: bool = False

    @rx.event
    async def on_load(self):
        await self._load_roles()
        # All authenticated roles can view a visit; patient portal has separate page
        redirect = await self._require_any_of(
            self.is_operator, self.is_doctor, self.is_account_admin, self.is_admin
        )
        if redirect:
            return redirect
        await self._load_visit()

    @rx.event
    def go_back(self):
        if self.visit and self.visit.program_id:
            return rx.redirect(f"/campaign/{self.visit.program_id}")
        return rx.redirect("/campaigns")

    @rx.var
    def visit_status_index(self) -> int:
        """Return the 0-based index of the current visit status in the workflow order."""
        order = ["pending", "visit_done", "lab_done", "doctor_clinic_validated", "doctor_company_validated"]
        if not self.visit:
            return 0
        try:
            return order.index(self.visit.status)
        except ValueError:
            return 0

    @rx.event
    async def set_workflow_status(self, status: str):
        """Force-set visit to any workflow status (supports going back)."""
        if not self.visit:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign_visit.campaign_visit_service import CampaignVisitService
                CampaignVisitService.force_set_status(self.visit.id, status)
            await self._load_visit()
        except Exception as e:
            self.error_message = str(e)

    @rx.var
    def all_exams_have_values(self) -> bool:
        """True only if there is at least one exam and every exam has a primary_value."""
        if not self.exam_results:
            return False
        return all(r.primary_value != "" for r in self.exam_results)

    @rx.event
    def set_exam_edit_value(self, etm_id: str, value: str):
        """Update the draft edit value for a row identified by exam_type_model_id."""
        self.exam_results = [
            ExamResultRowDTO(**{**r.dict(), "edit_value": value})
            if r.exam_type_model_id == etm_id
            else r
            for r in self.exam_results
        ]

    @rx.event
    async def save_exam_result(self, etm_id: str):
        """Save the exam result for the row identified by exam_type_model_id.

        Creates an Exam record if none exists yet for this visit + exam type.
        """
        if not self.visit:
            return
        target = next((r for r in self.exam_results if r.exam_type_model_id == etm_id), None)
        if target is None:
            return
        value_str = target.edit_value.strip()
        if not value_str:
            return
        self.error_message = ""
        self.is_saving_exam = True
        try:
            with await self.authenticate_user():
                from datetime import date

                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_result_dto import SaveExamResultDTO
                from gws_care.exam.exam_result_service import ExamResultService
                from gws_care.exam.exam_type_service import ExamTypeService

                exam_id = target.exam_id
                if not exam_id:
                    # No Exam record yet — create it from the ExamTypeModel
                    et_model = ExamTypeService.get_exam_type(etm_id)
                    exam = Exam()
                    exam.patient_id = self.visit.patient_id
                    exam.exam_type = et_model.category
                    exam.exam_date = date.today()
                    exam.visit_id = self.visit.id
                    exam.save()
                    exam_id = str(exam.id)

                try:
                    primary_value = float(value_str.replace(",", "."))
                except ValueError:
                    primary_value = None
                ExamResultService.save_result(
                    exam_id,
                    SaveExamResultDTO(
                        result_data={"value": primary_value if primary_value is not None else value_str},
                        primary_value=primary_value,
                        exam_type_model_id=etm_id,
                    ),
                )
            await self._load_visit()
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_saving_exam = False

    @rx.event
    def set_clinic_interpretation(self, value: str):
        self.clinic_interpretation = value

    @rx.event
    def set_company_interpretation(self, value: str):
        self.company_interpretation = value

    @rx.event
    def set_company_message(self, value: str):
        self.company_message = value

    # ── Certificate form setters ──────────────────────────────────────────────

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
    def set_cert_form_restrictions(self, value: str):
        self.cert_form_restrictions = value

    @rx.event
    def open_certificate_dialog(self):
        from datetime import date
        self.cert_form_issue_date = date.today().isoformat()
        self.cert_form_conclusion = ""
        self.cert_form_is_fit_for_work = True
        self.cert_form_restrictions = ""
        self.cert_dialog_open = True

    @rx.event
    def close_certificate_dialog(self):
        self.cert_dialog_open = False

    @rx.event
    async def submit_certificate(self):
        if not self.visit:
            return
        if not self.cert_form_conclusion.strip():
            self.error_message = "La conclusion est requise."
            return
        self.error_message = ""
        self.is_issuing_certificate = True
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.certificate.medical_certificate import (
                    MedicalCertificateService,
                    SaveMedicalCertificateDTO,
                )
                from gws_care.user.user import User

                doctor = User.get_by_id(str(auth_user.id))
                dto = SaveMedicalCertificateDTO(
                    patient_id=self.visit.patient_id,
                    exam_id=None,
                    issue_date=self.cert_form_issue_date,
                    conclusion=self.cert_form_conclusion,
                    is_fit_for_work=self.cert_form_is_fit_for_work,
                    restrictions=self.cert_form_restrictions or None,
                )
                MedicalCertificateService.create_certificate(dto, doctor)

            self.cert_dialog_open = False
            self.success_message = "Certificat émis avec succès."
            await self._load_visit()
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_issuing_certificate = False

    @rx.event
    async def download_certificate_pdf(self, certificate_id: str):
        """Download a medical certificate as PDF."""
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_certificate_pdf
                pdf_bytes = generate_certificate_pdf(certificate_id)
            return rx.download(data=pdf_bytes, filename=f"certificat_{certificate_id[:8]}.pdf")
        except Exception as e:
            self.error_message = f"Erreur génération PDF : {e}"

    @rx.event
    async def mark_terrain_done(self):
        if not self.visit:
            return
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign_visit.campaign_visit import CampaignVisit
                from gws_care.campaign_visit.campaign_visit_service import CampaignVisitService
                from gws_care.patient.patient import Patient
                CampaignVisitService.mark_terrain_done(self.visit.id)

                # Phase 5 — send on-site thank-you notification
                try:
                    from gws_care.notification.notification_service import NotificationService
                    visit_obj = CampaignVisit.get_by_id(self.visit.id)
                    patient_obj = Patient.get_by_id(str(visit_obj.patient_id))
                    NotificationService.send_terrain_thank_you(patient_obj, visit_obj)
                except Exception:
                    pass  # Notification failure must never block the workflow

            await self._load_visit()
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def validate_lab(self):
        if not self.visit:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.campaign_visit.campaign_visit_service import CampaignVisitService
                from gws_care.user.user import User
                user = User.get_by_id(str(auth_user.id))
                CampaignVisitService.validate_lab(self.visit.id, user)
            await self._load_visit()
            self.success_message = "Lab validation completed."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def validate_clinic(self):
        if not self.visit:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.campaign_visit.campaign_visit_dto import ValidateDoctorClinicDTO
                from gws_care.campaign_visit.campaign_visit_service import CampaignVisitService
                from gws_care.user.user import User
                user = User.get_by_id(str(auth_user.id))
                dto = ValidateDoctorClinicDTO(interpretation=self.clinic_interpretation)
                CampaignVisitService.validate_doctor_clinic(self.visit.id, user, dto)
            await self._load_visit()
            self.success_message = "Clinic validation completed."
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def validate_company(self):
        if not self.visit:
            return
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.campaign_visit.campaign_visit_dto import ValidateDoctorCompanyDTO
                from gws_care.campaign_visit.campaign_visit_service import CampaignVisitService
                from gws_care.user.user import User
                user = User.get_by_id(str(auth_user.id))
                dto = ValidateDoctorCompanyDTO(
                    interpretation=self.company_interpretation,
                    message=self.company_message,
                )
                CampaignVisitService.validate_doctor_company(self.visit.id, user, dto)
            await self._load_visit()
            self.success_message = "Company validation completed."
        except Exception as e:
            self.error_message = str(e)

    # ── Internal loader ───────────────────────────────────────────────────────

    @rx.event
    async def download_results_pdf(self):
        """Generate and download the visit results PDF."""
        if not self.visit:
            return
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_visit_results_pdf
                pdf_bytes = generate_visit_results_pdf(self.visit.id)
            filename = f"resultats_{self.visit.visit_number}.pdf"
            return rx.download(data=pdf_bytes, filename=filename)
        except Exception as e:
            self.error_message = f"Erreur génération PDF : {e}"

    async def _load_visit(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        self.error_message = ""
        try:
            visit_id = self.router.page.params.get("campaign_visit_id_param", "")
            if not visit_id:
                self.visit = None
                return

            with await self.authenticate_user():
                from gws_care.campaign_visit.campaign_visit_service import CampaignVisitService
                from gws_care.exam.exam_result_service import ExamResultService
                from gws_care.exam.exam_service import ExamService
                from gws_care.workflow.visit_validation_workflow import (
                    VisitValidationStep,
                    VisitValidationWorkflow,
                )

                visit = CampaignVisitService.get_visit(visit_id)

                # Load validation audit rows from workflow table
                def _workflow_row(step: VisitValidationStep):
                    try:
                        return VisitValidationWorkflow.get(
                            (VisitValidationWorkflow.visit == visit.id)
                            & (VisitValidationWorkflow.step == step)
                        )
                    except VisitValidationWorkflow.DoesNotExist:
                        return None

                def _user_name(row) -> str:
                    if row is None or not row.validated_by_id:
                        return ""
                    try:
                        from gws_care.user.user import User
                        u = User.get_by_id(str(row.validated_by_id))
                        return f"{u.first_name} {u.last_name}"
                    except Exception:
                        return ""

                lab_row = _workflow_row(VisitValidationStep.LAB_DONE)
                clinic_row = _workflow_row(VisitValidationStep.DOCTOR_CLINIC_VALIDATED)
                company_row = _workflow_row(VisitValidationStep.DOCTOR_COMPANY_VALIDATED)

                self.visit = VisitDetailDTO(
                    id=str(visit.id),
                    visit_number=visit.visit_number,
                    patient_name=visit.patient.get_full_name() if visit.patient_id else "",
                    patient_id=str(visit.patient_id) if visit.patient_id else "",
                    campaign_name=visit.program.name if visit.program_id else "",
                    program_id=str(visit.program_id) if visit.program_id else "",
                    status=visit.status.value,
                    status_label=visit.status.get_label(),
                    lab_validated_by=_user_name(lab_row),
                    lab_validated_at=str(lab_row.validated_at) if lab_row else "",
                    doctor_clinic_validated_by=_user_name(clinic_row),
                    doctor_clinic_validated_at=str(clinic_row.validated_at) if clinic_row else "",
                    doctor_clinic_interpretation=visit.doctor_clinic_interpretation or "",
                    doctor_company_validated_by=_user_name(company_row),
                    doctor_company_validated_at=str(company_row.validated_at) if company_row else "",
                    doctor_company_interpretation=visit.doctor_company_interpretation or "",
                    doctor_company_message=visit.doctor_company_message or "",
                )
                # Pre-fill editable interpretation fields
                self.clinic_interpretation = visit.doctor_clinic_interpretation or ""
                self.company_interpretation = visit.doctor_company_interpretation or ""
                self.company_message = visit.doctor_company_message or ""

                # Load exam results from campaign exam types (creates rows for all
                # configured exam types, even those without a result yet).
                try:
                    from gws_care.campaign.campaign_service import CampaignService
                    from gws_care.exam.exam import Exam

                    rows = []
                    if visit.program_id:
                        campaign_exam_types = CampaignService.get_exam_types(str(visit.program_id))

                        # Index existing exam records by their exam_type category
                        existing_exams = list(Exam.select().where(Exam.visit_id == str(visit_id)))
                        exams_by_category: dict = {}
                        for ex in existing_exams:
                            if ex.exam_type:
                                exams_by_category[ex.exam_type.value] = ex

                        for et_model in campaign_exam_types:
                            cat_key = et_model.category.value if et_model.category else ""
                            exam = exams_by_category.get(cat_key)

                            result = ExamResultService.get_result_for_exam(str(exam.id)) if exam else None
                            appr = ""
                            appr_label = ""
                            appr_override = False
                            primary_val = ""
                            result_data = {}
                            if result:
                                appr = result.appreciation.value if result.appreciation else ""
                                appr_label = _APPRECIATION_LABELS.get(appr, appr)
                                appr_override = result.appreciation_override or False
                                result_data = result.result_data or {}
                                if isinstance(result_data, dict) and result_data.get("primary_value") is not None:
                                    primary_val = str(result_data["primary_value"])
                                elif isinstance(result_data, dict) and result_data.get("value") is not None:
                                    primary_val = str(result_data["value"])

                            rows.append(ExamResultRowDTO(
                                exam_id=str(exam.id) if exam else "",
                                exam_type_model_id=str(et_model.id),
                                exam_type_name=et_model.name,
                                exam_type_code=et_model.code,
                                status=exam.status.value if exam else "",
                                result_data=result_data,
                                primary_value=primary_val,
                                edit_value=primary_val,
                                appreciation=appr,
                                appreciation_label=appr_label,
                                appreciation_override=appr_override,
                            ))

                    self.exam_results = rows
                except Exception as ex:
                    # Non-fatal: visit loads even without exam results
                    print(f"[VisitDetailState] Could not load exam results: {ex}")
                    self.exam_results = []

                # Load certificates for this patient
                try:
                    from gws_care.certificate.medical_certificate import (
                        MedicalCertificate,
                        MedicalCertificateService,
                    )
                    from gws_care.user.user import User as UserModel
                    certs_raw = MedicalCertificateService.list_for_patient(str(visit.patient_id))
                    cert_rows = []
                    for cert in certs_raw:
                        issued_name = ""
                        if cert.issued_by_id:
                            try:
                                u = UserModel.get_by_id(str(cert.issued_by_id))
                                issued_name = f"{u.first_name} {u.last_name}"
                            except Exception:
                                pass
                        cert_rows.append(VisitCertificateRowDTO(
                            id=str(cert.id),
                            issue_date=str(cert.issue_date),
                            conclusion=cert.conclusion,
                            is_fit_for_work=cert.is_fit_for_work,
                            issued_by_name=issued_name,
                            restrictions=cert.restrictions or "",
                        ))
                    self.certificates = cert_rows
                except Exception as ex:
                    print(f"[VisitDetailState] Could not load certificates: {ex}")
                    self.certificates = []

        except Exception as e:
            self.error_message = str(e)
            self.visit = None
        finally:
            self.is_loading = False
