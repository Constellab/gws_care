"""Consultation list page component (/consultations)."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.empty_state_component import empty_state
from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..common.patient_picker_component import patient_picker_widget
from .consultation_list_state import (
    AccountOptionDTO,
    ConsultationListState,
    ConsultationRowDTO,
    PatientAccountOption,
)


def _status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("pending", rx.badge("En attente", color_scheme="gray", variant="soft", size="1")),
        ("cancelled", rx.badge("Annulée", color_scheme="red", variant="soft", size="1")),
        ("visit_done", rx.badge("Clôturée", color_scheme="green", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _consultation_row(row: ConsultationRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.cond(
                row.visit_number,
                rx.text(row.visit_number, size="2", weight="medium"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.link(
                row.patient_name,
                on_click=lambda: ConsultationListState.go_to_patient(row.patient_id),
                cursor="pointer",
                size="2",
            )
        ),
        rx.table.cell(
            rx.cond(
                row.account_name,
                rx.text(row.account_name, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                row.scheduled_at,
                rx.text(row.scheduled_at[:10], size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(_status_badge(row.status)),
        rx.table.cell(
            rx.cond(
                row.exam_count > 0,
                rx.badge(row.exam_count, color_scheme="blue", variant="soft", size="1"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)", "cursor": "pointer"}},
        on_click=lambda: ConsultationListState.go_to_consultation(row.id),
    )


def _account_option(account: AccountOptionDTO) -> rx.Component:
    return rx.select.item(account.name, value=account.id)


def _patient_account_option(option: PatientAccountOption) -> rx.Component:
    return rx.select.item(option.name, value=option.id)


def _new_consultation_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nouvelle consultation"),
            rx.vstack(
                rx.vstack(
                    rx.text("Patient *", size="2", weight="medium"),
                    patient_picker_widget(ConsultationListState),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Date prévue", size="2", weight="medium"),
                    rx.input(
                        type="date",
                        value=ConsultationListState.new_scheduled_at,
                        on_change=ConsultationListState.set_new_scheduled_at,
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.cond(
                    ConsultationListState.new_patient_accounts.length() > 0,
                    rx.vstack(
                        rx.text("Compte de facturation", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(placeholder="Sélectionner un compte"),
                            rx.select.content(
                                rx.foreach(
                                    ConsultationListState.new_patient_accounts,
                                    _patient_account_option,
                                )
                            ),
                            value=ConsultationListState.new_account_id,
                            on_change=ConsultationListState.set_new_account_id,
                            size="2",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                ),
                rx.cond(
                    ConsultationListState.new_error != "",
                    rx.callout.root(
                        rx.callout.icon(rx.icon("circle-alert", size=16)),
                        rx.callout.text(ConsultationListState.new_error),
                        color_scheme="red",
                        size="1",
                    ),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Annuler", variant="soft", color_scheme="gray", size="2"),
                    ),
                    rx.button(
                        "Créer",
                        on_click=ConsultationListState.save_new_consultation,
                        loading=ConsultationListState.new_is_saving,
                        size="2",
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="480px",
            on_interact_outside=ConsultationListState.close_new_dialog,
            on_escape_key_down=ConsultationListState.close_new_dialog,
        ),
        open=ConsultationListState.show_new_dialog,
    )


def _filters_bar() -> rx.Component:
    return rx.hstack(
        rx.input(
            placeholder="Rechercher un patient…",
            value=ConsultationListState.search,
            on_change=ConsultationListState.set_search,
            size="2",
            width="220px",
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Statut"),
            rx.select.content(
                rx.select.item("Tous les statuts", value="ALL"),
                rx.select.item("En attente", value="pending"),
                rx.select.item("Clôturée", value="visit_done"),
                rx.select.item("Annulée", value="cancelled"),
            ),
            value=ConsultationListState.filter_status,
            on_change=ConsultationListState.set_filter_status,
            size="2",
        ),
        rx.input(
            type="date",
            value=ConsultationListState.filter_date_from,
            on_change=ConsultationListState.set_filter_date_from,
            size="2",
        ),
        rx.input(
            type="date",
            value=ConsultationListState.filter_date_to,
            on_change=ConsultationListState.set_filter_date_to,
            size="2",
        ),
        rx.button(
            rx.icon("x", size=14),
            "Réinitialiser",
            variant="ghost",
            color_scheme="gray",
            size="2",
            on_click=ConsultationListState.clear_filters,
        ),
        spacing="2",
        wrap="wrap",
        align="center",
        width="100%",
    )


def _consultations_table() -> rx.Component:
    return rx.cond(
        ConsultationListState.is_loading,
        rx.center(rx.spinner(size="3"), padding_y="4em"),
        rx.cond(
            ConsultationListState.error_message != "",
            rx.callout.root(
                rx.callout.icon(rx.icon("circle-alert", size=16)),
                rx.callout.text(ConsultationListState.error_message),
                color_scheme="red",
            ),
            rx.cond(
                ConsultationListState.consultations.length() == 0,
                empty_state("stethoscope", "Aucune consultation trouvée."),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(rx.text("N° Visite", size="2")),
                            rx.table.column_header_cell(rx.text("Patient", size="2")),
                            rx.table.column_header_cell(rx.text("Compte", size="2")),
                            rx.table.column_header_cell(rx.text("Date prévue", size="2")),
                            rx.table.column_header_cell(rx.text("Statut", size="2")),
                            rx.table.column_header_cell(rx.text("Examens", size="2")),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            ConsultationListState.consultations,
                            _consultation_row,
                        )
                    ),
                    width="100%",
                    variant="surface",
                ),
            ),
        ),
    )


def consultation_list_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                rx.hstack(
                    rx.heading("Consultations", size="6"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nouvelle consultation",
                        on_click=ConsultationListState.open_new_dialog,
                        size="2",
                    ),
                    width="100%",
                    align="center",
                ),
                _filters_bar(),
                _consultations_table(),
                _new_consultation_dialog(),
                spacing="4",
                width="100%",
                padding="1.5em",
            )
        )
    )
