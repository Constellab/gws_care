"""Appointment detail page component (/appointment/[visit_id_param])."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .appointment_detail_state import AppointmentDetailState, DoctorOptionDTO


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
        rx.badge(mode, color_scheme="gray", variant="soft", size="1"),
    )


def _info_row(label: str, value: rx.Component) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="2", color="var(--gray-9)", min_width="160px"),
        value,
        spacing="3",
        align="center",
        width="100%",
    )


def _doctor_option(doc: DoctorOptionDTO) -> rx.Component:
    return rx.select.item(doc.name, value=doc.id)


# ── Address section (edit mode, mode == "address") ────────────────────────────

def _address_section_edit() -> rx.Component:
    return rx.cond(
        AppointmentDetailState.edit_mode == "address",
        rx.vstack(
            rx.text(LanguageState.tr["appt_address_label"], size="2", weight="medium"),
            rx.hstack(
                rx.input(
                    placeholder=LanguageState.tr["appt_address_placeholder"],
                    value=AppointmentDetailState.edit_appointment_address,
                    on_change=AppointmentDetailState.set_edit_appointment_address,
                    flex="1",
                ),
                rx.button(
                    rx.icon("map-pin", size=14),
                    LanguageState.tr["open_in_google_maps_btn"],
                    on_click=AppointmentDetailState.open_edit_address_in_google_maps,
                    variant="soft",
                    size="2",
                ),
                spacing="2",
                width="100%",
                align="center",
            ),
            spacing="1",
            width="100%",
        ),
    )


# ── View mode ─────────────────────────────────────────────────────────────────

def _view_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.text(AppointmentDetailState.visit_number, size="5", weight="bold"),
                        _status_badge(AppointmentDetailState.status),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        LanguageState.tr["appt_detail_page_title"],
                        size="2",
                        color="var(--gray-9)",
                    ),
                    spacing="1",
                ),
                rx.spacer(),
                # Open Consultation button (staff only)
                rx.cond(
                    ~AppointmentDetailState.is_patient_user,
                    rx.button(
                        rx.icon("stethoscope", size=14),
                        LanguageState.tr["open_consultation_btn"],
                        on_click=AppointmentDetailState.go_to_consultation,
                        variant="soft",
                        size="2",
                    ),
                ),
                width="100%",
                align="start",
            ),
            rx.divider(),
            # Info rows
            _info_row(
                LanguageState.tr["appt_date_label"],
                rx.text(AppointmentDetailState.scheduled_at, size="2"),
            ),
            _info_row(
                LanguageState.tr["appt_mode_label"],
                _mode_badge(AppointmentDetailState.appointment_mode),
            ),
            rx.cond(
                AppointmentDetailState.appointment_address != "",
                _info_row(
                    LanguageState.tr["appt_address_label"],
                    rx.hstack(
                        rx.text(AppointmentDetailState.appointment_address, size="2"),
                        rx.button(
                            rx.icon("map-pin", size=14),
                            LanguageState.tr["open_in_google_maps_btn"],
                            on_click=AppointmentDetailState.open_address_in_google_maps,
                            variant="soft",
                            size="2",
                        ),
                        spacing="3",
                        align="center",
                    ),
                ),
            ),
            _info_row(
                LanguageState.tr["appt_doctor_label"],
                rx.text(
                    rx.cond(
                        AppointmentDetailState.doctor_name != "",
                        AppointmentDetailState.doctor_name,
                        rx.text(LanguageState.tr["appt_doctor_placeholder"], color="var(--gray-9)"),
                    ),
                    size="2",
                ),
            ),
            # Patient link (staff only)
            rx.cond(
                ~AppointmentDetailState.is_patient_user,
                _info_row(
                    "Patient",
                    rx.link(
                        AppointmentDetailState.patient_name,
                        on_click=AppointmentDetailState.go_to_patient,
                        cursor="pointer",
                        color="var(--accent-9)",
                        size="2",
                    ),
                ),
            ),
            rx.cond(
                AppointmentDetailState.patient_notes != "",
                _info_row(
                    LanguageState.tr["appt_notes_label"],
                    rx.text(AppointmentDetailState.patient_notes, size="2"),
                ),
            ),
            # Success message
            rx.cond(
                AppointmentDetailState.success_message != "",
                rx.callout(
                    AppointmentDetailState.success_message,
                    icon="check",
                    color_scheme="green",
                    size="1",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


# ── Edit dialog ───────────────────────────────────────────────────────────────

def _edit_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["appt_edit_title"]),
            rx.vstack(
                # Date
                rx.vstack(
                    rx.text(LanguageState.tr["appt_date_label"], size="2", weight="medium"),
                    rx.input(
                        type="datetime-local",
                        value=AppointmentDetailState.edit_scheduled_at,
                        on_change=AppointmentDetailState.set_edit_scheduled_at,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Mode
                rx.vstack(
                    rx.text(LanguageState.tr["place_of_appointment_label"], size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(width="100%"),
                        rx.select.content(
                            rx.select.item(LanguageState.tr["appt_mode_at_home"], value="at_home"),
                            rx.select.item(LanguageState.tr["appt_mode_address"], value="address"),
                            rx.select.item(LanguageState.tr["appt_mode_visio"], value="visio"),
                            rx.select.item(LanguageState.tr["appt_mode_hospital"], value="hospital"),
                        ),
                        value=AppointmentDetailState.edit_mode,
                        on_change=AppointmentDetailState.set_edit_mode,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                _address_section_edit(),
                # Doctor
                rx.vstack(
                    rx.text(LanguageState.tr["appt_doctor_label"], size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(width="100%"),
                        rx.select.content(
                            rx.select.item(LanguageState.tr["appt_doctor_placeholder"], value="none"),
                            rx.foreach(AppointmentDetailState.doctor_options, _doctor_option),
                        ),
                        value=rx.cond(
                            AppointmentDetailState.edit_doctor_id != "",
                            AppointmentDetailState.edit_doctor_id,
                            "none",
                        ),
                        on_change=AppointmentDetailState.set_edit_doctor_id,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Status (staff only)
                rx.cond(
                    ~AppointmentDetailState.is_patient_user,
                    rx.vstack(
                        rx.text(LanguageState.tr["col_status"], size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(width="100%"),
                            rx.select.content(
                                rx.select.item(LanguageState.tr["appt_status_scheduled"], value="scheduled"),
                                rx.select.item(LanguageState.tr["appt_status_in_progress"], value="in_progress"),
                                rx.select.item(LanguageState.tr["appt_status_done"], value="done"),
                                rx.select.item(LanguageState.tr["appt_status_cancelled"], value="cancelled"),
                            ),
                            value=AppointmentDetailState.edit_status,
                            on_change=AppointmentDetailState.set_edit_status,
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                ),
                # Notes
                rx.vstack(
                    rx.text(LanguageState.tr["appt_notes_label"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=LanguageState.tr["appt_notes_placeholder"],
                        value=AppointmentDetailState.edit_notes,
                        on_change=AppointmentDetailState.set_edit_notes,
                        width="100%",
                        rows="3",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Error
                rx.cond(
                    AppointmentDetailState.edit_error != "",
                    rx.callout(
                        AppointmentDetailState.edit_error,
                        icon="alert-circle",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                # Buttons
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        LanguageState.tr["appt_back_btn"],
                        on_click=AppointmentDetailState.cancel_edit,
                        variant="soft",
                        size="2",
                    ),
                    rx.button(
                        LanguageState.tr["appt_save_btn"],
                        on_click=AppointmentDetailState.save_edit,
                        loading=AppointmentDetailState.is_saving,
                        size="2",
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                width="100%",
                padding_top="0.5rem",
            ),
            on_interact_outside=AppointmentDetailState.cancel_edit,
            on_escape_key_down=AppointmentDetailState.cancel_edit,
            max_width="600px",
        ),
        open=AppointmentDetailState.show_edit_dialog,
    )


# ── Dialogs ───────────────────────────────────────────────────────────────────

def _cancel_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(LanguageState.tr["appt_cancel_confirm_title"]),
            rx.alert_dialog.description(LanguageState.tr["appt_cancel_confirm_desc"]),
            rx.flex(
                rx.alert_dialog.cancel(
                    rx.button(LanguageState.tr["back"], variant="soft"),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        LanguageState.tr["appt_cancel_appt_btn"],
                        on_click=AppointmentDetailState.confirm_cancel,
                        loading=AppointmentDetailState.is_cancelling,
                        color_scheme="red",
                    ),
                ),
                spacing="3",
                justify="end",
                margin_top="4",
            ),
        ),
        open=AppointmentDetailState.show_cancel_dialog,
        on_open_change=AppointmentDetailState.close_cancel_dialog,
    )


def _delete_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(LanguageState.tr["appt_delete_confirm_title"]),
            rx.alert_dialog.description(LanguageState.tr["appt_delete_confirm_desc"]),
            rx.flex(
                rx.alert_dialog.cancel(
                    rx.button(LanguageState.tr["back"], variant="soft"),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Delete",
                        on_click=AppointmentDetailState.confirm_delete,
                        loading=AppointmentDetailState.is_deleting,
                        color_scheme="red",
                    ),
                ),
                spacing="3",
                justify="end",
                margin_top="4",
            ),
        ),
        open=AppointmentDetailState.show_delete_dialog,
        on_open_change=AppointmentDetailState.close_delete_dialog,
    )


# ── Main page ─────────────────────────────────────────────────────────────────

def appointment_detail_page() -> rx.Component:
    content = rx.vstack(
        # Back button + action buttons row
        rx.hstack(
            rx.button(
                rx.icon("arrow-left", size=14),
                LanguageState.tr["appt_back_btn"],
                on_click=AppointmentDetailState.go_back,
                variant="ghost",
                size="2",
            ),
            rx.spacer(),
            # Action buttons — only visible once loaded
            rx.cond(
                ~AppointmentDetailState.is_loading & ~AppointmentDetailState.not_found,
                rx.hstack(
                    rx.cond(
                        AppointmentDetailState.can_edit,
                        rx.button(
                            rx.icon("pencil", size=14),
                            LanguageState.tr["appt_edit_title"],
                            on_click=AppointmentDetailState.start_edit,
                            variant="soft",
                            size="2",
                        ),
                    ),
                    rx.cond(
                        AppointmentDetailState.can_cancel,
                        rx.button(
                            rx.icon("x", size=14),
                            LanguageState.tr["appt_cancel_appt_btn"],
                            on_click=AppointmentDetailState.open_cancel_dialog,
                            color_scheme="red",
                            variant="soft",
                            size="2",
                        ),
                    ),
                    rx.cond(
                        AppointmentDetailState.can_delete,
                        rx.button(
                            rx.icon("trash-2", size=14),
                            "Delete",
                            on_click=AppointmentDetailState.open_delete_dialog,
                            color_scheme="red",
                            variant="soft",
                            size="2",
                        ),
                    ),
                    spacing="2",
                ),
            ),
            width="100%",
            align="center",
            margin_bottom="2",
        ),
        # Main content
        rx.cond(
            AppointmentDetailState.is_loading,
            rx.center(rx.spinner(size="3"), padding="8"),
            rx.cond(
                AppointmentDetailState.not_found,
                rx.callout(
                    "Appointment not found.",
                    icon="alert-circle",
                    color_scheme="red",
                ),
                _view_section(),
            ),
        ),
        rx.cond(
            AppointmentDetailState.error_message != "",
            rx.callout(
                AppointmentDetailState.error_message,
                icon="alert-circle",
                color_scheme="red",
                size="1",
            ),
        ),
        spacing="3",
        width="100%",
        padding_x="4",
        padding_y="4",
    )

    return main_component(
        page_layout(content),
        _cancel_dialog(),
        _delete_dialog(),
        _edit_dialog(),
    )
