"""Account detail page — shows account info and its patients."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from ..patient_list.patient_form_component import patient_form_dialog
from ..patient_list.patient_form_state import PatientFormState
from .account_detail_state import (
    AccountDetailDTO,
    AccountDetailState,
    AccountPatientRowDTO,
)


def _info_item(label: str, value: rx.Var) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", color="var(--gray-9)", weight="medium"),
        rx.cond(
            value != "",
            rx.text(value, size="2"),
            rx.text("—", size="2", color="var(--gray-7)"),
        ),
        spacing="0",
        align_items="start",
    )


def _account_info_card(account: AccountDetailDTO) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("building-2", size=18, color="var(--accent-9)"),
                rx.heading(account.name, size="5"),
                rx.cond(
                    account.is_active,
                    rx.badge("Active", color_scheme="green", variant="soft", size="1"),
                    rx.badge("Inactive", color_scheme="gray", variant="soft", size="1"),
                ),
                spacing="2",
                align="center",
            ),
            rx.separator(width="100%"),
            rx.grid(
                _info_item("Registration N°", account.registration_number),
                _info_item("City", account.city),
                _info_item("Address", account.address),
                _info_item("Postal Code", account.postal_code),
                _info_item("Phone", account.phone),
                _info_item("Email", account.email),
                _info_item("Contact", account.contact_name),
                columns="3",
                spacing="4",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def _gender_badge(gender: str) -> rx.Component:
    return rx.match(
        gender,
        ("M", rx.badge("M", color_scheme="blue", variant="soft", size="1")),
        ("F", rx.badge("F", color_scheme="pink", variant="soft", size="1")),
        rx.badge(gender, color_scheme="gray", variant="soft", size="1"),
    )


def _patient_row(p: AccountPatientRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p.patient_number, size="2", weight="medium")),
        rx.table.cell(rx.text(f"{p.first_name} {p.last_name}", size="2")),
        rx.table.cell(_gender_badge(p.gender)),
        rx.table.cell(rx.text(p.date_of_birth, size="2")),
        rx.table.cell(
            rx.cond(p.city, rx.text(p.city, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(p.phone, rx.text(p.phone, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("chevron-right", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: AccountDetailState.go_to_patient(p.id),
                    ),
                    content="View patient",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("unlink", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="red",
                        on_click=lambda: AccountDetailState.remove_patient(p.id),
                    ),
                    content="Remove from account",
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}, "cursor": "pointer"},
        on_click=lambda: AccountDetailState.go_to_patient(p.id),
    )


def _assign_patient_dialog() -> rx.Component:
    """Dialog to assign an existing unlinked patient to this account."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Assign Existing Patient"),
            rx.dialog.description(
                "Select a patient who is not yet assigned to any account.",
                size="2",
                margin_bottom="1rem",
            ),
            rx.cond(
                AccountDetailState.unassigned_patients.length() > 0,
                rx.vstack(
                    rx.select.root(
                        rx.select.trigger(placeholder="Search a patient…", width="100%"),
                        rx.select.content(
                            rx.foreach(
                                AccountDetailState.unassigned_patients,
                                lambda p: rx.select.item(p.label, value=p.id),
                            )
                        ),
                        value=AccountDetailState.assign_patient_id,
                        on_change=AccountDetailState.set_assign_patient_id,
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            on_click=AccountDetailState.close_assign_dialog,
                            disabled=AccountDetailState.is_assigning,
                        ),
                        rx.button(
                            rx.cond(
                                AccountDetailState.is_assigning,
                                rx.spinner(size="2"),
                                rx.text("Assign"),
                            ),
                            on_click=AccountDetailState.confirm_assign,
                            disabled=(AccountDetailState.assign_patient_id == "")
                            | AccountDetailState.is_assigning,
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    width="100%",
                    spacing="4",
                ),
                rx.vstack(
                    rx.text(
                        "All patients are already assigned to an account.",
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.button(
                        "Close",
                        variant="soft",
                        color_scheme="gray",
                        on_click=AccountDetailState.close_assign_dialog,
                    ),
                    spacing="3",
                    align_items="end",
                    width="100%",
                ),
            ),
            on_interact_outside=AccountDetailState.close_assign_dialog,
            on_escape_key_down=AccountDetailState.close_assign_dialog,
            max_width="480px",
        ),
        open=AccountDetailState.assign_dialog_open,
    )


def _patients_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Patients", size="4"),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("user-plus", size=14),
                    "Assign existing",
                    variant="outline",
                    size="2",
                    on_click=AccountDetailState.open_assign_dialog,
                ),
                rx.button(
                    rx.icon("plus", size=14),
                    "New patient",
                    size="2",
                    on_click=lambda: PatientFormState.open_create_for_account(AccountDetailState.account.id),
                ),
                spacing="2",
            ),
            width="100%",
            align="center",
        ),
        rx.separator(width="100%"),
        rx.cond(
            AccountDetailState.patients.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("N°"),
                        rx.table.column_header_cell("Patient"),
                        rx.table.column_header_cell("Gender"),
                        rx.table.column_header_cell("Date of Birth"),
                        rx.table.column_header_cell("City"),
                        rx.table.column_header_cell("Phone"),
                        rx.table.column_header_cell("Actions"),
                    )
                ),
                rx.table.body(
                    rx.foreach(AccountDetailState.patients, _patient_row)
                ),
                width="100%",
                variant="surface",
            ),
            rx.center(
                rx.text(
                    "No patients assigned to this account yet.",
                    size="2",
                    color="var(--gray-9)",
                ),
                padding="2rem",
            ),
        ),
        width="100%",
        spacing="3",
    )


def account_detail_page() -> rx.Component:
    """Account detail page."""
    return main_component(
        page_layout(
            rx.button(
                rx.icon("arrow-left", size=16),
                "Back to accounts",
                on_click=AccountDetailState.go_back,
                variant="ghost",
                size="2",
            ),
            rx.cond(
                AccountDetailState.error_message != "",
                rx.callout(
                    AccountDetailState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                AccountDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    AccountDetailState.account,
                    rx.vstack(
                        _account_info_card(AccountDetailState.account),
                        _patients_section(),
                        width="100%",
                        spacing="5",
                    ),
                    rx.center(
                        rx.text("Account not found.", color="var(--gray-9)"),
                        padding="3rem",
                    ),
                ),
            ),
            _assign_patient_dialog(),
            patient_form_dialog(),
        )
    )
