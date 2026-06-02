"""Campaigns list page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .campaign_list_state import CampaignListRowDTO, CampaignListState, ExamTypeOption

_STATUS_OPTIONS = [
    ("ALL", "Tous les statuts"),
    ("DRAFT", "Brouillon"),
    ("AWAITING_OP_VALIDATION", "En attente validation"),
    ("OPERATIONALLY_VALIDATED", "Validée opé"),
    ("AWAITING_MEDICAL_VALIDATION", "En attente médicale"),
    ("MEDICALLY_VALIDATED", "Validée médicalement"),
    ("READY_FOR_CONVOCATION", "Prête convocations"),
    ("CONVOCATIONS_SENT", "Convocations envoyées"),
    ("TERRAIN_EN_COURS", "Terrain en cours"),
    ("TERRAIN_CLOTURE", "Terrain clôturé"),
    ("LABO_EN_COURS", "Labo en cours"),
    ("LABO_VALIDE", "Labo validé"),
    ("VALIDE_MEDECIN_PSC", "Validé PSC"),
    ("PUBLIE_MEDECIN_ENTREPRISE", "Publié médecin entreprise"),
    ("PUBLIE_PATIENT", "Publié patient"),
    ("ARCHIVED", "Archivée"),
]


def _selected_exam_chip(exam: ExamTypeOption) -> rx.Component:
    """Badge amovible représentant un type d'examen sélectionné."""
    return rx.badge(
        exam.name,
        rx.icon(
            "x",
            size=12,
            cursor="pointer",
            on_click=CampaignListState.remove_exam_from_campaign(exam.id),
            style={"margin_left": "4px"},
        ),
        color_scheme="blue",
        variant="soft",
        size="2",
        cursor="default",
    )


def _campaign_row(c: CampaignListRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.link(c.name, href=f"/campaign/{c.id}",
                    style={"font_weight": "500", "color": "var(--accent-9)", "_hover": {"text_decoration": "underline"}})
        ),
        rx.table.cell(rx.text(c.company_name, size="2")),
        rx.table.cell(rx.badge(c.status_label, color_scheme=c.status_color, size="1", variant="soft")),
        rx.table.cell(rx.text(rx.cond(c.start_date != "", c.start_date, "—"), size="2")),
        rx.table.cell(rx.text(rx.cond(c.location != "", c.location, "—"), size="2")),
        rx.table.cell(rx.text(c.patient_count, size="2")),
        rx.table.cell(rx.text(rx.cond(c.psc_doctor_name != "", c.psc_doctor_name, "—"), size="2")),
        rx.table.cell(
            rx.hstack(
                rx.icon_button(
                    rx.icon("chevron-right", size=14),
                    variant="ghost", size="1",
                    on_click=lambda: CampaignListState.go_to_campaign(c.id),
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("archive", size=14),
                        variant="ghost", size="1", color_scheme="orange",
                        on_click=CampaignListState.open_confirm_archive(c.id, c.name),
                    ),
                    content="Archiver la campagne",
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}, "cursor": "pointer"},
        on_click=lambda: CampaignListState.go_to_campaign(c.id),
    )


def _create_campaign_dialog() -> rx.Component:
    """Dialog pour créer une nouvelle campagne."""
    exam_option_items = rx.foreach(
        CampaignListState.exam_type_options,
        lambda opt: rx.select.item(opt.name + " (" + opt.category_label + ")", value=opt.id),
    )
    company_option_items = rx.foreach(
        CampaignListState.company_options,
        lambda opt: rx.select.item(opt.name, value=opt.id),
    )
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("plus-circle", size=18, color="var(--accent-9)"),
                    rx.text("Nouvelle campagne"),
                    spacing="2",
                ),
            ),
            rx.vstack(
                # Nom
                rx.vstack(
                    rx.text("Nom de la campagne *", size="2", weight="medium"),
                    rx.input(
                        placeholder="Ex. Bilan annuel 2026 — Entreprise XYZ",
                        value=CampaignListState.create_name,
                        on_change=CampaignListState.set_create_name,
                        size="2",
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                # Entreprise
                rx.vstack(
                    rx.text("Entreprise *", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Sélectionner une entreprise…"),
                        rx.select.content(company_option_items),
                        value=CampaignListState.create_company_id,
                        on_change=CampaignListState.set_create_company_id,
                        size="2",
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                # Dates
                rx.grid(
                    rx.vstack(
                        rx.text("Date de début", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=CampaignListState.create_start_date,
                            on_change=CampaignListState.set_create_start_date,
                            size="2",
                            width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Date de fin", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=CampaignListState.create_end_date,
                            on_change=CampaignListState.set_create_end_date,
                            size="2",
                            width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),
                # Lieu
                rx.vstack(
                    rx.text("Lieu", size="2", weight="medium"),
                    rx.input(
                        placeholder="Ex. Site Paris — Bâtiment B",
                        value=CampaignListState.create_location,
                        on_change=CampaignListState.set_create_location,
                        size="2",
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                # Types d'examens
                rx.vstack(
                    rx.text("Types d'examens", size="2", weight="medium"),
                    rx.hstack(
                        rx.select.root(
                            rx.select.trigger(placeholder="Ajouter un examen…"),
                            rx.select.content(exam_option_items),
                            value=CampaignListState.create_add_exam_select,
                            on_change=CampaignListState.add_exam_to_campaign,
                            size="2",
                        ),
                        spacing="2", width="100%", align="center",
                    ),
                    rx.cond(
                        CampaignListState.create_selected_exams.length() > 0,
                        rx.hstack(
                            rx.foreach(CampaignListState.create_selected_exams, _selected_exam_chip),
                            flex_wrap="wrap",
                            spacing="2",
                        ),
                        rx.fragment(),
                    ),
                    spacing="2", width="100%",
                ),
                # Notes
                rx.vstack(
                    rx.text("Notes", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Contexte, instructions particulières…",
                        value=CampaignListState.create_notes,
                        on_change=CampaignListState.set_create_notes,
                        size="2",
                        width="100%",
                        rows="3",
                    ),
                    spacing="1", width="100%",
                ),
                # Erreur
                rx.cond(
                    CampaignListState.create_error != "",
                    rx.callout(
                        CampaignListState.create_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                # Actions
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Annuler",
                            variant="soft",
                            color_scheme="gray",
                            on_click=CampaignListState.close_create_dialog,
                        ),
                    ),
                    rx.button(
                        rx.icon("plus", size=14),
                        "Créer la campagne",
                        on_click=CampaignListState.submit_create,
                        loading=CampaignListState.is_creating,
                    ),
                    justify="end",
                    spacing="2",
                    margin_top="0.5rem",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="560px",
        ),
        open=CampaignListState.show_create_dialog,
        on_open_change=lambda _: CampaignListState.close_create_dialog(),
    )


def campaigns_list_page() -> rx.Component:
    return main_component(
        page_layout(
            _create_campaign_dialog(),
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Campagnes médicales", size="6"),
                        rx.text("Toutes les campagnes de médecine préventive", size="2", color="var(--gray-9)"),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=14),
                        "Nouvelle campagne",
                        on_click=CampaignListState.go_to_create,
                        size="2",
                    ),
                    width="100%", align="end",
                ),
                # Filters
                rx.card(
                    rx.hstack(
                        rx.input(
                            placeholder="Rechercher par nom…",
                            value=CampaignListState.search,
                            on_change=CampaignListState.set_search,
                            flex="1",
                        ),
                        rx.select.root(
                            rx.select.trigger(placeholder="Statut"),
                            rx.select.content(
                                *[rx.select.item(label, value=val) for val, label in _STATUS_OPTIONS]
                            ),
                            value=CampaignListState.filter_status,
                            on_change=CampaignListState.set_filter_status,
                        ),
                        rx.button(
                            rx.icon("refresh-cw", size=14), "Actualiser",
                            variant="soft", size="2",
                            on_click=CampaignListState.on_load,
                        ),
                        spacing="3", width="100%", align="center",
                    ),
                    width="100%",
                ),
                rx.cond(
                    CampaignListState.error != "",
                    rx.callout(CampaignListState.error, icon="info", color_scheme="red", size="2"),
                ),
                rx.cond(
                    CampaignListState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="4rem"),
                    rx.cond(
                        CampaignListState.campaigns.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Nom"),
                                    rx.table.column_header_cell("Compte"),
                                    rx.table.column_header_cell("Statut"),
                                    rx.table.column_header_cell("Début"),
                                    rx.table.column_header_cell("Lieu"),
                                    rx.table.column_header_cell("Patients"),
                                    rx.table.column_header_cell("Médecin PSC"),
                                    rx.table.column_header_cell(""),
                                )
                            ),
                            rx.table.body(rx.foreach(CampaignListState.campaigns, _campaign_row)),
                            width="100%",
                            variant="surface",
                        ),
                        rx.center(
                            rx.text("Aucune campagne trouvée.", size="2", color="var(--gray-9)"),
                            padding="4rem",
                        ),
                    ),
                ),
                # ── Pagination ──────────────────────────────────────────────
                rx.cond(
                    CampaignListState.total_count > 0,
                    rx.hstack(
                        rx.text(
                            CampaignListState.total_count.to(str)
                            + " campagne(s) — page ",
                            CampaignListState.page.to(str),
                            " / ",
                            CampaignListState.total_pages.to(str),
                            size="2",
                            color="var(--gray-9)",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("chevron-left", size=14),
                            on_click=CampaignListState.prev_page,
                            variant="soft",
                            size="2",
                            disabled=~CampaignListState.has_prev_page,
                        ),
                        rx.button(
                            rx.icon("chevron-right", size=14),
                            on_click=CampaignListState.next_page,
                            variant="soft",
                            size="2",
                            disabled=~CampaignListState.has_next_page,
                        ),
                        width="100%",
                        align="center",
                        padding_top="0.5rem",
                    ),
                ),
                spacing="4",
                width="100%",
            ),
            # ── Confirm archivage campagne ────────────────────────────────────
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(
                        rx.hstack(rx.icon("archive", size=18, color="var(--orange-9)"),
                                  rx.text("Archiver cette campagne ?"), spacing="2"),
                    ),
                    rx.dialog.description(
                        rx.vstack(
                            rx.text(
                                "La campagne « ",
                                rx.text.strong(CampaignListState.confirm_archive_name),
                                " » sera archivée et passée au statut ARCHIVÉE.",
                                size="2",
                            ),
                            rx.text("Les données (patients, examens) sont conservées.",
                                    size="2", color="var(--gray-9)"),
                            spacing="2",
                        ),
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Annuler", variant="soft", color_scheme="gray",
                                      on_click=CampaignListState.dismiss_confirm_archive),
                        ),
                        rx.button("Archiver", color_scheme="orange",
                                  on_click=CampaignListState.confirmed_archive),
                        justify="end", spacing="2", margin_top="1rem", width="100%",
                    ),
                    max_width="440px",
                ),
                open=CampaignListState.confirm_archive_open,
                on_open_change=lambda _: CampaignListState.dismiss_confirm_archive(),
            ),
        )
    )

