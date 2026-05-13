"""CRUD + domain service for Exam sessions."""

from gws_core import BadRequestException, NotFoundException

from gws_care.exam.exam import Exam
from gws_care.exam.exam_dto import ExamRowDTO, InterpretExamDTO, SaveExamDTO, UpdateExamSectionsDTO
from gws_care.exam.exam_type import ExamStatus
from gws_care.patient.patient import Patient
from gws_care.user.user import User


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
        return ExamRowDTO(
            id=str(exam.id),
            exam_date=exam.exam_date.isoformat(),
            exam_type=exam.exam_type.value,
            exam_type_label=exam.exam_type.get_label(),
            status=exam.status.value,
        )

    @classmethod
    def create_exam(cls, dto: SaveExamDTO) -> Exam:
        patient = Patient.get_or_none(Patient.id == dto.patient_id)
        if patient is None:
            raise BadRequestException(f"Patient '{dto.patient_id}' not found")

        exam = Exam()
        exam.patient = patient
        exam.billing_account_id = dto.account_id
        exam.exam_date = dto.exam_date
        exam.exam_type = dto.exam_type
        exam.status = ExamStatus.DRAFT
        exam.reason_for_visit = dto.reason_for_visit
        exam.medical_history = dto.medical_history
        exam.weight = dto.weight
        exam.height = dto.height
        exam.bmi = dto.bmi
        exam.blood_pressure = dto.blood_pressure
        exam.heart_rate = dto.heart_rate
        exam.temperature = dto.temperature
        exam.conclusion = dto.conclusion
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
        exam.conclusion = dto.conclusion
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
        exam.conclusion = dto.conclusion
        exam.save()
        return exam

    @classmethod
    def set_pending(cls, exam_id: str) -> Exam:
        """Mark exam as PENDING (results entered, awaiting interpretation)."""
        exam = cls.get_exam(exam_id)
        exam.status = ExamStatus.PENDING
        exam.save()
        return exam

    @classmethod
    def interpret_exam(cls, exam_id: str, dto: InterpretExamDTO, doctor: User) -> Exam:
        """Save doctor's interpretation and mark exam as INTERPRETED."""
        if not dto.interpretation or not dto.interpretation.strip():
            raise BadRequestException("Interpretation text is required")
        exam = cls.get_exam(exam_id)
        exam.interpretation = dto.interpretation.strip()
        exam.interpreted_by = doctor
        exam.status = ExamStatus.INTERPRETED
        exam.save()
        return exam

    @classmethod
    def delete_exam(cls, exam_id: str) -> None:
        exam = cls.get_exam(exam_id)
        exam.delete_instance()

    # ── Phase 4 — Terrain / QR code methods ──────────────────────────────────

    @classmethod
    def assign_tube_qr(cls, exam_id: str, tube_qr_code: str) -> Exam:
        """Assign a tube QR code to an exam."""
        exam = cls.get_exam(exam_id)
        exam.tube_qr_code = tube_qr_code
        exam.save()
        return exam

    @classmethod
    def mark_terrain_done(cls, exam_id: str) -> Exam:
        """Mark an exam as done on-site (OT checks off the exam)."""
        exam = cls.get_exam(exam_id)
        exam.is_done_on_site = True
        exam.save()
        return exam

    @classmethod
    def find_by_tube_qr(cls, qr_code: str) -> dict | None:
        """Lookup an exam by its tube QR code.

        The tube QR code format is TUBE-<patient_number>-<exam_type_code>.
        Returns a dict with keys: patient, visit, exams_to_do (list of Exam).
        Returns None if not found.
        """
        from gws_care.patient.patient import Patient as PatientModel
        from gws_care.visit.visit import Visit

        exam = Exam.get_or_none(Exam.tube_qr_code == qr_code)
        if exam is None:
            return None

        patient = PatientModel.get_or_none(PatientModel.id == exam.patient_id)
        if patient is None:
            return None

        # All exams for the same patient (regardless of visit — standalone or visit-linked)
        all_exams_for_patient = list(
            Exam.select()
            .where(Exam.patient == exam.patient_id)
            .order_by(Exam.exam_date.desc())
        )

        return {
            "patient": patient,
            "visit": None,  # visit FK not yet on Exam; extension point
            "exams_to_do": [e for e in all_exams_for_patient if not e.is_done_on_site],
        }

    @classmethod
    def list_exams_for_campaign_terrain(cls, program_id: str) -> list[Exam]:
        """Return all exams (via Visit) for a program for on-site view.

        Falls back to patient-level exams if no visit FK is present.
        """
        from gws_care.medical_program.medical_program_service import MedicalProgramService
        from gws_care.visit.visit import Visit
        patients = MedicalProgramService.get_patients(program_id)
        if not patients:
            return []
        patient_ids = [str(p.id) for p in patients]
        return list(
            Exam.select()
            .where(Exam.patient << patient_ids)
            .order_by(Exam.patient_id, Exam.exam_date)
        )
