"""Appointment list page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .appointment_form_component import appointment_form_dialog
from .appointment_form_state import AppointmentFormState
from .appointment_list_state import (
    AccountOptionDTO,
    AppointmentListState,
    AppointmentRowDTO,
    CalendarDayDTO,
)


def _status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("SCHEDULED", rx.badge(LanguageState.tr["status_scheduled"], color_scheme="blue", variant="soft", size="1")),
        ("IN_PROGRESS", rx.badge(LanguageState.tr["status_in_progress"], color_scheme="orange", variant="soft", size="1")),
        ("DONE", rx.badge(LanguageState.tr["status_done"], color_scheme="green", variant="soft", size="1")),
        ("CANCELLED", rx.badge(LanguageState.tr["status_cancelled"], color_scheme="gray", variant="soft", size="1")),
        ("campaign", rx.badge("Inscrit", color_scheme="blue", variant="surface", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _appointment_row(appt: AppointmentRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.link(
                appt.patient_name,
                on_click=lambda: AppointmentListState.go_to_patient(appt.patient_id),
                cursor="pointer",
                size="2",
            )
        ),
        rx.table.cell(
            rx.cond(
                appt.campaign_name,
                rx.hstack(
                    rx.badge(appt.campaign_name, color_scheme="purple", variant="soft", size="1"),
                    spacing="1",
                ),
                rx.cond(
                    appt.account_name,
                    rx.text(appt.account_name, size="2"),
                    rx.text("—", size="2", color="var(--gray-7)"),
                ),
            )
        ),
        rx.table.cell(rx.text(appt.scheduled_at[:16].replace("T", " "), size="2")),
        rx.table.cell(rx.text(appt.exam_type_label, size="2")),
        rx.table.cell(_status_badge(appt.status)),
        rx.table.cell(
            rx.hstack(
                # Edit button — only for SCHEDULED
                rx.cond(
                    appt.status == "SCHEDULED",
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("pencil", size=14),
                            variant="ghost",
                            size="1",
                            on_click=lambda: AppointmentFormState.open_edit_dialog(appt.id),
                        ),
                        content=LanguageState.tr["tooltip_edit_appt"],
                    ),
                ),
                # Start button — SCHEDULED → IN_PROGRESS
                rx.cond(
                    appt.status == "SCHEDULED",
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("play", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="orange",
                            on_click=lambda: AppointmentListState.start_appointment(appt.id),
                        ),
                        content=LanguageState.tr["tooltip_start_appt"],
                    ),
                ),
                # Complete button — IN_PROGRESS → DONE
                rx.cond(
                    appt.status == "IN_PROGRESS",
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("check", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="green",
                            on_click=lambda: AppointmentListState.complete_appointment(appt.id),
                        ),
                        content=LanguageState.tr["tooltip_done_appt"],
                    ),
                ),
                # Exam sheet button — IN_PROGRESS or DONE
                rx.cond(
                    (appt.status == "IN_PROGRESS") | (appt.status == "DONE"),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("clipboard-list", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="blue",
                            on_click=lambda: AppointmentListState.go_to_or_create_exam(appt.id),
                        ),
                        content=rx.cond(
                            appt.linked_exam_id != "",
                            "View exam file",
                            "Create exam file",
                        ),
                    ),
                ),
                # Cancel button — SCHEDULED or IN_PROGRESS
                rx.cond(
                    (appt.status == "SCHEDULED") | (appt.status == "IN_PROGRESS"),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("ban", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="red",
                            on_click=lambda: AppointmentListState.cancel_appointment(appt.id),
                        ),
                        content=LanguageState.tr["tooltip_cancel_appt"],
                    ),
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _account_filter_option(account: AccountOptionDTO) -> rx.Component:
    return rx.select.item(account.name, value=account.id)


def _sortable_header(label: str, column: str) -> rx.Component:
    """Column header cell with a sort-direction arrow."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                AppointmentListState.sort_column == column,
                rx.cond(
                    AppointmentListState.sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: AppointmentListState.set_sort(column),
        style={"cursor": "pointer"},
    )


# ── Calendar view ─────────────────────────────────────────────────────────────

def _cal_appt_pill(appt: AppointmentRowDTO) -> rx.Component:
    """Compact appointment chip for a calendar day cell."""
    bg = rx.match(
        appt.status,
        ("SCHEDULED", "var(--blue-3)"),
        ("IN_PROGRESS", "var(--orange-3)"),
        ("DONE", "var(--green-3)"),
        ("CANCELLED", "var(--gray-3)"),
        "var(--gray-3)",
    )
    color = rx.match(
        appt.status,
        ("SCHEDULED", "var(--blue-11)"),
        ("IN_PROGRESS", "var(--orange-11)"),
        ("DONE", "var(--green-11)"),
        ("CANCELLED", "var(--gray-9)"),
        "var(--gray-9)",
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
        on_click=lambda: AppointmentListState.go_to_patient(appt.patient_id),
    )


def _cal_day_cell(day: CalendarDayDTO) -> rx.Component:
    """One cell in the monthly calendar grid."""
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
    """Monthly calendar grid of appointments."""
    _DAY_HEADERS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return rx.vstack(
        # Month navigation
        rx.hstack(
            rx.icon_button(
                rx.icon("chevron-left", size=16),
                variant="ghost",
                size="2",
                on_click=AppointmentListState.calendar_prev_month,
            ),
            rx.text(
                AppointmentListState.calendar_month_label,
                size="4",
                weight="medium",
                min_width="180px",
                text_align="center",
            ),
            rx.icon_button(
                rx.icon("chevron-right", size=16),
                variant="ghost",
                size="2",
                on_click=AppointmentListState.calendar_next_month,
            ),
            spacing="2",
            align="center",
            justify="center",
            width="100%",
        ),
        # Weekday header row
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
        # Day cells
        rx.grid(
            rx.foreach(AppointmentListState.calendar_days, _cal_day_cell),
            columns="7",
            width="100%",
        ),
        width="100%",
        spacing="2",
    )


def appointment_list_page() -> rx.Component:
    """Appointment list page with filters and action buttons."""
    return main_component(
        page_layout(
            appointment_form_dialog(),
            rx.hstack(
                rx.heading(LanguageState.tr["appointments_page_title"], size="6"),
                rx.spacer(),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("calendar-clock", size=16),
                        variant="soft", size="2", color_scheme="gray",
                        on_click=rx.redirect("/schedule"),
                    ),
                    content="View doctor availability",
                ),
                rx.segmented_control.root(
                    rx.segmented_control.item(rx.icon("list", size=15), value="list"),
                    rx.segmented_control.item(rx.icon("calendar-days", size=15), value="calendar"),
                    value=AppointmentListState.view_mode,
                    on_change=AppointmentListState.set_view_mode,
                    size="1",
                ),
                rx.button(
                    rx.icon("plus", size=16),
                    LanguageState.tr["new_appointment_page_btn"],
                    on_click=AppointmentFormState.open_create_dialog_standalone,
                    size="2",
                ),
                width="100%",
                align="center",
                spacing="3",
            ),
            # Patient context banner — shown when navigated from a patient page
            rx.cond(
                AppointmentListState.patient_context_id != "",
                rx.callout(
                    rx.hstack(
                        rx.icon("user", size=14),
                        rx.text(
                            "Affichage des rendez-vous de\u00a0: ",
                            rx.text.strong(AppointmentListState.patient_context_name),
                            size="2",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=13),
                            "Voir tous les rendez-vous",
                            on_click=AppointmentListState.clear_patient_context,
                            variant="ghost",
                            size="1",
                            color_scheme="gray",
                        ),
                        width="100%",
                        align="center",
                        spacing="2",
                    ),
                    icon="info",
                    color_scheme="blue",
                    size="1",
                ),
            ),
            # Doctor view banner
            rx.cond(
                AppointmentListState.is_doctor_view,
                rx.callout(
                    rx.hstack(
                        rx.icon("stethoscope", size=14),
                        rx.text("Affichage de vos rendez-vous uniquement", size="2"),
                        width="100%",
                        align="center",
                        spacing="2",
                    ),
                    icon="info",
                    color_scheme="teal",
                    size="1",
                ),
            ),
            # Filters
            rx.vstack(
                rx.hstack(
                    rx.input(
                        placeholder=LanguageState.tr["search_patient_placeholder"],
                        value=AppointmentListState.search,
                        on_change=AppointmentListState.set_search,
                        size="2",
                        max_width="260px",
                    ),
                    rx.select.root(
                        rx.select.trigger(placeholder=LanguageState.tr["all_statuses"]),
                        rx.select.content(
                            rx.select.item(LanguageState.tr["all_statuses"], value="ALL"),
                            rx.select.item(LanguageState.tr["status_scheduled"], value="SCHEDULED"),
                            rx.select.item(LanguageState.tr["status_in_progress"], value="IN_PROGRESS"),
                            rx.select.item(LanguageState.tr["status_done"], value="DONE"),
                            rx.select.item(LanguageState.tr["status_cancelled"], value="CANCELLED"),
                        ),
                        value=AppointmentListState.filter_status,
                        on_change=AppointmentListState.set_filter_status,
                        size="2",
                    ),
                    rx.select.root(
                        rx.select.trigger(placeholder=LanguageState.tr["all_accounts"]),
                        rx.select.content(
                            rx.select.item(LanguageState.tr["all_accounts"], value="ALL"),
                            rx.foreach(AppointmentListState.companies, _account_filter_option),
                        ),
                        value=AppointmentListState.filter_account_id,
                        on_change=AppointmentListState.set_filter_account,
                        size="2",
                    ),
                    spacing="3",
                    wrap="wrap",
                    width="100%",
                ),
                # Date range — only relevant in list mode
                rx.cond(
                    AppointmentListState.view_mode == "list",
                    rx.hstack(
                        rx.text(LanguageState.tr["date_filter_label"], size="2", color="var(--gray-9)", white_space="nowrap"),
                        rx.input(
                            type="date",
                            value=AppointmentListState.filter_date_from,
                            on_change=AppointmentListState.set_filter_date_from,
                            size="2",
                        ),
                        rx.text(LanguageState.tr["date_range_arrow"], size="2", color="var(--gray-9)"),
                        rx.input(
                            type="date",
                            value=AppointmentListState.filter_date_to,
                            on_change=AppointmentListState.set_filter_date_to,
                            size="2",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=14),
                            LanguageState.tr["clear_btn"],
                            on_click=AppointmentListState.clear_filters,
                            variant="outline",
                            size="2",
                        ),
                        spacing="2",
                        align="center",
                        wrap="wrap",
                        width="100%",
                    ),
                    # Calendar mode: show clear button without date pickers
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=14),
                            LanguageState.tr["clear_btn"],
                            on_click=AppointmentListState.clear_filters,
                            variant="outline",
                            size="2",
                        ),
                        width="100%",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            # Error
            rx.cond(
                AppointmentListState.error_message != "",
                rx.callout(
                    AppointmentListState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            # List or Calendar
            rx.cond(
                AppointmentListState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    AppointmentListState.view_mode == "list",
                    # ── List view ──
                    rx.cond(
                        AppointmentListState.appointments,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    _sortable_header(LanguageState.tr["col_patient"], "patient_name"),
                                    _sortable_header(LanguageState.tr["col_account"], "account_name"),
                                    _sortable_header(LanguageState.tr["col_scheduled"], "scheduled_at"),
                                    _sortable_header(LanguageState.tr["col_exam_type"], "exam_type_label"),
                                    _sortable_header(LanguageState.tr["col_status"], "status"),
                                    rx.table.column_header_cell(""),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(AppointmentListState.appointments, _appointment_row),
                            ),
                            width="100%",
                            variant="surface",
                        ),
                        rx.center(
                            rx.text(LanguageState.tr["no_appointments_found"], size="2", color="var(--gray-8)"),
                            padding="3rem",
                        ),
                    ),
                    # ── Calendar view ──
                    _calendar_view(),
                ),
            ),
            # ── Pagination (list mode only) ─────────────────────────────
            rx.cond(
                (AppointmentListState.view_mode == "list")
                & (AppointmentListState.total_count > 0)
                & ~AppointmentListState.patient_context_id.bool(),
                rx.hstack(
                    rx.text(
                        AppointmentListState.total_count.to(str)
                        + " rendez-vous — page ",
                        AppointmentListState.page.to(str),
                        " / ",
                        AppointmentListState.total_pages.to(str),
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("chevron-left", size=14),
                        on_click=AppointmentListState.prev_page,
                        variant="soft",
                        size="2",
                        disabled=~AppointmentListState.has_prev_page,
                    ),
                    rx.button(
                        rx.icon("chevron-right", size=14),
                        on_click=AppointmentListState.next_page,
                        variant="soft",
                        size="2",
                        disabled=~AppointmentListState.has_next_page,
                    ),
                    width="100%",
                    align="center",
                    padding_top="0.5rem",
                ),
            ),
        )
    )
