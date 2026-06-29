"""Exam type referential management page (US-040, US-041)."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class ExamTypeRowVM(BaseModel):
    id: str
    name: str
    category: str
    category_label: str
    department: str = ""
    is_active: bool
    allows_attachment: bool
    requires_attachment: bool
    required_sample_type: str = ""
    parameter_count: int


class ExamParamVM(BaseModel):
    id: str
    name: str
    value_type: str
    unit: str
    ref_low: str = ""
    ref_high: str = ""
    critical_low: str = ""
    critical_high: str = ""
    is_required: bool
    is_active: bool = True
    display_order: int
    code: str = ""
    is_computed: bool = False
    formula: str = ""
    target_gender: str = "ALL"
    ref_low_m: str = ""
    ref_high_m: str = ""
    critical_low_m: str = ""
    critical_high_m: str = ""
    ref_low_f: str = ""
    ref_high_f: str = ""
    critical_low_f: str = ""
    critical_high_f: str = ""


class ExamTypeFormVM(BaseModel):
    name: str = ""
    category: str = ""          # vide — l'utilisateur doit choisir
    department: str = ""        # département (ex: Radiologie, Cytologie…)
    description: str = ""
    is_active: bool = True
    allows_attachment: bool = False
    requires_attachment: bool = False
    required_sample_type: str = ""  # type de prélèvement associé (ex: "Sang total (EDTA)")


class ExamParamFormVM(BaseModel):
    name: str = ""
    value_type: str = ""        # vide — l'utilisateur doit choisir
    unit: str = ""
    ref_low: str = ""
    ref_high: str = ""
    critical_low: str = ""
    critical_high: str = ""
    is_required: bool = False
    display_order: int = 0
    code: str = ""
    is_computed: bool = False
    formula: str = ""
    target_gender: str = "ALL"
    ref_low_m: str = ""
    ref_high_m: str = ""
    critical_low_m: str = ""
    critical_high_m: str = ""
    ref_low_f: str = ""
    ref_high_f: str = ""
    critical_low_f: str = ""
    critical_high_f: str = ""


class ExamTypesState(ReflexMainState):
    exam_types: list[ExamTypeRowVM] = []
    selected_type_id: str = ""
    selected_type_name: str = ""
    selected_type_category: str = ""
    selected_type_department: str = ""
    selected_type_description: str = ""
    selected_type_active: bool = True
    selected_type_allows_attachment: bool = False
    selected_type_requires_attachment: bool = False
    parameters: list[ExamParamVM] = []
    is_loading: bool = False
    error: str = ""
    success: str = ""

    # Navigation : "list" | "detail"
    view: str = "list"

    # Catégories existantes (pour autocomplete — libres, saisies par l'utilisateur)
    existing_categories: list[str] = []
    # Départements existants (pour autocomplete)
    existing_departments: list[str] = []

    # Type form dialog
    type_dialog_open: bool = False
    is_editing_type: bool = False
    type_form: ExamTypeFormVM = ExamTypeFormVM()
    type_form_error: str = ""
    is_saving_type: bool = False

    # Param form dialog
    param_dialog_open: bool = False
    is_editing_param: bool = False
    edit_param_id: str = ""
    param_form: ExamParamFormVM = ExamParamFormVM()
    param_form_error: str = ""
    is_saving_param: bool = False
    available_param_codes: list[str] = []  # codes of sibling params (for formula references)

    # Confirm archivage — paramètre
    confirm_deactivate_param_open: bool = False
    confirm_deactivate_param_id: str = ""
    confirm_deactivate_param_name: str = ""
    confirm_deactivate_param_comment: str = ""

    # Confirm réactivation — paramètre
    confirm_reactivate_param_open: bool = False
    confirm_reactivate_param_id: str = ""
    confirm_reactivate_param_name: str = ""

    # Confirm suppression — paramètre
    confirm_delete_param_open: bool = False
    confirm_delete_param_id: str = ""
    confirm_delete_param_comment: str = ""

    # Confirm désactivation — type d'examen
    confirm_deactivate_type_open: bool = False
    confirm_deactivate_type_id: str = ""
    confirm_deactivate_type_name: str = ""
    confirm_deactivate_type_comment: str = ""

    # Confirm réactivation — type d'examen
    confirm_reactivate_type_open: bool = False
    confirm_reactivate_type_id: str = ""
    confirm_reactivate_type_name: str = ""

    # Confirm suppression totale — type d'examen
    confirm_delete_type_open: bool = False
    confirm_delete_type_id: str = ""
    confirm_delete_type_name: str = ""
    confirm_delete_type_comment: str = ""

    @rx.event
    async def on_load(self):
        await self._load_types()

    @rx.event
    async def go_to_detail(self, type_id: str):
        """Ouvre la vue détail d'un type d'examen avec ses paramètres."""
        self.view = "detail"
        # Trouver le type dans la liste existante
        found = next((t for t in self.exam_types if t.id == type_id), None)
        if found:
            self.selected_type_id = found.id
            self.selected_type_name = found.name
            self.selected_type_category = found.category_label
            self.selected_type_department = found.department
            self.selected_type_description = ""
            self.selected_type_active = found.is_active
            self.selected_type_allows_attachment = found.allows_attachment
            self.selected_type_requires_attachment = found.requires_attachment
        else:
            self.selected_type_id = type_id
        await self._load_parameters(type_id)

    @rx.event
    def back_to_list(self):
        """Retour à la liste des types d'examens."""
        self.view = "list"
        self.selected_type_id = ""
        self.selected_type_name = ""
        self.selected_type_department = ""
        self.selected_type_category = ""
        self.parameters = []
        self.error = ""
        self.success = ""

    @rx.event
    async def select_type(self, type_id: str, type_name: str):
        """Compatibilité — redirige vers go_to_detail."""
        await self.go_to_detail(type_id)

    # Type dialog
    @rx.event
    def open_create_type_dialog(self):
        self.type_form = ExamTypeFormVM()
        self.is_editing_type = False
        self.type_form_error = ""
        self.type_dialog_open = True

    @rx.event
    def close_type_dialog(self):
        self.type_dialog_open = False

    @rx.event
    def set_type_name(self, v: str):
        self.type_form = ExamTypeFormVM(**{**self.type_form.dict(), "name": v})

    @rx.event
    def set_type_category(self, v: str):
        self.type_form = ExamTypeFormVM(**{**self.type_form.dict(), "category": v})

    @rx.event
    def set_type_description(self, v: str):
        self.type_form = ExamTypeFormVM(**{**self.type_form.dict(), "description": v})

    @rx.event
    def set_type_active(self, v: bool):
        self.type_form = ExamTypeFormVM(**{**self.type_form.dict(), "is_active": v})

    @rx.event
    def set_type_allows_attachment(self, v: bool):
        self.type_form = ExamTypeFormVM(**{**self.type_form.dict(), "allows_attachment": v})

    @rx.event
    def set_type_requires_attachment(self, v: bool):
        self.type_form = ExamTypeFormVM(**{**self.type_form.dict(), "requires_attachment": v})

    @rx.event
    def set_type_department(self, v: str):
        self.type_form = ExamTypeFormVM(**{**self.type_form.dict(), "department": v})

    @rx.event
    def set_type_required_sample_type(self, v: str):
        self.type_form = ExamTypeFormVM(**{**self.type_form.dict(), "required_sample_type": v if v != "NONE" else ""})

    @rx.event
    async def save_type(self):
        if not self.type_form.name.strip():
            self.type_form_error = "Le nom est obligatoire."
            return
        if not self.type_form.category:
            self.type_form_error = "La catégorie est obligatoire."
            return
        self.is_saving_type = True
        self.type_form_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_dto import SaveExamTypeRefDTO
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                dto = SaveExamTypeRefDTO(
                    name=self.type_form.name.strip(),
                    category=self.type_form.category,
                    department=self.type_form.department or None,
                    description=self.type_form.description or None,
                    is_active=self.type_form.is_active,
                    allows_attachment=self.type_form.allows_attachment,
                    requires_attachment=self.type_form.requires_attachment,
                    required_sample_type=self.type_form.required_sample_type or None,
                )
                ExamTypeRefService.create(dto)
            self.type_dialog_open = False
            self.success = "Type d'examen créé."
            await self._load_types()
        except Exception as e:
            self.type_form_error = str(e)
        finally:
            self.is_saving_type = False

    @rx.event
    async def deactivate_type(self, type_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                ExamTypeRefService.deactivate(type_id)
            self.success = "Type d'examen désactivé."
            await self._load_types()
        except Exception as e:
            self.error = str(e)

    # Param dialog
    @rx.event
    def open_create_param_dialog(self):
        self.param_form = ExamParamFormVM()
        self.is_editing_param = False
        self.edit_param_id = ""
        self.param_form_error = ""
        self.available_param_codes = [p.code for p in self.parameters if p.code and p.is_active]
        self.param_dialog_open = True

    @rx.event
    def close_param_dialog(self):
        self.param_dialog_open = False

    @rx.event
    def open_edit_param_dialog(self, param_id: str):
        found = next((p for p in self.parameters if p.id == param_id), None)
        if not found:
            return
        self.param_form = ExamParamFormVM(
            name=found.name,
            value_type=found.value_type,
            unit=found.unit,
            ref_low=found.ref_low,
            ref_high=found.ref_high,
            critical_low=found.critical_low,
            critical_high=found.critical_high,
            is_required=found.is_required,
            display_order=found.display_order,
            code=found.code,
            is_computed=found.is_computed,
            formula=found.formula,
            target_gender=found.target_gender,
            ref_low_m=found.ref_low_m,
            ref_high_m=found.ref_high_m,
            critical_low_m=found.critical_low_m,
            critical_high_m=found.critical_high_m,
            ref_low_f=found.ref_low_f,
            ref_high_f=found.ref_high_f,
            critical_low_f=found.critical_low_f,
            critical_high_f=found.critical_high_f,
        )
        self.is_editing_param = True
        self.edit_param_id = param_id
        self.param_form_error = ""
        # Exclude the param being edited from available codes (it can't reference itself)
        self.available_param_codes = [
            p.code for p in self.parameters
            if p.code and p.is_active and p.id != param_id
        ]
        self.param_dialog_open = True

    @rx.event
    def set_param_name(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "name": v})

    @rx.event
    def set_param_value_type(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "value_type": v})

    @rx.event
    def set_param_unit(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "unit": v})

    @rx.event
    def set_param_ref_low(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "ref_low": v})

    @rx.event
    def set_param_ref_high(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "ref_high": v})

    @rx.event
    def set_param_critical_low(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "critical_low": v})

    @rx.event
    def set_param_critical_high(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "critical_high": v})

    @rx.event
    def set_param_required(self, v: bool):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "is_required": v})

    @rx.event
    def set_param_code(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "code": v.strip().lower()})

    @rx.event
    def set_param_is_computed(self, v: bool):
        updates = {"is_computed": v}
        if v:
            updates["value_type"] = "NUMERIC"
        else:
            updates["formula"] = ""
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), **updates})

    @rx.event
    def set_param_target_gender(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "target_gender": v})

    @rx.event
    def set_param_ref_low_m(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "ref_low_m": v})

    @rx.event
    def set_param_ref_high_m(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "ref_high_m": v})

    @rx.event
    def set_param_critical_low_m(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "critical_low_m": v})

    @rx.event
    def set_param_critical_high_m(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "critical_high_m": v})

    @rx.event
    def set_param_ref_low_f(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "ref_low_f": v})

    @rx.event
    def set_param_ref_high_f(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "ref_high_f": v})

    @rx.event
    def set_param_critical_low_f(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "critical_low_f": v})

    @rx.event
    def set_param_critical_high_f(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "critical_high_f": v})

    @rx.event
    def set_param_formula(self, v: str):
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "formula": v})

    @rx.event
    def append_code_to_formula(self, code: str):
        current = self.param_form.formula
        if not current.strip():
            new_formula = code
        elif current.rstrip()[-1] in ("+", "-", "*", "/", "("):
            new_formula = current.rstrip() + " " + code
        else:
            new_formula = current.rstrip() + " " + code
        self.param_form = ExamParamFormVM(**{**self.param_form.dict(), "formula": new_formula})

    @rx.event
    async def save_param(self):
        if not self.param_form.name.strip():
            self.param_form_error = "Le nom est obligatoire."
            return
        if not self.param_form.value_type:
            self.param_form_error = "Le type de valeur est obligatoire."
            return
        if not self.selected_type_id:
            self.param_form_error = "Aucun type d'examen sélectionné."
            return
        if self.param_form.is_computed and self.param_form.value_type != "NUMERIC":
            self.param_form_error = "Un paramètre calculé doit être de type Numérique."
            return
        if self.param_form.is_computed:
            if not self.param_form.formula.strip():
                self.param_form_error = "La formule est obligatoire pour un paramètre calculé."
                return
            from gws_care.exam_type_ref.exam_formula_engine import ExamFormulaEngine
            err = ExamFormulaEngine.validate(
                self.param_form.formula, self.available_param_codes
            )
            if err:
                self.param_form_error = err
                return
        self.is_saving_param = True
        self.param_form_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_dto import SaveExamParameterDTO
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService

                def _parse_float(s: str) -> float | None:
                    try:
                        return float(s) if s.strip() else None
                    except ValueError:
                        return None

                dto = SaveExamParameterDTO(
                    name=self.param_form.name.strip(),
                    value_type=self.param_form.value_type,
                    unit=self.param_form.unit or None,
                    ref_low=_parse_float(self.param_form.ref_low),
                    ref_high=_parse_float(self.param_form.ref_high),
                    critical_low=_parse_float(self.param_form.critical_low),
                    critical_high=_parse_float(self.param_form.critical_high),
                    is_required=self.param_form.is_required,
                    display_order=self.param_form.display_order,
                    code=self.param_form.code.strip().lower() or None,
                    is_computed=self.param_form.is_computed,
                    formula=self.param_form.formula.strip() or None,
                    target_gender=self.param_form.target_gender or "ALL",
                    ref_low_m=_parse_float(self.param_form.ref_low_m),
                    ref_high_m=_parse_float(self.param_form.ref_high_m),
                    critical_low_m=_parse_float(self.param_form.critical_low_m),
                    critical_high_m=_parse_float(self.param_form.critical_high_m),
                    ref_low_f=_parse_float(self.param_form.ref_low_f),
                    ref_high_f=_parse_float(self.param_form.ref_high_f),
                    critical_low_f=_parse_float(self.param_form.critical_low_f),
                    critical_high_f=_parse_float(self.param_form.critical_high_f),
                )
                if self.is_editing_param:
                    ExamTypeRefService.update_parameter(self.edit_param_id, dto)
                else:
                    ExamTypeRefService.add_parameter(self.selected_type_id, dto)
            self.param_dialog_open = False
            self.success = "Paramètre modifié." if self.is_editing_param else "Paramètre ajouté."
            self.is_editing_param = False
            self.edit_param_id = ""
            await self._load_parameters(self.selected_type_id)
        except Exception as e:
            self.param_form_error = str(e)
        finally:
            self.is_saving_param = False

    @rx.event
    async def delete_param(self, param_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                ExamTypeRefService.delete_parameter(param_id)
            await self._load_parameters(self.selected_type_id)
        except Exception as e:
            self.error = str(e)

    # ── Confirm archivage paramètre ───────────────────────────────────────
    @rx.event
    def open_confirm_deactivate_param(self, param_id: str, param_name: str):
        self.confirm_deactivate_param_id = param_id
        self.confirm_deactivate_param_name = param_name
        self.confirm_deactivate_param_comment = ""
        self.confirm_deactivate_param_open = True

    @rx.event
    def set_deactivate_param_comment(self, v: str):
        self.confirm_deactivate_param_comment = v

    @rx.event
    def dismiss_confirm_deactivate_param(self):
        self.confirm_deactivate_param_open = False
        self.confirm_deactivate_param_id = ""
        self.confirm_deactivate_param_name = ""
        self.confirm_deactivate_param_comment = ""

    @rx.event
    async def confirmed_deactivate_param(self):
        if not self.confirm_deactivate_param_comment.strip():
            return
        param_id = self.confirm_deactivate_param_id
        self.confirm_deactivate_param_open = False
        self.confirm_deactivate_param_id = ""
        self.confirm_deactivate_param_name = ""
        self.confirm_deactivate_param_comment = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                ExamTypeRefService.deactivate_parameter(param_id)
            self.success = "Paramètre archivé."
            await self._load_parameters(self.selected_type_id)
        except Exception as e:
            self.error = str(e)

    # ── Confirm réactivation paramètre ────────────────────────────────────
    @rx.event
    def open_confirm_reactivate_param(self, param_id: str, param_name: str):
        self.confirm_reactivate_param_id = param_id
        self.confirm_reactivate_param_name = param_name
        self.confirm_reactivate_param_open = True

    @rx.event
    def dismiss_confirm_reactivate_param(self):
        self.confirm_reactivate_param_open = False
        self.confirm_reactivate_param_id = ""
        self.confirm_reactivate_param_name = ""

    @rx.event
    async def confirmed_reactivate_param(self):
        param_id = self.confirm_reactivate_param_id
        self.confirm_reactivate_param_open = False
        self.confirm_reactivate_param_id = ""
        self.confirm_reactivate_param_name = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                ExamTypeRefService.reactivate_parameter(param_id)
            self.success = "Paramètre réactivé."
            await self._load_parameters(self.selected_type_id)
        except Exception as e:
            self.error = str(e)

    # ── Confirm suppression paramètre ─────────────────────────────────────
    @rx.event
    def open_confirm_delete_param(self, param_id: str):
        self.confirm_delete_param_id = param_id
        self.confirm_delete_param_comment = ""
        self.confirm_delete_param_open = True

    @rx.event
    def set_delete_param_comment(self, v: str):
        self.confirm_delete_param_comment = v

    @rx.event
    def dismiss_confirm_delete_param(self):
        self.confirm_delete_param_open = False
        self.confirm_delete_param_id = ""
        self.confirm_delete_param_comment = ""

    @rx.event
    async def confirmed_delete_param(self):
        if not self.confirm_delete_param_comment.strip():
            return
        param_id = self.confirm_delete_param_id
        self.confirm_delete_param_open = False
        self.confirm_delete_param_id = ""
        self.confirm_delete_param_comment = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                ExamTypeRefService.delete_parameter(param_id)
            await self._load_parameters(self.selected_type_id)
        except Exception as e:
            self.error = str(e)

    # ── Confirm suppression totale type d'examen ────────────────────────
    @rx.event
    def open_confirm_delete_type(self, type_id: str, type_name: str):
        self.confirm_delete_type_id = type_id
        self.confirm_delete_type_name = type_name
        self.confirm_delete_type_comment = ""
        self.confirm_delete_type_open = True

    @rx.event
    def set_delete_type_comment(self, v: str):
        self.confirm_delete_type_comment = v

    @rx.event
    def dismiss_confirm_delete_type(self):
        self.confirm_delete_type_open = False
        self.confirm_delete_type_id = ""
        self.confirm_delete_type_name = ""
        self.confirm_delete_type_comment = ""

    @rx.event
    async def confirmed_delete_type(self):
        if not self.confirm_delete_type_comment.strip():
            return
        type_id = self.confirm_delete_type_id
        self.confirm_delete_type_open = False
        self.confirm_delete_type_id = ""
        self.confirm_delete_type_name = ""
        self.confirm_delete_type_comment = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                ExamTypeRefService.delete(type_id)
            self.success = "Type d'examen supprimé définitivement."
            await self._load_types()
        except Exception as e:
            self.error = str(e)

    # ── Confirm désactivation type d'examen ───────────────────────────────
    @rx.event
    def open_confirm_deactivate_type(self, type_id: str, type_name: str):
        self.confirm_deactivate_type_id = type_id
        self.confirm_deactivate_type_name = type_name
        self.confirm_deactivate_type_comment = ""
        self.confirm_deactivate_type_open = True

    @rx.event
    def set_deactivate_type_comment(self, v: str):
        self.confirm_deactivate_type_comment = v

    @rx.event
    def dismiss_confirm_deactivate_type(self):
        self.confirm_deactivate_type_open = False
        self.confirm_deactivate_type_id = ""
        self.confirm_deactivate_type_name = ""
        self.confirm_deactivate_type_comment = ""

    @rx.event
    async def confirmed_deactivate_type(self):
        if not self.confirm_deactivate_type_comment.strip():
            return
        type_id = self.confirm_deactivate_type_id
        comment = self.confirm_deactivate_type_comment
        self.confirm_deactivate_type_open = False
        self.confirm_deactivate_type_id = ""
        self.confirm_deactivate_type_name = ""
        self.confirm_deactivate_type_comment = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                ExamTypeRefService.deactivate(type_id, reason=comment)
            self.success = "Type d'examen archivé."
            await self._load_types()
        except Exception as e:
            self.error = str(e)

    # ── Confirm réactivation type d'examen ──────────────────────────────────────
    @rx.event
    def open_confirm_reactivate_type(self, type_id: str, type_name: str):
        self.confirm_reactivate_type_id = type_id
        self.confirm_reactivate_type_name = type_name
        self.confirm_reactivate_type_open = True

    @rx.event
    def dismiss_confirm_reactivate_type(self):
        self.confirm_reactivate_type_open = False
        self.confirm_reactivate_type_id = ""
        self.confirm_reactivate_type_name = ""

    @rx.event
    async def confirmed_reactivate_type(self):
        type_id = self.confirm_reactivate_type_id
        self.confirm_reactivate_type_open = False
        self.confirm_reactivate_type_id = ""
        self.confirm_reactivate_type_name = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                ExamTypeRefService.reactivate(type_id)
            self.success = "Type d'examen réactivé."
            await self._load_types()
        except Exception as e:
            self.error = str(e)

    @rx.event
    def dismiss_messages(self):
        self.error = ""
        self.success = ""

    async def _load_types(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                rows = ExamTypeRefService.list_all()
                self.exam_types = [
                    ExamTypeRowVM(
                        id=r.id, name=r.name, category=r.category,
                        category_label=r.category_label,
                        department=r.department or "",
                        is_active=r.is_active,
                        allows_attachment=r.allows_attachment,
                        requires_attachment=r.requires_attachment,
                        parameter_count=r.parameter_count,
                    )
                    for r in rows
                ]
                # Catégories uniques déjà définies (pour l'autocomplete) — valeur brute
                seen = []
                for r in rows:
                    if r.category and r.category not in seen:
                        seen.append(r.category)
                self.existing_categories = seen
                # Départements uniques (pour l'autocomplete)
                seen_depts = []
                for r in rows:
                    if r.department and r.department not in seen_depts:
                        seen_depts.append(r.department)
                self.existing_departments = seen_depts
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading = False

    async def _load_parameters(self, type_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                detail = ExamTypeRefService.get(type_id)
                def _f(v):
                    return str(v) if v is not None else ""

                self.parameters = [
                    ExamParamVM(
                        id=p.id, name=p.name, value_type=p.value_type,
                        unit=p.unit or "",
                        ref_low=_f(p.ref_low),
                        ref_high=_f(p.ref_high),
                        critical_low=_f(p.critical_low),
                        critical_high=_f(p.critical_high),
                        is_required=p.is_required, is_active=p.is_active,
                        display_order=p.display_order,
                        code=p.code or "",
                        is_computed=p.is_computed,
                        formula=p.formula or "",
                        target_gender=p.target_gender or "ALL",
                        ref_low_m=_f(p.ref_low_m),
                        ref_high_m=_f(p.ref_high_m),
                        critical_low_m=_f(p.critical_low_m),
                        critical_high_m=_f(p.critical_high_m),
                        ref_low_f=_f(p.ref_low_f),
                        ref_high_f=_f(p.ref_high_f),
                        critical_low_f=_f(p.critical_low_f),
                        critical_high_f=_f(p.critical_high_f),
                    )
                    for p in detail.parameters
                ]
        except Exception as e:
            self.error = str(e)
