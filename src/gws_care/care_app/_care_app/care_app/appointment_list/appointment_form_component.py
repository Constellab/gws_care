"""Appointment create / edit form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from ..common.language_state import LanguageState
from .appointment_form_state import AppointmentFormState


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
                    rx.select.trigger(width="100%", placeholder="Sélectionner un examen..."),
                    rx.select.content(
                        rx.foreach(
                            AppointmentFormState.exam_type_options,
                            lambda o: rx.select.item(
                                o.name + " (" + o.category_label + ")",
                                value=o.id,
                            ),
                        ),
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
        rx.grid(
            _field(
                "Médecin assigné",
                rx.select.root(
                    rx.select.trigger(width="100%", placeholder="Aucun médecin..."),
                    rx.select.content(
                        rx.select.item("— Aucun —", value="_none_"),
                        rx.foreach(
                            AppointmentFormState.doctor_options,
                            lambda d: rx.select.item(
                                rx.cond(d.specialty != "", d.name + " — " + d.specialty, d.name),
                                value=d.id,
                            ),
                        ),
                    ),
                    value=AppointmentFormState.form_doctor_id,
                    on_change=AppointmentFormState.set_form_doctor_id,
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "Cabinet / salle",
                rx.input(
                    value=AppointmentFormState.form_room,
                    on_change=AppointmentFormState.set_form_room,
                    placeholder="Ex : Cabinet 3",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "Durée (min)",
                rx.input(
                    value=AppointmentFormState.form_duration,
                    on_change=AppointmentFormState.set_form_duration,
                    type="number",
                    min="5",
                    max="240",
                    size="2",
                    width="100%",
                ),
            ),
            columns="3",
            spacing="3",
            width="100%",
        ),
        rx.cond(
            AppointmentFormState.form_error != "",
            rx.callout(
                AppointmentFormState.form_error,
                icon="triangle-alert",
                color_scheme="red",
                size="1",
            ),
            rx.fragment(),
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
