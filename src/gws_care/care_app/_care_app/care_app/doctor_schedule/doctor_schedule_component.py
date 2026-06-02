"""UI component for doctor schedule management page."""

import reflex as rx

from ..common.page_layout import page_layout
from .doctor_schedule_state import DoctorScheduleState, ScheduleBlockDTO, DoctorOptionDTO, UnavailableDayDTO


def _active_badge(block: ScheduleBlockDTO) -> rx.Component:
    return rx.cond(
        block.is_active,
        rx.badge("Actif", color_scheme="green", variant="soft", size="1"),
        rx.badge("Inactif", color_scheme="gray", variant="soft", size="1"),
    )


def _block_row(block: ScheduleBlockDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(block.doctor_name, size="2", weight="medium")),
        rx.table.cell(rx.text(block.day_label, size="2")),
        rx.table.cell(
            rx.hstack(
                rx.text(block.start_time, size="2"),
                rx.text("→", size="1", color="var(--gray-8)"),
                rx.text(block.end_time, size="2"),
                spacing="1", align="center",
            )
        ),
        rx.table.cell(
            rx.badge(
                block.slot_duration_minutes.to_string(), " min",
                color_scheme="blue", variant="soft", size="1",
            )
        ),
        rx.table.cell(
            rx.cond(
                block.room != "",
                rx.text(block.room, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(_active_badge(block)),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.cond(
                            block.is_active,
                            rx.icon("pause", size=14),
                            rx.icon("play", size=14),
                        ),
                        variant="ghost", size="1",
                        color_scheme=rx.cond(block.is_active, "orange", "green"),
                        on_click=DoctorScheduleState.toggle_block_active(block.id),
                    ),
                    content=rx.cond(block.is_active, "Désactiver ce créneau", "Activer ce créneau"),
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("trash-2", size=14),
                        variant="ghost", size="1", color_scheme="red",
                        on_click=DoctorScheduleState.delete_block(block.id),
                    ),
                    content="Supprimer ce créneau",
                ),
                spacing="1",
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _schedule_table() -> rx.Component:
    return rx.cond(
        DoctorScheduleState.filtered_blocks.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Médecin"),
                    rx.table.column_header_cell("Jour"),
                    rx.table.column_header_cell("Horaires"),
                    rx.table.column_header_cell("Durée créneaux"),
                    rx.table.column_header_cell("Salle"),
                    rx.table.column_header_cell("Statut"),
                    rx.table.column_header_cell("Actions"),
                )
            ),
            rx.table.body(
                rx.foreach(DoctorScheduleState.filtered_blocks, _block_row)
            ),
            width="100%",
            variant="surface",
            size="2",
        ),
        rx.center(
            rx.vstack(
                rx.icon("calendar-clock", size=40, color="var(--gray-7)"),
                rx.text(
                    "Aucun créneau de disponibilité défini",
                    size="3", color="var(--gray-9)",
                ),
                rx.text(
                    "Ajoutez les créneaux hebdomadaires de chaque médecin pour gérer l'agenda.",
                    size="2", color="var(--gray-7)", text_align="center",
                ),
                align="center", spacing="2",
            ),
            padding="4rem",
        ),
    )


def _doctor_option(opt: DoctorOptionDTO) -> rx.Component:
    return rx.select.item(
        rx.cond(opt.specialty != "", opt.name + " — " + opt.specialty, opt.name),
        value=opt.id,
    )


_SPECIALTY_CHOICES = [
    "Généraliste", "Cardiologue", "Pneumologue", "Ophtalmologue", "ORL",
    "Radiologue", "Rhumatologue", "Neurologue", "Dermatologue", "Gynécologue",
    "Pédiatre", "Endocrinologue", "Néphrologue", "Gastro-entérologue",
    "Infectiologue", "Médecin du travail", "Autre",
]


def _doctor_specialty_row(opt: DoctorOptionDTO) -> rx.Component:
    """One row for a doctor with specialty selector."""
    return rx.hstack(
        rx.text(opt.name, size="2", flex="1"),
        rx.select.root(
            rx.select.trigger(
                placeholder="Spécialité...",
                width="200px",
            ),
            rx.select.content(
                rx.select.item("— Aucune —", value="__none__"),
                *[rx.select.item(s, value=s) for s in _SPECIALTY_CHOICES],
            ),
            value=rx.cond(opt.specialty != "", opt.specialty, "__none__"),
            on_change=lambda v: DoctorScheduleState.set_doctor_specialty(opt.id, v),
            size="2",
        ),
        spacing="3",
        align="center",
        width="100%",
        padding_y="0.25rem",
    )


def _create_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nouveau créneau de disponibilité"),
            rx.vstack(
                # Doctor
                rx.text("Médecin *", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(placeholder="Sélectionner un médecin...", width="100%"),
                    rx.select.content(
                        rx.foreach(DoctorScheduleState.doctors, _doctor_option),
                    ),
                    value=DoctorScheduleState.form_doctor_id,
                    on_change=DoctorScheduleState.set_form_doctor,
                    width="100%",
                ),
                # Day
                rx.text("Jour de la semaine *", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(placeholder="Choisir le jour...", width="100%"),
                    rx.select.content(
                        rx.select.item("Lundi", value="0"),
                        rx.select.item("Mardi", value="1"),
                        rx.select.item("Mercredi", value="2"),
                        rx.select.item("Jeudi", value="3"),
                        rx.select.item("Vendredi", value="4"),
                        rx.select.item("Samedi", value="5"),
                        rx.select.item("Dimanche", value="6"),
                    ),
                    value=DoctorScheduleState.form_day.to_string(),
                    on_change=DoctorScheduleState.set_form_day,
                    width="100%",
                ),
                # Times
                rx.grid(
                    rx.vstack(
                        rx.text("Heure début *", size="2", weight="medium"),
                        rx.input(
                            type="time",
                            value=DoctorScheduleState.form_start,
                            on_change=DoctorScheduleState.set_form_start,
                            width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Heure fin *", size="2", weight="medium"),
                        rx.input(
                            type="time",
                            value=DoctorScheduleState.form_end,
                            on_change=DoctorScheduleState.set_form_end,
                            width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    columns="2", spacing="4", width="100%",
                ),
                # Slot duration
                rx.text("Durée d'un créneau (minutes)", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(placeholder="Durée...", width="100%"),
                    rx.select.content(
                        rx.select.item("10 min", value="10"),
                        rx.select.item("15 min", value="15"),
                        rx.select.item("20 min", value="20"),
                        rx.select.item("30 min", value="30"),
                        rx.select.item("45 min", value="45"),
                        rx.select.item("60 min", value="60"),
                    ),
                    value=DoctorScheduleState.form_slot.to_string(),
                    on_change=DoctorScheduleState.set_form_slot,
                    width="100%",
                ),
                # Room
                rx.text("Salle / Cabinet", size="2", weight="medium"),
                rx.input(
                    placeholder="Ex: Cabinet 1, Salle A...",
                    value=DoctorScheduleState.form_room,
                    on_change=DoctorScheduleState.set_form_room,
                    width="100%",
                ),
                # Error
                rx.cond(
                    DoctorScheduleState.error_message != "",
                    rx.callout(
                        DoctorScheduleState.error_message,
                        icon="triangle-alert",
                        color_scheme="red", variant="soft", size="1",
                    ),
                    rx.fragment(),
                ),
                spacing="3", width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Annuler", variant="soft", color_scheme="gray",
                              on_click=DoctorScheduleState.close_create_dialog),
                ),
                rx.button(
                    "Enregistrer",
                    on_click=DoctorScheduleState.save_block,
                    color_scheme="blue",
                ),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="480px",
        ),
        open=DoctorScheduleState.create_dialog_open,
    )


def _unavail_dialog() -> rx.Component:
    """Dialog to add a new unavailable day for a doctor."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajouter un jour d'indisponibilité"),
            rx.vstack(
                rx.text("Médecin *", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(placeholder="Sélectionner un médecin...", width="100%"),
                    rx.select.content(
                        rx.foreach(DoctorScheduleState.doctors, _doctor_option),
                    ),
                    value=DoctorScheduleState.unavail_form_doctor_id,
                    on_change=DoctorScheduleState.set_unavail_doctor,
                    width="100%",
                ),
                rx.text("Date *", size="2", weight="medium"),
                rx.input(
                    type="date",
                    value=DoctorScheduleState.unavail_form_date,
                    on_change=DoctorScheduleState.set_unavail_date,
                    width="100%",
                ),
                rx.text("Raison (optionnel)", size="2", weight="medium"),
                rx.input(
                    placeholder="Ex : Congé, Formation, ...",
                    value=DoctorScheduleState.unavail_form_reason,
                    on_change=DoctorScheduleState.set_unavail_reason,
                    width="100%",
                ),
                rx.cond(
                    DoctorScheduleState.unavail_error != "",
                    rx.callout(
                        DoctorScheduleState.unavail_error,
                        icon="triangle-alert",
                        color_scheme="red", variant="soft", size="1",
                    ),
                    rx.fragment(),
                ),
                spacing="3", width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Annuler", variant="soft", color_scheme="gray",
                              on_click=DoctorScheduleState.close_unavail_form),
                ),
                rx.button(
                    "Enregistrer",
                    on_click=DoctorScheduleState.save_unavail_day,
                    color_scheme="red",
                ),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="420px",
        ),
        open=DoctorScheduleState.unavail_form_open,
    )


def _unavail_row(u: UnavailableDayDTO) -> rx.Component:
    return rx.hstack(
        rx.badge(u.date, color_scheme="red", variant="soft", size="2"),
        rx.text(u.doctor_name, size="2", weight="medium", flex="1"),
        rx.cond(
            u.reason != "",
            rx.text(u.reason, size="1", color="var(--gray-9)"),
            rx.fragment(),
        ),
        rx.icon_button(
            rx.icon("trash-2", size=14),
            variant="ghost", size="1", color_scheme="red",
            on_click=DoctorScheduleState.delete_unavail_day(u.id),
        ),
        align="center", spacing="3", width="100%",
        padding="0.4rem 0.75rem",
        border="1px solid var(--red-5)",
        border_radius="8px",
        background="var(--red-2)",
    )


def _unavailable_days_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("calendar-off", size=18, color="var(--red-9)"),
            rx.heading("Jours d'indisponibilité", size="4"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                "Ajouter",
                on_click=DoctorScheduleState.open_unavail_form,
                size="2",
                color_scheme="red",
                variant="soft",
            ),
            align="center", spacing="2", width="100%",
        ),
        rx.text(
            "Les patients ne pourront pas réserver sur ces dates.",
            size="2", color="var(--gray-9)",
        ),
        rx.cond(
            DoctorScheduleState.filtered_unavail_days.length() > 0,
            rx.vstack(
                rx.foreach(DoctorScheduleState.filtered_unavail_days, _unavail_row),
                spacing="2",
                width="100%",
            ),
            rx.text("Aucun jour bloqué.", size="2", color="var(--gray-7)"),
        ),
        spacing="3",
        width="100%",
        padding="1.25rem",
        border="1px solid var(--red-4)",
        border_radius="12px",
        background="var(--red-1)",
        margin_top="1.5rem",
    )


def doctor_schedule_page() -> rx.Component:
    return page_layout(
        _create_dialog(),
        _unavail_dialog(),
        rx.hstack(
            rx.hstack(
                rx.icon("calendar-clock", size=22, color="var(--accent-9)"),
                rx.heading("Disponibilités médecins", size="6"),
                spacing="2", align="center",
            ),
            rx.spacer(),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("calendar", size=16),
                    variant="soft", size="2", color_scheme="gray",
                    on_click=rx.redirect("/appointments"),
                ),
                content="Voir le planning des rendez-vous",
            ),
            rx.button(
                rx.icon("plus", size=16),
                "Ajouter un créneau",
                on_click=DoctorScheduleState.open_create_dialog,
                size="2",
            ),
            width="100%", align="center", spacing="3",
        ),
        # Doctor filter
        rx.hstack(
            rx.text("Médecin :", size="2", color="var(--gray-9)"),
            rx.select.root(
                rx.select.trigger(placeholder="Tous les médecins", width="220px"),
                rx.select.content(
                    rx.select.item("Tous les médecins", value="ALL"),
                    rx.foreach(DoctorScheduleState.doctors, _doctor_option),
                ),
                value=DoctorScheduleState.selected_doctor_id,
                on_change=DoctorScheduleState.set_doctor_filter,
            ),
            spacing="2", align="center",
        ),
        rx.cond(
            DoctorScheduleState.error_message != "",
            rx.callout(
                DoctorScheduleState.error_message,
                icon="triangle-alert",
                color_scheme="red", variant="soft",
            ),
            rx.fragment(),
        ),
        rx.cond(
            DoctorScheduleState.is_loading,
            rx.center(rx.spinner(size="3"), padding="2rem"),
            _schedule_table(),
        ),
        _unavailable_days_section(),
    )
