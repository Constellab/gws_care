"""Prebilling page component (US-190, US-191)."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .prebilling_state import PrebillingRowVM, PrebillingState


def _prebilling_row(p: PrebillingRowVM) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p.account_name, size="2", weight="medium")),
        rx.table.cell(rx.text(p.campaign_name, size="2")),
        rx.table.cell(rx.text(rx.cond(p.period_start != "", p.period_start, "—"), size="2")),
        rx.table.cell(
            rx.text(
                rx.cond(p.total_amount > 0, f"{p.total_amount:.2f} €", "0,00 €"),
                size="2", weight="medium",
            )
        ),
        rx.table.cell(
            rx.badge(p.status_label, color_scheme=p.status_color, size="1", variant="soft")
        ),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    p.status == "DRAFT",
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("check", size=14), variant="ghost", size="1", color_scheme="blue",
                            on_click=lambda: PrebillingState.validate_prebilling(p.id),
                        ),
                        content="Valider la préfacturation",
                    ),
                ),
                rx.cond(
                    p.status == "VALIDATED",
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("file-text", size=14), variant="ghost", size="1", color_scheme="green",
                            on_click=lambda: PrebillingState.generate_invoice(p.id),
                        ),
                        content="Générer la facture définitive",
                    ),
                ),
                spacing="1",
            )
        ),
    )


def _gen_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Générer une préfacturation"),
            rx.dialog.description(
                "La préfacturation est calculée sur la base des patients présents dans la campagne sélectionnée.",
                size="2", color="var(--gray-9)",
            ),
            rx.vstack(
                rx.vstack(
                    rx.text("Campagne *", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Sélectionner une campagne", width="100%"),
                        rx.select.content(
                            rx.foreach(
                                PrebillingState.campaign_options,
                                lambda c: rx.select.item(c.name, value=c.id),
                            )
                        ),
                        value=PrebillingState.gen_campaign_id,
                        on_change=PrebillingState.set_gen_campaign,
                    ),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.text("Prix unitaire (€)", size="2", weight="medium"),
                    rx.input(
                        type="number",
                        value=PrebillingState.gen_unit_price,
                        on_change=PrebillingState.set_gen_unit_price,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.cond(
                    PrebillingState.gen_error != "",
                    rx.callout(PrebillingState.gen_error, icon="info", color_scheme="red", size="1"),
                ),
                spacing="3", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=PrebillingState.close_gen_dialog)),
                rx.button("Générer", on_click=PrebillingState.generate_prebilling,
                          loading=PrebillingState.is_generating),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="480px",
        ),
        open=PrebillingState.gen_dialog_open,
        on_open_change=lambda _: PrebillingState.close_gen_dialog(),
    )


def prebilling_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Préfacturation", size="6"),
                        rx.text("Gestion des préfacturations et factures", size="2", color="var(--gray-9)"),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.button(rx.icon("plus", size=16), "Générer",
                              on_click=PrebillingState.open_gen_dialog),
                    width="100%", align="end",
                ),
                rx.cond(
                    PrebillingState.error != "",
                    rx.callout(PrebillingState.error, icon="info", color_scheme="red", size="2",
                               on_click=PrebillingState.dismiss_messages, style={"cursor": "pointer"}),
                ),
                rx.cond(
                    PrebillingState.success != "",
                    rx.callout(PrebillingState.success, icon="check", color_scheme="green", size="2",
                               on_click=PrebillingState.dismiss_messages, style={"cursor": "pointer"}),
                ),
                rx.cond(
                    PrebillingState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="4rem"),
                    rx.cond(
                        PrebillingState.prebillings.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Compte"),
                                    rx.table.column_header_cell("Campagne"),
                                    rx.table.column_header_cell("Période"),
                                    rx.table.column_header_cell("Montant"),
                                    rx.table.column_header_cell("Statut"),
                                    rx.table.column_header_cell(""),
                                )
                            ),
                            rx.table.body(rx.foreach(PrebillingState.prebillings, _prebilling_row)),
                            width="100%", variant="surface",
                        ),
                        rx.center(
                            rx.text("Aucune préfacturation.", size="2", color="var(--gray-9)"),
                            padding="4rem",
                        ),
                    ),
                ),
                spacing="4", width="100%",
            ),
            _gen_dialog(),
        )
    )
