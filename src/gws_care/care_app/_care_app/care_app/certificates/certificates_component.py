"""UI component for the medical certificates list page."""

import reflex as rx

from ..common.page_layout import page_layout
from .certificates_state import CertificateRowDTO, CertificatesState


def _fit_badge(row: CertificateRowDTO) -> rx.Component:
    return rx.cond(
        row.is_fit_for_work,
        rx.badge("Apte", color_scheme="green", variant="soft", size="1"),
        rx.badge("Inapte", color_scheme="red", variant="solid", size="1"),
    )


def _certificate_row(row: CertificateRowDTO) -> rx.Component:
    return rx.table.row(
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
        rx.table.cell(rx.text(row.issue_date, size="2")),
        rx.table.cell(_fit_badge(row)),
        rx.table.cell(
            rx.text(
                row.conclusion,
                size="2",
                max_width="280px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            )
        ),
        rx.table.cell(
            rx.cond(
                row.restrictions != "",
                rx.text(
                    row.restrictions,
                    size="2",
                    color="var(--orange-11)",
                    max_width="200px",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                row.issued_by_name != "",
                rx.text(row.issued_by_name, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.icon_button(
                rx.icon("arrow-right", size=14),
                variant="ghost", size="1", color_scheme="gray",
                on_click=rx.redirect(f"/patient/{row.patient_id}"),
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _certificates_table() -> rx.Component:
    return rx.cond(
        CertificatesState.filtered_rows.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Patient"),
                    rx.table.column_header_cell("Date"),
                    rx.table.column_header_cell("Aptitude"),
                    rx.table.column_header_cell("Conclusion"),
                    rx.table.column_header_cell("Restrictions"),
                    rx.table.column_header_cell("Médecin rédacteur"),
                    rx.table.column_header_cell(""),
                )
            ),
            rx.table.body(
                rx.foreach(CertificatesState.filtered_rows, _certificate_row)
            ),
            width="100%",
            variant="surface",
            size="2",
        ),
        rx.center(
            rx.vstack(
                rx.icon("file-check", size=40, color="var(--gray-7)"),
                rx.text("Aucun certificat médical trouvé", size="3", color="var(--gray-9)"),
                rx.text(
                    "Les certificats médicaux émis depuis les dossiers patients apparaîtront ici.",
                    size="2", color="var(--gray-7)", text_align="center",
                ),
                align="center", spacing="2",
            ),
            padding="4rem",
        ),
    )


def _filter_btn(label: str, value: str) -> rx.Component:
    is_active = CertificatesState.fit_filter == value
    return rx.button(
        label,
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=rx.cond(is_active, "blue", "gray"),
        size="2",
        on_click=CertificatesState.set_fit_filter(value),
    )


def certificates_page() -> rx.Component:
    return page_layout(
        rx.hstack(
            rx.hstack(
                rx.icon("file-check", size=22, color="var(--accent-9)"),
                rx.heading("Certificats médicaux", size="6"),
                spacing="2", align="center",
            ),
            rx.spacer(),
            rx.badge(
                CertificatesState.filtered_rows.length().to_string(),
                " résultat(s)",
                color_scheme="gray", variant="soft", size="2",
            ),
            width="100%", align="center",
        ),
        rx.hstack(
            rx.input(
                placeholder="Rechercher un patient, médecin...",
                value=CertificatesState.search_query,
                on_change=CertificatesState.set_search,
                width="280px",
                size="2",
            ),
            rx.separator(orientation="vertical", height="28px"),
            _filter_btn("Tous", "ALL"),
            _filter_btn("Aptes", "FIT"),
            _filter_btn("Inaptes", "NOT_FIT"),
            spacing="2", align="center",
        ),
        rx.cond(
            CertificatesState.error_message != "",
            rx.callout(
                CertificatesState.error_message,
                icon="triangle-alert",
                color_scheme="red", variant="soft",
            ),
            rx.fragment(),
        ),
        rx.cond(
            CertificatesState.is_loading,
            rx.center(rx.spinner(size="3"), padding="2rem"),
            _certificates_table(),
        ),
    )
