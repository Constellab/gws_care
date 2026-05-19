"""Patient list page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
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
            rx.cond(patient.account_name, rx.text(patient.account_name, size="2"), rx.text("—", color="var(--gray-8)", size="2"))
        ),
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


def _sortable_header(label: str, column: str) -> rx.Component:
    """Column header cell with a sort-direction arrow."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                PatientListState.sort_column == column,
                rx.cond(
                    PatientListState.sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: PatientListState.set_sort(column),
        style={"cursor": "pointer"},
    )


def _filter_bar() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.input(
                placeholder=LanguageState.tr["search_patient_number"],
                value=PatientListState.search_patient_number,
                on_change=PatientListState.handle_patient_number_change,
                min_width="180px",
                size="2",
            ),
            rx.input(
                placeholder=LanguageState.tr["search_name_placeholder"],
                value=PatientListState.search_name,
                on_change=PatientListState.handle_name_change,
                min_width="220px",
                size="2",
            ),
            rx.input(
                placeholder=LanguageState.tr["search_phone_placeholder"],
                value=PatientListState.search_phone,
                on_change=PatientListState.handle_phone_change,
                min_width="160px",
                size="2",
            ),
            rx.select.root(
                rx.select.trigger(placeholder=LanguageState.tr["all_accounts"]),
                rx.select.content(
                    rx.select.item(LanguageState.tr["all_accounts"], value="ALL"),
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
            rx.text(LanguageState.tr["dob_label"], size="2", color="var(--gray-9)", white_space="nowrap"),
            rx.input(
                type="date",
                value=PatientListState.filter_dob_from,
                on_change=PatientListState.set_filter_dob_from,
                size="2",
            ),
            rx.text(LanguageState.tr["date_range_arrow"], size="2", color="var(--gray-9)"),
            rx.input(
                type="date",
                value=PatientListState.filter_dob_to,
                on_change=PatientListState.set_filter_dob_to,
                size="2",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("x", size=14),
                LanguageState.tr["clear_btn"],
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


def _confirm_delete_dialog() -> rx.Component:
    """Double-confirmation dialog before deleting a patient."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("trash-2", size=20, color="var(--red-9)"),
                    rx.dialog.title("Supprimer le patient"),
                    spacing="2",
                    align="center",
                ),
                rx.callout(
                    rx.vstack(
                        rx.text.strong("Cette action est irréversible."),
                        rx.text(
                            "Le patient ",
                            rx.text.strong(PatientListState.confirm_delete_patient_name),
                            " sera définitivement supprimé.",
                        ),
                        spacing="1",
                    ),
                    icon="triangle-alert",
                    color_scheme="red",
                    variant="soft",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Annuler",
                            variant="outline",
                            on_click=PatientListState.dismiss_confirm_delete,
                        ),
                    ),
                    rx.button(
                        rx.icon("trash-2", size=14),
                        "Supprimer définitivement",
                        color_scheme="red",
                        on_click=PatientListState.confirmed_delete_patient,
                        loading=PatientListState.is_deleting,
                    ),
                    justify="end",
                    spacing="3",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="420px",
        ),
        open=PatientListState.confirm_delete_patient_open,
        on_open_change=lambda _: PatientListState.dismiss_confirm_delete(),
    )


def patient_list_page() -> rx.Component:
    """Patient list page."""
    return main_component(
        page_layout(
            rx.hstack(
                rx.heading(LanguageState.tr["patients_page_title"], size="6"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    LanguageState.tr["new_patient_btn"],
                    on_click=PatientFormState.open_create_dialog,
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            patient_form_dialog(),
            _confirm_delete_dialog(),
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
                                _sortable_header(LanguageState.tr["col_patient_number"], "patient_number"),
                                _sortable_header(LanguageState.tr["col_name"], "last_name"),
                                _sortable_header(LanguageState.tr["col_dob"], "date_of_birth"),
                                _sortable_header(LanguageState.tr["col_gender"], "gender"),
                                _sortable_header(LanguageState.tr["col_account"], "account_name"),
                                _sortable_header(LanguageState.tr["col_city"], "city"),
                                _sortable_header(LanguageState.tr["col_phone"], "phone"),
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
                            rx.text(LanguageState.tr["no_patients_found"], color="var(--gray-9)"),
                            align="center",
                            spacing="2",
                        ),
                        padding="3rem",
                    ),
                ),
            ),
        )
    )
