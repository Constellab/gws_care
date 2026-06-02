"""State for the 'Nouvelle consultation' dialog on the patient detail page.

A consultation groups the clinical context (filled once by the doctor) with
N exam types that are ordered during the same visit.
"""

from __future__ import annotations

from typing import AsyncGenerator

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class ParamCheckOption(BaseModel):
    """One parameter within an exam type, checkable."""
    id: str
    name: str
    unit: str = ""
    is_selected: bool = True  # all selected by default


class ExamTypeCheckOption(BaseModel):
    """One exam type that can be ordered within the consultation form."""

    id: str
    name: str
    category_label: str
    is_selected: bool = False
    params: list[ParamCheckOption] = []   # parameters of this exam type
    params_expanded: bool = False          # whether the param list is shown


class AccountOption(BaseModel):
    id: str
    name: str


class ConsultationFormState(rx.State):
    """Manages the 'Nouvelle consultation' dialog."""

    dialog_open: bool = False
    is_saving: bool = False
    error: str = ""

    # Clinical context fields
    form_date: str = ""
    form_account_id: str = ""
    form_reason: str = ""
    form_history: str = ""
    form_weight: str = ""
    form_height: str = ""
    form_bmi: str = ""
    form_bp: str = ""
    form_hr: str = ""
    form_temp: str = ""
    form_conclusion: str = ""

    # Exam type selection
    exam_type_options: list[ExamTypeCheckOption] = []

    # Account options for billing
    account_options: list[AccountOption] = []

    # Private context
    _patient_id: str = ""

    # ── Setters ───────────────────────────────────────────────────────────────

    @rx.event
    def set_form_date(self, v: str): self.form_date = v

    @rx.event
    def set_form_account(self, v: str): self.form_account_id = v if v not in ("NONE", "PRIVE") else ""

    @rx.event
    def set_form_reason(self, v: str): self.form_reason = v

    @rx.event
    def set_form_history(self, v: str): self.form_history = v

    @rx.event
    def set_form_weight(self, v: str): self.form_weight = v

    @rx.event
    def set_form_height(self, v: str):
        self.form_height = v
        self._auto_bmi()

    @rx.event
    def set_form_bmi(self, v: str): self.form_bmi = v

    @rx.event
    def set_form_bp(self, v: str): self.form_bp = v

    @rx.event
    def set_form_hr(self, v: str): self.form_hr = v

    @rx.event
    def set_form_temp(self, v: str): self.form_temp = v

    @rx.event
    def set_form_conclusion(self, v: str): self.form_conclusion = v

    def _auto_bmi(self):
        """Auto-compute BMI from weight and height if both are filled."""
        try:
            w = float(self.form_weight.replace(",", "."))
            h = float(self.form_height.replace(",", ".")) / 100
            if h > 0:
                self.form_bmi = f"{w / (h * h):.1f}"
        except (ValueError, ZeroDivisionError):
            pass

    @rx.event
    def toggle_exam_type(self, type_id: str):
        """Toggle an exam type in/out of the selection; expand params when selecting."""
        updated = []
        for o in self.exam_type_options:
            if o.id == type_id:
                new_selected = not o.is_selected
                updated.append(ExamTypeCheckOption(**{
                    **o.model_dump(),
                    "is_selected": new_selected,
                    "params_expanded": new_selected,   # expand on select, collapse on deselect
                }))
            else:
                updated.append(o)
        self.exam_type_options = updated

    @rx.event
    def toggle_params_expanded(self, type_id: str):
        """Toggle visibility of the parameter list for a selected exam type."""
        self.exam_type_options = [
            ExamTypeCheckOption(**{**o.model_dump(), "params_expanded": not o.params_expanded})
            if o.id == type_id else o
            for o in self.exam_type_options
        ]

    @rx.event
    def toggle_param(self, type_id: str, param_id: str):
        """Toggle one parameter inside an exam type."""
        updated = []
        for o in self.exam_type_options:
            if o.id == type_id:
                new_params = [
                    ParamCheckOption(**{**p.model_dump(), "is_selected": not p.is_selected})
                    if p.id == param_id else p
                    for p in o.params
                ]
                updated.append(ExamTypeCheckOption(**{**o.model_dump(), "params": new_params}))
            else:
                updated.append(o)
        self.exam_type_options = updated

    @rx.event
    def select_all_params(self, type_id: str):
        """Select all parameters for an exam type."""
        self.exam_type_options = [
            ExamTypeCheckOption(**{
                **o.model_dump(),
                "params": [ParamCheckOption(**{**p.model_dump(), "is_selected": True}) for p in o.params],
            }) if o.id == type_id else o
            for o in self.exam_type_options
        ]

    # ── Open / Close ──────────────────────────────────────────────────────────

    @rx.event
    def open_dialog(self, patient_id: str):
        """Open the dialog for a given patient."""
        from datetime import date
        self._patient_id = patient_id
        self.form_date = date.today().isoformat()
        self.form_account_id = ""
        self.form_reason = ""
        self.form_history = ""
        self.form_weight = ""
        self.form_height = ""
        self.form_bmi = ""
        self.form_bp = ""
        self.form_hr = ""
        self.form_temp = ""
        self.form_conclusion = ""
        self.error = ""
        self._load_exam_types()
        self._load_accounts()
        self.dialog_open = True

    @rx.event
    def close_dialog(self):
        self.dialog_open = False

    def _load_exam_types(self):
        try:
            from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
            from gws_care.exam_type_ref.exam_parameter import ExamParameter
            refs = list(
                ExamTypeRef.select()
                .where(ExamTypeRef.is_active == True)
                .order_by(ExamTypeRef.category, ExamTypeRef.name)
            )
            # Batch-load all parameters for all refs (1 query)
            ref_ids = [str(r.id) for r in refs]
            params_by_ref: dict[str, list[ParamCheckOption]] = {}
            if ref_ids:
                for p in (
                    ExamParameter.select()
                    .where(ExamParameter.exam_type_ref.in_(ref_ids))
                    .order_by(ExamParameter.display_order)
                ):
                    params_by_ref.setdefault(str(p.exam_type_ref_id), []).append(
                        ParamCheckOption(
                            id=str(p.id),
                            name=p.name,
                            unit=p.unit or "",
                            is_selected=True,
                        )
                    )
            self.exam_type_options = [
                ExamTypeCheckOption(
                    id=str(r.id),
                    name=r.name,
                    category_label=r.get_category_label(),
                    params=params_by_ref.get(str(r.id), []),
                )
                for r in refs
            ]
        except Exception as exc:
            self.exam_type_options = []

    def _load_accounts(self):
        try:
            from gws_care.account.account_service import AccountService
            from gws_care.patient.patient_service import PatientService
            from gws_care.account.account import Account

            patient = PatientService.get_patient(self._patient_id)

            # Build ordered list: patient's own account first, then company accounts
            seen_ids: set[str] = set()
            options: list[AccountOption] = []

            # 1. Patient's pre-declared billing account (from their profile)
            if patient.billing_account_id:
                try:
                    acc = Account.get_by_id(patient.billing_account_id)
                    aid = str(acc.id)
                    options.append(AccountOption(id=aid, name=acc.name))
                    seen_ids.add(aid)
                    # Pre-select it
                    if not self.form_account_id:
                        self.form_account_id = aid
                except Exception:
                    pass

            # 2. Accounts linked to the patient's company
            if patient.company_id:
                company_accs = AccountService.list_accounts_for_company(str(patient.company_id))
                for a in company_accs:
                    aid = str(a.id)
                    if aid not in seen_ids:
                        options.append(AccountOption(id=aid, name=a.name))
                        seen_ids.add(aid)

            # 3. Privé option (no billing account — patient pays themselves)
            options.append(AccountOption(id="PRIVE", name="Privé (paiement direct)"))

            self.account_options = options
        except Exception as exc:
            self.account_options = [AccountOption(id="PRIVE", name="Privé (paiement direct)")]

    # ── Submit ────────────────────────────────────────────────────────────────

    @rx.event
    async def submit(self) -> AsyncGenerator:
        """Create the consultation and all ordered exams."""
        if not self.form_date:
            self.error = "La date de consultation est obligatoire."
            return

        selected = [o for o in self.exam_type_options if o.is_selected]
        if not selected:
            self.error = "Sélectionnez au moins un examen à prescrire."
            return

        self.is_saving = True
        self.error = ""
        yield

        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.consultation.consultation_service import (
                    ConsultationService,
                    CreateConsultationDTO,
                    ExamOrderDTO,
                )

                def _to_float(s: str) -> float | None:
                    s = s.strip()
                    if not s:
                        return None
                    try:
                        return float(s.replace(",", "."))
                    except ValueError:
                        return None

                dto = CreateConsultationDTO(
                    patient_id=self._patient_id,
                    consultation_date=self.form_date,
                    account_id=self.form_account_id or None,
                    reason_for_visit=self.form_reason or None,
                    medical_history=self.form_history or None,
                    weight=_to_float(self.form_weight),
                    height=_to_float(self.form_height),
                    bmi=_to_float(self.form_bmi),
                    blood_pressure=self.form_bp or None,
                    heart_rate=_to_float(self.form_hr),
                    temperature=_to_float(self.form_temp),
                    conclusion=self.form_conclusion or None,
                    exam_orders=[
                        ExamOrderDTO(
                            exam_type_id=o.id,
                            selected_param_ids=[
                                p.id for p in o.params if p.is_selected
                            ],
                        )
                        for o in selected
                    ],
                )
                ConsultationService.create_consultation_with_exams(dto)

            self.dialog_open = False
            yield rx.toast.success("Consultation créée.")
            from .patient_detail_state import PatientDetailState
            yield PatientDetailState.on_load()
        except Exception as exc:
            self.error = str(exc)
        finally:
            self.is_saving = False
