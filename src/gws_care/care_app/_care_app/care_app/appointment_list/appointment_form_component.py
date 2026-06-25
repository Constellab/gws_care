"""Appointment booking dialog — Doctolib-style step wizard.

Step 1 — Specialty  : choose a medical specialty (or 'all doctors')
Step 2 — Doctor     : click a doctor card filtered by specialty
Step 3 — Slot       : pick date + time slot, add notes, confirm
Edit mode           : flat form (direct editing, no wizard)
"""

import reflex as rx

from ..common.language_state import LanguageState
from ..common.role_state import RoleState
from .appointment_form_state import AppointmentFormState, DoctorOption


# ── Shared helpers ────────────────────────────────────────────────────────────

def _field(label: str, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _step_breadcrumb() -> rx.Component:
    """Shows current wizard position as a simple breadcrumb."""
    def _crumb(n: int, label: str) -> rx.Component:
        is_active = AppointmentFormState.booking_step == n
        is_done = AppointmentFormState.booking_step > n
        return rx.hstack(
            rx.box(
                rx.text(str(n), size="1", weight="bold",
                        color=rx.cond(is_active | is_done, "white", "var(--gray-9)")),
                width="20px", height="20px",
                border_radius="50%",
                background=rx.cond(
                    is_active, "var(--accent-9)",
                    rx.cond(is_done, "var(--green-9)", "var(--gray-4)")
                ),
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),
            rx.text(
                label, size="1",
                color=rx.cond(is_active, "var(--accent-11)", "var(--gray-9)"),
                weight=rx.cond(is_active, "medium", "regular"),
            ),
            spacing="1", align="center",
        )

    return rx.hstack(
        _crumb(1, "Spécialité"),
        rx.icon("chevron-right", size=12, color="var(--gray-6)"),
        _crumb(2, "Médecin"),
        rx.icon("chevron-right", size=12, color="var(--gray-6)"),
        _crumb(3, "Créneau"),
        spacing="1", align="center",
    )


# ── Step 1 — Specialty ────────────────────────────────────────────────────────

def _specialty_pill(specialty: str) -> rx.Component:
    return rx.button(
        rx.icon("stethoscope", size=14),
        specialty,
        variant="soft",
        color_scheme="blue",
        size="2",
        on_click=lambda: AppointmentFormState.select_booking_specialty(specialty),
        cursor="pointer",
    )


def _specialty_option_row(s: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("stethoscope", size=14, color="var(--accent-9)"),
            rx.text(s, size="2"),
            spacing="2", align="center",
        ),
        padding="0.4rem 0.75rem",
        cursor="pointer",
        _hover={"background": "var(--accent-2)"},
        on_click=lambda: AppointmentFormState.select_booking_specialty(s),
    )


def _step_specialty() -> rx.Component:
    return rx.vstack(
        rx.text("Choisissez une spécialité médicale", size="3", weight="medium"),
        rx.separator(width="100%"),
        rx.vstack(
            rx.input(
                placeholder="Rechercher une spécialité…",
                value=AppointmentFormState.specialty_search,
                on_change=AppointmentFormState.set_specialty_search,
                size="2",
                width="100%",
            ),
            rx.cond(
                AppointmentFormState.specialty_options.length() > 0,
                rx.box(
                    # "All doctors" option
                    rx.box(
                        rx.hstack(
                            rx.icon("users", size=14, color="var(--gray-9)"),
                            rx.text("Tous les médecins", size="2", color="var(--gray-11)"),
                            spacing="2", align="center",
                        ),
                        padding="0.4rem 0.75rem",
                        cursor="pointer",
                        border_bottom="1px solid var(--gray-3)",
                        _hover={"background": "var(--gray-2)"},
                        on_click=lambda: AppointmentFormState.select_booking_specialty("_all_"),
                    ),
                    rx.cond(
                        AppointmentFormState.filtered_specialty_options.length() > 0,
                        rx.foreach(AppointmentFormState.filtered_specialty_options, _specialty_option_row),
                        rx.box(
                            rx.text("Aucune spécialité trouvée.", size="2", color="var(--gray-9)"),
                            padding="0.5rem 0.75rem",
                        ),
                    ),
                    border="1px solid var(--gray-5)",
                    border_radius="var(--radius-2)",
                    background="var(--gray-1)",
                    width="100%",
                    max_height="220px",
                    overflow_y="auto",
                ),
                rx.callout(
                    "Aucune spécialité enregistrée. Créez des médecins avec une spécialité dans l'onglet Médecins.",
                    icon="info", color_scheme="orange", size="1", width="100%",
                ),
            ),
            spacing="1",
            width="100%",
        ),
        width="100%",
        spacing="3",
        padding_top="0.5rem",
    )


# ── Step 2 — Doctor cards ─────────────────────────────────────────────────────

def _doctor_card(doc: DoctorOption) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon("circle-user-round", size=30, color="var(--accent-9)"),
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(doc.name, size="2", weight="bold"),
                rx.cond(
                    doc.specialty != "",
                    rx.badge(doc.specialty, color_scheme="blue", variant="soft", size="1"),
                    rx.fragment(),
                ),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.icon("chevron-right", size=16, color="var(--gray-7)"),
            spacing="3", align="center", width="100%",
        ),
        padding="0.75rem 1rem",
        border="1px solid var(--gray-4)",
        border_radius="10px",
        cursor="pointer",
        width="100%",
        _hover={"border_color": "var(--accent-7)", "background": "var(--accent-2)"},
        on_click=lambda: AppointmentFormState.select_booking_doctor_card(doc.id, doc.name),
    )


def _step_doctors() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon_button(
                rx.icon("arrow-left", size=14),
                variant="ghost", size="1",
                on_click=lambda: AppointmentFormState.go_back_to_step(1),
            ),
            rx.cond(
                AppointmentFormState.specialty_filter != "",
                rx.hstack(
                    rx.text("Médecins —", size="3", weight="medium"),
                    rx.badge(
                        AppointmentFormState.specialty_filter,
                        color_scheme="blue", variant="soft", size="2",
                    ),
                    spacing="2", align="center",
                ),
                rx.text("Tous les médecins", size="3", weight="medium"),
            ),
            spacing="2", align="center", width="100%",
        ),
        rx.separator(width="100%"),
        rx.cond(
            AppointmentFormState.doctor_options.length() > 0,
            rx.vstack(
                rx.foreach(AppointmentFormState.doctor_options, _doctor_card),
                width="100%",
                spacing="2",
                max_height="320px",
                overflow_y="auto",
            ),
            rx.callout(
                "Aucun médecin disponible pour cette spécialité.",
                icon="info", color_scheme="orange", size="1", width="100%",
            ),
        ),
        width="100%",
        spacing="3",
        padding_top="0.5rem",
    )


# ── Step 3 — Date + Slot ──────────────────────────────────────────────────────

def _slot_button(slot: str) -> rx.Component:
    time_str = slot[11:16]
    is_selected = AppointmentFormState.form_scheduled_at == slot
    return rx.button(
        time_str,
        variant=rx.cond(is_selected, "solid", "soft"),
        color_scheme=rx.cond(is_selected, "blue", "gray"),
        size="2",
        on_click=AppointmentFormState.set_form_slot(slot),
        border_radius="8px",
        min_width="64px",
    )


def _step_slot() -> rx.Component:
    return rx.vstack(
        # Header with back + doctor name
        rx.hstack(
            rx.icon_button(
                rx.icon("arrow-left", size=14),
                variant="ghost", size="1",
                on_click=lambda: AppointmentFormState.go_back_to_step(2),
            ),
            rx.hstack(
                rx.icon("circle-user-round", size=18, color="var(--accent-9)"),
                rx.text(AppointmentFormState.selected_doctor_name, size="3", weight="medium"),
                spacing="2", align="center",
            ),
            spacing="2", align="center", width="100%",
        ),
        rx.separator(width="100%"),
        # Date picker
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
        # Slot picker
        rx.cond(
            AppointmentFormState.form_booking_date != "",
            rx.vstack(
                rx.hstack(
                    rx.text("Créneaux disponibles *", size="2", weight="medium"),
                    rx.cond(
                        AppointmentFormState.form_slots_loading,
                        rx.spinner(size="1"),
                        rx.fragment(),
                    ),
                    spacing="2", align="center",
                ),
                rx.cond(
                    AppointmentFormState.form_available_slots.length() > 0,
                    rx.flex(
                        rx.foreach(AppointmentFormState.form_available_slots, _slot_button),
                        wrap="wrap", gap="0.4rem",
                    ),
                    rx.callout(
                        "Aucun créneau disponible pour cette date. Essayez une autre date.",
                        icon="calendar-x", color_scheme="orange", variant="soft", size="1",
                    ),
                ),
                rx.cond(
                    AppointmentFormState.form_scheduled_at != "",
                    rx.hstack(
                        rx.icon("circle-check", size=14, color="var(--green-9)"),
                        rx.text(
                            AppointmentFormState.form_scheduled_at[0:10]
                            + " à "
                            + AppointmentFormState.form_scheduled_at[11:16],
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
        # Notes + room (hidden for patient users)
        rx.cond(
            ~RoleState.is_patient_user,
            rx.grid(
                _field(
                    "Cabinet / salle",
                    rx.input(
                        value=AppointmentFormState.form_room,
                        on_change=AppointmentFormState.set_form_room,
                        placeholder="Ex : Cabinet 3",
                        size="2", width="100%",
                    ),
                ),
                _field(
                    "Notes",
                    rx.input(
                        value=AppointmentFormState.form_notes,
                        on_change=AppointmentFormState.set_form_notes,
                        placeholder="Motif, informations…",
                        size="2", width="100%",
                    ),
                ),
                columns="2", spacing="3", width="100%",
            ),
        ),
        # Error
        rx.cond(
            AppointmentFormState.form_error != "",
            rx.callout(
                AppointmentFormState.form_error,
                icon="triangle-alert", color_scheme="red", size="1",
            ),
            rx.fragment(),
        ),
        width="100%",
        spacing="3",
        padding_top="0.5rem",
    )


# ── Edit mode flat form (legacy) ──────────────────────────────────────────────

def _edit_flat_form() -> rx.Component:
    """Flat form used when editing an existing appointment."""
    return rx.vstack(
        # Patient label
        rx.cond(
            AppointmentFormState.form_patient_label != "",
            _field(
                "Patient",
                rx.input(
                    value=AppointmentFormState.form_patient_label,
                    read_only=True, size="2", width="100%",
                    color="var(--gray-9)",
                ),
            ),
            rx.fragment(),
        ),
        # Doctor
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
                size="2", width="100%",
            ),
        ),
        # Date picker
        _field(
            "Date du rendez-vous *",
            rx.input(
                type="date",
                value=AppointmentFormState.form_booking_date,
                on_change=AppointmentFormState.set_form_booking_date,
                size="2", width="100%",
            ),
        ),
        # Slots
        rx.cond(
            AppointmentFormState.form_doctor_id != "",
            rx.vstack(
                rx.hstack(
                    rx.text("Créneau *", size="2", weight="medium"),
                    rx.cond(AppointmentFormState.form_slots_loading, rx.spinner(size="1"), rx.fragment()),
                    spacing="2", align="center",
                ),
                rx.cond(
                    AppointmentFormState.form_available_slots.length() > 0,
                    rx.flex(
                        rx.foreach(AppointmentFormState.form_available_slots, _slot_button),
                        wrap="wrap", gap="0.4rem",
                    ),
                    rx.cond(
                        AppointmentFormState.form_booking_date != "",
                        rx.callout(
                            "Aucun créneau disponible. Choisissez une autre date.",
                            icon="calendar-x", color_scheme="orange", variant="soft", size="1",
                        ),
                        rx.text("Sélectionnez une date pour voir les créneaux.", size="1", color="var(--gray-9)"),
                    ),
                ),
                rx.cond(
                    AppointmentFormState.form_scheduled_at != "",
                    rx.hstack(
                        rx.icon("circle-check", size=14, color="var(--green-9)"),
                        rx.text(
                            AppointmentFormState.form_scheduled_at[0:10]
                            + " à "
                            + AppointmentFormState.form_scheduled_at[11:16],
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
        # Notes + room
        rx.grid(
            _field(
                "Cabinet / salle",
                rx.input(
                    value=AppointmentFormState.form_room,
                    on_change=AppointmentFormState.set_form_room,
                    placeholder="Ex : Cabinet 3",
                    size="2", width="100%",
                ),
            ),
            _field(
                "Notes",
                rx.input(
                    value=AppointmentFormState.form_notes,
                    on_change=AppointmentFormState.set_form_notes,
                    placeholder="Motif, informations…",
                    size="2", width="100%",
                ),
            ),
            columns="2", spacing="3", width="100%",
        ),
        rx.cond(
            AppointmentFormState.form_error != "",
            rx.callout(AppointmentFormState.form_error, icon="triangle-alert", color_scheme="red", size="1"),
            rx.fragment(),
        ),
        width="100%",
        spacing="3",
    )


# ── Main dialog ───────────────────────────────────────────────────────────────

def _wizard_content() -> rx.Component:
    """Step wizard content (create mode)."""
    return rx.vstack(
        # Patient label at top (always shown when known)
        rx.cond(
            AppointmentFormState.form_patient_label != "",
            rx.hstack(
                rx.icon("user-round", size=14, color="var(--accent-9)"),
                rx.text(
                    "Patient : " + AppointmentFormState.form_patient_label,
                    size="2", color="var(--accent-11)", weight="medium",
                ),
                spacing="2", align="center",
                padding="6px 10px",
                background="var(--accent-2)",
                border_radius="6px",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Patient picker in standalone mode (step 1 only)
        rx.cond(
            (AppointmentFormState.form_patient_label == "")
            & (AppointmentFormState.booking_step == 1),
            _field(
                "Patient *",
                rx.select.root(
                    rx.select.trigger(placeholder="Rechercher un patient…", width="100%"),
                    rx.select.content(
                        rx.foreach(
                            AppointmentFormState.patient_options,
                            lambda opt: rx.select.item(opt[1], value=opt[0]),
                        ),
                    ),
                    value=AppointmentFormState.form_patient_id,
                    on_change=AppointmentFormState.set_form_patient_id,
                    size="2", width="100%",
                ),
            ),
            rx.fragment(),
        ),
        # Step progress
        _step_breadcrumb(),
        rx.separator(width="100%"),
        # Step content
        rx.match(
            AppointmentFormState.booking_step,
            (1, _step_specialty()),
            (2, _step_doctors()),
            (3, _step_slot()),
            rx.fragment(),
        ),
        width="100%",
        spacing="3",
    )


def appointment_form_dialog() -> rx.Component:
    """Render the appointment booking dialog."""
    return rx.dialog.root(
        rx.dialog.content(
            # Title row
            rx.hstack(
                rx.dialog.title(
                    rx.cond(
                        AppointmentFormState.is_create_mode,
                        LanguageState.tr["new_appointment_form_title"],
                        LanguageState.tr["edit_appointment_form_title"],
                    )
                ),
                rx.dialog.close(
                    rx.icon_button(
                        rx.icon("x", size=14),
                        variant="ghost", size="1", color_scheme="gray",
                        on_click=AppointmentFormState.close_dialog,
                    )
                ),
                justify="between",
                align="center",
                width="100%",
            ),
            # Body
            rx.cond(
                AppointmentFormState.is_update_mode,
                _edit_flat_form(),
                _wizard_content(),
            ),
            # Footer buttons
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="soft", color_scheme="gray",
                        on_click=AppointmentFormState.close_dialog,
                    )
                ),
                rx.cond(
                    AppointmentFormState.is_update_mode,
                    rx.button(
                        "Enregistrer",
                        on_click=AppointmentFormState.confirm_booking,
                        loading=AppointmentFormState.is_loading,
                    ),
                    rx.cond(
                        AppointmentFormState.booking_step == 3,
                        rx.button(
                            rx.icon("calendar-check", size=14),
                            "Confirmer le rendez-vous",
                            on_click=AppointmentFormState.confirm_booking,
                            loading=AppointmentFormState.is_loading,
                            disabled=(AppointmentFormState.form_scheduled_at == "")
                            | (AppointmentFormState.form_doctor_id == ""),
                        ),
                        rx.fragment(),
                    ),
                ),
                spacing="2",
                justify="end",
                padding_top="1rem",
                width="100%",
            ),
            on_interact_outside=AppointmentFormState.close_dialog,
            on_escape_key_down=AppointmentFormState.close_dialog,
            max_width="520px",
        ),
        open=AppointmentFormState.dialog_opened,
    )
