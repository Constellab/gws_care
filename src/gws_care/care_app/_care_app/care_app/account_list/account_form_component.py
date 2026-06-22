"""Account create / edit form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from ..common.language_state import LanguageState
from .account_form_state import AccountFormState


def _field(label: str | rx.Component, input_component: rx.Component) -> rx.Component:
    """Render a labeled form field."""
    return rx.vstack(
        label if not isinstance(label, str) else rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _type_selector() -> rx.Component:
    """Account type radio: Company or Individual."""
    return rx.vstack(
        rx.text(LanguageState.tr["field_account_type"], size="2", weight="medium"),
        rx.radio_group.root(
            rx.hstack(
                rx.radio_group.item(value="COMPANY"),
                rx.text(LanguageState.tr["account_type_company"], size="2"),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.radio_group.item(value="INDIVIDUAL"),
                rx.text(LanguageState.tr["account_type_individual"], size="2"),
                spacing="2",
                align="center",
            ),
            value=AccountFormState.form_account_type,
            on_change=AccountFormState.set_form_account_type,
            spacing="4",
        ),
        width="100%",
        spacing="1",
    )


def _patient_fill_row(patient) -> rx.Component:
    is_selected = AccountFormState.selected_patient_fill == patient.id
    return rx.table.row(
        rx.table.cell(rx.text(patient.patient_number, size="2", weight="medium")),
        rx.table.cell(rx.text(patient.display, size="2")),
        rx.table.cell(rx.text(patient.date_of_birth, size="2")),
        rx.table.cell(
            rx.match(
                patient.gender,
                ("M", rx.badge("M", color_scheme="blue", variant="soft", size="1")),
                ("F", rx.badge("F", color_scheme="pink", variant="soft", size="1")),
                rx.text("", size="2"),
            )
        ),
        style=rx.cond(
            is_selected,
            {"background_color": "var(--accent-3)", "cursor": "pointer"},
            {"cursor": "pointer"},
        ),
        _hover={"background_color": "var(--accent-2)"},
        on_click=lambda: AccountFormState.select_patient_fill(
            patient.id,
            patient.display + " (" + patient.patient_number + ")",
        ),
    )


def _fill_from_patient_section() -> rx.Component:
    """Searchable patient picker to pre-fill the form (shown for Individual accounts)."""
    return rx.cond(
        AccountFormState.form_account_type == "INDIVIDUAL",
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("user-search", size=14, color="var(--accent-9)"),
                    rx.text(LanguageState.tr["fill_from_patient"], size="2", weight="medium", color="var(--accent-9)"),
                    spacing="2",
                    align="center",
                ),
                # Filter bar
                rx.hstack(
                    rx.input(
                        placeholder=LanguageState.tr["search_patient_number"],
                        value=AccountFormState.patient_fill_filter_number,
                        on_change=AccountFormState.set_patient_fill_filter_number,
                        size="2",
                        min_width="140px",
                        flex="1",
                    ),
                    rx.input(
                        placeholder=LanguageState.tr["search_name_placeholder"],
                        value=AccountFormState.patient_fill_filter_name,
                        on_change=AccountFormState.set_patient_fill_filter_name,
                        size="2",
                        min_width="160px",
                        flex="2",
                    ),
                    rx.button(
                        rx.icon("x", size=14),
                        on_click=AccountFormState.clear_patient_fill_filters,
                        variant="ghost",
                        size="2",
                        color_scheme="gray",
                        title="Clear filters",
                    ),
                    spacing="2",
                    width="100%",
                    align="center",
                ),
                # Patient table
                rx.cond(
                    AccountFormState.patient_fill_is_loading,
                    rx.center(rx.spinner(size="2"), padding="1rem"),
                    rx.cond(
                        AccountFormState.patient_fill_options.length() > 0,
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell(
                                            rx.text(LanguageState.tr["col_patient_number"], size="1")
                                        ),
                                        rx.table.column_header_cell(
                                            rx.text(LanguageState.tr["col_name"], size="1")
                                        ),
                                        rx.table.column_header_cell(
                                            rx.text(LanguageState.tr["col_dob"], size="1")
                                        ),
                                        rx.table.column_header_cell(
                                            rx.text(LanguageState.tr["col_gender"], size="1")
                                        ),
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(AccountFormState.patient_fill_options, _patient_fill_row)
                                ),
                                width="100%",
                                size="1",
                                variant="surface",
                            ),
                            max_height="240px",
                            overflow_y="auto",
                            width="100%",
                            border_radius="var(--radius-2)",
                        ),
                        rx.center(
                            rx.text(
                                LanguageState.tr["no_patients_found"],
                                size="2",
                                color="var(--gray-9)",
                            ),
                            padding="1rem",
                        ),
                    ),
                ),
                # Selected patient confirmation banner
                rx.cond(
                    AccountFormState.selected_patient_fill != "",
                    rx.hstack(
                        rx.icon("check", size=16, color="var(--green-9)"),
                        rx.text(
                            AccountFormState.patient_fill_selected_label,
                            size="2",
                            color="var(--green-11)",
                            weight="medium",
                        ),
                        spacing="2",
                        align="center",
                        padding="0.4rem 0.6rem",
                        border="1px solid var(--green-6)",
                        border_radius="var(--radius-2)",
                        background="var(--green-2)",
                        width="100%",
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            background_color="var(--accent-2)",
            width="100%",
            padding="0.75rem",
        ),
    )


def _company_selector() -> rx.Component:
    """Select the linked Entreprise (only for COMPANY accounts)."""
    return rx.cond(
        AccountFormState.form_account_type == "COMPANY",
        _field(
            rx.hstack(
                rx.icon("building-2", size=13, color="var(--accent-9)"),
                rx.text("Entreprise liée", size="2", weight="medium"),
                spacing="1", align="center",
            ),
            rx.select.root(
                rx.select.trigger(placeholder="Sélectionner une entreprise…", width="100%"),
                rx.select.content(
                    rx.select.item("— Aucune —", value=""),
                    rx.foreach(
                        AccountFormState.company_options,
                        lambda c: rx.select.item(c.name, value=c.id),
                    ),
                ),
                value=AccountFormState.form_company_id,
                on_change=AccountFormState.set_form_company_id,
                width="100%",
            ),
        ),
    )


def _form_fields() -> rx.Component:
    """Build the form content with all account fields."""
    return rx.vstack(
        _type_selector(),
        _company_selector(),
        _fill_from_patient_section(),
        rx.separator(width="100%"),
        _field(
            rx.text(
                rx.cond(
                    AccountFormState.form_account_type == "COMPANY",
                    LanguageState.tr["field_company_name"],
                    LanguageState.tr["field_full_name"],
                ),
                size="2",
                weight="medium",
            ),
            rx.input(
                value=AccountFormState.form_name,
                on_change=AccountFormState.set_form_name,
                placeholder=rx.cond(
                    AccountFormState.form_account_type == "COMPANY",
                    "PS CONSULTING",
                    "Jean Dupont",
                ),
                size="2",
                width="100%",
            ),
        ),
        rx.cond(
            AccountFormState.form_account_type == "COMPANY",
            _field(
                LanguageState.tr["field_registration_number"],
                rx.input(
                    value=AccountFormState.form_registration_number,
                    on_change=AccountFormState.set_form_registration_number,
                    placeholder="SIRET / Registration ID",
                    size="2",
                    width="100%",
                ),
            ),
        ),
        rx.separator(width="100%"),
        rx.text(LanguageState.tr["section_address"], size="2", weight="bold", color="var(--gray-9)"),
        _field(
            LanguageState.tr["field_street_address"],
            rx.input(
                value=AccountFormState.form_address,
                on_change=AccountFormState.set_form_address,
                placeholder="12 rue de la Paix",
                size="2",
                width="100%",
            ),
        ),
        rx.grid(
            _field(
                LanguageState.tr["field_postal_code"],
                rx.input(
                    value=AccountFormState.form_postal_code,
                    on_change=AccountFormState.set_form_postal_code,
                    placeholder="75001",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_city"],
                rx.input(
                    value=AccountFormState.form_city,
                    on_change=AccountFormState.set_form_city,
                    placeholder="Paris",
                    size="2",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        rx.separator(width="100%"),
        rx.text(LanguageState.tr["section_contact"], size="2", weight="bold", color="var(--gray-9)"),
        rx.cond(
            AccountFormState.form_account_type == "COMPANY",
            rx.grid(
                _field(
                    LanguageState.tr["field_contact_first_name"],
                    rx.input(
                        value=AccountFormState.form_contact_first_name,
                        on_change=AccountFormState.set_form_contact_first_name,
                        placeholder="Jean",
                        size="2",
                        width="100%",
                    ),
                ),
                _field(
                    LanguageState.tr["field_contact_last_name"],
                    rx.input(
                        value=AccountFormState.form_contact_last_name,
                        on_change=AccountFormState.set_form_contact_last_name,
                        placeholder="Dupont",
                        size="2",
                        width="100%",
                    ),
                ),
                columns="2",
                spacing="3",
                width="100%",
            ),
        ),
        rx.grid(
            _field(
                LanguageState.tr["field_phone"],
                rx.input(
                    value=AccountFormState.form_phone,
                    on_change=AccountFormState.set_form_phone,
                    placeholder="+33 1 00 00 00 00",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_email"],
                rx.input(
                    value=AccountFormState.form_email,
                    on_change=AccountFormState.set_form_email,
                    placeholder="contact@account.com",
                    type="email",
                    size="2",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        rx.cond(
            AccountFormState.form_error != "",
            rx.callout(
                AccountFormState.form_error,
                icon="triangle-alert",
                color_scheme="red",
                size="1",
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.button(
                LanguageState.tr["cancel_btn"],
                variant="soft",
                color_scheme="gray",
                on_click=AccountFormState.close_dialog,
                disabled=AccountFormState.is_loading,
            ),
            rx.button(
                rx.cond(
                    AccountFormState.is_loading,
                    rx.spinner(size="2"),
                    rx.cond(
                        AccountFormState.is_create_mode,
                        rx.text(LanguageState.tr["create_account_btn"]),
                        rx.text(LanguageState.tr["save_changes_btn"]),
                    ),
                ),
                type="submit",
                disabled=AccountFormState.is_loading,
            ),
            spacing="3",
            justify="end",
            width="100%",
            padding_top="0.5rem",
        ),
        width="100%",
        spacing="3",
    )


def account_form_dialog() -> rx.Component:
    """The account create / edit dialog. Include once per page that needs it."""
    return form_dialog_component(
        state=AccountFormState,
        title=rx.cond(
            AccountFormState.is_create_mode,
            LanguageState.tr["new_account_form_title"],
            LanguageState.tr["edit_account_form_title"],
        ),
        description=rx.cond(
            AccountFormState.is_create_mode,
            LanguageState.tr["new_account_desc"],
            LanguageState.tr["edit_account_desc"],
        ),
        form_content=_form_fields(),
        max_width="600px",
    )

