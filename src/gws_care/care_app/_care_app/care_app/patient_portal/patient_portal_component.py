"""Patient portal page components (7.5).

Three pages sharing PatientPortalState:
  /my-results       — visits completed by company doctor
  /my-appointments  — upcoming & past appointments
  /my-documents     — medical certificates
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .patient_portal_state import (
    PatientPortalState,
    PortalAppointmentDTO,
    PortalDocumentDTO,
    PortalExamResultDTO,
    PortalMessageDTO,
)

# ── Shared sub-components ─────────────────────────────────────────────────────


def _portal_nav() -> rx.Component:
    """Horizontal sub-nav tabs for the portal."""
    return rx.hstack(
        rx.button(
            rx.icon("file-heart", size=15),
            LanguageState.tr["nav_my_results"],
            variant="ghost",
            size="2",
            on_click=PatientPortalState.go_to_results,
        ),
        rx.button(
            rx.icon("calendar-check", size=15),
            LanguageState.tr["nav_my_appointments"],
            variant="ghost",
            size="2",
            on_click=PatientPortalState.go_to_appointments,
        ),
        rx.button(
            rx.icon("mail", size=15),
            LanguageState.tr["nav_my_messages"],
            variant="ghost",
            size="2",
            on_click=PatientPortalState.go_to_messages,
        ),
        rx.button(
            rx.icon("file-text", size=15),
            LanguageState.tr["nav_my_documents"],
            variant="ghost",
            size="2",
            on_click=PatientPortalState.go_to_documents,
        ),
        spacing="2",
        padding_bottom="0.5rem",
        border_bottom="1px solid var(--gray-4)",
        width="100%",
    )


# ── My Results ────────────────────────────────────────────────────────────────


def _visit_result_card(v: PortalExamResultDTO) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.heading(v.exam_type_label, size="4"),
                    rx.hstack(
                        rx.icon("calendar", size=13, color="var(--gray-9)"),
                        rx.text(v.exam_date, size="2", color="var(--gray-9)"),
                        rx.cond(
                            v.visit_number != "",
                            rx.fragment(
                                rx.separator(orientation="vertical"),
                                rx.text(v.visit_number, size="2", color="var(--gray-9)"),
                            ),
                        ),
                        rx.cond(
                            v.campaign_name != "",
                            rx.fragment(
                                rx.separator(orientation="vertical"),
                                rx.text(v.campaign_name, size="2", color="var(--gray-9)"),
                            ),
                        ),
                        spacing="1",
                        align="center",
                    ),
                    spacing="1",
                    align_items="start",
                ),
                rx.spacer(),
                rx.badge(v.status_label, color_scheme="green", size="2"),
                align="start",
                width="100%",
            ),
            rx.cond(
                v.interpretation != "",
                rx.vstack(
                    rx.text(
                        LanguageState.tr["patient_message_label"] + ":",
                        size="2",
                        weight="medium",
                        color="var(--gray-11)",
                    ),
                    rx.box(
                        rx.text(v.interpretation, size="2"),
                        padding="0.75rem",
                        border_radius="var(--radius-2)",
                        background="var(--accent-2)",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
            ),
            width="100%",
            spacing="3",
        )
    )


def my_results_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.heading(LanguageState.tr["my_results_title"], size="6"),
            _portal_nav(),
            rx.cond(
                PatientPortalState.visits_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    PatientPortalState.visits_error != "",
                    rx.callout(
                        PatientPortalState.visits_error,
                        color_scheme="red",
                        icon="triangle-alert",
                    ),
                    rx.cond(
                        PatientPortalState.portal_exam_results.length() == 0,
                        rx.center(
                            rx.vstack(
                                rx.icon("file-search", size=40, color="var(--gray-7)"),
                                rx.text(LanguageState.tr["no_visits_portal"], size="3", color="var(--gray-9)"),
                                spacing="3",
                                align="center",
                            ),
                            padding="4rem",
                        ),
                        rx.vstack(
                            rx.foreach(PatientPortalState.portal_exam_results, _visit_result_card),
                            width="100%",
                            spacing="3",
                        ),
                    ),
                ),
            ),
        )
    )


# ── My Appointments ───────────────────────────────────────────────────────────


def _appointment_row(a: PortalAppointmentDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(a.scheduled_at, size="2")),
        rx.table.cell(rx.text(a.visit_number, size="2")),
        rx.table.cell(
            rx.match(
                a.status,
                ("scheduled", rx.badge(a.status_label, color_scheme="blue", variant="soft", size="1")),
                ("in_progress", rx.badge(a.status_label, color_scheme="amber", variant="soft", size="1")),
                ("done", rx.badge(a.status_label, color_scheme="green", variant="soft", size="1")),
                ("cancelled", rx.badge(a.status_label, color_scheme="red", variant="soft", size="1")),
                rx.badge(a.status_label, color_scheme="gray", variant="soft", size="1"),
            )
        ),
        rx.table.cell(""),
    )


def my_appointments_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.heading(LanguageState.tr["my_appointments_title"], size="6"),
            _portal_nav(),
            rx.cond(
                PatientPortalState.appointments_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    PatientPortalState.appointments_error != "",
                    rx.callout(
                        PatientPortalState.appointments_error,
                        color_scheme="red",
                        icon="triangle-alert",
                    ),
                    rx.cond(
                        PatientPortalState.portal_appointments.length() == 0,
                        rx.center(
                            rx.vstack(
                                rx.icon("calendar-x", size=40, color="var(--gray-7)"),
                                rx.text(LanguageState.tr["no_appts_portal"], size="3", color="var(--gray-9)"),
                                spacing="3",
                                align="center",
                            ),
                            padding="4rem",
                        ),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell(LanguageState.tr["col_date"]),
                                    rx.table.column_header_cell(LanguageState.tr["col_visit_number"]),
                                    rx.table.column_header_cell(LanguageState.tr["col_status"]),
                                    rx.table.column_header_cell(""),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(PatientPortalState.portal_appointments, _appointment_row)
                            ),
                            width="100%",
                        ),
                    ),
                ),
            ),
        )
    )


# ── My Documents ─────────────────────────────────────────────────────────────


def _document_card(doc: PortalDocumentDTO) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(doc.issue_date, size="2", weight="medium"),
                    rx.cond(
                        doc.issued_by != "",
                        rx.text(doc.issued_by, size="1", color="var(--gray-9)"),
                    ),
                    spacing="0",
                    align_items="start",
                ),
                rx.spacer(),
                rx.cond(
                    doc.is_fit_for_work,
                    rx.badge(LanguageState.tr.get("fit_for_work", "Apte"), color_scheme="green", size="2"),
                    rx.badge(LanguageState.tr.get("not_fit_for_work", "Inapte"), color_scheme="red", size="2"),
                ),
                align="center",
                width="100%",
            ),
            rx.cond(
                doc.conclusion != "",
                rx.text(doc.conclusion, size="2", color="var(--gray-11)"),
            ),
            rx.cond(
                doc.restrictions != "",
                rx.hstack(
                    rx.icon("circle_alert", size=13, color="var(--amber-9)"),
                    rx.text(doc.restrictions, size="2", color="var(--amber-11)"),
                    spacing="1",
                    align="center",
                ),
            ),
            rx.button(
                rx.icon("file-down", size=14),
                "Télécharger le certificat PDF",
                variant="soft",
                size="1",
                color_scheme="blue",
                on_click=lambda: PatientPortalState.download_certificate_pdf(doc.id),
            ),
            width="100%",
            spacing="2",
        )
    )


def my_documents_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.heading(LanguageState.tr["my_documents_title"], size="6"),
            _portal_nav(),
            rx.cond(
                PatientPortalState.documents_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    PatientPortalState.documents_error != "",
                    rx.callout(
                        PatientPortalState.documents_error,
                        color_scheme="red",
                        icon="triangle-alert",
                    ),
                    rx.cond(
                        PatientPortalState.portal_documents.length() == 0,
                        rx.center(
                            rx.vstack(
                                rx.icon("file-x", size=40, color="var(--gray-7)"),
                                rx.text(LanguageState.tr["no_documents_portal"], size="3", color="var(--gray-9)"),
                                spacing="3",
                                align="center",
                            ),
                            padding="4rem",
                        ),
                        rx.vstack(
                            rx.foreach(PatientPortalState.portal_documents, _document_card),
                            width="100%",
                            spacing="3",
                        ),
                    ),
                ),
            ),
        )
    )


# ── My Messages ───────────────────────────────────────────────────────────────


def _message_card(msg: PortalMessageDTO) -> rx.Component:
    """Card displaying a single notification/message received by the patient."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(msg.subject, size="2", weight="medium"),
                    rx.hstack(
                        rx.cond(
                            msg.sent_at != "",
                            rx.text(
                                LanguageState.tr["msg_sent_at_label"] + " : " + msg.sent_at,
                                size="1",
                                color="var(--gray-9)",
                            ),
                        ),
                        rx.cond(
                            msg.channel != "",
                            rx.badge(msg.channel, color_scheme="gray", variant="outline", size="1"),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    spacing="1",
                    align_items="start",
                ),
                rx.spacer(),
                rx.cond(
                    msg.status == "SENT",
                    rx.icon("circle_check", size=14, color="var(--green-9)"),
                    rx.cond(
                        msg.status == "FAILED",
                        rx.icon("circle_x", size=14, color="var(--red-9)"),
                        rx.icon("clock", size=14, color="var(--gray-7)"),
                    ),
                ),
                align="start",
                width="100%",
            ),
            rx.cond(
                msg.body != "",
                rx.box(
                    rx.text(msg.body, size="2", color="var(--gray-11)"),
                    padding="0.75rem",
                    border_radius="var(--radius-2)",
                    background="var(--gray-2)",
                    width="100%",
                ),
            ),
            width="100%",
            spacing="2",
        )
    )


def my_messages_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.heading(LanguageState.tr["my_messages_title"], size="6"),
            _portal_nav(),
            rx.cond(
                PatientPortalState.messages_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    PatientPortalState.messages_error != "",
                    rx.callout(
                        PatientPortalState.messages_error,
                        color_scheme="red",
                        icon="triangle-alert",
                    ),
                    rx.cond(
                        PatientPortalState.portal_messages.length() == 0,
                        rx.center(
                            rx.vstack(
                                rx.icon("mail_open", size=40, color="var(--gray-7)"),
                                rx.text(LanguageState.tr["no_messages_portal"], size="3", color="var(--gray-9)"),
                                spacing="3",
                                align="center",
                            ),
                            padding="4rem",
                        ),
                        rx.vstack(
                            rx.foreach(PatientPortalState.portal_messages, _message_card),
                            width="100%",
                            spacing="3",
                        ),
                    ),
                ),
            ),
        )
    )
