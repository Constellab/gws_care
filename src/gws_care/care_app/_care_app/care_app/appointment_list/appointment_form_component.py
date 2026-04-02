"""Appointment create / edit form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from .appointment_form_state import AppointmentFormState

_EXAM_TYPE_OPTIONS = [
    ("biology", "Biology"),
    ("radiology", "Radiology"),
    ("ophthalmology", "Ophthalmology"),
    ("orl", "ORL"),
    ("ecg", "ECG"),
    ("spirometry", "Spirometry"),
    ("clinical", "Clinical Exam"),
    ("hormones", "Hormones"),
    ("hematology", "Hematology"),
    ("bacteriology", "Bacteriology"),
    ("parasitology", "Parasitology"),
    ("drug_test", "Drug Test"),
    ("immunology", "Immunology"),
    ("hepatic_markers", "Hepatic Markers"),
    ("other", "Other"),
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
                "Patient",
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
                "Patient *",
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Select a patient…",
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
                "Date & Time *",
                rx.input(
                    value=AppointmentFormState.form_scheduled_at,
                    on_change=AppointmentFormState.set_form_scheduled_at,
                    type="datetime-local",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "Exam Type *",
                rx.select.root(
                    rx.select.trigger(width="100%"),
                    rx.select.content(
                        *[rx.select.item(label, value=value) for value, label in _EXAM_TYPE_OPTIONS],
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
            "Notes",
            rx.text_area(
                value=AppointmentFormState.form_notes,
                on_change=AppointmentFormState.set_form_notes,
                placeholder="Optional notes...",
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
            "New Appointment",
            "Edit Appointment",
        ),
        form_content=_form_fields(),
    )
