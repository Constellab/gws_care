"""Doctor Enterprise page component (US-130, US-131, US-132)."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .doctor_enterprise_state import DoctorEnterpriseState, EntDossierRowDTO


def _dossier_row(d: EntDossierRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(d.patient_name, size="2", weight="medium"),
                rx.text(d.patient_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(rx.text(d.campaign_name, size="2")),
        rx.table.cell(
            rx.badge(d.medical_status_label, color_scheme=d.medical_status_color, size="1", variant="soft")
        ),
        rx.table.cell(
            rx.cond(
                d.psc_notes != "",
                rx.tooltip(
                    rx.icon("file-text", size=14, color="var(--gray-9)"),
                    content=d.psc_notes,
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                d.patient_message != "",
                rx.tooltip(
                    rx.icon("mail", size=14, color="var(--accent-9)"),
                    content=d.patient_message,
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pen-line", size=14),
                        variant="ghost", size="1", color_scheme="violet",
                        on_click=lambda: DoctorEnterpriseState.open_dialog(
                            d.campaign_id, d.patient_id, d.patient_name,
                            d.enterprise_notes, d.patient_message
                        ),
                    ),
                    content="Ajouter / modifier l'interprétation",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("check", size=14),
                        variant="ghost", size="1", color_scheme="green",
                        on_click=lambda: DoctorEnterpriseState.validate_patient(d.campaign_id, d.patient_id),
                        disabled=d.medical_status != "ENTERPRISE_INTERPRETED",
                    ),
                    content="Valider l'interprétation entreprise",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("send", size=14),
                        variant="ghost", size="1", color_scheme="indigo",
                        on_click=lambda: DoctorEnterpriseState.publish_patient(d.campaign_id, d.patient_id),
                        disabled=d.medical_status != "ENTERPRISE_VALIDATED",
                    ),
                    content="Publier au patient",
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _interpretation_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text("Interprétation entreprise — "),
                    rx.text(DoctorEnterpriseState.dialog_patient_name, weight="bold"),
                    spacing="1",
                )
            ),
            rx.vstack(
                rx.callout(
                    "Le message patient sera visible par le patient après publication. Ne pas inclure de données médicales brutes.",
                    icon="info", color_scheme="blue", size="1",
                ),
                rx.text("Commentaire interne", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Notes internes (non visibles par le patient)…",
                    value=DoctorEnterpriseState.enterprise_notes_input,
                    on_change=DoctorEnterpriseState.set_enterprise_notes,
                    width="100%", rows="3",
                ),
                rx.text("Message destiné au patient *", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Message qui sera affiché dans l'espace patient…",
                    value=DoctorEnterpriseState.patient_message_input,
                    on_change=DoctorEnterpriseState.set_patient_message,
                    width="100%", rows="4",
                ),
                rx.cond(
                    DoctorEnterpriseState.dialog_error != "",
                    rx.callout(DoctorEnterpriseState.dialog_error, icon="info",
                               color_scheme="red", size="1"),
                ),
                spacing="3", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=DoctorEnterpriseState.close_dialog)),
                rx.button("Enregistrer", on_click=DoctorEnterpriseState.save_interpretation,
                          loading=DoctorEnterpriseState.is_saving),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="600px",
        ),
        open=DoctorEnterpriseState.dialog_open,
        on_open_change=lambda _: DoctorEnterpriseState.close_dialog(),
    )


def doctor_enterprise_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Espace Médecin Entreprise", size="6"),
                        rx.text("Dossiers PSC validés — interprétation et publication", size="2", color="var(--gray-9)"),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.button(rx.icon("refresh-cw", size=14), "Actualiser",
                              variant="soft", size="2", on_click=DoctorEnterpriseState.on_load),
                    width="100%", align="end",
                ),
                rx.cond(
                    DoctorEnterpriseState.error != "",
                    rx.callout(DoctorEnterpriseState.error, icon="info", color_scheme="red", size="2",
                               on_click=DoctorEnterpriseState.dismiss_messages, style={"cursor": "pointer"}),
                ),
                rx.cond(
                    DoctorEnterpriseState.success != "",
                    rx.callout(DoctorEnterpriseState.success, icon="check", color_scheme="green", size="2",
                               on_click=DoctorEnterpriseState.dismiss_messages, style={"cursor": "pointer"}),
                ),
                rx.cond(
                    DoctorEnterpriseState.dossiers_truncated,
                    rx.callout(
                        "Résultats limités à 500 dossiers. Utilisez les filtres Campagne ou Statut pour affiner la sélection.",
                        icon="triangle-alert",
                        color_scheme="orange",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    DoctorEnterpriseState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="4rem"),
                    rx.cond(
                        DoctorEnterpriseState.dossiers.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Patient"),
                                    rx.table.column_header_cell("Campagne"),
                                    rx.table.column_header_cell("Statut"),
                                    rx.table.column_header_cell("Interprétation PSC"),
                                    rx.table.column_header_cell("Message patient"),
                                    rx.table.column_header_cell("Actions"),
                                )
                            ),
                            rx.table.body(rx.foreach(DoctorEnterpriseState.dossiers, _dossier_row)),
                            width="100%", variant="surface",
                        ),
                        rx.center(
                            rx.text("Aucun dossier disponible.", size="2", color="var(--gray-9)"),
                            padding="4rem",
                        ),
                    ),
                ),
                spacing="4", width="100%",
            ),
            _interpretation_dialog(),
        )
    )
