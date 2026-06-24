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
    display_order: int


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


class ExamTypesState(ReflexMainState):
    exam_types: list[ExamTypeRowVM] = []
    selected_type_id: str = ""
    selected_type_name: str = ""
    selected_type_category: str = ""
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

    # Confirm suppression — paramètre
    confirm_delete_param_open: bool = False
    confirm_delete_param_id: str = ""

    # Confirm désactivation — type d'examen
    confirm_deactivate_type_open: bool = False
    confirm_deactivate_type_id: str = ""
    confirm_deactivate_type_name: str = ""

    # Confirm réactivation — type d'examen
    confirm_reactivate_type_open: bool = False
    confirm_reactivate_type_id: str = ""
    confirm_reactivate_type_name: str = ""

    # Confirm suppression totale — type d'examen
    confirm_delete_type_open: bool = False
    confirm_delete_type_id: str = ""
    confirm_delete_type_name: str = ""

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
        )
        self.is_editing_param = True
        self.edit_param_id = param_id
        self.param_form_error = ""
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

    # ── Confirm suppression paramètre ─────────────────────────────────────
    @rx.event
    def open_confirm_delete_param(self, param_id: str):
        self.confirm_delete_param_id = param_id
        self.confirm_delete_param_open = True

    @rx.event
    def dismiss_confirm_delete_param(self):
        self.confirm_delete_param_open = False
        self.confirm_delete_param_id = ""

    @rx.event
    async def confirmed_delete_param(self):
        param_id = self.confirm_delete_param_id
        self.confirm_delete_param_open = False
        self.confirm_delete_param_id = ""
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
        self.confirm_delete_type_open = True

    @rx.event
    def dismiss_confirm_delete_type(self):
        self.confirm_delete_type_open = False
        self.confirm_delete_type_id = ""
        self.confirm_delete_type_name = ""

    @rx.event
    async def confirmed_delete_type(self):
        type_id = self.confirm_delete_type_id
        self.confirm_delete_type_open = False
        self.confirm_delete_type_id = ""
        self.confirm_delete_type_name = ""
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
        self.confirm_deactivate_type_open = True

    @rx.event
    def dismiss_confirm_deactivate_type(self):
        self.confirm_deactivate_type_open = False
        self.confirm_deactivate_type_id = ""
        self.confirm_deactivate_type_name = ""

    @rx.event
    async def confirmed_deactivate_type(self):
        type_id = self.confirm_deactivate_type_id
        self.confirm_deactivate_type_open = False
        self.confirm_deactivate_type_id = ""
        self.confirm_deactivate_type_name = ""
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                ExamTypeRefService.deactivate(type_id)
            self.success = "Type d'examen désactivé."
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
                # Catégories uniques déjà définies (pour l'autocomplete)
                seen = []
                for r in rows:
                    if r.category_label and r.category_label not in seen:
                        seen.append(r.category_label)
                self.existing_categories = seen
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading = False

    async def _load_parameters(self, type_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
                detail = ExamTypeRefService.get(type_id)
                self.parameters = [
                    ExamParamVM(
                        id=p.id, name=p.name, value_type=p.value_type,
                        unit=p.unit or "",
                        ref_low=str(p.ref_low) if p.ref_low is not None else "",
                        ref_high=str(p.ref_high) if p.ref_high is not None else "",
                        critical_low=str(p.critical_low) if p.critical_low is not None else "",
                        critical_high=str(p.critical_high) if p.critical_high is not None else "",
                        is_required=p.is_required, display_order=p.display_order,
                    )
                    for p in detail.parameters
                ]
        except Exception as e:
            self.error = str(e)
