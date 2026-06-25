"""Doctor assigned exams page — shows campaigns where this doctor is assigned to an exam type."""

import reflex as rx

from ..common.page_layout import page_layout
from .doctor_assigned_exams_state import AssignedExamRowDTO, DoctorAssignedExamsState


def _status_badge(row: AssignedExamRowDTO) -> rx.Component:
    return rx.match(
        row.campaign_status,
        ("draft", rx.badge(row.campaign_status_label, color_scheme="gray", variant="soft", size="1")),
        ("validated", rx.badge(row.campaign_status_label, color_scheme="blue", variant="soft", size="1")),
        ("in_progress", rx.badge(row.campaign_status_label, color_scheme="amber", variant="soft", size="1")),
        ("completed", rx.badge(row.campaign_status_label, color_scheme="green", variant="soft", size="1")),
        rx.badge(row.campaign_status_label, color_scheme="gray", variant="soft", size="1"),
    )


def _exam_row(row: AssignedExamRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(row.campaign_name, size="2", weight="medium"),
                rx.text(row.campaign_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(_status_badge(row)),
        rx.table.cell(rx.text(row.exam_type_name, size="2")),
        rx.table.cell(rx.text(row.exam_category, size="2", color="var(--gray-9)")),
        rx.table.cell(
            rx.badge(
                row.patient_count.to_string() + " patient(s)",
                color_scheme="blue", variant="soft", size="1",
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.link(
                        rx.icon_button(
                            rx.icon("external-link", size=14),
                            variant="soft", size="1", color_scheme="blue",
                        ),
                        href="/campaign/" + row.campaign_id,
                    ),
                    content="Voir la campagne",
                ),
                spacing="1",
            )
        ),
    )


def doctor_assigned_exams_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("stethoscope", size=24, color="var(--accent-9)"),
                rx.vstack(
                    rx.heading("Mes examens assignés", size="6"),
                    rx.cond(
                        DoctorAssignedExamsState.doctor_name != "",
                        rx.text(
                            "Connecté en tant que : " + DoctorAssignedExamsState.doctor_name,
                            size="2", color="var(--gray-9)",
                        ),
                        rx.fragment(),
                    ),
                    spacing="0",
                ),
                spacing="3", align="center", width="100%",
            ),
            rx.separator(width="100%"),
            # Loading / error states
            rx.cond(
                DoctorAssignedExamsState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    DoctorAssignedExamsState.error != "",
                    rx.callout(
                        DoctorAssignedExamsState.error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="2",
                        width="100%",
                    ),
                    rx.cond(
                        DoctorAssignedExamsState.rows.length() == 0,
                        rx.center(
                            rx.vstack(
                                rx.icon("inbox", size=48, color="var(--gray-6)"),
                                rx.text(
                                    "Aucun examen ne vous est assigné pour l'instant.",
                                    size="3", color="var(--gray-9)", text_align="center",
                                ),
                                rx.text(
                                    "Un opérateur peut vous assigner des types d'examens depuis le détail d'une campagne.",
                                    size="2", color="var(--gray-8)", text_align="center",
                                ),
                                spacing="3", align="center",
                            ),
                            padding="4rem",
                            border="1px dashed var(--gray-5)",
                            border_radius="12px",
                            width="100%",
                        ),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell(rx.text("Campagne", size="2")),
                                    rx.table.column_header_cell(rx.text("Statut", size="2")),
                                    rx.table.column_header_cell(rx.text("Examen assigné", size="2")),
                                    rx.table.column_header_cell(rx.text("Catégorie", size="2")),
                                    rx.table.column_header_cell(rx.text("Patients", size="2")),
                                    rx.table.column_header_cell(""),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(DoctorAssignedExamsState.rows, _exam_row)
                            ),
                            width="100%",
                            variant="surface",
                        ),
                    ),
                ),
            ),
            width="100%",
            spacing="4",
        )
    )
