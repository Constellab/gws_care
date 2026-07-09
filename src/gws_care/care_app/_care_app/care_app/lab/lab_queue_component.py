"""Lab queue page component — list of exams with pending lab analyses."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .lab_queue_state import LabQueueRowDTO, LabQueueState


def _queue_row(row: LabQueueRowDTO) -> rx.Component:
    source_badge = rx.match(
        row.source,
        ("consultation", rx.badge(LanguageState.tr["visit_type_consultation"], color_scheme="blue", variant="soft", size="1")),
        ("campaign", rx.badge(LanguageState.tr["visit_type_campaign"], color_scheme="violet", variant="soft", size="1")),
        ("appointment", rx.badge(LanguageState.tr["nav_appointments"], color_scheme="teal", variant="soft", size="1")),
        rx.fragment(),
    )
    action_button = rx.match(
        row.source,
        (
            "consultation",
            rx.button(
                rx.icon("flask-conical", size=13),
                "Enter results",
                on_click=rx.redirect("/exam/" + row.exam_id),
                size="2",
                color_scheme="blue",
                variant="soft",
            ),
        ),
        (
            "campaign",
            rx.button(
                rx.icon("flask-conical", size=13),
                "Ouvrir le dossier",
                on_click=rx.redirect("/campaign-patient/" + row.campaign_id + "/" + row.patient_id),
                size="2",
                color_scheme="violet",
                variant="soft",
            ),
        ),
        (
            "appointment",
            rx.cond(
                row.exam_id != "",
                rx.button(
                    rx.icon("flask-conical", size=13),
                    "Enter results",
                    on_click=rx.redirect("/exam/" + row.exam_id),
                    size="2",
                    color_scheme="teal",
                    variant="soft",
                ),
                rx.button(
                    rx.icon("calendar", size=13),
                    "Voir le patient",
                    on_click=rx.redirect("/patient/" + row.patient_id),
                    size="2",
                    color_scheme="teal",
                    variant="soft",
                ),
            ),
        ),
        rx.fragment(),
    )
    # Extra info line: campaign name or doctor name
    extra_info = rx.match(
        row.source,
        ("campaign", rx.cond(
            row.campaign_name != "",
            rx.text(row.campaign_name, size="1", color="var(--gray-9)"),
            rx.fragment(),
        )),
        ("appointment", rx.cond(
            row.doctor_name != "",
            rx.text("Dr. " + row.doctor_name, size="1", color="var(--gray-9)"),
            rx.fragment(),
        )),
        rx.fragment(),
    )
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(row.exam_date, size="2"),
                source_badge,
                spacing="1",
                align="start",
            )
        ),
        rx.table.cell(
            rx.vstack(
                rx.link(
                    row.patient_name,
                    href="/patient/" + row.patient_id,
                    size="2",
                    weight="medium",
                ),
                extra_info,
                spacing="0",
                align="start",
            )
        ),
        rx.table.cell(rx.text(row.exam_type_label, size="2")),
        rx.table.cell(
            rx.vstack(
                rx.text(row.param_names, size="1", color="var(--gray-11)"),
                rx.hstack(
                    rx.cond(
                        row.pending_count > 0,
                        rx.badge(
                            row.pending_count.to_string() + " en attente",
                            color_scheme="orange",
                            variant="soft",
                            size="1",
                        ),
                        rx.badge(
                            "Complet",
                            color_scheme="green",
                            variant="soft",
                            size="1",
                        ),
                    ),
                    rx.badge(
                        row.param_count.to_string() + " analyses",
                        color_scheme="gray",
                        variant="outline",
                        size="1",
                    ),
                    spacing="1",
                ),
                spacing="1",
                align="start",
            )
        ),
        rx.table.cell(action_button),
    )


def _queue_table() -> rx.Component:
    return rx.cond(
        LabQueueState.filtered_rows,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Date / Source"),
                    rx.table.column_header_cell("Patient"),
                    rx.table.column_header_cell("Type d'examen"),
                    rx.table.column_header_cell("Analyses prescrites"),
                    rx.table.column_header_cell(""),
                )
            ),
            rx.table.body(
                rx.foreach(LabQueueState.filtered_rows, _queue_row),
            ),
            width="100%",
            size="2",
        ),
        rx.vstack(
            rx.icon("flask-conical", size=40, color="var(--gray-5)"),
            rx.text(LanguageState.tr["no_analysis_in_category"], size="3", weight="medium", color="var(--gray-9)"),
            rx.text(
                "Prescribed analyses (consultations, campaigns and appointments) will appear here.",
                size="2",
                color="var(--gray-8)",
            ),
            align="center",
            spacing="3",
            padding_y="4rem",
            width="100%",
        ),
    )


def lab_queue_page() -> rx.Component:
    return page_layout(
        main_component(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.heading(LanguageState.tr["lab_queue_title"], size="6"),
                        rx.text(
                            "Prescribed analyses (consultations + campaigns + appointments) awaiting results",
                            size="2",
                            color="var(--gray-9)",
                        ),
                        spacing="1",
                    ),
                    rx.button(
                        rx.icon("refresh-cw", size=14),
                        "Actualiser",
                        on_click=LabQueueState.refresh,
                        size="2",
                        variant="outline",
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                rx.divider(),
                # ── Status filter ─────────────────────────────────────────
                rx.hstack(
                    rx.text(LanguageState.tr["show_label"], size="2", color="var(--gray-9)"),
                    rx.segmented_control.root(
                        rx.segmented_control.item("Pending", value="pending"),
                        rx.segmented_control.item("Complete", value="done"),
                        rx.segmented_control.item("All", value="all"),
                        value=LabQueueState.status_filter,
                        on_change=LabQueueState.set_status_filter,
                        size="1",
                    ),
                    spacing="3",
                    align="center",
                ),
                rx.cond(
                    LabQueueState.error_message != "",
                    rx.callout(
                        LabQueueState.error_message,
                        icon="triangle-alert",
                        color_scheme="red",
                        width="100%",
                    ),
                ),
                rx.cond(
                    LabQueueState.is_loading,
                    rx.center(rx.spinner(size="3"), width="100%", padding_y="4rem"),
                    _queue_table(),
                ),
                width="100%",
                spacing="4",
                padding="2rem",
            ),
        )
    )
