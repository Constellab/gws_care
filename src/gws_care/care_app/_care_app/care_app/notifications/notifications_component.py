"""Notifications page component — history, preferences, and compose."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .notifications_state import (
    AccountOption,
    CampaignOption,
    NotificationLogRow,
    NotificationsState,
    PatientOption,
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
        ("MANUAL_PATIENT", rx.badge(LanguageState.tr["notif_type_patient"], color_scheme="purple", variant="soft", size="1")),
        ("MANUAL_ACCOUNT", rx.badge(LanguageState.tr["notif_type_account"], color_scheme="cyan", variant="soft", size="1")),
        rx.badge(ntype, color_scheme="gray", variant="soft", size="1"),
    )


def _channel_badge(channel: str) -> rx.Component:
    return rx.match(
        channel,
        ("EMAIL", rx.badge(LanguageState.tr["notif_channel_email"], color_scheme="blue", variant="soft", size="1")),
        ("SMS", rx.badge(LanguageState.tr["notif_channel_sms"], color_scheme="orange", variant="soft", size="1")),
        ("WHATSAPP", rx.badge(LanguageState.tr["notif_channel_whatsapp"], color_scheme="green", variant="soft", size="1")),
        rx.badge(channel, color_scheme="gray", variant="soft", size="1"),
    )


# ── History tab ───────────────────────────────────────────────────────────────

def _sortable_header(label: str, column: str) -> rx.Component:
    """Column header cell with a sort-direction arrow."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                NotificationsState.sort_column == column,
                rx.cond(
                    NotificationsState.sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: NotificationsState.set_sort(column),
        style={"cursor": "pointer"},
    )


def _log_row(log: NotificationLogRow) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(log.created_at, size="1", color="var(--gray-9)")),
        rx.table.cell(_type_badge(log.notification_type)),
        rx.table.cell(_channel_badge(log.channel)),
        rx.table.cell(_status_badge(log.status)),
        rx.table.cell(rx.text(log.recipient_name, size="2")),
        rx.table.cell(rx.text(log.recipient_email, size="2", color="var(--gray-10)")),
        rx.table.cell(rx.text(log.subject, size="2")),
        rx.table.cell(rx.text(log.sent_by_name, size="1", color="var(--gray-9)")),
    )


def _history_tab() -> rx.Component:
    return rx.vstack(
        # Filter bar
        rx.hstack(
            rx.select.root(
                rx.select.trigger(placeholder=LanguageState.tr["history_all_types"]),
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
            rx.spacer(),
            rx.text(
                NotificationsState.logs.length(),
                LanguageState.tr["entries_suffix"],
                size="2",
                color="var(--gray-9)",
            ),
            width="100%",
            align="center",
        ),
        # Table
        rx.cond(
            NotificationsState.is_loading_logs,
            rx.center(rx.spinner(size="3"), padding="2rem"),
            rx.cond(
                NotificationsState.logs.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            _sortable_header(LanguageState.tr["col_date"], "created_at"),
                            _sortable_header(LanguageState.tr["col_type"], "notification_type"),
                            _sortable_header(LanguageState.tr["col_channel"], "channel"),
                            _sortable_header(LanguageState.tr["col_status"], "status"),
                            _sortable_header(LanguageState.tr["col_recipient"], "recipient_name"),
                            _sortable_header(LanguageState.tr["col_email"], "recipient_email"),
                            _sortable_header(LanguageState.tr["col_subject"], "subject"),
                            _sortable_header(LanguageState.tr["col_sent_by"], "sent_by_name"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(NotificationsState.logs, _log_row)
                    ),
                    width="100%",
                    variant="surface",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("bell-off", size=36, color="var(--gray-7)"),
                        rx.text(LanguageState.tr["no_notifications_history"], color="var(--gray-9)"),
                        align="center",
                        spacing="2",
                    ),
                    padding="3rem",
                ),
            ),
        ),
        spacing="3",
        width="100%",
    )


# ── Compose tab ───────────────────────────────────────────────────────────────

def _patient_option(p: PatientOption) -> rx.Component:
    return rx.select.item(p.display, value=p.id)


def _account_option(a: AccountOption) -> rx.Component:
    return rx.select.item(a.name, value=a.id)


def _campaign_option(c: CampaignOption) -> rx.Component:
    return rx.select.item(c.name, value=c.id)


def _channel_checkbox(label: str, value: str, color: str) -> rx.Component:
    """Checkbox pour sélectionner un canal d'envoi."""
    return rx.box(
        rx.hstack(
            rx.checkbox(
                checked=NotificationsState.compose_channels.contains(value),
                on_change=lambda _: NotificationsState.toggle_compose_channel(value),
                size="2",
            ),
            rx.badge(label, color_scheme=color, variant="soft", size="2"),
            spacing="2",
            align="center",
            cursor="pointer",
            on_click=NotificationsState.toggle_compose_channel(value),
        ),
        padding="0.4rem 0.75rem",
        border="1px solid var(--gray-4)",
        border_radius="var(--radius-2)",
        _hover={"background": "var(--gray-2)"},
    )


def _patient_multiselect_row(p: PatientOption) -> rx.Component:
    """Ligne patient avec checkbox pour la multi-sélection."""
    is_selected = NotificationsState.compose_patient_ids.contains(p.id)
    return rx.hstack(
        rx.checkbox(
            checked=is_selected,
            on_change=lambda _: NotificationsState.toggle_compose_patient(p.id),
            size="2",
        ),
        rx.text(p.display, size="2"),
        spacing="2",
        align="center",
        width="100%",
        padding="0.3rem 0.5rem",
        border_radius="var(--radius-1)",
        background=rx.cond(is_selected, "var(--accent-3)", "transparent"),
        _hover={"background": rx.cond(is_selected, "var(--accent-4)", "var(--gray-2)")},
        cursor="pointer",
        on_click=NotificationsState.toggle_compose_patient(p.id),
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
                rx.separator(width="100%"),
                # Mode toggle
                rx.hstack(
                    rx.text(LanguageState.tr["send_to_label"], size="2", weight="medium"),
                    rx.segmented_control.root(
                        rx.segmented_control.item(LanguageState.tr["send_to_patient"], value="patient"),
                        rx.segmented_control.item(LanguageState.tr["send_to_account"], value="account"),
                        value=NotificationsState.compose_mode,
                        on_change=NotificationsState.set_compose_mode,
                        size="2",
                    ),
                    spacing="3",
                    align="center",
                ),
                # ── Multi-canal : checkboxes ──────────────────────────────
                rx.vstack(
                    rx.text(LanguageState.tr["channel_label"], size="2", weight="medium"),
                    rx.hstack(
                        _channel_checkbox(LanguageState.tr["channel_email"], "EMAIL", "blue"),
                        _channel_checkbox(LanguageState.tr["channel_sms"], "SMS", "orange"),
                        _channel_checkbox(LanguageState.tr["channel_whatsapp"], "WHATSAPP", "green"),
                        spacing="2",
                        flex_wrap="wrap",
                    ),
                    rx.text(
                        "Vous pouvez sélectionner plusieurs canaux simultanément.",
                        size="1",
                        color="var(--gray-9)",
                    ),
                    spacing="2",
                    width="100%",
                ),
                # ── Destinataires ─────────────────────────────────────────
                rx.cond(
                    NotificationsState.compose_mode == "patient",
                    rx.vstack(
                        rx.hstack(
                            rx.text("Patients destinataires", size="2", weight="medium"),
                            rx.cond(
                                NotificationsState.compose_patient_ids.length() > 0,
                                rx.badge(
                                    NotificationsState.compose_patient_ids.length(),
                                    color_scheme="blue",
                                    size="1",
                                ),
                            ),
                            spacing="2",
                            align="center",
                        ),
                        # ── Filtres ────────────────────────────────────────
                        rx.hstack(
                            rx.input(
                                placeholder="Chercher par nom ou numéro…",
                                value=NotificationsState.compose_patient_search,
                                on_change=NotificationsState.set_compose_patient_search,
                                size="2",
                                width="100%",
                            ),
                            rx.select.root(
                                rx.select.trigger(placeholder="Filtrer par campagne"),
                                rx.select.content(
                                    rx.select.item("— Toutes les campagnes —", value="__all__"),
                                    rx.foreach(
                                        NotificationsState.campaigns,
                                        _campaign_option,
                                    ),
                                ),
                                value=NotificationsState.compose_campaign_filter_id,
                                on_change=NotificationsState.set_compose_campaign_filter,
                                size="2",
                                width="180px",
                            ),
                            spacing="2",
                            align="center",
                            width="100%",
                        ),
                        rx.box(
                            rx.foreach(
                                NotificationsState.patients_filtered,
                                _patient_multiselect_row,
                            ),
                            max_height="220px",
                            overflow_y="auto",
                            border="1px solid var(--gray-4)",
                            border_radius="var(--radius-2)",
                            padding="0.25rem",
                            width="100%",
                        ),
                        rx.text(
                            "Cliquez sur les patients pour les sélectionner / désélectionner.",
                            size="1",
                            color="var(--gray-9)",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(LanguageState.tr["send_to_account"], size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(placeholder=LanguageState.tr["select_account_notif"]),
                            rx.select.content(
                                rx.foreach(NotificationsState.accounts, _account_option)
                            ),
                            value=NotificationsState.compose_account_id,
                            on_change=NotificationsState.set_compose_account,
                            size="2",
                            width="100%",
                        ),
                        rx.text(
                            LanguageState.tr["account_patients_note"],
                            size="1",
                            color="var(--gray-9)",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                ),
                # Subject (si EMAIL sélectionné)
                rx.cond(
                    NotificationsState.compose_channels.contains("EMAIL"),
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
                        rx.hstack(rx.icon("pencil-line", size=15), rx.text(LanguageState.tr["tab_compose"]), spacing="1", align="center"),
                        value="compose",
                    ),
                    rx.tabs.trigger(
                        rx.hstack(rx.icon("history", size=15), rx.text(LanguageState.tr["tab_history"]), spacing="1", align="center"),
                        value="history",
                    ),
                ),
                rx.tabs.content(_compose_tab(), value="compose", padding_top="1rem"),
                rx.tabs.content(_history_tab(), value="history", padding_top="1rem"),
                default_value="compose",
                width="100%",
            ),
        )
    )
