"""Appointment create / edit form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from ..common.language_state import LanguageState
from .appointment_form_state import AppointmentFormState

_EXAM_TYPE_KEYS = [
    ("biology", "exam_type_biology"),
    ("radiology", "exam_type_radiology"),
    ("ophthalmology", "exam_type_ophthalmology"),
    ("orl", "exam_type_orl"),
    ("ecg", "exam_type_ecg"),
    ("spirometry", "exam_type_spirometry"),
    ("clinical", "exam_type_clinical"),
    ("hormones", "exam_type_hormones"),
    ("hematology", "exam_type_hematology"),
    ("bacteriology", "exam_type_bacteriology"),
    ("parasitology", "exam_type_parasitology"),
    ("drug_test", "exam_type_drug_test"),
    ("immunology", "exam_type_immunology"),
    ("hepatic_markers", "exam_type_hepatic_markers"),
    ("other", "exam_type_other"),
]


def _field(label: str, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _form_fields() -> rx.Component:
    return rx.vstack(
        # Patient — read-only when pre-filled (from patient detail), selector when standalone
        rx.cond(
            AppointmentFormState.form_patient_label != "",
            # Pre-filled: show read-only
            _field(
                LanguageState.tr["field_patient_readonly"],
                rx.input(
                    value=AppointmentFormState.form_patient_label,
                    read_only=True,
                    size="2",
                    width="100%",
                    color="var(--gray-9)",
                ),
            ),
            # Standalone: show select
            _field(
                LanguageState.tr["field_patient_required"],
                rx.select.root(
                    rx.select.trigger(
                        placeholder=LanguageState.tr["select_patient_placeholder"],
                        width="100%",
                    ),
                    rx.select.content(
                        rx.foreach(
                            AppointmentFormState.patient_options,
                            lambda opt: rx.select.item(opt[1], value=opt[0]),
                        ),
                    ),
                    value=AppointmentFormState.form_patient_id,
                    on_change=AppointmentFormState.set_form_patient_id,
                    size="2",
                    width="100%",
                ),
            ),
        ),
        rx.grid(
            _field(
                LanguageState.tr["field_datetime"],
                rx.input(
                    value=AppointmentFormState.form_scheduled_at,
                    on_change=AppointmentFormState.set_form_scheduled_at,
                    type="datetime-local",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_exam_type_required"],
                rx.select.root(
                    rx.select.trigger(width="100%"),
                    rx.select.content(
                        *[rx.select.item(LanguageState.tr[key], value=value) for value, key in _EXAM_TYPE_KEYS],
                    ),
                    value=AppointmentFormState.form_exam_type,
                    on_change=AppointmentFormState.set_form_exam_type,
                    size="2",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        _field(
            LanguageState.tr["field_notes"],
            rx.text_area(
                value=AppointmentFormState.form_notes,
                on_change=AppointmentFormState.set_form_notes,
                placeholder=LanguageState.tr["notes_placeholder"],
                size="2",
                width="100%",
                rows="3",
            ),
        ),
        width="100%",
        spacing="4",
    )


def appointment_form_dialog() -> rx.Component:
    """Render the appointment form dialog (place in component tree)."""
    return form_dialog_component(
        state=AppointmentFormState,
        title=rx.cond(
            AppointmentFormState.is_create_mode,
            LanguageState.tr["new_appointment_form_title"],
            LanguageState.tr["edit_appointment_form_title"],
        ),
        form_content=_form_fields(),
    )
