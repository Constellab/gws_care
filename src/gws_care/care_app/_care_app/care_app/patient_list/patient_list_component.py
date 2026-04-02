"""Patient list page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .patient_form_component import patient_form_dialog
from .patient_form_state import PatientFormState
from .patient_list_state import AccountOptionDTO, PatientListState, PatientRowDTO


def _gender_badge(gender: str) -> rx.Component:
    return rx.match(
        gender,
        ("M", rx.badge("M", color_scheme="blue", variant="soft")),
        ("F", rx.badge("F", color_scheme="pink", variant="soft")),
        rx.badge(gender, color_scheme="gray", variant="soft"),
    )


def _patient_row(patient: PatientRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(patient.patient_number, size="2", weight="medium")),
        rx.table.cell(
            rx.text(f"{patient.first_name} {patient.last_name}", size="2")
        ),
        rx.table.cell(rx.text(patient.date_of_birth, size="2")),
        rx.table.cell(_gender_badge(patient.gender)),
        rx.table.cell(
            rx.cond(patient.city, rx.text(patient.city, size="2"), rx.text("—", color="var(--gray-8)", size="2"))
        ),
        rx.table.cell(
            rx.cond(patient.phone, rx.text(patient.phone, size="2"), rx.text("—", color="var(--gray-8)", size="2"))
        ),
        rx.table.cell(
            rx.icon_button(
                rx.icon("chevron-right", size=16),
                variant="ghost",
                size="1",
                on_click=lambda: PatientListState.go_to_patient(patient.id),
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}, "cursor": "pointer"},
        on_click=lambda: PatientListState.go_to_patient(patient.id),
    )


def _account_filter_option(account: AccountOptionDTO) -> rx.Component:
    return rx.select.item(account.name, value=account.id)


def _filter_bar() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.input(
                placeholder="Patient number…",
                value=PatientListState.search_patient_number,
                on_change=PatientListState.handle_patient_number_change,
                min_width="180px",
                size="2",
            ),
            rx.input(
                placeholder="Search by name…",
                value=PatientListState.search_name,
                on_change=PatientListState.handle_name_change,
                min_width="220px",
                size="2",
            ),
            rx.input(
                placeholder="Phone…",
                value=PatientListState.search_phone,
                on_change=PatientListState.handle_phone_change,
                min_width="160px",
                size="2",
            ),
            rx.select.root(
                rx.select.trigger(placeholder="All Accounts"),
                rx.select.content(
                    rx.select.item("All Accounts", value="ALL"),
                    rx.foreach(PatientListState.companies, _account_filter_option),
                ),
                value=PatientListState.filter_account_id,
                on_change=PatientListState.set_filter_account,
                size="2",
            ),
            spacing="3",
            wrap="wrap",
            width="100%",
        ),
        rx.hstack(
            rx.text("Date of birth:", size="2", color="var(--gray-9)", white_space="nowrap"),
            rx.input(
                type="date",
                value=PatientListState.filter_dob_from,
                on_change=PatientListState.set_filter_dob_from,
                size="2",
            ),
            rx.text("→", size="2", color="var(--gray-9)"),
            rx.input(
                type="date",
                value=PatientListState.filter_dob_to,
                on_change=PatientListState.set_filter_dob_to,
                size="2",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("x", size=14),
                "Clear",
                on_click=PatientListState.clear_filters,
                variant="outline",
                size="2",
            ),
            spacing="2",
            align="center",
            wrap="wrap",
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def patient_list_page() -> rx.Component:
    """Patient list page."""
    return main_component(
        page_layout(
            rx.hstack(
                rx.heading("Patients", size="6"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    "New Patient",
                    on_click=PatientFormState.open_create_dialog,
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            patient_form_dialog(),
            _filter_bar(),
            rx.cond(
                PatientListState.error_message != "",
                rx.callout(
                    PatientListState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                PatientListState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    PatientListState.patients.length() > 0,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("N° Dossier"),
                                rx.table.column_header_cell("Name"),
                                rx.table.column_header_cell("Date of Birth"),
                                rx.table.column_header_cell("Gender"),
                                rx.table.column_header_cell("City"),
                                rx.table.column_header_cell("Phone"),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(PatientListState.patients, _patient_row)
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("user-x", size=40, color="var(--gray-7)"),
                            rx.text("No patients found", color="var(--gray-9)"),
                            align="center",
                            spacing="2",
                        ),
                        padding="3rem",
                    ),
                ),
            ),
        )
    )
