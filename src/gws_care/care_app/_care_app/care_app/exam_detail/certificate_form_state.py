"""State for the medical certificate issue dialog (on exam detail page)."""

from datetime import date
from typing import AsyncGenerator

import reflex as rx
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState


class CertificateFormState(FormDialogState, rx.State):
    """Manages the create / issue certificate dialog."""

    # Form fields
    form_issue_date: str = ""
    form_conclusion: str = ""
    form_fitness_decision: str = "FIT"
    form_restrictions: str = ""
    form_error: str = ""

    # Context
    _patient_id: str = ""
    _exam_id: str = ""

    # ── Setters ───────────────────────────────────────────────────────────────

    @rx.event
    def set_form_issue_date(self, value: str):
        self.form_issue_date = value

    @rx.event
    def set_form_conclusion(self, value: str):
        self.form_conclusion = value

    @rx.event
    def set_form_fitness_decision(self, value: str):
        self.form_fitness_decision = value

    @rx.event
    def set_form_restrictions(self, value: str):
        self.form_restrictions = value

    # ── Open ──────────────────────────────────────────────────────────────────

    @rx.event
    def open_for_exam(self, patient_id: str, exam_id: str):
        """Open the dialog linked to a specific exam."""
        self._patient_id = patient_id
        self._exam_id = exam_id
        self.form_issue_date = date.today().isoformat()
        self.form_conclusion = ""
        self.form_fitness_decision = "FIT"
        self.form_restrictions = ""
        self.is_update_mode = False
        self.dialog_opened = True

    # ── FormDialogState implementation ───────────────────────────────────────

    async def _clear_form_state(self) -> None:
        self.form_issue_date = ""
        self.form_conclusion = ""
        self.form_fitness_decision = "FIT"
        self.form_restrictions = ""
        self._patient_id = ""
        self._exam_id = ""
        self.is_update_mode = False
        self.form_error = ""

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Issue a medical certificate."""
        async with self:
            self.form_error = ""
        if not self.form_conclusion.strip():
            async with self:
                self.form_error = "Conclusion is required."
            return

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user() as auth_user:
            from gws_care.certificate.medical_certificate import (
                MedicalCertificateService,
                SaveMedicalCertificateDTO,
            )
            from gws_care.user.user import User

            doctor = User.get_or_none(User.email == auth_user.email)
            dto = SaveMedicalCertificateDTO(
                patient_id=self._patient_id,
                exam_id=self._exam_id or None,
                issue_date=self.form_issue_date,
                conclusion=self.form_conclusion,
                fitness_decision=self.form_fitness_decision,
                restrictions=self.form_restrictions or None,
            )
            MedicalCertificateService.create_certificate(dto, doctor)

        yield rx.toast.success("Certificate issued")
        from .exam_detail_state import ExamDetailState
        yield ExamDetailState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Certificates cannot be edited."""
        async with self:
            self.form_error = "Certificates cannot be edited."
        return
        yield  # make it a generator
