"""Patient appointments page — list + calendar view with "Plan Appointment" dialog."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .patient_appointments_state import (
    AppointmentRowDTO,
    CalendarDayDTO,
    DoctorOptionDTO,
    PatientAppointmentsState,
)


# ── Status badge ──────────────────────────────────────────────────────────────

def _status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("scheduled", rx.badge(LanguageState.tr["appt_status_scheduled"], color_scheme="blue", variant="soft", size="1")),
        ("in_progress", rx.badge(LanguageState.tr["appt_status_in_progress"], color_scheme="amber", variant="soft", size="1")),
        ("done", rx.badge(LanguageState.tr["appt_status_done"], color_scheme="green", variant="soft", size="1")),
        ("cancelled", rx.badge(LanguageState.tr["appt_status_cancelled"], color_scheme="red", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _mode_icon(mode: str) -> rx.Component:
    return rx.match(
        mode,
        ("onsite", rx.icon("building-2", size=13, color="var(--gray-9)")),
        ("visio", rx.icon("video", size=13, color="var(--blue-9)")),
        ("hospital", rx.icon("hospital", size=13, color="var(--purple-9)")),
        rx.icon("calendar", size=13, color="var(--gray-9)"),
    )


# ── List view ─────────────────────────────────────────────────────────────────

def _appt_row(appt: AppointmentRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.cond(
                appt.scheduled_at,
                rx.text(appt.scheduled_at[:16].replace("T", " "), size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.hstack(
                _mode_icon(appt.appointment_mode),
                rx.text(appt.appointment_mode_label, size="2"),
                spacing="1",
                align="center",
            )
        ),
        rx.table.cell(
            rx.cond(
                appt.doctor_name,
                rx.text(appt.doctor_name, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(_status_badge(appt.status)),
        style={":hover": {"background_color": "var(--gray-2)", "cursor": "pointer"}},
        on_click=lambda: PatientAppointmentsState.go_to_consultation(appt.id),
    )


def _list_view() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell(LanguageState.tr["col_date"], size="2"),
                rx.table.column_header_cell(LanguageState.tr["appt_mode"], size="2"),
                rx.table.column_header_cell(LanguageState.tr["appt_doctor"], size="2"),
                rx.table.column_header_cell(LanguageState.tr["col_status"], size="2"),
            )
        ),
        rx.table.body(
            rx.foreach(PatientAppointmentsState.appointments, _appt_row)
        ),
        width="100%",
        variant="surface",
    )


# ── Calendar view ─────────────────────────────────────────────────────────────

def _cal_pill(appt: AppointmentRowDTO) -> rx.Component:
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
            appt.scheduled_at[11:16],
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
        on_click=lambda: PatientAppointmentsState.go_to_consultation(appt.id),
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
                    rx.foreach(day.visits, _cal_pill),
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
                           on_click=PatientAppointmentsState.calendar_prev_month),
            rx.text(PatientAppointmentsState.calendar_month_label, size="4", weight="medium",
                    min_width="180px", text_align="center"),
            rx.icon_button(rx.icon("chevron-right", size=16), variant="ghost", size="2",
                           on_click=PatientAppointmentsState.calendar_next_month),
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
            rx.foreach(PatientAppointmentsState.calendar_days, _cal_day_cell),
            columns="7", width="100%",
        ),
        width="100%", spacing="2",
    )


# ── Booking dialog ────────────────────────────────────────────────────────────

def _doctor_option(doctor: DoctorOptionDTO) -> rx.Component:
    return rx.select.item(
        doctor.name,
        value=doctor.id,
    )


def _booking_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["appt_book_title"]),
            rx.dialog.description(LanguageState.tr["appt_book_desc"]),
            rx.vstack(
                # Date & time
                rx.vstack(
                    rx.text(LanguageState.tr["appt_date_label"], size="2", weight="medium"),
                    rx.input(
                        type="datetime-local",
                        value=PatientAppointmentsState.booking_scheduled_at,
                        on_change=PatientAppointmentsState.set_booking_scheduled_at,
                        min=PatientAppointmentsState.booking_min_datetime,
                        size="2",
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                # Doctor (optional)
                rx.vstack(
                    rx.text(LanguageState.tr["appt_doctor_label"], size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder=LanguageState.tr["appt_doctor_placeholder"],
                            width="100%",
                        ),
                        rx.select.content(
                            rx.select.item("— No preference —", value="none"),
                            rx.foreach(PatientAppointmentsState.doctor_options, _doctor_option),
                        ),
                        value=PatientAppointmentsState.booking_doctor_id,
                        on_change=PatientAppointmentsState.set_booking_doctor_id,
                        size="2",
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                # Mode
                rx.vstack(
                    rx.text(LanguageState.tr["appt_mode_label"], size="2", weight="medium"),
                    rx.radio_group.root(
                        rx.hstack(
                            rx.radio_group.item(value="onsite"),
                            rx.hstack(rx.icon("building-2", size=13), rx.text(LanguageState.tr["appt_mode_onsite"], size="2"), spacing="1", align="center"),
                            rx.radio_group.item(value="visio"),
                            rx.hstack(rx.icon("video", size=13), rx.text(LanguageState.tr["appt_mode_visio"], size="2"), spacing="1", align="center"),
                            rx.radio_group.item(value="hospital"),
                            rx.hstack(rx.icon("hospital", size=13), rx.text(LanguageState.tr["appt_mode_hospital"], size="2"), spacing="1", align="center"),
                            spacing="2",
                            align="center",
                            wrap="wrap",
                        ),
                        value=PatientAppointmentsState.booking_mode,
                        on_change=PatientAppointmentsState.set_booking_mode,
                    ),
                    spacing="1", width="100%",
                ),
                # Notes
                rx.vstack(
                    rx.text(LanguageState.tr["appt_notes_label"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=LanguageState.tr["appt_notes_placeholder"],
                        value=PatientAppointmentsState.booking_notes,
                        on_change=PatientAppointmentsState.set_booking_notes,
                        rows="3",
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                # Error
                rx.cond(
                    PatientAppointmentsState.booking_error,
                    rx.callout(
                        PatientAppointmentsState.booking_error,
                        icon="alert-circle",
                        color_scheme="red",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                # Buttons
                rx.hstack(
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="outline",
                        color_scheme="gray",
                        on_click=PatientAppointmentsState.close_booking_dialog,
                    ),
                    rx.button(
                        rx.cond(
                            PatientAppointmentsState.booking_is_saving,
                            rx.spinner(size="2"),
                            rx.hstack(
                                rx.icon("calendar-plus", size=14),
                                rx.text(LanguageState.tr["appt_book_submit"]),
                                spacing="1",
                            ),
                        ),
                        on_click=PatientAppointmentsState.submit_booking,
                        disabled=PatientAppointmentsState.booking_is_saving,
                        color_scheme="teal",
                    ),
                    justify="end",
                    width="100%",
                    spacing="3",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="520px",
        ),
        open=PatientAppointmentsState.show_booking_dialog,
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def patient_appointments_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                # Header row
                rx.hstack(
                    rx.heading(LanguageState.tr["nav_my_appointments"], size="6"),
                    rx.spacer(),
                    # View toggle
                    rx.segmented_control.root(
                        rx.segmented_control.item(rx.icon("list", size=15), value="list"),
                        rx.segmented_control.item(rx.icon("calendar-days", size=15), value="calendar"),
                        value=PatientAppointmentsState.view_mode,
                        on_change=PatientAppointmentsState.set_view_mode,
                    ),
                    # Book button
                    rx.button(
                        rx.icon("calendar-plus", size=14),
                        LanguageState.tr["appt_plan_btn"],
                        on_click=PatientAppointmentsState.open_booking_dialog,
                        color_scheme="teal",
                        size="2",
                    ),
                    width="100%",
                    align="center",
                    spacing="3",
                    wrap="wrap",
                ),
                # Error
                rx.cond(
                    PatientAppointmentsState.error_message,
                    rx.callout(
                        PatientAppointmentsState.error_message,
                        icon="alert-circle",
                        color_scheme="red",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                # Loading / content
                rx.cond(
                    PatientAppointmentsState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="4rem"),
                    rx.cond(
                        PatientAppointmentsState.view_mode == "calendar",
                        _calendar_view(),
                        rx.cond(
                            PatientAppointmentsState.appointments,
                            _list_view(),
                            rx.center(
                                rx.vstack(
                                    rx.icon("calendar-x", size=36, color="var(--gray-7)"),
                                    rx.text(LanguageState.tr["appt_empty"], size="3", color="var(--gray-9)"),
                                    rx.button(
                                        rx.icon("calendar-plus", size=14),
                                        LanguageState.tr["appt_plan_btn"],
                                        on_click=PatientAppointmentsState.open_booking_dialog,
                                        color_scheme="teal",
                                        variant="outline",
                                        size="2",
                                    ),
                                    spacing="3",
                                    align="center",
                                ),
                                padding="4rem",
                            ),
                        ),
                    ),
                ),
                spacing="4",
                width="100%",
            ),
        ),
        _booking_dialog(),
    )
