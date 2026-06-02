"""Reusable patient deletion dialog component.

Import ``patient_delete_dialog`` and render it once per page that needs it.
Use ``PatientDeleteState.open_delete_dialog(patient_id, patient_name, redirect_to=...)``
to open the dialog from any event handler.
"""

import reflex as rx

from ..common.language_state import LanguageState
from .patient_delete_state import PatientDeleteState


def patient_delete_dialog() -> rx.Component:
    """Deletion confirmation dialog with a mandatory reason field.

    Include this component once in the page layout::

        patient_delete_dialog(),

    Then trigger it with::

        PatientDeleteState.open_delete_dialog(patient_id, full_name, redirect_to="/")
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # ── Title ──────────────────────────────────────────────────
                rx.hstack(
                    rx.icon("trash-2", size=20, color="var(--red-9)"),
                    rx.dialog.title(
                        LanguageState.tr["patient_delete_title"],
                        size="5",
                    ),
                    spacing="2",
                    align="center",
                ),
                # ── Warning callout ────────────────────────────────────────
                rx.callout(
                    rx.vstack(
                        rx.text.strong(LanguageState.tr["patient_delete_irreversible"]),
                        rx.text(
                            LanguageState.tr["patient_delete_warning_prefix"],
                            rx.text.strong(PatientDeleteState.delete_patient_name),
                            LanguageState.tr["patient_delete_warning_suffix"],
                        ),
                        spacing="1",
                    ),
                    icon="triangle-alert",
                    color_scheme="red",
                    variant="soft",
                ),
                # ── Reason field ───────────────────────────────────────────
                rx.vstack(
                    rx.text(
                        LanguageState.tr["patient_delete_reason_label"],
                        size="2",
                        weight="medium",
                    ),
                    rx.text_area(
                        value=PatientDeleteState.delete_reason,
                        on_change=PatientDeleteState.set_delete_reason,
                        placeholder=LanguageState.tr["patient_delete_reason_placeholder"],
                        width="100%",
                        rows="3",
                        size="2",
                        # Red border when there is an error
                        style=rx.cond(
                            PatientDeleteState.delete_reason_error != "",
                            {"border": "1px solid var(--red-9)"},
                            {},
                        ),
                    ),
                    rx.cond(
                        PatientDeleteState.delete_reason_error != "",
                        rx.text(
                            LanguageState.tr["patient_delete_reason_required"],
                            size="1",
                            color="var(--red-9)",
                        ),
                    ),
                    width="100%",
                    spacing="1",
                ),
                # ── Action buttons ────────────────────────────────────────
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            LanguageState.tr["cancel_btn"],
                            variant="outline",
                            color_scheme="gray",
                            on_click=PatientDeleteState.dismiss_delete,
                            disabled=PatientDeleteState.is_deleting,
                        ),
                    ),
                    rx.button(
                        rx.cond(
                            PatientDeleteState.is_deleting,
                            rx.spinner(size="2"),
                            rx.icon("trash-2", size=14),
                        ),
                        LanguageState.tr["patient_delete_confirm_btn"],
                        color_scheme="red",
                        on_click=PatientDeleteState.confirm_delete,
                        disabled=PatientDeleteState.is_deleting
                        | (PatientDeleteState.delete_reason.strip() == ""),
                    ),
                    justify="end",
                    spacing="3",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="460px",
        ),
        open=PatientDeleteState.delete_dialog_open,
        on_open_change=lambda _: PatientDeleteState.dismiss_delete(),
    )
