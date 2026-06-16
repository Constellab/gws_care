"""My Consultations page component for the patient portal (/my-consultations)."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .patient_consultations_state import (
    CalendarDayDTO,
    PatientConsultationRowDTO,
    PatientConsultationsState,
)


# ── Status badge ──────────────────────────────────────────────────────────────

def _status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("scheduled", rx.badge(LanguageState.tr["status_scheduled"], color_scheme="gray", variant="soft", size="1")),
        ("in_progress", rx.badge(LanguageState.tr["status_in_progress"], color_scheme="amber", variant="soft", size="1")),
        ("done", rx.badge(LanguageState.tr["status_done"], color_scheme="green", variant="soft", size="1")),
        ("cancelled", rx.badge(LanguageState.tr["status_cancelled"], color_scheme="red", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


# ── List view ─────────────────────────────────────────────────────────────────

def _consultation_row(row: PatientConsultationRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.cond(row.visit_number != "", rx.text(row.visit_number, size="2", weight="medium"), rx.text("—", size="2", color="var(--gray-7)"))
        ),
        rx.table.cell(
            rx.cond(row.account_name != "", rx.text(row.account_name, size="2"), rx.text("—", size="2", color="var(--gray-7)"))
        ),
        rx.table.cell(
            rx.cond(row.scheduled_at != "", rx.text(row.scheduled_at, size="2"), rx.text("—", size="2", color="var(--gray-7)"))
        ),
        rx.table.cell(_status_badge(row.status)),
        rx.table.cell(
            rx.cond(row.exam_count > 0, rx.badge(row.exam_count, color_scheme="blue", variant="soft", size="1"), rx.text("—", size="2", color="var(--gray-7)"))
        ),
        style={":hover": {"background_color": "var(--gray-2)", "cursor": "pointer"}},
        on_click=lambda: PatientConsultationsState.go_to_consultation(row.id),
    )


def _filters_bar() -> rx.Component:
    return rx.hstack(
        rx.select.root(
            rx.select.trigger(placeholder=LanguageState.tr["all_statuses"], width="180px"),
            rx.select.content(
                rx.select.item(LanguageState.tr["all_statuses"], value="ALL"),
                rx.select.item(LanguageState.tr["status_scheduled"], value="scheduled"),
                rx.select.item(LanguageState.tr["status_in_progress"], value="in_progress"),
                rx.select.item(LanguageState.tr["status_done"], value="done"),
                rx.select.item(LanguageState.tr["status_cancelled"], value="cancelled"),
            ),
            value=PatientConsultationsState.filter_status,
            on_change=PatientConsultationsState.set_filter_status,
            size="2",
        ),
        rx.input(type="date", value=PatientConsultationsState.filter_date_from,
                 on_change=PatientConsultationsState.set_filter_date_from, size="2"),
        rx.input(type="date", value=PatientConsultationsState.filter_date_to,
                 on_change=PatientConsultationsState.set_filter_date_to, size="2"),
        rx.spacer(),
        rx.button(rx.icon("x", size=14), LanguageState.tr["clear_btn"],
                  variant="outline", size="2", on_click=PatientConsultationsState.clear_filters),
        spacing="3", wrap="wrap", align="center", width="100%",
    )


def _list_view() -> rx.Component:
    return rx.cond(
        PatientConsultationsState.is_loading,
        rx.center(rx.spinner(size="3"), padding_y="4em"),
        rx.cond(
            PatientConsultationsState.error_message != "",
            rx.callout(PatientConsultationsState.error_message, icon="triangle-alert", color_scheme="red"),
            rx.cond(
                PatientConsultationsState.filtered_consultations.length() == 0,
                rx.center(
                    rx.vstack(
                        rx.icon("stethoscope", size=40, color="var(--gray-6)"),
                        rx.text(LanguageState.tr["no_my_consultations"], size="2", color="var(--gray-9)"),
                        spacing="2", align="center",
                    ),
                    padding="4rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="8px",
                    width="100%",
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(
                                rx.hstack(rx.text(LanguageState.tr["col_visit_number"], size="2"),
                                          rx.cond(PatientConsultationsState.sort_column == "visit_number",
                                                  rx.cond(PatientConsultationsState.sort_ascending, rx.icon("chevron-up", size=13, color="var(--accent-9)"), rx.icon("chevron-down", size=13, color="var(--accent-9)")),
                                                  rx.icon("chevrons-up-down", size=13, color="var(--gray-7)")),
                                          spacing="1", align="center"),
                                on_click=lambda: PatientConsultationsState.set_sort("visit_number"),
                                style={"cursor": "pointer"},
                            ),
                            rx.table.column_header_cell(
                                rx.hstack(rx.text(LanguageState.tr["col_account"], size="2"),
                                          rx.cond(PatientConsultationsState.sort_column == "account_name",
                                                  rx.cond(PatientConsultationsState.sort_ascending, rx.icon("chevron-up", size=13, color="var(--accent-9)"), rx.icon("chevron-down", size=13, color="var(--accent-9)")),
                                                  rx.icon("chevrons-up-down", size=13, color="var(--gray-7)")),
                                          spacing="1", align="center"),
                                on_click=lambda: PatientConsultationsState.set_sort("account_name"),
                                style={"cursor": "pointer"},
                            ),
                            rx.table.column_header_cell(
                                rx.hstack(rx.text(LanguageState.tr["col_scheduled"], size="2"),
                                          rx.cond(PatientConsultationsState.sort_column == "scheduled_at",
                                                  rx.cond(PatientConsultationsState.sort_ascending, rx.icon("chevron-up", size=13, color="var(--accent-9)"), rx.icon("chevron-down", size=13, color="var(--accent-9)")),
                                                  rx.icon("chevrons-up-down", size=13, color="var(--gray-7)")),
                                          spacing="1", align="center"),
                                on_click=lambda: PatientConsultationsState.set_sort("scheduled_at"),
                                style={"cursor": "pointer"},
                            ),
                            rx.table.column_header_cell(
                                rx.hstack(rx.text(LanguageState.tr["col_status"], size="2"),
                                          rx.cond(PatientConsultationsState.sort_column == "status",
                                                  rx.cond(PatientConsultationsState.sort_ascending, rx.icon("chevron-up", size=13, color="var(--accent-9)"), rx.icon("chevron-down", size=13, color="var(--accent-9)")),
                                                  rx.icon("chevrons-up-down", size=13, color="var(--gray-7)")),
                                          spacing="1", align="center"),
                                on_click=lambda: PatientConsultationsState.set_sort("status"),
                                style={"cursor": "pointer"},
                            ),
                            rx.table.column_header_cell(rx.text(LanguageState.tr["tab_exams"], size="2")),
                        )
                    ),
                    rx.table.body(rx.foreach(PatientConsultationsState.filtered_consultations, _consultation_row)),
                    width="100%", variant="surface",
                ),
            ),
        ),
    )


# ── Calendar view ─────────────────────────────────────────────────────────────

def _cal_pill(visit: PatientConsultationRowDTO) -> rx.Component:
    bg = rx.match(
        visit.status,
        ("scheduled", "var(--gray-3)"),
        ("in_progress", "var(--amber-3)"),
        ("done", "var(--green-3)"),
        ("cancelled", "var(--red-3)"),
        "var(--gray-3)",
    )
    color = rx.match(
        visit.status,
        ("scheduled", "var(--gray-11)"),
        ("in_progress", "var(--amber-11)"),
        ("done", "var(--green-11)"),
        ("cancelled", "var(--red-11)"),
        "var(--gray-11)",
    )
    return rx.box(
        rx.text(
            rx.cond(visit.scheduled_at != "", visit.scheduled_at[11:16] + " ", ""),
            rx.cond(visit.account_name != "", visit.account_name, visit.visit_number),
            size="1", color=color,
            overflow="hidden", text_overflow="ellipsis", white_space="nowrap",
        ),
        background=bg,
        border_radius="3px",
        padding="1px 4px",
        width="100%",
        overflow="hidden",
        cursor="pointer",
        on_click=lambda: PatientConsultationsState.go_to_consultation(visit.id),
    )


def _cal_day_cell(day: CalendarDayDTO) -> rx.Component:
    return rx.box(
        rx.cond(
            day.day_num > 0,
            rx.vstack(
                rx.box(
                    rx.text(
                        day.day_num, size="1",
                        weight=rx.cond(day.is_today, "bold", "regular"),
                        color=rx.cond(day.is_today, "white", "var(--gray-11)"),
                        text_align="center", line_height="1.4rem", width="1.4rem",
                    ),
                    border_radius="50%",
                    background=rx.cond(day.is_today, "var(--accent-9)", "transparent"),
                    width="fit-content",
                ),
                rx.vstack(
                    rx.foreach(day.visits, _cal_pill),
                    spacing="1", width="100%", overflow="hidden",
                ),
                spacing="1", width="100%", align="start",
            ),
            rx.fragment(),
        ),
        min_height="80px",
        border="1px solid var(--gray-4)",
        padding="4px",
        background=rx.cond(day.is_current_month, "var(--gray-1)", "var(--gray-2)"),
        overflow="hidden",
    )


def _calendar_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon_button(rx.icon("chevron-left", size=16), variant="ghost", size="2",
                           on_click=PatientConsultationsState.calendar_prev_month),
            rx.text(PatientConsultationsState.calendar_month_label, size="4", weight="medium",
                    min_width="180px", text_align="center"),
            rx.icon_button(rx.icon("chevron-right", size=16), variant="ghost", size="2",
                           on_click=PatientConsultationsState.calendar_next_month),
            spacing="2", align="center", justify="center", width="100%",
        ),
        rx.grid(
            rx.text(LanguageState.tr["cal_mon"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_tue"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_wed"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_thu"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_fri"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_sat"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_sun"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            columns="7", width="100%",
        ),
        rx.grid(
            rx.foreach(PatientConsultationsState.calendar_days, _cal_day_cell),
            columns="7", width="100%",
        ),
        width="100%", spacing="2",
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def patient_consultations_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.hstack(
                rx.heading(LanguageState.tr["my_consultations_title"], size="6"),
                rx.spacer(),
                rx.segmented_control.root(
                    rx.segmented_control.item(rx.icon("list", size=15), value="list"),
                    rx.segmented_control.item(rx.icon("calendar-days", size=15), value="calendar"),
                    value=PatientConsultationsState.view_mode,
                    on_change=PatientConsultationsState.set_view_mode,
                ),
                width="100%",
                align="center",
            ),
            _filters_bar(),
            rx.cond(
                PatientConsultationsState.view_mode == "list",
                _list_view(),
                rx.cond(
                    PatientConsultationsState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="3rem"),
                    _calendar_view(),
                ),
            ),
        )
    )
