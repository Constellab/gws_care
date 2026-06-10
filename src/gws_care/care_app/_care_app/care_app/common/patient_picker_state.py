"""Reusable patient picker state — filter + table, then select one patient."""

from __future__ import annotations

import reflex as rx
from pydantic import BaseModel

from .role_state import RoleState


class PatientPickerRowDTO(BaseModel):
    id: str
    patient_number: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    account_name: str = ""


class PatientPickerState(RoleState):
    """Embeddable state for picking a patient from a filtered table.

    Each subclass MUST declare the following vars in its own class body so
    Reflex stores them in a separate state node (prevents cross-page sharing):

        picker_patients: list[PatientPickerRowDTO] = []
        picker_is_loading: bool = False
        picker_error: str = ""
        picker_filter_name: str = ""
        picker_filter_number: str = ""
        picker_account_id: str = ""
        picker_is_open: bool = False
        picker_selected_id: str = ""
        picker_selected_label: str = ""

    Usage pattern
    -------------
    1. Inherit this class and declare the vars above in the subclass.
    2. Call ``open_picker(account_id="...")`` to reset state and load the first
       page of patients restricted to the given account (or all if empty).
    3. The component renders a filter bar + table.  When the user clicks a row
       ``on_confirm`` is emitted — the consumer (program_detail / visit_list)
       must connect that to its own selection logic via ``confirm_patient()``.
    4. ``selected_id`` / ``selected_label`` hold the picked values.
    """

    # ── Dialog lifecycle (private — subclasses expose these as @rx.event) ─────

    async def _open_patient_picker(self):
        """Open the patient picker dialog and load initial list."""
        await self._open_picker()
        self.picker_is_open = True

    # ── Setters ───────────────────────────────────────────────────────────────

    async def _picker_set_filter_name(self, value: str):
        self.picker_filter_name = value
        await self._run_picker_search()

    async def _picker_set_filter_number(self, value: str):
        self.picker_filter_number = value
        await self._run_picker_search()

    async def _picker_clear_filters(self):
        self.picker_filter_name = ""
        self.picker_filter_number = ""
        await self._run_picker_search()

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _open_picker(self, account_id: str = ""):
        """Reset filters and load patient list. Does not clear current selection so that
        closing the picker without choosing a patient preserves the existing link."""
        self.picker_filter_name = ""
        self.picker_filter_number = ""
        self.picker_account_id = account_id
        self.picker_error = ""
        self.picker_patients = []
        await self._run_picker_search()

    async def _run_picker_search(self):
        """Reload the picker table with current filters."""
        self.picker_is_loading = True
        self.picker_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                account_id = self.picker_account_id or None
                name_term = self.picker_filter_name.strip() or None
                raw_pn = self.picker_filter_number.strip()
                if raw_pn.upper().startswith("PAT-"):
                    raw_pn = raw_pn[4:]
                pn_prefix = f"PAT-{raw_pn}" if raw_pn else None
                patients = PatientService.search_patients(
                    search=name_term,
                    patient_number_prefix=pn_prefix,
                    account_id=account_id,
                    limit=50,
                )
                # Batch-fetch account names
                from gws_care.account.account import Account
                from gws_care.patient.patient_account import PatientAccount
                patient_ids = [p.id for p in patients]
                account_names_by_patient: dict[str, list[str]] = {}
                if patient_ids:
                    links = (
                        PatientAccount.select(PatientAccount, Account)
                        .join(Account)
                        .where(PatientAccount.patient_id.in_(patient_ids))
                    )
                    for link in links:
                        pid = str(link.patient_id)
                        account_names_by_patient.setdefault(pid, []).append(link.account.name)
                self.picker_patients = [
                    PatientPickerRowDTO(
                        id=str(p.id),
                        patient_number=p.patient_number,
                        first_name=p.first_name,
                        last_name=p.last_name,
                        date_of_birth=p.date_of_birth.isoformat() if p.date_of_birth else "",
                        gender=p.gender or "",
                        account_name=", ".join(account_names_by_patient.get(str(p.id), [])),
                    )
                    for p in patients
                ]
        except Exception as e:
            self.picker_error = str(e)
        finally:
            self.picker_is_loading = False
