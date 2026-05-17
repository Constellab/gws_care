"""Account detail page — shows account info and its patients."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..common.patient_picker_component import patient_picker_widget
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
            rx.text(value, size="2", overflow_wrap="break-word", word_break="break-word"),
            rx.text("—", size="2", color="var(--gray-7)"),
        ),
        spacing="0",
        align_items="start",
        min_width="0",
    )


def _account_info_card(account: AccountDetailDTO) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("building-2", size=18, color="var(--accent-9)"),
                rx.heading(account.name, size="5"),
                rx.cond(
                    account.is_active,
                    rx.badge(LanguageState.tr["active_badge"], color_scheme="green", variant="soft", size="1"),
                    rx.badge(LanguageState.tr["inactive_badge"], color_scheme="gray", variant="soft", size="1"),
                ),
                spacing="2",
                align="center",
            ),
            rx.separator(width="100%"),
            rx.grid(
                _info_item(LanguageState.tr["info_registration"], account.registration_number),
                _info_item(LanguageState.tr["info_city"], account.city),
                _info_item(LanguageState.tr["info_address"], account.address),
                _info_item(LanguageState.tr["info_postal_code"], account.postal_code),
                _info_item(LanguageState.tr["info_phone"], account.phone),
                _info_item(LanguageState.tr["info_email"], account.email),
                _info_item(LanguageState.tr["info_contact"], account.contact_name),
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
            rx.box(
                rx.hstack(
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("chevron-right", size=14),
                            variant="ghost",
                            size="1",
                            on_click=lambda: AccountDetailState.go_to_patient(p.id),
                        ),
                        content=LanguageState.tr["tooltip_view_patient"],
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("unlink", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="red",
                            on_click=lambda: AccountDetailState.remove_patient(p.id),
                        ),
                        content=LanguageState.tr["tooltip_remove_from_account"],
                    ),
                    spacing="1",
                ),
                on_click=rx.stop_propagation,
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}, "cursor": "pointer"},
        on_click=lambda: AccountDetailState.go_to_patient(p.id),
    )


def _assign_patient_dialog() -> rx.Component:
    """Dialog to assign an existing patient to this account."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["assign_patient_dialog_title"]),
            rx.dialog.description(
                LanguageState.tr["assign_patient_dialog_desc"],
                size="2",
                margin_bottom="0.5rem",
            ),
            rx.vstack(
                patient_picker_widget(AccountDetailState),
                rx.hstack(
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="soft",
                        color_scheme="gray",
                        on_click=AccountDetailState.close_assign_dialog,
                        disabled=AccountDetailState.is_assigning,
                    ),
                    rx.button(
                        rx.cond(
                            AccountDetailState.is_assigning,
                            rx.spinner(size="2"),
                            rx.text(LanguageState.tr["assign_btn"]),
                        ),
                        on_click=AccountDetailState.confirm_assign,
                        disabled=(AccountDetailState.picker_selected_id == "")
                        | AccountDetailState.is_assigning,
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            on_interact_outside=AccountDetailState.close_assign_dialog,
            on_escape_key_down=AccountDetailState.close_assign_dialog,
            max_width="700px",
        ),
        open=AccountDetailState.assign_dialog_open,
    )


def _patients_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading(LanguageState.tr["patients_in_account_title"], size="4"),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("user-plus", size=14),
                    LanguageState.tr["assign_existing_btn"],
                    variant="outline",
                    size="2",
                    on_click=AccountDetailState.open_assign_dialog,
                ),
                rx.button(
                    rx.icon("plus", size=14),
                    LanguageState.tr["new_patient_small_btn"],
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
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(LanguageState.tr["col_patient_number"]),
                            rx.table.column_header_cell(LanguageState.tr["col_patient"]),
                            rx.table.column_header_cell(LanguageState.tr["col_gender"]),
                            rx.table.column_header_cell(LanguageState.tr["col_dob"]),
                            rx.table.column_header_cell(LanguageState.tr["col_city"]),
                            rx.table.column_header_cell(LanguageState.tr["col_phone"]),
                            rx.table.column_header_cell(LanguageState.tr["col_actions"]),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(AccountDetailState.patients, _patient_row)
                    ),
                    width="100%",
                    variant="surface",
                ),
                overflow_x="auto",
                width="100%",
            ),
            rx.center(
                rx.text(
                    LanguageState.tr["no_patients_assigned"],
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
                LanguageState.tr["back_to_accounts"],
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
                        rx.text(LanguageState.tr["account_not_found"], color="var(--gray-9)"),
                        padding="3rem",
                    ),
                ),
            ),
            _assign_patient_dialog(),
            patient_form_dialog(),
        )
    )
