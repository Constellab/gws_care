"""HR Portal page component — administrative data only, NO medical data (US-150)."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .hr_portal_state import HRCampaignDTO, HRPatientDTO, HRPortalState


def _campaign_row(c: HRCampaignDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(c.name, size="2", weight="medium")),
        rx.table.cell(rx.badge(c.status_label, color_scheme=c.status_color, size="1", variant="soft")),
        rx.table.cell(rx.text(rx.cond(c.start_date != "", c.start_date, "—"), size="2")),
        rx.table.cell(rx.text(rx.cond(c.location != "", c.location, "—"), size="2")),
        rx.table.cell(rx.text(c.total_patients, size="2")),
        rx.table.cell(
            rx.hstack(
                rx.badge(c.present_count, color_scheme="green", size="1"),
                rx.badge(c.absent_count, color_scheme="red", size="1"),
                rx.badge(c.pending_count, color_scheme="gray", size="1"),
                spacing="1",
            )
        ),
        rx.table.cell(
            rx.icon_button(
                rx.icon("chevron-right", size=14),
                variant="ghost", size="1",
                on_click=lambda: HRPortalState.select_campaign(c.id, c.name),
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}, "cursor": "pointer"},
        on_click=lambda: HRPortalState.select_campaign(c.id, c.name),
    )


def _patient_row(p: HRPatientDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p.patient_number, size="2", weight="medium")),
        rx.table.cell(rx.text(p.patient_name, size="2")),
        rx.table.cell(
            rx.cond(p.phone != "", rx.text(p.phone, size="2"), rx.text("—", size="2", color="var(--gray-7)"))
        ),
        rx.table.cell(rx.badge(p.presence_label, color_scheme=p.presence_color, size="1", variant="soft")),
        rx.table.cell(
            rx.cond(
                p.result_published,
                rx.badge("Résultat disponible", color_scheme="green", size="1", variant="soft"),
                rx.cond(
                    p.exam_done,
                    rx.badge("Examen réalisé", color_scheme="blue", size="1", variant="soft"),
                    rx.badge("En attente", color_scheme="gray", size="1", variant="soft"),
                ),
            )
        ),
    )


def hr_portal_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Espace RH Entreprise", size="6"),
                        rx.text("Suivi administratif des campagnes — données médicales non accessibles", size="2", color="var(--gray-9)"),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.button(rx.icon("refresh-cw", size=14), "Actualiser",
                              variant="soft", size="2", on_click=HRPortalState.on_load),
                    width="100%", align="end",
                ),
                rx.callout(
                    "Espace RH — aucune donnée médicale individuelle n'est affichée dans cet espace.",
                    icon="shield",
                    color_scheme="blue",
                    size="2",
                ),
                rx.cond(
                    HRPortalState.error != "",
                    rx.callout(HRPortalState.error, icon="info", color_scheme="red", size="2"),
                ),
                rx.cond(
                    HRPortalState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="4rem"),
                    rx.vstack(
                        # Campaigns table
                        rx.heading("Campagnes", size="4"),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Nom"),
                                    rx.table.column_header_cell("Statut"),
                                    rx.table.column_header_cell("Début"),
                                    rx.table.column_header_cell("Lieu"),
                                    rx.table.column_header_cell("Nb patients"),
                                    rx.table.column_header_cell("Présents / Absents / En attente"),
                                    rx.table.column_header_cell(""),
                                )
                            ),
                            rx.table.body(rx.foreach(HRPortalState.campaigns, _campaign_row)),
                            width="100%", variant="surface",
                        ),
                        # Selected campaign patients
                        rx.cond(
                            HRPortalState.selected_campaign_id != "",
                            rx.vstack(
                                rx.hstack(
                                    rx.heading(
                                        rx.hstack(
                                            rx.text("Patients — "),
                                            rx.text(HRPortalState.selected_campaign_name, weight="bold"),
                                            spacing="1",
                                        ),
                                        size="4",
                                    ),
                                    width="100%",
                                ),
                                rx.cond(
                                    HRPortalState.is_loading_patients,
                                    rx.center(rx.spinner(size="2")),
                                    rx.table.root(
                                        rx.table.header(
                                            rx.table.row(
                                                rx.table.column_header_cell("N° dossier"),
                                                rx.table.column_header_cell("Nom"),
                                                rx.table.column_header_cell("Téléphone"),
                                                rx.table.column_header_cell("Présence"),
                                                rx.table.column_header_cell("Statut examen"),
                                            )
                                        ),
                                        rx.table.body(rx.foreach(HRPortalState.patients, _patient_row)),
                                        width="100%", variant="surface",
                                    ),
                                ),
                                spacing="3", width="100%",
                            ),
                        ),
                        spacing="4", width="100%",
                    ),
                ),
                spacing="4", width="100%",
            )
        )
    )
