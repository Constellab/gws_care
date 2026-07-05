"""Doctor assigned exams page — per-patient rows with medical status and action link."""

import reflex as rx

from ..common.page_layout import page_layout
from .doctor_assigned_exams_state import (
    AssignedDoctorOption,
    AssignedExamRowDTO,
    DoctorAssignedExamsState,
)


def _medical_status_badge(row: AssignedExamRowDTO) -> rx.Component:
    """Colour-coded badge for CampaignPatient.medical_status."""
    return rx.match(
        row.medical_status,
        ("PENDING",                     rx.badge(row.medical_status_label, color_scheme="gray",   variant="soft", size="1")),
        ("LAB_ENTERED",                 rx.badge(row.medical_status_label, color_scheme="orange", variant="soft", size="1")),
        ("LAB_VALIDATED",               rx.badge(row.medical_status_label, color_scheme="amber",  variant="soft", size="1")),
        ("PSC_INTERPRETED",             rx.badge(row.medical_status_label, color_scheme="blue",   variant="soft", size="1")),
        ("PSC_VALIDATED",               rx.badge(row.medical_status_label, color_scheme="blue",   variant="soft", size="1")),
        ("TRANSMITTED_TREATING_DOCTOR", rx.badge(row.medical_status_label, color_scheme="teal",   variant="soft", size="1")),
        ("ENTERPRISE_VALIDATED",        rx.badge(row.medical_status_label, color_scheme="green",  variant="soft", size="1")),
        ("PUBLISHED",                   rx.badge(row.medical_status_label, color_scheme="green",  variant="soft", size="1")),
        rx.badge(row.medical_status_label, color_scheme="gray", variant="soft", size="1"),
    )


def _campaign_status_badge(row: AssignedExamRowDTO) -> rx.Component:
    return rx.match(
        row.campaign_status,
        ("draft",           rx.badge(row.campaign_status_label, color_scheme="gray",   variant="soft", size="1")),
        ("validated",       rx.badge(row.campaign_status_label, color_scheme="blue",   variant="soft", size="1")),
        ("terrain_exam",    rx.badge(row.campaign_status_label, color_scheme="amber",  variant="soft", size="1")),
        ("sample_analysis", rx.badge(row.campaign_status_label, color_scheme="orange", variant="soft", size="1")),
        ("lab_done",        rx.badge(row.campaign_status_label, color_scheme="teal",   variant="soft", size="1")),
        ("closed",          rx.badge(row.campaign_status_label, color_scheme="green",  variant="soft", size="1")),
        ("archived",        rx.badge(row.campaign_status_label, color_scheme="green",  variant="soft", size="1")),
        rx.badge(row.campaign_status_label, color_scheme="gray", variant="soft", size="1"),
    )


def _exam_row(row: AssignedExamRowDTO) -> rx.Component:
    return rx.table.row(
        # Médecin assigné
        rx.table.cell(
            rx.text(row.assigned_doctor_name, size="2", color="var(--gray-11)"),
        ),
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
                    content="Saisir / voir les résultats",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("external-link", size=14),
                        variant="soft", size="1", color_scheme="gray",
                        disabled=True,
                    ),
                    content="La campagne n'est pas en phase active",
                ),
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _doctor_option(opt: AssignedDoctorOption) -> rx.Component:
    return rx.select.item(opt.name, value=opt.id)


def doctor_assigned_exams_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("stethoscope", size=24, color="var(--accent-9)"),
                rx.heading("Mes examens assignés", size="6"),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("refresh-cw", size=16),
                    variant="ghost",
                    size="2",
                    on_click=DoctorAssignedExamsState.on_load,
                    title="Rafraîchir",
                ),
                spacing="3", align="center", width="100%",
            ),
            rx.separator(width="100%"),

            # Filters
            rx.hstack(
                # Doctor filter
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Tous les médecins",
                        size="2",
                        width="220px",
                    ),
                    rx.select.content(
                        rx.select.item("Tous les médecins", value="__all__"),
                        rx.foreach(
                            DoctorAssignedExamsState.available_doctors,
                            _doctor_option,
                        ),
                    ),
                    value=DoctorAssignedExamsState.filter_doctor_id,
                    on_change=DoctorAssignedExamsState.set_filter_doctor_id,
                    size="2",
                ),
                # Status filter
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Tous les statuts",
                        size="2",
                        width="220px",
                    ),
                    rx.select.content(
                        rx.select.item("Tous les statuts",         value="__all__"),
                        rx.select.item("En attente",               value="PENDING"),
                        rx.select.item("Résultats saisis",         value="LAB_ENTERED"),
                        rx.select.item("Résultats validés labo",   value="LAB_VALIDATED"),
                        rx.select.item("Interprétation PSC",       value="PSC_INTERPRETED"),
                        rx.select.item("Validé PSC",               value="PSC_VALIDATED"),
                        rx.select.item("Transmis médecin traitant", value="TRANSMITTED_TREATING_DOCTOR"),
                        rx.select.item("Validé médecin travail",   value="ENTERPRISE_VALIDATED"),
                        rx.select.item("Dossier terminé",          value="PUBLISHED"),
                    ),
                    value=DoctorAssignedExamsState.filter_status,
                    on_change=DoctorAssignedExamsState.set_filter_status,
                    size="2",
                ),
                # Text search
                rx.input(
                    placeholder="Rechercher (patient, examen, campagne…)",
                    value=DoctorAssignedExamsState.filter_search,
                    on_change=DoctorAssignedExamsState.set_filter_search,
                    size="2",
                    width="280px",
                ),
                spacing="3",
                wrap="wrap",
            ),

            # Loading / error / table
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
                                            "Aucun examen assigné pour l'instant.",
                                            size="3", color="var(--gray-9)", text_align="center",
                                        ),
                                        rx.text(
                                            "Un opérateur peut assigner des examens depuis le détail d'une campagne.",
                                            size="2", color="var(--gray-8)", text_align="center",
                                        ),
                                        spacing="2", align="center",
                                    ),
                                    rx.text(
                                        "Aucun résultat pour ces filtres.",
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
                                        rx.table.column_header_cell(rx.text("Médecin", size="2")),
                                        rx.table.column_header_cell(rx.text("Patient", size="2")),
                                        rx.table.column_header_cell(rx.text("Campagne", size="2")),
                                        rx.table.column_header_cell(rx.text("Statut campagne", size="2")),
                                        rx.table.column_header_cell(rx.text("Examen assigné", size="2")),
                                        rx.table.column_header_cell(rx.text("Avancement", size="2")),
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
