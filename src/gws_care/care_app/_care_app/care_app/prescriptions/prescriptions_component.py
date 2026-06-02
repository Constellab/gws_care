"""UI component for the prescriptions list page."""

import reflex as rx

from ..common.page_layout import page_layout
from .prescriptions_state import PrescriptionRowDTO, PrescriptionsState


# ── Helpers ───────────────────────────────────────────────────────────────────

_TYPE_COLORS = {
    "DRUG": "blue",
    "LAB_ORDER": "violet",
    "IMAGING": "orange",
    "SPECIALIST": "teal",
    "PHYSIOTHERAPY": "green",
    "OTHER": "gray",
}


def _type_badge(row: PrescriptionRowDTO) -> rx.Component:
    return rx.match(
        row.prescription_type,
        ("DRUG", rx.badge(row.type_label, color_scheme="blue", variant="soft", size="1")),
        ("LAB_ORDER", rx.badge(row.type_label, color_scheme="violet", variant="soft", size="1")),
        ("IMAGING", rx.badge(row.type_label, color_scheme="orange", variant="soft", size="1")),
        ("SPECIALIST", rx.badge(row.type_label, color_scheme="teal", variant="soft", size="1")),
        ("PHYSIOTHERAPY", rx.badge(row.type_label, color_scheme="green", variant="soft", size="1")),
        rx.badge(row.type_label, color_scheme="gray", variant="soft", size="1"),
    )


def _prescription_row(row: PrescriptionRowDTO) -> rx.Component:
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
        rx.table.cell(rx.text(row.doctor_name, size="2")),
        rx.table.cell(_type_badge(row)),
        rx.table.cell(rx.text(row.issued_at, size="2")),
        rx.table.cell(
            rx.cond(
                row.valid_until != "",
                rx.text(row.valid_until, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.badge(
                row.line_count.to_string(), " ligne(s)",
                color_scheme="gray", variant="soft", size="1",
            )
        ),
        rx.table.cell(
            rx.cond(
                row.is_renewable,
                rx.badge("Renouvelable", color_scheme="green", variant="soft", size="1"),
                rx.fragment(),
            )
        ),
        rx.table.cell(
            rx.cond(
                row.consultation_id != "",
                rx.icon_button(
                    rx.icon("arrow-right", size=14),
                    variant="ghost", size="1", color_scheme="gray",
                    on_click=rx.redirect(f"/patient/{row.patient_id}"),
                ),
                rx.fragment(),
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _prescriptions_table() -> rx.Component:
    return rx.cond(
        PrescriptionsState.rows.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Patient"),
                    rx.table.column_header_cell("Médecin prescripteur"),
                    rx.table.column_header_cell("Type"),
                    rx.table.column_header_cell("Date"),
                    rx.table.column_header_cell("Valide jusqu'au"),
                    rx.table.column_header_cell("Lignes"),
                    rx.table.column_header_cell(""),
                    rx.table.column_header_cell(""),
                )
            ),
            rx.table.body(
                rx.foreach(PrescriptionsState.rows, _prescription_row)
            ),
            width="100%",
            variant="surface",
            size="2",
        ),
        rx.center(
            rx.vstack(
                rx.icon("pill", size=40, color="var(--gray-7)"),
                rx.text("Aucune ordonnance trouvée", size="3", color="var(--gray-9)"),
                rx.text(
                    "Les ordonnances émises depuis les dossiers patients apparaîtront ici.",
                    size="2", color="var(--gray-7)", text_align="center",
                ),
                align="center", spacing="2",
            ),
            padding="4rem",
        ),
    )


def _type_filter_btn(label: str, value: str) -> rx.Component:
    is_active = PrescriptionsState.type_filter == value
    return rx.button(
        label,
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=rx.cond(is_active, "blue", "gray"),
        size="2",
        on_click=PrescriptionsState.set_type_filter(value),
    )


def prescriptions_page() -> rx.Component:
    return page_layout(
        rx.hstack(
            rx.hstack(
                rx.icon("pill", size=22, color="var(--accent-9)"),
                rx.heading("Ordonnances", size="6"),
                spacing="2", align="center",
            ),
            rx.spacer(),
            rx.badge(
                PrescriptionsState.total_count.to(str),
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
                        placeholder="Rechercher un patient, médecin…",
                        value=PrescriptionsState.search_query,
                        on_change=PrescriptionsState.set_search,
                        width="280px",
                        size="2",
                    ),
                    debounce_timeout=350,
                ),
                rx.separator(orientation="vertical", height="28px"),
                _type_filter_btn("Tous", "ALL"),
                _type_filter_btn("Médicaments", "DRUG"),
                _type_filter_btn("Bilan bio", "LAB_ORDER"),
                _type_filter_btn("Imagerie", "IMAGING"),
                _type_filter_btn("Spécialiste", "SPECIALIST"),
                spacing="2", align="center", flex_wrap="wrap",
            ),
            rx.hstack(
                rx.text("Période :", size="2", color="var(--gray-9)", white_space="nowrap"),
                rx.input(
                    type="date",
                    value=PrescriptionsState.date_from,
                    on_change=PrescriptionsState.set_date_from,
                    size="2",
                ),
                rx.text("→", size="2", color="var(--gray-9)"),
                rx.input(
                    type="date",
                    value=PrescriptionsState.date_to,
                    on_change=PrescriptionsState.set_date_to,
                    size="2",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14),
                    "Réinitialiser",
                    on_click=PrescriptionsState.clear_filters,
                    variant="outline",
                    size="2",
                ),
                spacing="2", align="center", wrap="wrap", width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        # Error
        rx.cond(
            PrescriptionsState.error_message != "",
            rx.callout(
                PrescriptionsState.error_message,
                icon="triangle-alert",
                color_scheme="red", variant="soft",
            ),
            rx.fragment(),
        ),
        # Loading
        rx.cond(
            PrescriptionsState.is_loading,
            rx.center(rx.spinner(size="3"), padding="2rem"),
            rx.vstack(
                _prescriptions_table(),
                # Pagination
                rx.hstack(
                    rx.text(
                        PrescriptionsState.total_count.to(str),
                        " ordonnance(s) — page ",
                        PrescriptionsState.page.to(str),
                        " / ",
                        PrescriptionsState.total_pages.to(str),
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("chevron-left", size=14),
                        on_click=PrescriptionsState.prev_page,
                        variant="soft", size="2",
                        disabled=~PrescriptionsState.has_prev_page,
                    ),
                    rx.button(
                        rx.icon("chevron-right", size=14),
                        on_click=PrescriptionsState.next_page,
                        variant="soft", size="2",
                        disabled=~PrescriptionsState.has_next_page,
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
