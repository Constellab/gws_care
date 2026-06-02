"""Reusable state for the patient permanent-deletion dialog.

This state is imported by any page that needs a "delete patient" button:
  - patient list page
  - patient detail page
  - company / account detail page

Usage in a page event:
    PatientDeleteState.open_delete_dialog(patient_id, patient_full_name, redirect_to="/")

After a successful deletion the state redirects to *post_delete_redirect*.
"""

import reflex as rx
from gws_reflex_main import ReflexMainState


class PatientDeleteState(ReflexMainState):
    """Manages the patient deletion confirmation dialog (with mandatory reason)."""

    delete_dialog_open: bool = False
    delete_patient_id: str = ""
    delete_patient_name: str = ""
    delete_reason: str = ""
    delete_reason_error: str = ""
    is_deleting: bool = False
    # Where to redirect after successful deletion (set by the caller).
    post_delete_redirect: str = "/"

    @rx.event
    def open_delete_dialog(self, patient_id: str, patient_name: str, redirect_to: str = "/"):
        """Open the deletion dialog for the given patient."""
        self.delete_patient_id = patient_id
        self.delete_patient_name = patient_name
        self.delete_reason = ""
        self.delete_reason_error = ""
        self.post_delete_redirect = redirect_to
        self.delete_dialog_open = True

    @rx.event
    def dismiss_delete(self):
        """Close the dialog without deleting."""
        self.delete_dialog_open = False
        self.delete_patient_id = ""
        self.delete_patient_name = ""
        self.delete_reason = ""
        self.delete_reason_error = ""

    @rx.event
    def set_delete_reason(self, value: str):
        """Update the reason text and clear any previous error."""
        self.delete_reason = value
        if value.strip():
            self.delete_reason_error = ""

    @rx.event
    async def confirm_delete(self):
        """Validate the reason, delete the patient, then redirect."""
        if not self.delete_reason.strip():
            self.delete_reason_error = "patient_delete_reason_required"
            return

        patient_id = self.delete_patient_id
        reason = self.delete_reason.strip()
        redirect_to = self.post_delete_redirect

        self.is_deleting = True
        self.delete_dialog_open = False

        deleted_by = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.patient.patient_service import PatientService
                try:
                    from gws_core import User
                    local_user = User.get_or_none(User.id == str(auth_user.id))
                    if local_user:
                        deleted_by = f"{local_user.first_name} {local_user.last_name}".strip()
                    if not deleted_by:
                        deleted_by = getattr(auth_user, "email", "")
                except Exception as exc:
                    deleted_by = ""
                PatientService.delete_patient(patient_id, reason=reason, deleted_by=deleted_by)
        except Exception as e:
            self.is_deleting = False
            self.delete_reason_error = str(e)
            self.delete_dialog_open = True
            return

        self.is_deleting = False
        self.delete_patient_id = ""
        self.delete_patient_name = ""
        self.delete_reason = ""
        return rx.redirect(redirect_to)
