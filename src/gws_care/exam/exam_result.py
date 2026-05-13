"""ExamResult model — stores typed result data for one exam."""

from gws_core import EnumField
from gws_core.core.model.db_field import JSONField
from peewee import BooleanField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam.appreciation import Appreciation
from gws_care.exam.exam import Exam
from gws_care.exam.exam_result_dto import ExamResultDTO


class ExamResult(ModelWithUser):
    """Stores the result data for a single exam session.

    `result_data` is a JSON dict whose shape depends on the exam type.
    `image_paths` is a JSON list of file path strings (for image-based exams).
    One exam should have at most one ExamResult row.

    Phase 3 additions:
    - `appreciation` — current appreciation level (auto-calculated or overridden)
    - `calculated_appreciation` — the original auto-calculated value (preserved after manual override)
    - `appreciation_override` — True when a doctor manually changed the appreciation
    """

    exam: Exam = ForeignKeyField(Exam, null=False, backref="results", on_delete="CASCADE")
    result_data: dict = JSONField(null=True)
    image_paths: list = JSONField(null=True)
    # Phase 3 — appreciation
    appreciation: Appreciation = EnumField(choices=Appreciation, null=True)
    calculated_appreciation: Appreciation = EnumField(choices=Appreciation, null=True)
    appreciation_override: bool = BooleanField(default=False, null=False)

    def to_dto(self) -> ExamResultDTO:
        return ExamResultDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            exam_id=str(self.exam_id),
            result_data=self.result_data or {},
            image_paths=self.image_paths or [],
            appreciation=self.appreciation,
            calculated_appreciation=self.calculated_appreciation,
            appreciation_override=self.appreciation_override,
        )

    class Meta:
        table_name = "gws_care_exam_result"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
