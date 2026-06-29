"""Service layer for ExamTypeRef and ExamParameter (US-040, US-041)."""

from gws_care.exam_type_ref.exam_parameter import ExamParameter
from gws_care.exam_type_ref.exam_type_ref import ExamCategory, ExamTypeRef
from gws_care.exam_type_ref.exam_type_ref_dto import (
    ExamParameterDTO,
    ExamTypeRefDTO,
    ExamTypeRefRowDTO,
    SaveExamParameterDTO,
    SaveExamTypeRefDTO,
)


class ExamTypeRefService:
    """CRUD operations for the configurable exam type referential."""

    @classmethod
    def list_all(cls, active_only: bool = False) -> list[ExamTypeRefRowDTO]:
        query = ExamTypeRef.select()
        if active_only:
            query = query.where(ExamTypeRef.is_active == True)
        query = query.order_by(ExamTypeRef.category, ExamTypeRef.name)
        return [cls._to_row_dto(e) for e in query]

    @classmethod
    def get(cls, exam_type_ref_id: str) -> ExamTypeRefDTO:
        ref = ExamTypeRef.get_by_id_and_check(exam_type_ref_id)
        params = list(
            ExamParameter.select()
            .where(ExamParameter.exam_type_ref == exam_type_ref_id)
            .order_by(ExamParameter.display_order)
        )
        return ExamTypeRefDTO(
            id=str(ref.id),
            name=ref.name,
            category=ref.category,
            category_label=ref.get_category_label(),
            description=ref.description,
            is_active=ref.is_active,
            allows_attachment=ref.allows_attachment,
            requires_attachment=ref.requires_attachment,
            parameters=[cls._param_to_dto(p) for p in params],
        )

    @classmethod
    def create(cls, dto: SaveExamTypeRefDTO) -> ExamTypeRefDTO:
        ref = ExamTypeRef()
        ref.name = dto.name
        ref.category = dto.category
        ref.department = getattr(dto, "department", None) or None
        ref.description = dto.description
        ref.is_active = dto.is_active
        ref.allows_attachment = dto.allows_attachment
        ref.requires_attachment = dto.requires_attachment
        ref.required_sample_type = dto.required_sample_type or None
        ref.save()
        return cls.get(str(ref.id))

    @classmethod
    def update(cls, exam_type_ref_id: str, dto: SaveExamTypeRefDTO) -> ExamTypeRefDTO:
        ref = ExamTypeRef.get_by_id_and_check(exam_type_ref_id)
        ref.name = dto.name
        ref.category = dto.category
        ref.department = getattr(dto, "department", None) or None
        ref.description = dto.description
        ref.is_active = dto.is_active
        ref.allows_attachment = dto.allows_attachment
        ref.requires_attachment = dto.requires_attachment
        ref.required_sample_type = dto.required_sample_type or None
        ref.save()
        return cls.get(exam_type_ref_id)

    @classmethod
    def deactivate(cls, exam_type_ref_id: str, reason: str = None) -> None:
        ref = ExamTypeRef.get_by_id_and_check(exam_type_ref_id)
        ref.is_active = False
        if reason:
            ref.deactivation_reason = reason
        ref.save()

    @classmethod
    def reactivate(cls, exam_type_ref_id: str) -> None:
        ref = ExamTypeRef.get_by_id_and_check(exam_type_ref_id)
        ref.is_active = True
        ref.save()

    @classmethod
    def add_parameter(cls, exam_type_ref_id: str, dto: SaveExamParameterDTO) -> ExamParameterDTO:
        ref = ExamTypeRef.get_by_id_and_check(exam_type_ref_id)
        cls._validate_code_unique(exam_type_ref_id, dto.code, exclude_id=None)
        p = ExamParameter()
        p.exam_type_ref = ref
        p.name = dto.name
        p.value_type = dto.value_type
        p.unit = dto.unit
        p.ref_low = dto.ref_low
        p.ref_high = dto.ref_high
        p.critical_low = dto.critical_low
        p.critical_high = dto.critical_high
        p.is_required = dto.is_required
        p.display_order = dto.display_order
        p.code = dto.code or None
        p.is_computed = dto.is_computed
        p.formula = dto.formula or None
        p.target_gender = dto.target_gender or "ALL"
        p.ref_low_m = dto.ref_low_m
        p.ref_high_m = dto.ref_high_m
        p.critical_low_m = dto.critical_low_m
        p.critical_high_m = dto.critical_high_m
        p.ref_low_f = dto.ref_low_f
        p.ref_high_f = dto.ref_high_f
        p.critical_low_f = dto.critical_low_f
        p.critical_high_f = dto.critical_high_f
        p.save()
        return cls._param_to_dto(p)

    @classmethod
    def update_parameter(cls, parameter_id: str, dto: SaveExamParameterDTO) -> ExamParameterDTO:
        p = ExamParameter.get_by_id_and_check(parameter_id)
        cls._validate_code_unique(str(p.exam_type_ref_id), dto.code, exclude_id=parameter_id)
        p.name = dto.name
        p.value_type = dto.value_type
        p.unit = dto.unit
        p.ref_low = dto.ref_low
        p.ref_high = dto.ref_high
        p.critical_low = dto.critical_low
        p.critical_high = dto.critical_high
        p.is_required = dto.is_required
        p.display_order = dto.display_order
        p.code = dto.code or None
        p.is_computed = dto.is_computed
        p.formula = dto.formula or None
        p.target_gender = dto.target_gender or "ALL"
        p.ref_low_m = dto.ref_low_m
        p.ref_high_m = dto.ref_high_m
        p.critical_low_m = dto.critical_low_m
        p.critical_high_m = dto.critical_high_m
        p.ref_low_f = dto.ref_low_f
        p.ref_high_f = dto.ref_high_f
        p.critical_low_f = dto.critical_low_f
        p.critical_high_f = dto.critical_high_f
        p.save()
        return cls._param_to_dto(p)

    @classmethod
    def delete(cls, exam_type_ref_id: str) -> None:
        """Permanently delete an exam type and all its parameters."""
        ref = ExamTypeRef.get_by_id_and_check(exam_type_ref_id)
        ExamParameter.delete().where(ExamParameter.exam_type_ref == ref.id).execute()
        ref.delete_instance()

    @classmethod
    def deactivate_parameter(cls, parameter_id: str) -> None:
        """Archive (soft-delete) a parameter."""
        p = ExamParameter.get_by_id_and_check(parameter_id)
        p.is_active = False
        p.save()

    @classmethod
    def reactivate_parameter(cls, parameter_id: str) -> None:
        """Restore a previously archived parameter."""
        p = ExamParameter.get_by_id_and_check(parameter_id)
        p.is_active = True
        p.save()

    @classmethod
    def delete_parameter(cls, parameter_id: str) -> None:
        p = ExamParameter.get_by_id_and_check(parameter_id)
        p.delete_instance()

    @classmethod
    def _to_row_dto(cls, ref: ExamTypeRef) -> ExamTypeRefRowDTO:
        param_count = ExamParameter.select().where(ExamParameter.exam_type_ref == ref.id).count()
        return ExamTypeRefRowDTO(
            id=str(ref.id),
            name=ref.name,
            category=ref.category,
            category_label=ref.get_category_label(),
            department=getattr(ref, "department", None) or None,
            is_active=ref.is_active,
            allows_attachment=ref.allows_attachment,
            requires_attachment=ref.requires_attachment,
            parameter_count=param_count,
        )

    @classmethod
    def _param_to_dto(cls, p: ExamParameter) -> ExamParameterDTO:
        return ExamParameterDTO(
            id=str(p.id),
            exam_type_ref_id=str(p.exam_type_ref_id),
            name=p.name,
            value_type=p.value_type,
            unit=p.unit,
            ref_low=p.ref_low,
            ref_high=p.ref_high,
            critical_low=p.critical_low,
            critical_high=p.critical_high,
            is_required=p.is_required,
            is_active=p.is_active,
            display_order=p.display_order,
            code=p.code or None,
            is_computed=bool(p.is_computed),
            formula=p.formula or None,
            target_gender=p.target_gender or "ALL",
            ref_low_m=p.ref_low_m,
            ref_high_m=p.ref_high_m,
            critical_low_m=p.critical_low_m,
            critical_high_m=p.critical_high_m,
            ref_low_f=p.ref_low_f,
            ref_high_f=p.ref_high_f,
            critical_low_f=p.critical_low_f,
            critical_high_f=p.critical_high_f,
        )

    @classmethod
    def _validate_code_unique(
        cls, exam_type_ref_id: str, code: str | None, exclude_id: str | None
    ) -> None:
        """Raise ValueError if code is already used by another parameter in the same exam type."""
        if not code:
            return
        query = (
            ExamParameter.select()
            .where(
                (ExamParameter.exam_type_ref == exam_type_ref_id)
                & (ExamParameter.code == code)
            )
        )
        if exclude_id:
            query = query.where(ExamParameter.id != exclude_id)
        if query.exists():
            raise ValueError(
                f"Le code '{code}' est déjà utilisé par un autre paramètre de cet examen."
            )
