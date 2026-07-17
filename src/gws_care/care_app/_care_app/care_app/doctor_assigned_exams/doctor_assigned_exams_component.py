"""Doctor assigned exams page — role-based task dashboard."""

import reflex as rx

from ..admin.general_settings_state import GeneralSettingsState
from ..common.page_layout import page_layout
from .doctor_assigned_exams_state import (
    AssignedDoctorOption,
    AssignedExamRowDTO,
    DoctorAssignedExamsState,
)


def _medical_status_badge(row: AssignedExamRowDTO) -> rx.Component:
    return rx.match(
        row.medical_status,
        # Campaign medical statuses
        ("PENDING",                     rx.badge(row.medical_status_label, color_scheme="gray",   variant="soft", size="1")),
        ("LAB_ENTERED",                 rx.badge(row.medical_status_label, color_scheme="orange", variant="soft", size="1")),
        ("LAB_VALIDATED",               rx.badge(row.medical_status_label, color_scheme="amber",  variant="soft", size="1")),
        ("INTERNAL_INTERPRETED",        rx.badge(row.medical_status_label, color_scheme="blue",   variant="soft", size="1")),
        ("INTERNAL_VALIDATED",          rx.badge(row.medical_status_label, color_scheme="blue",   variant="soft", size="1")),
        ("TRANSMITTED_TREATING_DOCTOR", rx.badge(row.medical_status_label, color_scheme="teal",   variant="soft", size="1")),
        ("ENTERPRISE_VALIDATED",        rx.badge(row.medical_status_label, color_scheme="green",  variant="soft", size="1")),
        ("PUBLISHED",                   rx.badge(row.medical_status_label, color_scheme="green",  variant="soft", size="1")),
        # Exam statuses (private consultations)
        ("todo",                        rx.badge(row.medical_status_label, color_scheme="gray",   variant="soft", size="1")),
        ("in_progress_results",         rx.badge(row.medical_status_label, color_scheme="orange", variant="soft", size="1")),
        ("transmitted_to_lab",          rx.badge(row.medical_status_label, color_scheme="amber",  variant="soft", size="1")),
        ("in_progress_interpretation",  rx.badge(row.medical_status_label, color_scheme="blue",   variant="soft", size="1")),
        ("done",                        rx.badge(row.medical_status_label, color_scheme="green",  variant="soft", size="1")),
        rx.badge(row.medical_status_label, color_scheme="gray", variant="soft", size="1"),
    )


def _campaign_status_badge(row: AssignedExamRowDTO) -> rx.Component:
    return rx.match(
        row.campaign_status,
        ("",            rx.fragment()),
        ("draft",           rx.badge(row.campaign_status_label, color_scheme="gray",   variant="soft", size="1")),
        ("validated",       rx.badge(row.campaign_status_label, color_scheme="blue",   variant="soft", size="1")),
        ("terrain_exam",    rx.badge(row.campaign_status_label, color_scheme="amber",  variant="soft", size="1")),
        ("sample_analysis", rx.badge(row.campaign_status_label, color_scheme="orange", variant="soft", size="1")),
        ("lab_done",        rx.badge(row.campaign_status_label, color_scheme="teal",   variant="soft", size="1")),
        ("closed",          rx.badge(row.campaign_status_label, color_scheme="green",  variant="soft", size="1")),
        ("archived",        rx.badge(row.campaign_status_label, color_scheme="green",  variant="soft", size="1")),
        rx.badge(row.campaign_status_label, color_scheme="gray", variant="soft", size="1"),
    )


def _assignee_badge(row: AssignedExamRowDTO) -> rx.Component:
    """Badge or text for the Responsable column."""
    return rx.cond(
        row.row_type == "lab",
        rx.badge(
            rx.icon("flask-conical", size=11),
            "Lab",
            color_scheme="amber", variant="soft", size="1",
        ),
        rx.cond(
            row.row_type == "internal",
            rx.badge(
                rx.icon("stethoscope", size=11),
                GeneralSettingsState.org_acronym,
                color_scheme="blue", variant="soft", size="1",
            ),
            rx.text(row.assigned_doctor_name, size="2", color="var(--gray-11)"),
        ),
    )


def _exam_row(row: AssignedExamRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(_assignee_badge(row)),
        # Patient
        rx.table.cell(
            rx.vstack(
                rx.text(row.patient_name, size="2", weight="medium"),
                rx.text(row.patient_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        # Campagne
        rx.table.cell(
            rx.vstack(
                rx.text(row.campaign_name, size="2"),
                rx.text(row.campaign_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        # Date RDV
        rx.table.cell(
            rx.cond(
                row.scheduled_at != "",
                rx.text(row.scheduled_at, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        # Statut campagne
        rx.table.cell(_campaign_status_badge(row)),
        # Examen assigné
        rx.table.cell(
            rx.vstack(
                rx.text(row.exam_type_name, size="2"),
                rx.cond(
                    row.exam_category != "",
                    rx.text(row.exam_category, size="1", color="var(--gray-9)"),
                    rx.fragment(),
                ),
                spacing="0",
            )
        ),
        # Avancement
        rx.table.cell(_medical_status_badge(row)),
        # À faire
        rx.table.cell(
            rx.cond(
                row.pending_task != "",
                rx.badge(row.pending_task, color_scheme=row.pending_task_color, variant="soft", size="1"),
                rx.fragment(),
            ),
        ),
        # Action
        rx.table.cell(
            rx.cond(
                row.can_act,
                rx.tooltip(
                    rx.link(
                        rx.icon_button(
                            rx.icon("external-link", size=14),
                            variant="soft", size="1", color_scheme="indigo",
                        ),
                        href=row.action_url,
                    ),
                    content="Enter / view results",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("external-link", size=14),
                        variant="soft", size="1", color_scheme="gray", disabled=True,
                    ),
                    content="The campaign is not in an active phase",
                ),
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _assignee_option(opt: AssignedDoctorOption) -> rx.Component:
    return rx.select.item(opt.name, value=opt.id)


def doctor_assigned_exams_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # ── Header ────────────────────────────────────────────────────────
            rx.hstack(
                rx.icon("stethoscope", size=24, color="var(--accent-9)"),
                rx.heading("My assigned exams", size="6"),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("refresh-cw", size=16),
                    variant="ghost",
                    size="2",
                    on_click=DoctorAssignedExamsState.on_load,
                    title="Refresh",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.separator(width="100%"),
            # ── Filters ───────────────────────────────────────────────────────
            rx.hstack(
                # Assignee filter (Labo / internal doctor / doctor name)
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Show all",
                        size="2",
                        width="220px",
                    ),
                    rx.select.content(
                        rx.select.item("Show all", value="__all__"),
                        rx.foreach(
                            DoctorAssignedExamsState.available_assignees,
                            _assignee_option,
                        ),
                    ),
                    value=DoctorAssignedExamsState.filter_assignee,
                    on_change=DoctorAssignedExamsState.set_filter_assignee,
                    size="2",
                ),
                # Source filter (Campagnes / Consultations privées)
                rx.select.root(
                    rx.select.trigger(
                        placeholder="All sources",
                        size="2",
                        width="220px",
                    ),
                    rx.select.content(
                        rx.select.item("All sources",          value="__all__"),
                        rx.select.item("Campaigns",            value="campaign"),
                        rx.select.item("Private consultations", value="private"),
                    ),
                    value=DoctorAssignedExamsState.filter_source,
                    on_change=DoctorAssignedExamsState.set_filter_source,
                    size="2",
                ),
                # Medical status filter — adapts to selected source
                rx.match(
                    DoctorAssignedExamsState.filter_source,
                    # Private consultations → exam statuses
                    (
                        "private",
                        rx.select.root(
                            rx.select.trigger(placeholder="All statuses", size="2", width="220px"),
                            rx.select.content(
                                rx.select.item("All statuses",                 value="__all__"),
                                rx.select.item("To do",                        value="todo"),
                                rx.select.item("In progress — Results",        value="in_progress_results"),
                                rx.select.item("Sent to lab",                  value="transmitted_to_lab"),
                                rx.select.item("In progress — Interpretation", value="in_progress_interpretation"),
                                rx.select.item("Completed",                    value="done"),
                            ),
                            value=DoctorAssignedExamsState.filter_status,
                            on_change=DoctorAssignedExamsState.set_filter_status,
                            size="2",
                        ),
                    ),
                    # Default (all sources or campaign) → campaign medical statuses
                    rx.select.root(
                        rx.select.trigger(placeholder="All statuses", size="2", width="220px"),
                        rx.select.content(
                            rx.select.item("All statuses",              value="__all__"),
                            rx.select.item("Pending",                   value="PENDING"),
                            rx.select.item("Results entered",           value="LAB_ENTERED"),
                            rx.select.item("Lab validated",             value="LAB_VALIDATED"),
                            rx.select.item(f"{GeneralSettingsState.org_acronym} interpretation", value="INTERNAL_INTERPRETED"),
                            rx.select.item(f"{GeneralSettingsState.org_acronym} validated",      value="INTERNAL_VALIDATED"),
                            rx.select.item("Sent to treating doctor",   value="TRANSMITTED_TREATING_DOCTOR"),
                            rx.select.item("Work doctor validated",     value="ENTERPRISE_VALIDATED"),
                            rx.select.item("Record completed",          value="PUBLISHED"),
                            rx.select.item("To do",                     value="todo"),
                            rx.select.item("In progress — Results",     value="in_progress_results"),
                            rx.select.item("Sent to lab",               value="transmitted_to_lab"),
                            rx.select.item("In progress — Interpretation", value="in_progress_interpretation"),
                            rx.select.item("Completed",                 value="done"),
                        ),
                        value=DoctorAssignedExamsState.filter_status,
                        on_change=DoctorAssignedExamsState.set_filter_status,
                        size="2",
                    ),
                ),
                # Text search
                rx.input(
                    placeholder="Search (patient, exam, campaign…)",
                    value=DoctorAssignedExamsState.filter_search,
                    on_change=DoctorAssignedExamsState.set_filter_search,
                    size="2",
                    width="280px",
                ),
                spacing="3",
                wrap="wrap",
            ),
            # ── Loading / error / table ───────────────────────────────────────
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
                        DoctorAssignedExamsState.filtered_rows.length() == 0,
                        rx.center(
                            rx.vstack(
                                rx.icon("inbox", size=48, color="var(--gray-6)"),
                                rx.cond(
                                    DoctorAssignedExamsState.rows.length() == 0,
                                    rx.vstack(
                                        rx.text(
                                            "No assigned task for now.",
                                            size="3", color="var(--gray-9)", text_align="center",
                                        ),
                                        rx.text(
                                            "Tasks appear here once exams are assigned "
                                            "in a campaign's detail page.",
                                            size="2", color="var(--gray-8)", text_align="center",
                                        ),
                                        spacing="2", align="center",
                                    ),
                                    rx.text(
                                        "No result for these filters.",
                                        size="3", color="var(--gray-9)", text_align="center",
                                    ),
                                ),
                                spacing="3", align="center",
                            ),
                            padding="4rem",
                            border="1px dashed var(--gray-5)",
                            border_radius="12px",
                            width="100%",
                        ),
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell(rx.text("Assignee", size="2")),
                                        rx.table.column_header_cell(rx.text("Patient",      size="2")),
                                        rx.table.column_header_cell(rx.text("Campaign",  size="2")),
                                        rx.table.column_header_cell(rx.text("Appt. date", size="2")),
                                        rx.table.column_header_cell(rx.text("Camp. status", size="2")),
                                        rx.table.column_header_cell(rx.text("Examen",       size="2")),
                                        rx.table.column_header_cell(rx.text("Progress", size="2")),
                                        rx.table.column_header_cell(rx.text("To do",    size="2")),
                                        rx.table.column_header_cell(""),
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(DoctorAssignedExamsState.filtered_rows, _exam_row)
                                ),
                                width="100%",
                                variant="surface",
                            ),
                            overflow_x="auto",
                            width="100%",
                        ),
                    ),
                ),
            ),
            width="100%",
            spacing="4",
        ),
    )
