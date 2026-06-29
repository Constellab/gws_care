"""Appointments list page component — scheduling view of consultation visits."""

import reflex as rx
from gws_reflex_main import main_component

from ..appointment_list.appointment_form_component import appointment_form_dialog
from ..appointment_list.appointment_form_state import AppointmentFormState
from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .appointments_list_state import (
    AppointmentRowDTO,
    AppointmentsListState,
    CalendarDayDTO,
)


def _status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("scheduled", rx.badge(LanguageState.tr["appt_status_scheduled"], color_scheme="blue", variant="soft", size="1")),
        ("in_progress", rx.badge(LanguageState.tr["appt_status_in_progress"], color_scheme="amber", variant="soft", size="1")),
        ("done", rx.badge(LanguageState.tr["appt_status_done"], color_scheme="green", variant="soft", size="1")),
        ("cancelled", rx.badge(LanguageState.tr["appt_status_cancelled"], color_scheme="red", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _mode_badge(mode: str) -> rx.Component:
    return rx.match(
        mode,
        ("at_work", rx.badge(LanguageState.tr["appt_mode_at_work"], color_scheme="blue", variant="soft", size="1")),
        ("at_home", rx.badge(LanguageState.tr["appt_mode_at_home"], color_scheme="green", variant="soft", size="1")),
        ("address", rx.badge(LanguageState.tr["appt_mode_address"], color_scheme="orange", variant="soft", size="1")),
        ("visio", rx.badge(LanguageState.tr["appt_mode_visio"], color_scheme="purple", variant="soft", size="1")),
        ("hospital", rx.badge(LanguageState.tr["appt_mode_hospital"], color_scheme="teal", variant="soft", size="1")),
        rx.fragment(),
    )


def _sortable_header(label: str, column: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                AppointmentsListState.sort_column == column,
                rx.cond(
                    AppointmentsListState.sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: AppointmentsListState.set_sort(column),
        style={"cursor": "pointer"},
    )


def _appointment_row(appt: AppointmentRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.cond(
                appt.visit_number,
                rx.text(appt.visit_number, size="2", weight="medium"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.link(
                appt.patient_name,
                on_click=lambda: AppointmentsListState.go_to_patient(appt.patient_id),
                cursor="pointer",
                size="2",
            )
        ),
        rx.table.cell(
            rx.cond(
                appt.scheduled_at,
                rx.text(appt.scheduled_at[:16].replace("T", " "), size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                appt.appointment_mode != "",
                _mode_badge(appt.appointment_mode),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                appt.doctor_name != "",
                rx.text(appt.doctor_name, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(_status_badge(appt.status)),
        _hover={"background": "var(--gray-2)", "cursor": "pointer"},
        on_click=lambda: AppointmentsListState.go_to_appointment(appt.id),
    )


# ── Calendar view ─────────────────────────────────────────────────────────────

def _cal_appt_pill(appt: AppointmentRowDTO) -> rx.Component:
    bg = rx.match(
        appt.status,
        ("scheduled", "var(--blue-3)"),
        ("in_progress", "var(--amber-3)"),
        ("done", "var(--green-3)"),
        ("cancelled", "var(--red-3)"),
        "var(--gray-3)",
    )
    color = rx.match(
        appt.status,
        ("scheduled", "var(--blue-11)"),
        ("in_progress", "var(--amber-11)"),
        ("done", "var(--green-11)"),
        ("cancelled", "var(--red-11)"),
        "var(--gray-11)",
    )
    return rx.box(
        rx.text(
            appt.scheduled_at[11:16] + " " + appt.patient_name,
            size="1",
            color=color,
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        background=bg,
        border_radius="3px",
        padding="1px 4px",
        width="100%",
        overflow="hidden",
        cursor="pointer",
        on_click=lambda: AppointmentsListState.go_to_appointment(appt.id),
    )


def _cal_day_cell(day: CalendarDayDTO) -> rx.Component:
    return rx.box(
        rx.cond(
            day.day_num > 0,
            rx.vstack(
                rx.box(
                    rx.text(
                        day.day_num,
                        size="1",
                        weight=rx.cond(day.is_today, "bold", "regular"),
                        color=rx.cond(day.is_today, "white", "var(--gray-11)"),
                        text_align="center",
                        line_height="1.4rem",
                        width="1.4rem",
                    ),
                    border_radius="50%",
                    background=rx.cond(day.is_today, "var(--accent-9)", "transparent"),
                    width="fit-content",
                ),
                rx.vstack(
                    rx.foreach(day.appointments, _cal_appt_pill),
                    spacing="1",
                    width="100%",
                    overflow="hidden",
                ),
                spacing="1",
                width="100%",
                align="start",
            ),
            rx.fragment(),
        ),
        min_height="90px",
        border="1px solid var(--gray-4)",
        padding="4px",
        background=rx.cond(day.is_current_month, "var(--gray-1)", "var(--gray-2)"),
        overflow="hidden",
    )


def _calendar_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon_button(
                rx.icon("chevron-left", size=16),
                variant="ghost",
                size="2",
                on_click=AppointmentsListState.calendar_prev_month,
            ),
            rx.text(
                AppointmentsListState.calendar_month_label,
                size="4",
                weight="medium",
                min_width="180px",
                text_align="center",
            ),
            rx.icon_button(
                rx.icon("chevron-right", size=16),
                variant="ghost",
                size="2",
                on_click=AppointmentsListState.calendar_next_month,
            ),
            spacing="2",
            align="center",
            justify="center",
            width="100%",
        ),
        rx.grid(
            rx.text(LanguageState.tr["cal_mon"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_tue"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_wed"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_thu"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_fri"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_sat"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_sun"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            columns="7",
            width="100%",
        ),
        rx.grid(
            rx.foreach(AppointmentsListState.calendar_days, _cal_day_cell),
            columns="7",
            width="100%",
        ),
        width="100%",
        spacing="2",
    )


def appointments_list_page() -> rx.Component:
    """Appointments scheduling page — consultation visits with scheduling focus."""
    return main_component(
        page_layout(
            appointment_form_dialog(),
            rx.hstack(
                rx.heading(LanguageState.tr["appointments_page_title"], size="6"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    LanguageState.tr["new_appointment_page_btn"],
                    on_click=AppointmentFormState.open_create_dialog_standalone,
                    size="2",
                ),
                rx.segmented_control.root(
                    rx.segmented_control.item(rx.icon("list", size=15), value="list"),
                    rx.segmented_control.item(rx.icon("calendar-days", size=15), value="calendar"),
                    value=AppointmentsListState.view_mode,
                    on_change=AppointmentsListState.set_view_mode,
                    size="1",
                ),
                width="100%",
                align="center",
                spacing="3",
            ),
            # Filter bar
            rx.vstack(
                rx.hstack(
                    rx.select.root(
                        rx.select.trigger(placeholder=LanguageState.tr["col_mode"], size="2", width="140px"),
                        rx.select.content(
                            rx.select.item(LanguageState.tr["all_modes_option"], value="ALL"),
                            rx.select.item(LanguageState.tr["appt_mode_at_work"], value="at_work"),
                            rx.select.item(LanguageState.tr["appt_mode_at_home"], value="at_home"),
                            rx.select.item(LanguageState.tr["appt_mode_address"], value="address"),
                            rx.select.item(LanguageState.tr["appt_mode_visio"], value="visio"),
                            rx.select.item(LanguageState.tr["appt_mode_hospital"], value="hospital"),
                        ),
                        value=rx.cond(AppointmentsListState.filter_mode != "", AppointmentsListState.filter_mode, "ALL"),
                        on_change=AppointmentsListState.set_filter_mode,
                        size="2",
                    ),
                    rx.cond(
                        AppointmentsListState.doctor_options.length() > 0,
                        rx.select.root(
                            rx.select.trigger(placeholder=LanguageState.tr["col_doctor"], size="2", width="180px"),
                            rx.select.content(
                                rx.select.item(LanguageState.tr["all_doctors_option"], value="ALL"),
                                rx.foreach(
                                    AppointmentsListState.doctor_options,
                                    lambda d: rx.select.item(d, value=d),
                                ),
                            ),
                            value=rx.cond(AppointmentsListState.filter_doctor != "", AppointmentsListState.filter_doctor, "ALL"),
                            on_change=AppointmentsListState.set_filter_doctor,
                            size="2",
                        ),
                    ),
                    rx.select.root(
                        rx.select.trigger(placeholder=LanguageState.tr["all_statuses"], size="2", width="180px"),
                        rx.select.content(
                            rx.select.item(LanguageState.tr["all_statuses"], value="ALL"),
                            rx.select.item(LanguageState.tr["appt_status_scheduled"], value="scheduled"),
                            rx.select.item(LanguageState.tr["appt_status_in_progress"], value="in_progress"),
                            rx.select.item(LanguageState.tr["appt_status_done"], value="done"),
                            rx.select.item(LanguageState.tr["appt_status_cancelled"], value="cancelled"),
                        ),
                        value=rx.cond(AppointmentsListState.filter_status != "", AppointmentsListState.filter_status, "ALL"),
                        on_change=AppointmentsListState.set_filter_status,
                        size="2",
                    ),
                    spacing="3",
                    wrap="wrap",
                    width="100%",
                    align="center",
                ),
                # Date range — list mode only
                rx.cond(
                    AppointmentsListState.view_mode == "list",
                    rx.hstack(
                        rx.input(
                            type="date",
                            value=AppointmentsListState.filter_from,
                            on_change=AppointmentsListState.set_filter_from,
                            size="2",
                            width="140px",
                            placeholder=LanguageState.tr["placeholder_date_from"],
                        ),
                        rx.text(LanguageState.tr["date_range_arrow"], size="2", color="var(--gray-9)"),
                        rx.input(
                            type="date",
                            value=AppointmentsListState.filter_to,
                            on_change=AppointmentsListState.set_filter_to,
                            size="2",
                            width="140px",
                            placeholder=LanguageState.tr["placeholder_date_to"],
                        ),
                        rx.spacer(),
                        rx.tooltip(
                            rx.icon_button(
                                rx.icon("x", size=14),
                                on_click=AppointmentsListState.clear_filters,
                                variant="ghost",
                                color_scheme="gray",
                                size="2",
                            ),
                            content=LanguageState.tr["clear_filters_tooltip"],
                        ),
                        spacing="3",
                        wrap="wrap",
                        width="100%",
                        align="center",
                    ),
                    rx.hstack(
                        rx.spacer(),
                        rx.tooltip(
                            rx.icon_button(
                                rx.icon("x", size=14),
                                on_click=AppointmentsListState.clear_filters,
                                variant="ghost",
                                color_scheme="gray",
                                size="2",
                            ),
                            content=LanguageState.tr["clear_filters_tooltip"],
                        ),
                        width="100%",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            rx.cond(
                AppointmentsListState.error_message != "",
                rx.callout(
                    AppointmentsListState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                AppointmentsListState.is_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    AppointmentsListState.view_mode == "list",
                    # ── List view ──
                    rx.cond(
                        AppointmentsListState.filtered_sorted_appointments,
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        _sortable_header(LanguageState.tr["col_visit_number"], "visit_number"),
                                        _sortable_header(LanguageState.tr["col_patient"], "patient_name"),
                                        _sortable_header(LanguageState.tr["col_scheduled"], "scheduled_at"),
                                        _sortable_header(LanguageState.tr["col_mode"], "appointment_mode"),
                                        _sortable_header(LanguageState.tr["col_doctor"], "doctor_name"),
                                        _sortable_header(LanguageState.tr["col_status"], "status"),
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(
                                        AppointmentsListState.filtered_sorted_appointments,
                                        _appointment_row,
                                    )
                                ),
                                width="100%",
                                variant="surface",
                            ),
                            overflow_x="auto",
                            width="100%",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("calendar-x", size=40, color="var(--gray-6)"),
                                rx.text(LanguageState.tr["no_appointments_found"], color="var(--gray-9)", size="2"),
                                align="center",
                                spacing="2",
                            ),
                            padding="4rem",
                            border="1px dashed var(--gray-5)",
                            border_radius="8px",
                            width="100%",
                        ),
                    ),
                    # ── Calendar view ──
                    _calendar_view(),
                ),
            ),
        ),
    )
