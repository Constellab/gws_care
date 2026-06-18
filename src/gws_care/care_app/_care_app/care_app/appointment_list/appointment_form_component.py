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


def _slot_button(slot: str) -> rx.Component:
    """One available time slot as a selectable button."""
    time_str = slot[11:16]  # "HH:MM"
    is_selected = AppointmentFormState.form_scheduled_at == slot
    return rx.button(
        time_str,
        variant=rx.cond(is_selected, "solid", "soft"),
        color_scheme=rx.cond(is_selected, "blue", "gray"),
        size="1",
        on_click=AppointmentFormState.set_form_slot(slot),
        border_radius="6px",
    )


def _form_fields() -> rx.Component:
    return rx.vstack(
        # ── 1. Patient ────────────────────────────────────────────────────────
        rx.cond(
            AppointmentFormState.form_patient_label != "",
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
            _field(
                "Patient *",
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Rechercher un patient…",
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
        # ── 2. Médecin ────────────────────────────────────────────────────────
        _field(
            "Médecin *",
            rx.select.root(
                rx.select.trigger(width="100%", placeholder="Sélectionner un médecin…"),
                rx.select.content(
                    rx.foreach(
                        AppointmentFormState.doctor_options,
                        lambda d: rx.select.item(
                            rx.cond(d.specialty != "", d.name + " — " + d.specialty, d.name),
                            value=d.id,
                        ),
                    ),
                ),
                value=AppointmentFormState.form_doctor_id,
                on_change=AppointmentFormState.set_form_doctor_and_reload,
                size="2",
                width="100%",
            ),
        ),
        # ── 3. Date ───────────────────────────────────────────────────────────
        _field(
            "Date du rendez-vous *",
            rx.input(
                type="date",
                value=AppointmentFormState.form_booking_date,
                on_change=AppointmentFormState.set_form_booking_date,
                size="2",
                width="100%",
            ),
        ),
        # ── 4. Créneaux disponibles ───────────────────────────────────────────
        rx.cond(
            AppointmentFormState.form_doctor_id != "",
            rx.vstack(
                rx.hstack(
                    rx.text("Créneau disponible *", size="2", weight="medium"),
                    rx.cond(
                        AppointmentFormState.form_slots_loading,
                        rx.spinner(size="1"),
                        rx.fragment(),
                    ),
                    spacing="2", align="center",
                ),
                rx.cond(
                    AppointmentFormState.form_available_slots.length() > 0,
                    rx.box(
                        rx.flex(
                            rx.foreach(AppointmentFormState.form_available_slots, _slot_button),
                            wrap="wrap",
                            gap="0.4rem",
                        ),
                        width="100%",
                    ),
                    rx.cond(
                        AppointmentFormState.form_booking_date != "",
                        rx.callout(
                            "Aucun créneau disponible pour ce médecin à cette date. "
                            "Choisissez une autre date ou un autre médecin.",
                            icon="calendar-x",
                            color_scheme="orange",
                            variant="soft",
                            size="1",
                        ),
                        rx.text(
                            "Sélectionnez une date pour voir les créneaux disponibles.",
                            size="1", color="var(--gray-9)",
                        ),
                    ),
                ),
                rx.cond(
                    AppointmentFormState.form_scheduled_at != "",
                    rx.hstack(
                        rx.icon("circle-check", size=14, color="var(--green-9)"),
                        rx.text(
                            "Créneau sélectionné : " + AppointmentFormState.form_scheduled_at[0:10]
                            + " à " + AppointmentFormState.form_scheduled_at[11:16],
                            size="1", color="var(--green-11)", weight="medium",
                        ),
                        spacing="1", align="center",
                    ),
                    rx.fragment(),
                ),
                spacing="2", width="100%",
            ),
            rx.fragment(),
        ),
        # ── 5. Type d'examen (optionnel) ──────────────────────────────────────
        _field(
            "Type d'examen",
            rx.select.root(
                rx.select.trigger(width="100%", placeholder="— Consultation générale —"),
                rx.select.content(
                    rx.select.item("— Consultation générale —", value="_none_"),
                    rx.foreach(
                        AppointmentFormState.exam_type_options,
                        lambda o: rx.select.item(
                            o.name + " (" + o.category_label + ")",
                            value=o.id,
                        ),
                    ),
                ),
                value=rx.cond(
                    AppointmentFormState.form_exam_type != "",
                    AppointmentFormState.form_exam_type,
                    "_none_",
                ),
                on_change=AppointmentFormState.set_form_exam_type,
                size="2",
                width="100%",
            ),
        ),
        # ── 6. Notes + Cabinet ───────────────────────────────────────────────
        rx.grid(
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
                "Notes",
                rx.input(
                    value=AppointmentFormState.form_notes,
                    on_change=AppointmentFormState.set_form_notes,
                    placeholder="Motif, informations…",
                    size="2",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        # ── Error ────────────────────────────────────────────────────────────
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
        spacing="3",
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
