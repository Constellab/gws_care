"""State for the visit detail page (7.3)."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class ExamResultRowDTO(BaseModel):
    exam_id: str = ""  # empty when the Exam record hasn't been created yet
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
    campaign_id: str = ""
    campaign_visit_status: str
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


class VisitDetailState(RoleState):
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
    cert_form_fitness_decision: str = "FIT"
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
        return rx.call_script("window.history.back()")

    @rx.event
    def go_to_terrain(self):
        if self.visit and self.visit.campaign_id:
            return rx.redirect(f"/on-site/{self.visit.campaign_id}")

    @rx.event
    def open_exam_detail(self, exam_id: str):
        return rx.redirect(f"/exam/{exam_id}")

    @rx.event
    async def create_and_open_exam(self, exam_type_model_id: str):
        """Create an Exam record for this visit + exam type, then navigate to it.

        Auto-transitions PENDING → VISIT_DONE so result entry is possible
        without a separate "mark terrain done" step.
        """
        if not self.visit:
            return
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from datetime import date

                from gws_care.exam.exam import Exam
                from gws_care.exam.exam_type_service import ExamTypeService
                from gws_care.visit.campaign_visit_service import CampaignVisitService

                # Auto-transition PENDING → VISIT_DONE when starting result entry
                if self.visit.campaign_visit_status == "pending":
                    CampaignVisitService.mark_terrain_done(self.visit.id)
                    self.visit = self.visit.model_copy(
                        update={"campaign_visit_status": "visit_done"}
                    )

                # Reuse existing exam for this visit+type if already created
                existing = Exam.get_or_none(
                    (Exam.visit == self.visit.id) & (Exam.exam_type_ref_id == exam_type_model_id)
                )
                if existing:
                    return rx.redirect(f"/exam/{existing.id}")

                et_model = ExamTypeService.get_exam_type(exam_type_model_id)
                exam = Exam()
                exam.patient_id = self.visit.patient_id
                exam.exam_type = et_model.category
                exam.exam_type_ref_id = exam_type_model_id
                exam.exam_date = date.today()
                exam.visit_id = self.visit.id
                exam.save()
            return rx.redirect(f"/exam/{exam.id}")
        except Exception as e:
            self.error_message = str(e)

    @rx.var
    def visit_status_index(self) -> int:
        """Return the 0-based index of the current visit status in the workflow order."""
        order = [
            "pending",
            "visit_done",
            "lab_done",
            "doctor_clinic_validated",
            "doctor_company_validated",
        ]
        if not self.visit:
            return 0
        try:
            return order.index(self.visit.campaign_visit_status)
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
                from gws_care.visit.campaign_visit_service import CampaignVisitService

                CampaignVisitService.force_set_status(self.visit.id, status)
            await self._load_visit()
        except Exception as e:
            self.error_message = str(e)

    @rx.var
    def all_exams_done(self) -> bool:
        """True only if all exam types have at least been saved (non-empty exam_id)."""
        if not self.exam_results:
            return False
        return all(r.exam_id != "" for r in self.exam_results)

    @rx.event
    def go_to_results_entry(self):
        """Navigate to the campaign patient results entry page."""
        if self.visit and self.visit.campaign_id and self.visit.patient_id:
            return rx.redirect(
                f"/campaign-patient/{self.visit.campaign_id}/{self.visit.patient_id}"
            )

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
                        result_data={
                            "value": primary_value if primary_value is not None else value_str
                        },
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

    @rx.event
    async def save_interpretation_draft(self):
        """Silently persist interpretation fields to the Visit record (on blur, no toast)."""
        if not self.visit:
            return
        try:
            with await self.authenticate_user():
                from gws_care.visit.visit import Visit

                visit = Visit.get_by_id(self.visit.id)
                visit.doctor_clinic_interpretation = self.clinic_interpretation or None
                visit.doctor_company_interpretation = self.company_interpretation or None
                visit.doctor_company_message = self.company_message or None
                visit.save()
        except Exception:
            pass

    # ── Certificate form setters ──────────────────────────────────────────────

    @rx.event
    def set_cert_form_issue_date(self, value: str):
        self.cert_form_issue_date = value

    @rx.event
    def set_cert_form_conclusion(self, value: str):
        self.cert_form_conclusion = value

    @rx.event
    def set_cert_form_fitness_decision(self, value: str):
        self.cert_form_fitness_decision = value

    @rx.event
    def set_cert_form_restrictions(self, value: str):
        self.cert_form_restrictions = value

    @rx.event
    def open_certificate_dialog(self):
        from datetime import date

        self.cert_form_issue_date = date.today().isoformat()
        self.cert_form_conclusion = ""
        self.cert_form_fitness_decision = "FIT"
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
                    fitness_decision=self.cert_form_fitness_decision,
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
                from gws_care.patient.patient import Patient
                from gws_care.visit.campaign_visit_service import CampaignVisitService
                from gws_care.visit.visit import Visit

                CampaignVisitService.mark_terrain_done(self.visit.id)

                # Phase 5 — send on-site thank-you notification
                try:
                    from gws_care.notification.notification_service import NotificationService

                    visit_obj = Visit.get_by_id(self.visit.id)
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
                from gws_care.user.user import User
                from gws_care.visit.campaign_visit_service import CampaignVisitService

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
                from gws_care.user.user import User
                from gws_care.visit.campaign_visit_service import CampaignVisitService
                from gws_care.visit.visit_dto import ValidateDoctorClinicDTO

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
                from gws_care.user.user import User
                from gws_care.visit.campaign_visit_service import CampaignVisitService
                from gws_care.visit.visit_dto import ValidateDoctorCompanyDTO

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
            visit_id = self.router.page.params.get("visit_id_param", "")
            if not visit_id:
                self.visit = None
                return

            with await self.authenticate_user():
                from gws_care.exam.exam_result_service import ExamResultService
                from gws_care.exam.exam_service import ExamService
                from gws_care.visit.campaign_visit_service import CampaignVisitService
                from gws_care.workflow.campaign_visit_validation_workflow import (
                    CampaignVisitValidationStep,
                    CampaignVisitValidationWorkflow,
                )

                visit = CampaignVisitService.get_visit(visit_id)

                # Load validation audit rows from workflow table
                def _workflow_row(step: CampaignVisitValidationStep):
                    try:
                        return CampaignVisitValidationWorkflow.get(
                            (CampaignVisitValidationWorkflow.visit == visit.id)
                            & (CampaignVisitValidationWorkflow.step == step)
                        )
                    except CampaignVisitValidationWorkflow.DoesNotExist:
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

                lab_row = _workflow_row(CampaignVisitValidationStep.LAB_DONE)
                clinic_row = _workflow_row(CampaignVisitValidationStep.DOCTOR_CLINIC_VALIDATED)
                company_row = _workflow_row(CampaignVisitValidationStep.DOCTOR_COMPANY_VALIDATED)

                self.visit = VisitDetailDTO(
                    id=str(visit.id),
                    visit_number=visit.visit_number,
                    patient_name=visit.patient.get_full_name() if visit.patient_id else "",
                    patient_id=str(visit.patient_id) if visit.patient_id else "",
                    campaign_name=visit.campaign.name if visit.campaign_id else "",
                    campaign_id=str(visit.campaign_id) if visit.campaign_id else "",
                    campaign_visit_status=visit.campaign_visit_status.value,
                    status_label=visit.campaign_visit_status.get_label(),
                    lab_validated_by=_user_name(lab_row),
                    lab_validated_at=str(lab_row.validated_at) if lab_row else "",
                    doctor_clinic_validated_by=_user_name(clinic_row),
                    doctor_clinic_validated_at=str(clinic_row.validated_at) if clinic_row else "",
                    doctor_clinic_interpretation=visit.doctor_clinic_interpretation or "",
                    doctor_company_validated_by=_user_name(company_row),
                    doctor_company_validated_at=str(company_row.validated_at)
                    if company_row
                    else "",
                    doctor_company_interpretation=visit.doctor_company_interpretation or "",
                    doctor_company_message=visit.doctor_company_message or "",
                )
                # Pre-fill editable interpretation fields
                self.clinic_interpretation = visit.doctor_clinic_interpretation or ""
                self.company_interpretation = visit.doctor_company_interpretation or ""
                self.company_message = visit.doctor_company_message or ""

                # Load exam results from campaign exam types (new system: CampaignExam → ExamTypeRef).
                # Existing exam records are identified via reason_for_visit marker
                # "CAMP:{campaign_id}|REF:{ref_id}" (same convention as campaign_patient_exams page).
                try:
                    from gws_care.campaign.campaign_exam import CampaignExam
                    from gws_care.exam.exam import Exam

                    rows = []
                    if visit.campaign_id:
                        campaign_id_str = str(visit.campaign_id)
                        patient_id_str = str(visit.patient_id) if visit.patient_id else ""

                        campaign_exams = list(
                            CampaignExam.select()
                            .where(CampaignExam.campaign == campaign_id_str)
                            .order_by(CampaignExam.id)
                        )

                        # Index existing saved exams by ExamTypeRef id via marker
                        existing_map: dict = {}
                        if patient_id_str:
                            marker_prefix = f"CAMP:{campaign_id_str}|"
                            for ex in Exam.select().where(Exam.patient == patient_id_str):
                                rv = ex.reason_for_visit or ""
                                if rv.startswith(marker_prefix):
                                    try:
                                        ref_id = rv.split("|REF:")[1].split("|")[0]
                                        existing_map[ref_id] = ex
                                    except (IndexError, AttributeError):
                                        pass

                        for ce in campaign_exams:
                            ref = ce.exam_type_ref
                            ref_id = str(ref.id)
                            exam = existing_map.get(ref_id)

                            rows.append(
                                ExamResultRowDTO(
                                    exam_id=str(exam.id) if exam else "",
                                    exam_type_model_id=ref_id,
                                    exam_type_name=ref.name,
                                    exam_type_code=ref.get_category_label(),
                                    status=exam.status.value if exam else "",
                                    result_data={},
                                    primary_value="",
                                    edit_value="",
                                    appreciation="",
                                    appreciation_label="",
                                    appreciation_override=False,
                                )
                            )

                    self.exam_results = rows
                except Exception as ex:
                    import traceback

                    print(f"[VisitDetailState] Could not load exam results: {ex}")
                    traceback.print_exc()
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
                        cert_rows.append(
                            VisitCertificateRowDTO(
                                id=str(cert.id),
                                issue_date=str(cert.issue_date),
                                conclusion=cert.conclusion,
                                is_fit_for_work=cert.is_fit_for_work,
                                issued_by_name=issued_name,
                                restrictions=cert.restrictions or "",
                            )
                        )
                    self.certificates = cert_rows
                except Exception as ex:
                    print(f"[VisitDetailState] Could not load certificates: {ex}")
                    self.certificates = []

        except Exception as e:
            self.error_message = str(e)
            self.visit = None
        finally:
            self.is_loading = False
