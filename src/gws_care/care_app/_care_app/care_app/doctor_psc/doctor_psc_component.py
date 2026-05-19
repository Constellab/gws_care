"""Doctor PSC page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .doctor_psc_state import DossierRowDTO, DoctorPscState

_STATUS_FILTER_OPTIONS = [
    ("ALL", "Tous"),
    ("LAB_ENTERED", "Résultats saisis — en attente"),
    ("LAB_VALIDATED", "Labo validé — à interpréter"),
    ("PSC_INTERPRETED", "Interprété — à valider"),
    ("PSC_VALIDATED", "Validé PSC"),
]


def _dossier_row(d: DossierRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(d.patient_name, size="2", weight="medium"),
                rx.text(d.patient_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(rx.text(d.campaign_name, size="2")),
        rx.table.cell(rx.text(d.account_name, size="2")),
        rx.table.cell(rx.badge(d.medical_status_label, color_scheme=d.medical_status_color, size="1", variant="soft")),
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
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("clipboard-list", size=14),
                        variant="ghost", size="1", color_scheme="gray",
                        on_click=rx.redirect("/campaign-patient/" + d.campaign_id + "/" + d.patient_id),
                    ),
                    content="Voir les résultats saisis",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pen-line", size=14),
                        variant="ghost", size="1", color_scheme="blue",
                        on_click=lambda: DoctorPscState.open_interp_dialog(
                            d.campaign_id, d.patient_id, d.patient_name, d.psc_notes
                        ),
                    ),
                    content="Saisir / modifier l'interprétation",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("check", size=14),
                        variant="ghost", size="1", color_scheme="green",
                        on_click=lambda: DoctorPscState.validate_patient(d.campaign_id, d.patient_id),
                        disabled=d.medical_status != "PSC_INTERPRETED",
                    ),
                    content="Valider le dossier PSC",
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _interp_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text("Interprétation PSC — "), rx.text(DoctorPscState.interp_patient_name, weight="bold"),
                    spacing="1",
                )
            ),
            rx.vstack(
                rx.text("Interprétation / Conclusion *", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Saisir l'interprétation médicale…",
                    value=DoctorPscState.interp_notes,
                    on_change=DoctorPscState.set_interp_notes,
                    width="100%",
                    rows="6",
                ),
                spacing="2", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=DoctorPscState.close_interp_dialog)),
                rx.button("Enregistrer", on_click=DoctorPscState.save_interpretation,
                          loading=DoctorPscState.is_saving),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="600px",
        ),
        open=DoctorPscState.interp_dialog_open,
        on_open_change=lambda _: DoctorPscState.close_interp_dialog(),
    )


def doctor_psc_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("File d'attente — Médecin PSC", size="6"),
                        rx.text("Dossiers à interpréter et valider", size="2", color="var(--gray-9)"),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.select.root(
                        rx.select.trigger(placeholder="Filtrer par statut"),
                        rx.select.content(
                            *[rx.select.item(label, value=val) for val, label in _STATUS_FILTER_OPTIONS]
                        ),
                        value=DoctorPscState.filter_status,
                        on_change=DoctorPscState.set_filter_status,
                    ),
                    rx.button(rx.icon("refresh-cw", size=14), "Actualiser",
                              variant="soft", size="2", on_click=DoctorPscState.on_load),
                    width="100%", align="end", spacing="2",
                ),
                rx.cond(
                    DoctorPscState.error != "",
                    rx.callout(DoctorPscState.error, icon="info", color_scheme="red", size="2",
                               on_click=DoctorPscState.dismiss_messages, style={"cursor": "pointer"}),
                ),
                rx.cond(
                    DoctorPscState.success != "",
                    rx.callout(DoctorPscState.success, icon="check", color_scheme="green", size="2",
                               on_click=DoctorPscState.dismiss_messages, style={"cursor": "pointer"}),
                ),
                rx.cond(
                    DoctorPscState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="4rem"),
                    rx.cond(
                        DoctorPscState.dossiers.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Patient"),
                                    rx.table.column_header_cell("Campagne"),
                                    rx.table.column_header_cell("Entreprise"),
                                    rx.table.column_header_cell("Statut médical"),
                                    rx.table.column_header_cell("Interprétation"),
                                    rx.table.column_header_cell("Actions"),
                                )
                            ),
                            rx.table.body(rx.foreach(DoctorPscState.dossiers, _dossier_row)),
                            width="100%",
                            variant="surface",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("check", size=32, color="var(--green-9)"),
                                rx.text("Aucun dossier en attente.", size="2", color="var(--gray-9)"),
                                align="center", spacing="2",
                            ),
                            padding="4rem",
                        ),
                    ),
                ),
                spacing="4", width="100%",
            ),
            _interp_dialog(),
        )
    )
