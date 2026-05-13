"""DTOs for MedicalProgram."""

from datetime import date

from gws_core import BaseModelDTO, ModelDTO

from gws_care.medical_program.program_status import ProgramStatus


class MedicalProgramDTO(ModelDTO):
    """Full program record returned to callers."""

    program_number: str
    name: str
    account_id: str | None = None
    account_name: str | None = None
    start_date: date
    end_date: date
    status: ProgramStatus
    notes: str | None = None
    is_individual: bool = False


class ProgramRowDTO(BaseModelDTO):
    """Lightweight row for list views."""

    id: str
    program_number: str
    name: str
    account_name: str | None = None
    start_date: str   # ISO string
    end_date: str     # ISO string
    status: str
    status_label: str
    patient_count: int = 0
    exam_type_count: int = 0


class SaveProgramDTO(BaseModelDTO):
    """DTO for creating or updating a program."""

    name: str
    account_id: str
    start_date: str   # ISO date string YYYY-MM-DD
    end_date: str     # ISO date string YYYY-MM-DD
    notes: str | None = None
