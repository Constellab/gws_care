"""Notifications page component — inbox, sent, compose, preferences."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.account_picker_component import account_picker_button, account_picker_dialog
from .notifications_state import DoctorPickerRowDTO
from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..common.patient_picker_component import patient_picker_button, patient_picker_dialog
from .notifications_state import (
    NotificationLogRow,
    NotificationsState,
)

# ── Status / type badges ──────────────────────────────────────────────────────

def _status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("SENT", rx.badge(LanguageState.tr["notif_status_sent"], color_scheme="green", variant="soft", size="1")),
        ("FAILED", rx.badge(LanguageState.tr["notif_status_failed"], color_scheme="red", variant="soft", size="1")),
        ("PENDING", rx.badge(LanguageState.tr["notif_status_pending"], color_scheme="orange", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _type_badge(ntype: str) -> rx.Component:
    return rx.match(
        ntype,
        ("APPOINTMENT_REMINDER", rx.badge(LanguageState.tr["notif_type_reminder"], color_scheme="blue", variant="soft", size="1")),
        ("APPOINTMENT_REMINDER_15D", rx.badge(LanguageState.tr["notif_type_reminder"], color_scheme="blue", variant="soft", size="1")),
        ("APPOINTMENT_REMINDER_3D", rx.badge(LanguageState.tr["notif_type_reminder"], color_scheme="blue", variant="soft", size="1")),
        ("APPOINTMENT_REMINDER_1D", rx.badge(LanguageState.tr["notif_type_reminder"], color_scheme="blue", variant="soft", size="1")),
        ("MANUAL_PATIENT", rx.badge(LanguageState.tr["notif_type_patient"], color_scheme="purple", variant="soft", size="1")),
        ("MANUAL_ACCOUNT", rx.badge(LanguageState.tr["notif_type_account"], color_scheme="cyan", variant="soft", size="1")),
        rx.badge(ntype, color_scheme="gray", variant="soft", size="1"),
    )


# ── Inbox/Sent message row (email-client style) ───────────────────────────────

def _inbox_message_row(log: NotificationLogRow) -> rx.Component:
    """Email-client-style row for the inbox: two-line layout with reply button."""
    return rx.box(
        rx.vstack(
            # Line 1: badges + date + sender + reply button
            rx.hstack(
                _type_badge(log.notification_type),
                _status_badge(log.status),
                rx.text(log.sent_by_name, size="1", color="var(--gray-10)"),
                rx.spacer(),
                rx.text(log.created_at, size="1", color="var(--gray-9)"),
                rx.cond(
                    log.parent_log_id != "",
                    rx.badge(
                        rx.icon("corner-down-right", size=11),
                        LanguageState.tr["reply_badge"],
                        color_scheme="grass",
                        variant="soft",
                        size="1",
                    ),
                ),
                rx.button(
                    rx.icon("reply", size=13),
                    LanguageState.tr["reply_btn"],
                    size="1",
                    variant="ghost",
                    on_click=lambda: NotificationsState.open_reply(log.id, log.subject),
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            # Line 2: Subject (bold, full width)
            rx.text(
                log.subject,
                size="2",
                weight="bold",
                color="var(--gray-12)",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
                width="100%",
            ),
            # Line 3: body preview
            rx.cond(
                log.body_preview != "",
                rx.text(
                    log.body_preview,
                    size="1",
                    color="var(--gray-9)",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                    width="100%",
                ),
            ),
            spacing="1",
            width="100%",
        ),
        padding="0.75rem 1rem",
        border_bottom="1px solid var(--gray-4)",
        _hover={"background": "var(--gray-2)"},
        width="100%",
    )


def _sent_message_row(log: NotificationLogRow) -> rx.Component:
    """Email-client-style row for the sent box: two-line layout without reply."""
    return rx.box(
        rx.vstack(
            # Line 1: badges + date + recipient
            rx.hstack(
                _type_badge(log.notification_type),
                _status_badge(log.status),
                rx.text(
                    LanguageState.tr["col_to"],
                    size="1",
                    color="var(--gray-9)",
                ),
                rx.text(log.recipient_name, size="1", color="var(--gray-10)"),
                rx.spacer(),
                rx.text(log.created_at, size="1", color="var(--gray-9)"),
                rx.cond(
                    log.parent_log_id != "",
                    rx.badge(
                        rx.icon("corner-down-right", size=11),
                        LanguageState.tr["reply_badge"],
                        color_scheme="grass",
                        variant="soft",
                        size="1",
                    ),
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            # Line 2: Subject (bold, full width)
            rx.text(
                log.subject,
                size="2",
                weight="bold",
                color="var(--gray-12)",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
                width="100%",
            ),
            # Line 3: body preview
            rx.cond(
                log.body_preview != "",
                rx.text(
                    log.body_preview,
                    size="1",
                    color="var(--gray-9)",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                    width="100%",
                ),
            ),
            spacing="1",
            width="100%",
        ),
        padding="0.75rem 1rem",
        border_bottom="1px solid var(--gray-4)",
        _hover={"background": "var(--gray-2)"},
        width="100%",
    )


# ── Sort/filter toolbar ───────────────────────────────────────────────────────

def _sort_icon(column: str) -> rx.Component:
    return rx.cond(
        NotificationsState.sort_column == column,
        rx.cond(
            NotificationsState.sort_ascending,
            rx.icon("chevron-up", size=13, color="var(--accent-9)"),
            rx.icon("chevron-down", size=13, color="var(--accent-9)"),
        ),
        rx.icon("chevrons-up-down", size=13, color="var(--gray-6)"),
    )


def _sort_btn(label: str, column: str) -> rx.Component:
    return rx.button(
        label,
        _sort_icon(column),
        variant="ghost",
        size="1",
        color="var(--gray-11)",
        on_click=lambda: NotificationsState.set_sort(column),
    )


def _message_toolbar(count: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.select.root(
            rx.select.trigger(placeholder=LanguageState.tr["history_all_types"], size="2"),
            rx.select.content(
                rx.select.item(LanguageState.tr["history_all_types"], value="ALL"),
                rx.select.item(LanguageState.tr["history_reminders"], value="APPOINTMENT_REMINDER"),
                rx.select.item(LanguageState.tr["history_manual_patient"], value="MANUAL_PATIENT"),
                rx.select.item(LanguageState.tr["history_manual_account"], value="MANUAL_ACCOUNT"),
            ),
            value=NotificationsState.filter_type,
            on_change=NotificationsState.set_filter_type,
            size="2",
        ),
        rx.text(LanguageState.tr["sort_by_label"], size="1", color="var(--gray-9)"),
        _sort_btn(LanguageState.tr["col_date"], "created_at"),
        _sort_btn(LanguageState.tr["col_type"], "notification_type"),
        _sort_btn(LanguageState.tr["col_subject"], "subject"),
        rx.spacer(),
        rx.text(count, LanguageState.tr["entries_suffix"], size="1", color="var(--gray-9)"),
        align="center",
        spacing="2",
        width="100%",
        padding_x="0.5rem",
        padding_y="0.5rem",
    )


# ── Inbox tab ─────────────────────────────────────────────────────────────────

def _inbox_tab() -> rx.Component:
    return rx.vstack(
        _message_toolbar(NotificationsState.inbox_logs.length()),
        rx.cond(
            NotificationsState.is_loading_logs,
            rx.center(rx.spinner(size="3"), padding="2rem"),
            rx.cond(
                NotificationsState.inbox_logs.length() > 0,
                rx.box(
                    rx.foreach(NotificationsState.inbox_logs, _inbox_message_row),
                    border="1px solid var(--gray-4)",
                    border_radius="var(--radius-3)",
                    overflow="hidden",
                    width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("inbox", size=40, color="var(--gray-6)"),
                        rx.text(LanguageState.tr["inbox_empty"], size="2", color="var(--gray-9)"),
                        align="center",
                        spacing="2",
                    ),
                    padding="4rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="8px",
                    width="100%",
                ),
            ),
        ),
        spacing="2",
        width="100%",
    )


# ── Sent tab ──────────────────────────────────────────────────────────────────

def _sent_tab() -> rx.Component:
    return rx.vstack(
        _message_toolbar(NotificationsState.sent_logs.length()),
        rx.cond(
            NotificationsState.is_loading_logs,
            rx.center(rx.spinner(size="3"), padding="2rem"),
            rx.cond(
                NotificationsState.sent_logs.length() > 0,
                rx.box(
                    rx.foreach(NotificationsState.sent_logs, _sent_message_row),
                    border="1px solid var(--gray-4)",
                    border_radius="var(--radius-3)",
                    overflow="hidden",
                    width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("send", size=40, color="var(--gray-6)"),
                        rx.text(LanguageState.tr["sent_empty"], size="2", color="var(--gray-9)"),
                        align="center",
                        spacing="2",
                    ),
                    padding="4rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="8px",
                    width="100%",
                ),
            ),
        ),
        spacing="2",
        width="100%",
    )


# ── Compose tab ───────────────────────────────────────────────────────────────

def _doctor_picker_row(d: DoctorPickerRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(d.full_name, size="2", weight="medium")),
        rx.table.cell(
            rx.cond(d.specialization != "", rx.text(d.specialization, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        _hover={"background_color": "var(--accent-2)", "cursor": "pointer"},
        on_click=lambda: NotificationsState.doc_picker_confirm(d.id, d.full_name),
    )


def _doctor_picker_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["send_to_doctor"]),
            rx.vstack(
                rx.input(
                    rx.input.slot(rx.icon("search", size=14)),
                    placeholder=LanguageState.tr["select_doctor_placeholder"],
                    value=NotificationsState.doc_picker_filter,
                    on_change=NotificationsState.doc_picker_set_filter,
                    size="2", width="100%",
                ),
                rx.cond(
                    NotificationsState.doc_picker_error != "",
                    rx.callout(NotificationsState.doc_picker_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.cond(
                    NotificationsState.doc_picker_is_loading,
                    rx.center(rx.spinner(size="2"), padding="1.5rem"),
                    rx.cond(
                        NotificationsState.doc_picker_rows.length() > 0,
                        rx.box(
                            rx.table.root(
                                rx.table.header(rx.table.row(
                                    rx.table.column_header_cell(LanguageState.tr["col_name"]),
                                    rx.table.column_header_cell(LanguageState.tr["col_specialization"]),
                                )),
                                rx.table.body(rx.foreach(NotificationsState.doc_picker_rows, _doctor_picker_row)),
                                width="100%", variant="surface",
                            ),
                            max_height="320px", overflow_y="auto", width="100%",
                        ),
                        rx.center(rx.text(LanguageState.tr["no_doctors_found"], size="2", color="var(--gray-9)"), padding="1.5rem"),
                    ),
                ),
                rx.hstack(
                    rx.button(LanguageState.tr["cancel_btn"], variant="soft", color_scheme="gray",
                              on_click=NotificationsState.close_doctor_picker),
                    justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            on_interact_outside=NotificationsState.close_doctor_picker,
            on_escape_key_down=NotificationsState.close_doctor_picker,
            max_width="500px",
        ),
        open=NotificationsState.doc_picker_is_open,
    )


def _compose_tab() -> rx.Component:
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.heading(LanguageState.tr["compose_card_title"], size="4"),
                rx.text(
                    LanguageState.tr["compose_card_desc"],
                    size="2",
                    color="var(--gray-10)",
                ),
                # Reply banner (shown when replying to a message)
                rx.cond(
                    NotificationsState.reply_to_id != "",
                    rx.callout(
                        rx.hstack(
                            rx.text(
                                LanguageState.tr["replying_to_label"],
                                size="2",
                                weight="medium",
                            ),
                            rx.text(NotificationsState.reply_to_subject, size="2"),
                            rx.spacer(),
                            rx.icon_button(
                                rx.icon("x", size=13),
                                size="1",
                                variant="ghost",
                                on_click=NotificationsState.clear_reply,
                            ),
                            spacing="2",
                            align="center",
                            width="100%",
                        ),
                        icon="reply",
                        color_scheme="grass",
                        size="1",
                        width="100%",
                    ),
                ),
                rx.separator(width="100%"),
                # Mode toggle
                rx.hstack(
                    rx.text(LanguageState.tr["send_to_label"], size="2", weight="medium"),
                    rx.segmented_control.root(
                        rx.segmented_control.item(LanguageState.tr["send_to_patient"], value="patient"),
                        rx.segmented_control.item(LanguageState.tr["send_to_account"], value="account"),
                        rx.segmented_control.item(LanguageState.tr["send_to_doctor"], value="doctor"),
                        value=NotificationsState.compose_mode,
                        on_change=NotificationsState.set_compose_mode,
                        size="2",
                    ),
                    spacing="3",
                    align="center",
                ),
                # Recipient selector
                rx.cond(
                    NotificationsState.compose_mode == "patient",
                    rx.vstack(
                        rx.text(LanguageState.tr["send_to_patient"], size="2", weight="medium"),
                        patient_picker_button(NotificationsState),
                        spacing="2", width="100%",
                    ),
                    rx.cond(
                        NotificationsState.compose_mode == "doctor",
                        rx.vstack(
                            rx.text(LanguageState.tr["send_to_doctor"], size="2", weight="medium"),
                            rx.hstack(
                                rx.button(
                                    rx.icon("user-round-check", size=14),
                                    rx.cond(
                                        NotificationsState.doc_picker_selected_id != "",
                                        rx.text(NotificationsState.doc_picker_selected_name, size="2"),
                                        rx.text(LanguageState.tr["select_doctor_placeholder"], size="2"),
                                    ),
                                    on_click=NotificationsState.open_doctor_picker,
                                    variant=rx.cond(NotificationsState.doc_picker_selected_id != "", "soft", "outline"),
                                    color_scheme="purple",
                                    size="2",
                                    type="button",
                                ),
                                rx.cond(
                                    NotificationsState.doc_picker_selected_id != "",
                                    rx.icon_button(rx.icon("x", size=12), on_click=NotificationsState.doc_picker_clear,
                                                   variant="ghost", color_scheme="gray", size="2"),
                                    rx.fragment(),
                                ),
                                spacing="2", align="center",
                            ),
                            spacing="2", width="100%",
                        ),
                        rx.vstack(
                            rx.text(LanguageState.tr["send_to_account"], size="2", weight="medium"),
                            account_picker_button(NotificationsState),
                            rx.text(LanguageState.tr["account_patients_note"], size="1", color="var(--gray-9)"),
                            spacing="2", width="100%",
                        ),
                    ),
                ),
                # Subject
                rx.vstack(
                    rx.text(LanguageState.tr["subject_label"], size="2", weight="medium"),
                    rx.input(
                        placeholder=LanguageState.tr["subject_placeholder"],
                        value=NotificationsState.compose_subject,
                        on_change=NotificationsState.set_compose_subject,
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Body
                rx.vstack(
                    rx.text(LanguageState.tr["message_label"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=LanguageState.tr["message_placeholder"],
                        value=NotificationsState.compose_body,
                        on_change=NotificationsState.set_compose_body,
                        min_height="140px",
                        width="100%",
                        size="2",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Feedback
                rx.cond(
                    NotificationsState.send_error != "",
                    rx.callout(NotificationsState.send_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.cond(
                    NotificationsState.send_success != "",
                    rx.callout(NotificationsState.send_success, icon="check", color_scheme="green", size="1"),
                ),
                # Send button
                rx.button(
                    rx.icon("send", size=14),
                    LanguageState.tr["send_message_btn"],
                    on_click=NotificationsState.send_message,
                    loading=NotificationsState.is_sending,
                    size="2",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def notifications_page() -> rx.Component:
    return main_component(
        page_layout(
            account_picker_dialog(NotificationsState),
            patient_picker_dialog(NotificationsState),
            _doctor_picker_dialog(),
            rx.hstack(
                rx.icon("bell", size=22, color="var(--accent-9)"),
                rx.heading(LanguageState.tr["notifications_page_title"], size="6"),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger(
                        rx.hstack(
                            rx.icon("inbox", size=15),
                            rx.text(LanguageState.tr["tab_inbox"]),
                            rx.cond(
                                NotificationsState.inbox_logs.length() > 0,
                                rx.badge(
                                    NotificationsState.inbox_logs.length(),
                                    color_scheme="blue",
                                    variant="solid",
                                    size="1",
                                ),
                            ),
                            spacing="1",
                            align="center",
                        ),
                        value="inbox",
                    ),
                    rx.tabs.trigger(
                        rx.hstack(
                            rx.icon("send", size=15),
                            rx.text(LanguageState.tr["tab_sent"]),
                            spacing="1",
                            align="center",
                        ),
                        value="sent",
                    ),
                    rx.tabs.trigger(
                        rx.hstack(
                            rx.icon("pencil-line", size=15),
                            rx.text(LanguageState.tr["tab_compose"]),
                            spacing="1",
                            align="center",
                        ),
                        value="compose",
                    ),
                ),
                rx.tabs.content(_inbox_tab(), value="inbox", padding_top="1rem"),
                rx.tabs.content(_sent_tab(), value="sent", padding_top="1rem"),
                rx.tabs.content(_compose_tab(), value="compose", padding_top="1rem"),
                value=NotificationsState.active_tab,
                on_change=NotificationsState.set_active_tab,
                width="100%",
            ),
        )
    )

