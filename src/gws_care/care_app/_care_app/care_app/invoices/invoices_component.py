"""UI component for the patient invoices list page."""

import reflex as rx

from ..common.page_layout import page_layout
from .invoices_state import AccountFilterOption, InvoiceRowDTO, InvoicesState


def _status_badge(row: InvoiceRowDTO) -> rx.Component:
    return rx.badge(row.status_label, color_scheme=row.status_color, variant="soft", size="1")


def _invoice_row(row: InvoiceRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(row.invoice_number, size="2", weight="medium")),
        rx.table.cell(
            rx.vstack(
                rx.link(
                    row.patient_name,
                    href=rx.cond(row.patient_id != "", f"/patient/{row.patient_id}", "#"),
                    size="2",
                    color="var(--accent-9)",
                ),
                rx.text(row.patient_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(rx.text(row.invoice_date, size="2")),
        rx.table.cell(_status_badge(row)),
        rx.table.cell(
            rx.vstack(
                rx.text(row.total_ttc, " €", size="2", weight="medium"),
                rx.text("HT: ", row.total_ht, " €", size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(
            rx.cond(
                row.doctor_name != "",
                rx.text(row.doctor_name, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                row.account_name != "",
                rx.text(row.account_name, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.badge(
                row.line_count.to_string(), " acte(s)",
                color_scheme="gray", variant="soft", size="1",
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _invoices_table() -> rx.Component:
    return rx.cond(
        InvoicesState.rows.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("N° Facture"),
                    rx.table.column_header_cell("Patient"),
                    rx.table.column_header_cell("Date"),
                    rx.table.column_header_cell("Statut"),
                    rx.table.column_header_cell("Total TTC / HT"),
                    rx.table.column_header_cell("Médecin"),
                    rx.table.column_header_cell("Compte"),
                    rx.table.column_header_cell("Actes"),
                )
            ),
            rx.table.body(
                rx.foreach(InvoicesState.rows, _invoice_row)
            ),
            width="100%",
            variant="surface",
            size="2",
        ),
        rx.center(
            rx.vstack(
                rx.icon("receipt", size=40, color="var(--gray-7)"),
                rx.text("Aucune facture trouvée", size="3", color="var(--gray-9)"),
                rx.text(
                    "Les factures patient générées lors des consultations apparaîtront ici.",
                    size="2", color="var(--gray-7)", text_align="center",
                ),
                align="center", spacing="2",
            ),
            padding="4rem",
        ),
    )


def _filter_btn(label: str, value: str) -> rx.Component:
    is_active = InvoicesState.status_filter == value
    return rx.button(
        label,
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=rx.cond(is_active, "blue", "gray"),
        size="2",
        on_click=InvoicesState.set_status_filter(value),
    )


def _account_filter_option(account: AccountFilterOption) -> rx.Component:
    return rx.select.item(account.name, value=account.id)


def invoices_page() -> rx.Component:
    return page_layout(
        rx.hstack(
            rx.hstack(
                rx.icon("receipt", size=22, color="var(--accent-9)"),
                rx.heading("Factures patients", size="6"),
                spacing="2", align="center",
            ),
            rx.spacer(),
            rx.badge(
                InvoicesState.total_count.to(str),
                " résultat(s)",
                color_scheme="gray", variant="soft", size="2",
            ),
            width="100%", align="center",
        ),
        # Filters
        rx.vstack(
            rx.hstack(
                rx.debounce_input(
                    rx.input(
                        placeholder="Rechercher patient, N° facture…",
                        value=InvoicesState.search_query,
                        on_change=InvoicesState.set_search,
                        width="260px",
                        size="2",
                    ),
                    debounce_timeout=350,
                ),
                rx.select.root(
                    rx.select.trigger(placeholder="Tous les comptes"),
                    rx.select.content(
                        rx.select.item("Tous les comptes", value="ALL"),
                        rx.foreach(InvoicesState.account_options, _account_filter_option),
                    ),
                    value=InvoicesState.filter_account_id,
                    on_change=InvoicesState.set_filter_account,
                    size="2",
                ),
                rx.separator(orientation="vertical", height="28px"),
                _filter_btn("Toutes", "ALL"),
                _filter_btn("Brouillon", "DRAFT"),
                _filter_btn("Validées", "VALIDATED"),
                _filter_btn("Envoyées", "SENT"),
                _filter_btn("Payées", "PAID"),
                _filter_btn("Annulées", "CANCELLED"),
                spacing="2", align="center", flex_wrap="wrap",
            ),
            rx.hstack(
                rx.text("Période :", size="2", color="var(--gray-9)", white_space="nowrap"),
                rx.input(
                    type="date",
                    value=InvoicesState.date_from,
                    on_change=InvoicesState.set_date_from,
                    size="2",
                ),
                rx.text("→", size="2", color="var(--gray-9)"),
                rx.input(
                    type="date",
                    value=InvoicesState.date_to,
                    on_change=InvoicesState.set_date_to,
                    size="2",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14),
                    "Réinitialiser",
                    on_click=InvoicesState.clear_filters,
                    variant="outline",
                    size="2",
                ),
                spacing="2", align="center", wrap="wrap", width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        rx.cond(
            InvoicesState.error_message != "",
            rx.callout(
                InvoicesState.error_message,
                icon="triangle-alert",
                color_scheme="red", variant="soft",
            ),
            rx.fragment(),
        ),
        rx.cond(
            InvoicesState.is_loading,
            rx.center(rx.spinner(size="3"), padding="2rem"),
            rx.vstack(
                _invoices_table(),
                # Pagination
                rx.hstack(
                    rx.text(
                        InvoicesState.total_count.to(str),
                        " facture(s) — page ",
                        InvoicesState.page.to(str),
                        " / ",
                        InvoicesState.total_pages.to(str),
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("chevron-left", size=14),
                        on_click=InvoicesState.prev_page,
                        variant="soft", size="2",
                        disabled=~InvoicesState.has_prev_page,
                    ),
                    rx.button(
                        rx.icon("chevron-right", size=14),
                        on_click=InvoicesState.next_page,
                        variant="soft", size="2",
                        disabled=~InvoicesState.has_next_page,
                    ),
                    width="100%",
                    align="center",
                    padding_top="0.5rem",
                ),
                width="100%",
                spacing="2",
            ),
        ),
    )
