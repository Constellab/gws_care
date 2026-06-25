"""UI component for doctor schedule management page."""

import reflex as rx

from ..common.page_layout import page_layout
from .doctor_schedule_state import DoctorScheduleState, ScheduleBlockDTO, DoctorOptionDTO, UnavailableDayDTO


# ── Doctor filter bar ─────────────────────────────────────────────────────────

def _specialty_pill(specialty: str) -> rx.Component:
    is_selected = DoctorScheduleState.filter_specialty == specialty
    return rx.button(
        specialty,
        variant=rx.cond(is_selected, "solid", "soft"),
        color_scheme=rx.cond(is_selected, "blue", "gray"),
        size="1",
        border_radius="999px",
        on_click=lambda: DoctorScheduleState.set_filter_specialty(specialty),
    )


def _doctor_card(doc: DoctorOptionDTO) -> rx.Component:
    is_selected = DoctorScheduleState.selected_doctor_id == doc.id
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(
                    "circle-user-round", size=22,
                    color=rx.cond(is_selected, "white", "var(--accent-9)"),
                    flex_shrink="0",
                ),
                rx.vstack(
                    rx.text(
                        doc.name, size="2", weight="medium",
                        color=rx.cond(is_selected, "white", "inherit"),
                    ),
                    rx.cond(
                        doc.specialty != "",
                        rx.badge(
                            doc.specialty,
                            color_scheme=rx.cond(is_selected, "indigo", "blue"),
                            variant="soft", size="1",
                        ),
                        rx.fragment(),
                    ),
                    spacing="1", align_items="start",
                ),
                spacing="2", align="center",
            ),
            spacing="1", align_items="start",
        ),
        padding="0.6rem 0.9rem",
        border_radius="10px",
        cursor="pointer",
        min_width="180px",
        border=rx.cond(
            is_selected,
            "2px solid var(--accent-9)",
            "1px solid var(--gray-4)",
        ),
        background=rx.cond(
            is_selected,
            "var(--accent-9)",
            "var(--gray-1)",
        ),
        _hover={"border_color": "var(--accent-7)", "background": rx.cond(is_selected, "var(--accent-9)", "var(--accent-2)")},
        on_click=lambda: DoctorScheduleState.select_doctor(doc.id),
    )


def _filter_bar() -> rx.Component:
    return rx.vstack(
        # Row 1: specialty pills + search input
        rx.hstack(
            rx.hstack(
                rx.text("Spécialité :", size="2", color="var(--gray-9)", white_space="nowrap"),
                rx.button(
                    "Toutes",
                    variant=rx.cond(DoctorScheduleState.filter_specialty == "", "solid", "soft"),
                    color_scheme=rx.cond(DoctorScheduleState.filter_specialty == "", "blue", "gray"),
                    size="1", border_radius="999px",
                    on_click=lambda: DoctorScheduleState.set_filter_specialty("_all_"),
                ),
                rx.foreach(DoctorScheduleState.available_specialties, _specialty_pill),
                spacing="2", align="center", wrap="wrap", flex="1",
            ),
            rx.input(
                placeholder="🔍 Rechercher par nom...",
                value=DoctorScheduleState.search_name,
                on_change=DoctorScheduleState.set_search_name,
                size="2",
                width="220px",
                flex_shrink="0",
            ),
            spacing="3", align="center", width="100%", wrap="wrap",
        ),
        # Row 2: doctor cards (horizontal scroll)
        rx.cond(
            DoctorScheduleState.filtered_doctors.length() > 0,
            rx.box(
                rx.hstack(
                    rx.foreach(DoctorScheduleState.filtered_doctors, _doctor_card),
                    spacing="2", align="start",
                ),
                width="100%",
                overflow_x="auto",
                padding_y="0.25rem",
            ),
            rx.callout(
                "Aucun médecin actif ne correspond à votre recherche.",
                icon="info",
                color_scheme="orange",
                variant="soft",
                size="1",
            ),
        ),
        # Selection indicator
        rx.cond(
            DoctorScheduleState.selected_doctor_id != "ALL",
            rx.hstack(
                rx.icon("stethoscope", size=14, color="var(--accent-9)"),
                rx.text(
                    "Affichage des créneaux de ",
                    rx.text.strong(DoctorScheduleState.selected_doctor_name),
                    rx.cond(
                        DoctorScheduleState.selected_doctor_specialty != "",
                        " — " + DoctorScheduleState.selected_doctor_specialty,
                        "",
                    ),
                    size="2", color="var(--accent-11)",
                ),
                rx.button(
                    rx.icon("x", size=12), "Voir tous",
                    variant="ghost", size="1", color_scheme="gray",
                    on_click=DoctorScheduleState.clear_doctor_selection,
                ),
                spacing="2", align="center",
            ),
            rx.fragment(),
        ),
        spacing="3", width="100%",
    )


# ── Schedule table ────────────────────────────────────────────────────────────

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
                rx.text("Aucun créneau de disponibilité défini", size="3", color="var(--gray-9)"),
                rx.text(
                    "Ajoutez les créneaux hebdomadaires de chaque médecin pour gérer l'agenda.",
                    size="2", color="var(--gray-7)", text_align="center",
                ),
                align="center", spacing="2",
            ),
            padding="4rem",
        ),
    )


# ── Create block dialog ───────────────────────────────────────────────────────

def _doctor_option(opt: DoctorOptionDTO) -> rx.Component:
    return rx.select.item(
        rx.cond(opt.specialty != "", opt.name + " — " + opt.specialty, opt.name),
        value=opt.id,
    )


def _create_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nouveau créneau de disponibilité"),
            rx.vstack(
                rx.text("Médecin *", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(placeholder="Sélectionner un médecin...", width="100%"),
                    rx.select.content(
                        rx.foreach(DoctorScheduleState.schedulable_doctors, _doctor_option),
                    ),
                    value=DoctorScheduleState.form_doctor_id,
                    on_change=DoctorScheduleState.set_form_doctor,
                    width="100%",
                ),
                rx.text("Jours de la semaine *", size="2", weight="medium"),
                rx.hstack(
                    *[
                        rx.button(
                            label,
                            variant=rx.cond(DoctorScheduleState.form_days.contains(day_num), "solid", "soft"),
                            color_scheme=rx.cond(DoctorScheduleState.form_days.contains(day_num), "blue", "gray"),
                            size="2",
                            on_click=DoctorScheduleState.toggle_form_day(day_num),
                            border_radius="6px",
                        )
                        for day_num, label in [
                            (0, "Lu"), (1, "Ma"), (2, "Me"), (3, "Je"),
                            (4, "Ve"), (5, "Sa"), (6, "Di"),
                        ]
                    ],
                    spacing="1", width="100%", wrap="wrap",
                ),
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
                rx.text("Salle / Cabinet", size="2", weight="medium"),
                rx.input(
                    placeholder="Ex: Cabinet 1, Salle A...",
                    value=DoctorScheduleState.form_room,
                    on_change=DoctorScheduleState.set_form_room,
                    width="100%",
                ),
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


# ── Unavailability dialog ─────────────────────────────────────────────────────

def _unavail_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajouter une indisponibilité"),
            rx.vstack(
                rx.text("Médecin *", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(placeholder="Sélectionner un médecin...", width="100%"),
                    rx.select.content(
                        rx.foreach(DoctorScheduleState.schedulable_doctors, _doctor_option),
                    ),
                    value=DoctorScheduleState.unavail_form_doctor_id,
                    on_change=DoctorScheduleState.set_unavail_doctor,
                    width="100%",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Date de début *", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=DoctorScheduleState.unavail_form_date,
                            on_change=DoctorScheduleState.set_unavail_date,
                            width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Date de fin", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=DoctorScheduleState.unavail_form_date_end,
                            on_change=DoctorScheduleState.set_unavail_date_end,
                            width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    columns="2", spacing="3", width="100%",
                ),
                rx.text("Période", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(width="100%"),
                    rx.select.content(
                        rx.select.item("Journée entière", value="FULL"),
                        rx.select.item("Matin uniquement (avant 12h)", value="AM"),
                        rx.select.item("Après-midi uniquement (≥ 12h)", value="PM"),
                    ),
                    value=DoctorScheduleState.unavail_form_half_day,
                    on_change=DoctorScheduleState.set_unavail_half_day,
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
            max_width="480px",
        ),
        open=DoctorScheduleState.unavail_form_open,
    )


# ── Unavailability section ────────────────────────────────────────────────────

def _half_day_badge(half_day: str) -> rx.Component:
    return rx.match(
        half_day,
        ("AM", rx.badge("Matin", color_scheme="orange", variant="soft", size="1")),
        ("PM", rx.badge("Après-midi", color_scheme="orange", variant="soft", size="1")),
        rx.badge("Journée entière", color_scheme="red", variant="soft", size="1"),
    )


def _unavail_row(u: UnavailableDayDTO) -> rx.Component:
    return rx.hstack(
        rx.cond(
            (u.date_end != "") & (u.date_end != u.date),
            rx.badge(u.date + " → " + u.date_end, color_scheme="red", variant="soft", size="2"),
            rx.badge(u.date, color_scheme="red", variant="soft", size="2"),
        ),
        _half_day_badge(u.half_day),
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
            rx.heading("Indisponibilités", size="4"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14), "Ajouter",
                on_click=DoctorScheduleState.open_unavail_form,
                size="2", color_scheme="red", variant="soft",
            ),
            align="center", spacing="2", width="100%",
        ),
        rx.text("Les patients ne pourront pas réserver sur ces périodes.", size="2", color="var(--gray-9)"),
        rx.cond(
            DoctorScheduleState.filtered_unavail_days.length() > 0,
            rx.vstack(
                rx.foreach(DoctorScheduleState.filtered_unavail_days, _unavail_row),
                spacing="2", width="100%",
            ),
            rx.text("Aucune indisponibilité configurée.", size="2", color="var(--gray-7)"),
        ),
        spacing="3", width="100%",
        padding="1.25rem",
        border="1px solid var(--red-4)",
        border_radius="12px",
        background="var(--red-1)",
        margin_top="1.5rem",
    )


# ── Page ──────────────────────────────────────────────────────────────────────

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
                rx.icon("plus", size=16), "Ajouter un créneau",
                on_click=DoctorScheduleState.open_create_dialog,
                size="2",
            ),
            width="100%", align="center", spacing="3",
        ),
        # Filter bar: specialties + name search + doctor cards
        _filter_bar(),
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
