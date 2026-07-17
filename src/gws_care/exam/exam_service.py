"""CRUD + domain service for Exam sessions."""

from datetime import datetime

from gws_core import BadRequestException, NotFoundException

from gws_care.exam.exam import Exam
from gws_care.exam.exam_dto import ExamRowDTO, InterpretExamDTO, SaveExamDTO, UpdateExamSectionsDTO
from gws_care.exam.exam_type import ExamStatus
from gws_care.patient.patient import Patient
from gws_care.user.user import User
from gws_care.workflow.exam_validation_step import ExamValidationStep
from gws_care.workflow.exam_validation_workflow import ExamValidationWorkflow


class ExamService:
    """Service for managing exam sessions."""

    @classmethod
    def get_exam(cls, exam_id: str) -> Exam:
        exam = Exam.get_or_none(Exam.id == exam_id)
        if exam is None:
            raise NotFoundException(f"Exam '{exam_id}' not found")
        return exam

    @classmethod
    def list_exams_for_patient(cls, patient_id: str) -> list[Exam]:
        """Return all exams for a patient, newest first."""
        return list(
            Exam.select()
            .where(Exam.patient == patient_id)
            .order_by(Exam.exam_date.desc())
        )

    @classmethod
    def to_row_dto(cls, exam: Exam) -> ExamRowDTO:
        label = exam.exam_type.get_label()
        ref_id = exam.exam_type_ref_id or ""
        if ref_id:
            try:
                from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                ref = ExamTypeRef.get_or_none(ExamTypeRef.id == ref_id)
                if ref:
                    label = ref.name
            except Exception:
                pass
        return ExamRowDTO(
            id=str(exam.id),
            exam_date=exam.exam_date.isoformat(),
            exam_type=exam.exam_type.value,
            exam_type_label=label,
            status=exam.status.value,
        )

    @classmethod
    def create_exam(cls, dto: SaveExamDTO) -> Exam:
        from gws_care.visit.visit import Visit
        from gws_care.visit.campaign_visit_status import CampaignVisitStatus
        from gws_care.visit.visit_type import VisitType

        patient = Patient.get_or_none(Patient.id == dto.patient_id)
        if patient is None:
            raise BadRequestException(f"Patient '{dto.patient_id}' not found")

        if dto.visit_id:
            visit = Visit.get_or_none(Visit.id == dto.visit_id)
            if visit is None:
                raise BadRequestException(f"Visit '{dto.visit_id}' not found")
        else:
            visit = Visit()
            visit.visit_type = VisitType.CONSULTATION
            visit.patient = patient
            visit.billing_account_id = dto.account_id
            visit.campaign_visit_status = CampaignVisitStatus.PENDING
            visit.save()

        exam = Exam()
        exam.patient = patient
        exam.visit = visit
        exam.billing_account_id = dto.account_id
        exam.exam_date = dto.exam_date
        exam.exam_type = dto.exam_type
        exam.exam_type_ref_id = dto.exam_type_ref_id
        exam.requested_param_ids = dto.requested_param_ids or []
        exam.status = ExamStatus.TODO
        exam.reason_for_visit = dto.reason_for_visit
        exam.medical_history = dto.medical_history
        exam.weight = dto.weight
        exam.height = dto.height
        exam.bmi = dto.bmi
        exam.blood_pressure = dto.blood_pressure
        exam.heart_rate = dto.heart_rate
        exam.temperature = dto.temperature
        exam.save()
        return exam

    @classmethod
    def update_sections(cls, exam_id: str, dto: UpdateExamSectionsDTO) -> Exam:
        """Update the medical sections of an exam."""
        exam = cls.get_exam(exam_id)
        exam.reason_for_visit = dto.reason_for_visit
        exam.medical_history = dto.medical_history
        exam.weight = dto.weight
        exam.height = dto.height
        exam.bmi = dto.bmi
        exam.blood_pressure = dto.blood_pressure
        exam.heart_rate = dto.heart_rate
        exam.temperature = dto.temperature
        exam.lab_results = dto.lab_results
        exam.save()
        return exam

    @classmethod
    def update_exam(cls, exam_id: str, dto: SaveExamDTO) -> Exam:
        exam = cls.get_exam(exam_id)
        exam.exam_date = dto.exam_date
        exam.exam_type = dto.exam_type
        exam.billing_account_id = dto.account_id
        exam.reason_for_visit = dto.reason_for_visit
        exam.medical_history = dto.medical_history
        exam.weight = dto.weight
        exam.height = dto.height
        exam.bmi = dto.bmi
        exam.blood_pressure = dto.blood_pressure
        exam.heart_rate = dto.heart_rate
        exam.temperature = dto.temperature
        exam.save()
        return exam

    @classmethod
    def update_reason_and_history(cls, exam_id: str, reason: str | None, history: str | None) -> Exam:
        exam = cls.get_exam(exam_id)
        exam.reason_for_visit = reason
        exam.medical_history = history
        exam.save()
        return exam

    @classmethod
    def update_physical(
        cls,
        exam_id: str,
        weight: float | None,
        height: float | None,
        bmi: float | None,
        blood_pressure: str | None,
        heart_rate: float | None,
        temperature: float | None,
    ) -> Exam:
        exam = cls.get_exam(exam_id)
        exam.weight = weight
        exam.height = height
        exam.bmi = bmi
        exam.blood_pressure = blood_pressure
        exam.heart_rate = heart_rate
        exam.temperature = temperature
        exam.save()
        return exam

    @classmethod
    def update_lab_results(cls, exam_id: str, lab_results: list[dict]) -> Exam:
        exam = cls.get_exam(exam_id)
        exam.lab_results = lab_results
        exam.save()
        return exam

    @classmethod
    def set_in_progress_results(cls, exam_id: str, user: User | None = None) -> Exam:
        """Advance exam from TODO → IN_PROGRESS_RESULTS (informations saved)."""
        exam = cls.get_exam(exam_id)
        exam.status = ExamStatus.IN_PROGRESS_RESULTS
        exam.save()
        record = ExamValidationWorkflow()
        record.exam = exam
        record.step = ExamValidationStep.IN_PROGRESS_RESULTS
        record.reached_by = user
        record.reached_at = datetime.utcnow()
        record.save()
        return exam

    @classmethod
    def set_in_progress_interpretation(cls, exam_id: str, user: User | None = None) -> Exam:
        """Advance exam to IN_PROGRESS_INTERPRETATION (results submitted for review)."""
        exam = cls.get_exam(exam_id)
        exam.status = ExamStatus.IN_PROGRESS_INTERPRETATION
        exam.save()
        record = ExamValidationWorkflow()
        record.exam = exam
        record.step = ExamValidationStep.IN_PROGRESS_INTERPRETATION
        record.reached_by = user
        record.reached_at = datetime.utcnow()
        record.save()
        return exam

    @classmethod
    def interpret_exam(cls, exam_id: str, dto: InterpretExamDTO, doctor: User) -> Exam:
        """Save doctor's interpretation and mark exam as DONE."""
        if not dto.interpretation or not dto.interpretation.strip():
            raise BadRequestException("Interpretation text is required")
        exam = cls.get_exam(exam_id)
        exam.interpretation = dto.interpretation.strip()
        exam.interpreted_by = doctor
        exam.status = ExamStatus.DONE
        exam.save()
        record = ExamValidationWorkflow()
        record.exam = exam
        record.step = ExamValidationStep.DONE
        record.reached_by = doctor
        record.reached_at = datetime.utcnow()
        record.save()
        return exam

    @classmethod
    def delete_exam(cls, exam_id: str) -> None:
        exam = cls.get_exam(exam_id)
        exam.delete_instance()

    # ── Phase 4 — Terrain / QR code methods ──────────────────────────────────

    @classmethod
    def mark_terrain_done(cls, exam_id: str) -> Exam:
        """Mark an exam as done on-site (OT checks off the exam)."""
        exam = cls.get_exam(exam_id)
        exam.is_done_on_site = True
        exam.save()
        return exam

    @classmethod

    @classmethod
    def list_exams_for_campaign_terrain(cls, program_id: str) -> list[Exam]:
        """Return all exams (via CampaignVisit) for a program for on-site view.

        Falls back to patient-level exams if no visit FK is present.
        """
        from gws_care.campaign.campaign_service import CampaignService
        from gws_care.visit.visit import Visit
        patients = CampaignService.get_patients(program_id)
        if not patients:
            return []
        patient_ids = [str(p.id) for p in patients]
        return list(
            Exam.select()
            .where(Exam.patient << patient_ids)
            .order_by(Exam.patient_id, Exam.exam_date)
        )
