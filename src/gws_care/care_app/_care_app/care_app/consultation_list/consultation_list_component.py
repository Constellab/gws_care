"""UI component for the consultations list page — Patient | Entreprise tabs."""

import reflex as rx

from ..common.page_layout import page_layout
from .consultation_list_state import ConsultationListRowDTO, ConsultationListState


# ── Helpers ───────────────────────────────────────────────────────────────────

def _status_chip(row: ConsultationListRowDTO) -> rx.Component:
    return rx.cond(
        row.has_conclusion,
        rx.badge("Conclu", color_scheme="green", variant="soft", size="1"),
        rx.badge("En cours", color_scheme="orange", variant="soft", size="1"),
    )


def _type_badge(row: ConsultationListRowDTO) -> rx.Component:
    return rx.match(
        row.consultation_type,
        ("enterprise", rx.badge("Entreprise", color_scheme="blue", variant="soft", size="1")),
        ("patient", rx.badge("Patient", color_scheme="violet", variant="soft", size="1")),
        rx.badge(row.consultation_type, color_scheme="gray", variant="soft", size="1"),
    )


# ── Table row ─────────────────────────────────────────────────────────────────

def _consultation_row(row: ConsultationListRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.link(
                    row.patient_name,
                    href=f"/patient/{row.patient_id}",
                    size="2",
                    color="var(--accent-9)",
                ),
                rx.text(row.patient_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(rx.text(row.consultation_date, size="2")),
        rx.table.cell(
            rx.cond(
                row.reason_for_visit != "",
                rx.text(
                    row.reason_for_visit,
                    size="2",
                    max_width="240px",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                row.billing_account_name != "",
                rx.text(row.billing_account_name, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.badge(
                row.exam_count.to_string(),
                " examen(s)",
                color_scheme="blue",
                variant="soft",
                size="1",
            )
        ),
        rx.table.cell(_status_chip(row)),
        rx.table.cell(
            rx.icon_button(
                rx.icon("arrow-right", size=14),
                variant="ghost",
                size="1",
                color_scheme="gray",
                on_click=rx.redirect(f"/patient/{row.patient_id}"),
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


# ── Table ─────────────────────────────────────────────────────────────────────

def _consultations_table() -> rx.Component:
    return rx.cond(
        ConsultationListState.filtered_rows.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Patient"),
                    rx.table.column_header_cell("Date"),
                    rx.table.column_header_cell("Motif"),
                    rx.table.column_header_cell("Compte / Entreprise"),
                    rx.table.column_header_cell("Examens"),
                    rx.table.column_header_cell("Statut"),
                    rx.table.column_header_cell(""),
                )
            ),
            rx.table.body(
                rx.foreach(ConsultationListState.filtered_rows, _consultation_row)
            ),
            width="100%",
            variant="surface",
            size="2",
        ),
        rx.center(
            rx.vstack(
                rx.icon("stethoscope", size=40, color="var(--gray-7)"),
                rx.text("Aucune consultation trouvée", size="3", color="var(--gray-9)"),
                rx.text(
                    "Les consultations créées depuis les dossiers patients apparaîtront ici.",
                    size="2",
                    color="var(--gray-7)",
                    text_align="center",
                ),
                align="center",
                spacing="2",
            ),
            padding="4rem",
        ),
    )


# ── Tab button ────────────────────────────────────────────────────────────────

def _tab_btn(label: str, icon_tag: str, tab_id: str) -> rx.Component:
    is_active = ConsultationListState.active_tab == tab_id
    return rx.button(
        rx.icon(icon_tag, size=14),
        label,
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=rx.cond(is_active, "blue", "gray"),
        size="2",
        on_click=ConsultationListState.set_tab(tab_id),
    )


# ── Page ─────────────────────────────────────────────────────────────────────

def consultation_list_page() -> rx.Component:
    return page_layout(
        # Header
        rx.hstack(
            rx.vstack(
                rx.heading("Consultations", size="5"),
                rx.text(
                    "Consultations privées — examens hors campagne de masse",
                    size="2",
                    color="var(--gray-9)",
                ),
                spacing="1",
            ),
            rx.spacer(),
            width="100%",
            align="center",
        ),
        # Tabs + search bar
        rx.hstack(
            _tab_btn("Tous", "layout-list", "tous"),
            _tab_btn("Patient", "user", "patient"),
            _tab_btn("Entreprise", "building-2", "enterprise"),
            rx.spacer(),
            rx.debounce_input(
                rx.input(
                    placeholder="Rechercher patient, motif…",
                    value=ConsultationListState.search_query,
                    on_change=ConsultationListState.set_search,
                    width="280px",
                    size="2",
                ),
                debounce_timeout=350,
            ),
            rx.text(
                ConsultationListState.total_count.to(str),
                " résultat(s)",
                size="2",
                color="var(--gray-9)",
            ),
            width="100%",
            align="center",
            flex_wrap="wrap",
            spacing="2",
        ),
        rx.separator(width="100%"),
        # Content
        rx.cond(
            ConsultationListState.is_loading,
            rx.center(rx.spinner(size="3"), padding="3rem"),
            rx.vstack(
                rx.cond(
                    ConsultationListState.error_message != "",
                    rx.callout(
                        ConsultationListState.error_message,
                        icon="triangle-alert",
                        color_scheme="red",
                        variant="soft",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                _consultations_table(),
                # Pagination
                rx.cond(
                    ConsultationListState.total_pages > 1,
                    rx.hstack(
                        rx.text(
                            ConsultationListState.total_count.to(str),
                            " consultation(s) — page ",
                            ConsultationListState.page.to(str),
                            " / ",
                            ConsultationListState.total_pages.to(str),
                            size="2",
                            color="var(--gray-9)",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("chevron-left", size=14),
                            on_click=ConsultationListState.prev_page,
                            variant="soft", size="2",
                            disabled=~ConsultationListState.has_prev_page,
                        ),
                        rx.button(
                            rx.icon("chevron-right", size=14),
                            on_click=ConsultationListState.next_page,
                            variant="soft", size="2",
                            disabled=~ConsultationListState.has_next_page,
                        ),
                        width="100%",
                        align="center",
                        padding_top="0.5rem",
                    ),
                ),
                width="100%",
                spacing="3",
            ),
        ),
    )
