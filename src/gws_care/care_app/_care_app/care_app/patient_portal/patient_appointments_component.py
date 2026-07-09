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


def _mode_icon(mode: str) -> rx.Component:
    return rx.match(
        mode,
        ("at_work", rx.icon("briefcase", size=13, color="var(--blue-9)")),
        ("at_home", rx.icon("home", size=13, color="var(--green-9)")),
        ("address", rx.icon("map-pin", size=13, color="var(--orange-9)")),
        ("visio", rx.icon("video", size=13, color="var(--purple-9)")),
        ("hospital", rx.icon("hospital", size=13, color="var(--teal-9)")),
        rx.icon("calendar", size=13, color="var(--gray-9)"),
    )


# ── List view ─────────────────────────────────────────────────────────────────

def _sortable_col(label, column: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                PatientAppointmentsState.sort_column == column,
                rx.cond(
                    PatientAppointmentsState.sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: PatientAppointmentsState.set_sort(column),
        style={"cursor": "pointer"},
    )


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
        on_click=lambda: PatientAppointmentsState.go_to_appointment(appt.id),
    )


def _list_view() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                _sortable_col(LanguageState.tr["col_date"], "scheduled_at"),
                _sortable_col(LanguageState.tr["appt_mode"], "appointment_mode"),
                _sortable_col(LanguageState.tr["appt_doctor"], "doctor_name"),
                _sortable_col(LanguageState.tr["col_status"], "status"),
            )
        ),
        rx.table.body(
            rx.foreach(PatientAppointmentsState.filtered_sorted_appointments, _appt_row)
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
        on_click=lambda: PatientAppointmentsState.go_to_appointment(appt.id),
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


# ── Booking dialog (Doctolib-style) ──────────────────────────────────────────

def _booking_step_breadcrumb() -> rx.Component:
    def _crumb(n: int, label: str) -> rx.Component:
        is_active = PatientAppointmentsState.booking_step == n
        is_done = PatientAppointmentsState.booking_step > n
        return rx.hstack(
            rx.box(
                rx.text(str(n), size="1", weight="bold",
                        color=rx.cond(is_active | is_done, "white", "var(--gray-9)")),
                width="20px", height="20px", border_radius="50%",
                background=rx.cond(
                    is_active, "var(--accent-9)",
                    rx.cond(is_done, "var(--green-9)", "var(--gray-4)"),
                ),
                display="flex", align_items="center", justify_content="center", flex_shrink="0",
            ),
            rx.text(label, size="1",
                    color=rx.cond(is_active, "var(--accent-11)", "var(--gray-9)"),
                    weight=rx.cond(is_active, "medium", "regular")),
            spacing="1", align="center",
        )
    return rx.hstack(
        _crumb(1, "Specialty"),
        rx.icon("chevron-right", size=12, color="var(--gray-6)"),
        _crumb(2, "Doctor"),
        rx.icon("chevron-right", size=12, color="var(--gray-6)"),
        _crumb(3, "Slot"),
        spacing="1", align="center",
    )


def _booking_specialty_row(s: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("stethoscope", size=14, color="var(--accent-9)"),
            rx.text(s, size="2"),
            spacing="2", align="center",
        ),
        padding="0.4rem 0.75rem",
        cursor="pointer",
        _hover={"background": "var(--accent-2)"},
        on_click=lambda: PatientAppointmentsState.select_patient_booking_specialty(s),
    )


def _booking_doctor_card(doc: DoctorOptionDTO) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("circle-user-round", size=28, color="var(--accent-9)", flex_shrink="0"),
            rx.vstack(
                rx.text(doc.name, size="2", weight="bold"),
                rx.cond(
                    doc.specialization != "",
                    rx.badge(doc.specialization, color_scheme="blue", variant="soft", size="1"),
                    rx.fragment(),
                ),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.icon("chevron-right", size=16, color="var(--gray-7)"),
            spacing="3", align="center", width="100%",
        ),
        padding="0.75rem 1rem",
        border="1px solid var(--gray-4)", border_radius="10px",
        cursor="pointer", width="100%",
        _hover={"border_color": "var(--accent-7)", "background": "var(--accent-2)"},
        on_click=lambda: PatientAppointmentsState.select_patient_booking_doctor(
            doc.id, doc.name
        ),
    )


def _booking_slot_btn(slot: str) -> rx.Component:
    is_selected = PatientAppointmentsState.booking_scheduled_at == slot
    return rx.button(
        slot[11:16],
        variant=rx.cond(is_selected, "solid", "soft"),
        color_scheme=rx.cond(is_selected, "blue", "gray"),
        size="2", border_radius="8px", min_width="64px",
        on_click=lambda: PatientAppointmentsState.select_booking_slot(slot),
    )


def _booking_step1() -> rx.Component:
    return rx.vstack(
        rx.text("Choose a medical specialty", size="3", weight="medium"),
        rx.separator(width="100%"),
        rx.vstack(
            rx.input(
                placeholder="Search for a specialty…",
                value=PatientAppointmentsState.booking_specialty_search,
                on_change=PatientAppointmentsState.set_booking_specialty_search,
                size="2",
                width="100%",
            ),
            rx.cond(
                PatientAppointmentsState.doctor_options.length() > 0,
                rx.box(
                    rx.box(
                        rx.hstack(
                            rx.icon("users", size=14, color="var(--gray-9)"),
                            rx.text("All doctors", size="2", color="var(--gray-11)"),
                            spacing="2", align="center",
                        ),
                        padding="0.4rem 0.75rem",
                        cursor="pointer",
                        border_bottom="1px solid var(--gray-3)",
                        _hover={"background": "var(--gray-2)"},
                        on_click=lambda: PatientAppointmentsState.select_patient_booking_specialty("_all_"),
                    ),
                    rx.cond(
                        PatientAppointmentsState.filtered_booking_specialties.length() > 0,
                        rx.foreach(PatientAppointmentsState.filtered_booking_specialties, _booking_specialty_row),
                        rx.box(
                            rx.text("No specialty found.", size="2", color="var(--gray-9)"),
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
                    "No doctor available at the moment.",
                    icon="info", color_scheme="orange", size="1", width="100%",
                ),
            ),
            spacing="1",
            width="100%",
        ),
        width="100%", spacing="3", padding_top="0.5rem",
    )


def _booking_step2() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon_button(
                rx.icon("arrow-left", size=14), variant="ghost", size="1",
                on_click=lambda: PatientAppointmentsState.booking_go_back(1),
            ),
            rx.cond(
                PatientAppointmentsState.booking_specialty != "",
                rx.hstack(
                    rx.text("Doctors —", size="3", weight="medium"),
                    rx.badge(PatientAppointmentsState.booking_specialty, color_scheme="blue", variant="soft", size="2"),
                    spacing="2", align="center",
                ),
                rx.text("All doctors", size="3", weight="medium"),
            ),
            spacing="2", align="center", width="100%",
        ),
        rx.separator(width="100%"),
        rx.cond(
            PatientAppointmentsState.filtered_booking_doctors.length() > 0,
            rx.vstack(
                rx.foreach(PatientAppointmentsState.filtered_booking_doctors, _booking_doctor_card),
                width="100%", spacing="2", max_height="300px", overflow_y="auto",
            ),
            rx.callout("No doctor available.", icon="info", color_scheme="orange", size="1"),
        ),
        width="100%", spacing="3", padding_top="0.5rem",
    )


def _booking_step3() -> rx.Component:
    return rx.vstack(
        # Doctor header + back
        rx.hstack(
            rx.icon_button(
                rx.icon("arrow-left", size=14), variant="ghost", size="1",
                on_click=lambda: PatientAppointmentsState.booking_go_back(2),
            ),
            rx.hstack(
                rx.icon("circle-user-round", size=18, color="var(--accent-9)"),
                rx.text(PatientAppointmentsState.booking_doctor_name, size="3", weight="medium"),
                spacing="2", align="center",
            ),
            spacing="2", align="center", width="100%",
        ),
        # Available days hint
        rx.cond(
            PatientAppointmentsState.booking_doctor_days_str != "",
            rx.hstack(
                rx.icon("calendar-check", size=13, color="var(--green-9)"),
                rx.text(
                    "Disponible : " + PatientAppointmentsState.booking_doctor_days_str,
                    size="1", color="var(--green-11)",
                ),
                spacing="1", align="center",
            ),
            rx.fragment(),
        ),
        rx.separator(width="100%"),
        # Date
        rx.vstack(
            rx.text("Date du rendez-vous *", size="2", weight="medium"),
            rx.input(
                type="date",
                value=PatientAppointmentsState.booking_date,
                on_change=PatientAppointmentsState.set_booking_date_and_load_slots,
                size="2", width="100%",
            ),
            spacing="1", width="100%",
        ),
        # Slots
        rx.cond(
            PatientAppointmentsState.booking_date != "",
            rx.vstack(
                rx.hstack(
                    rx.text("Available slots *", size="2", weight="medium"),
                    rx.cond(PatientAppointmentsState.booking_slots_loading, rx.spinner(size="1"), rx.fragment()),
                    spacing="2", align="center",
                ),
                rx.cond(
                    PatientAppointmentsState.booking_slots_error != "",
                    rx.callout(
                        PatientAppointmentsState.booking_slots_error,
                        icon="triangle-alert", color_scheme="red", variant="soft", size="1",
                    ),
                    rx.cond(
                        PatientAppointmentsState.booking_available_slots.length() > 0,
                        rx.flex(
                            rx.foreach(PatientAppointmentsState.booking_available_slots, _booking_slot_btn),
                            wrap="wrap", gap="0.4rem",
                        ),
                        rx.cond(
                            PatientAppointmentsState.booking_doctor_days_str != "",
                            rx.callout(
                                "No slot available for this date. This doctor is available on: "
                                + PatientAppointmentsState.booking_doctor_days_str,
                                icon="calendar-x", color_scheme="orange", variant="soft", size="1",
                            ),
                            rx.callout(
                                "No slot available. This doctor has not yet declared any availability.",
                                icon="calendar-x", color_scheme="red", variant="soft", size="1",
                            ),
                        ),
                    ),
                ),
                rx.cond(
                    PatientAppointmentsState.booking_scheduled_at != "",
                    rx.hstack(
                        rx.icon("circle-check", size=14, color="var(--green-9)"),
                        rx.text(
                            PatientAppointmentsState.booking_scheduled_at[0:10]
                            + " at "
                            + PatientAppointmentsState.booking_scheduled_at[11:16],
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
        # Mode selector (visio / hôpital only for personal bookings)
        rx.vstack(
            rx.text("Mode de consultation *", size="2", weight="medium"),
            rx.radio_group.root(
                rx.hstack(
                    rx.radio_group.item(value="visio"),
                    rx.hstack(
                        rx.icon("video", size=13, color="var(--purple-9)"),
                        rx.text("Visio", size="2"),
                        spacing="1", align="center",
                    ),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.radio_group.item(value="hospital"),
                    rx.hstack(
                        rx.icon("building-2", size=13, color="var(--teal-9)"),
                        rx.text("Hospital", size="2"),
                        spacing="1", align="center",
                    ),
                    spacing="2", align="center",
                ),
                value=PatientAppointmentsState.booking_mode,
                on_change=PatientAppointmentsState.set_booking_mode,
                orientation="horizontal",
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
                rows="2", width="100%",
            ),
            spacing="1", width="100%",
        ),
        # Error
        rx.cond(
            PatientAppointmentsState.booking_error != "",
            rx.callout(PatientAppointmentsState.booking_error, icon="triangle-alert", color_scheme="red", size="1"),
            rx.fragment(),
        ),
        width="100%", spacing="3", padding_top="0.5rem",
    )


def _booking_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.dialog.title(LanguageState.tr["appt_book_title"]),
                rx.dialog.close(
                    rx.icon_button(
                        rx.icon("x", size=14), variant="ghost", size="1", color_scheme="gray",
                        on_click=PatientAppointmentsState.close_booking_dialog,
                    )
                ),
                justify="between", align="center", width="100%",
            ),
            # Breadcrumb (shown on all steps)
            _booking_step_breadcrumb(),
            rx.separator(width="100%"),
            # Step content
            rx.match(
                PatientAppointmentsState.booking_step,
                (1, _booking_step1()),
                (2, _booking_step2()),
                (3, _booking_step3()),
                rx.fragment(),
            ),
            # Footer buttons
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        LanguageState.tr["cancel_btn"], variant="outline", color_scheme="gray",
                        on_click=PatientAppointmentsState.close_booking_dialog,
                    )
                ),
                rx.cond(
                    PatientAppointmentsState.booking_step == 3,
                    rx.button(
                        rx.icon("calendar-plus", size=14),
                        LanguageState.tr["appt_book_submit"],
                        on_click=PatientAppointmentsState.submit_booking,
                        loading=PatientAppointmentsState.booking_is_saving,
                        disabled=(PatientAppointmentsState.booking_scheduled_at == "")
                        | PatientAppointmentsState.booking_is_saving,
                        color_scheme="teal",
                    ),
                    rx.fragment(),
                ),
                justify="end",
                width="100%",
                spacing="3",
                padding_top="0.5rem",
            ),
            max_width="520px",
            on_interact_outside=PatientAppointmentsState.close_booking_dialog,
            on_escape_key_down=PatientAppointmentsState.close_booking_dialog,
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
                # Filter bar (list view only)
                rx.cond(
                    PatientAppointmentsState.view_mode == "list",
                    rx.hstack(
                        rx.input(
                            type="date",
                            value=PatientAppointmentsState.filter_from,
                            on_change=PatientAppointmentsState.set_filter_from,
                            size="2",
                            width="140px",
                        ),
                        rx.text(LanguageState.tr["date_range_arrow"], size="2", color="var(--gray-8)"),
                        rx.input(
                            type="date",
                            value=PatientAppointmentsState.filter_to,
                            on_change=PatientAppointmentsState.set_filter_to,
                            size="2",
                            width="140px",
                        ),
                        rx.select.root(
                            rx.select.trigger(
                                placeholder=LanguageState.tr["all_statuses"],
                                width="160px",
                            ),
                            rx.select.content(
                                rx.select.item(LanguageState.tr["all_statuses"], value="ALL"),
                                rx.select.item(LanguageState.tr["appt_status_scheduled"], value="scheduled"),
                                rx.select.item(LanguageState.tr["appt_status_in_progress"], value="in_progress"),
                                rx.select.item(LanguageState.tr["appt_status_done"], value="done"),
                                rx.select.item(LanguageState.tr["appt_status_cancelled"], value="cancelled"),
                            ),
                            value=rx.cond(
                                PatientAppointmentsState.filter_status != "",
                                PatientAppointmentsState.filter_status,
                                "ALL",
                            ),
                            on_change=PatientAppointmentsState.set_filter_status,
                            size="2",
                        ),
                        rx.tooltip(
                            rx.icon_button(
                                rx.icon("x", size=14),
                                on_click=PatientAppointmentsState.clear_filters,
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
                ),
                # Loading / content
                rx.cond(
                    PatientAppointmentsState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="4rem"),
                    rx.cond(
                        PatientAppointmentsState.view_mode == "calendar",
                        _calendar_view(),
                        rx.cond(
                            PatientAppointmentsState.filtered_sorted_appointments,
                            _list_view(),
                            rx.center(
                                rx.vstack(
                                    rx.icon("calendar-x", size=40, color="var(--gray-6)"),
                                    rx.text(LanguageState.tr["appt_empty"], size="2", color="var(--gray-9)"),
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
                                border="1px dashed var(--gray-5)",
                                border_radius="8px",
                                width="100%",
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
