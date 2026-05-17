"""Patient create / edit form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from ..common.language_state import LanguageState
from .patient_form_state import AccountPickerRowDTO, PatientFormState


def _account_picker_row(account: AccountPickerRowDTO) -> rx.Component:
    """One row in the account picker table inside the patient form."""
    return rx.table.row(
        rx.table.cell(rx.text(account.name, size="2", weight="medium")),
        rx.table.cell(
            rx.cond(
                account.city,
                rx.text(account.city, size="2"),
                rx.text("—", size="2", color="var(--gray-8)"),
            )
        ),
        _hover={"background_color": "var(--accent-2)", "cursor": "pointer"},
        on_click=lambda: PatientFormState.acct_picker_confirm(account.id, account.name),
    )


def _account_picker_dialog() -> rx.Component:
    """Account picker dialog embedded in the patient form."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["acct_picker_title"]),
            rx.vstack(
                rx.input(
                    rx.input.slot(rx.icon("search", size=14)),
                    placeholder=LanguageState.tr["acct_picker_filter_placeholder"],
                    value=PatientFormState.acct_picker_filter,
                    on_change=PatientFormState.acct_picker_set_filter,
                    size="2",
                    width="100%",
                ),
                rx.cond(
                    PatientFormState.acct_picker_error != "",
                    rx.callout(
                        PatientFormState.acct_picker_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                rx.cond(
                    PatientFormState.acct_picker_is_loading,
                    rx.center(rx.spinner(size="2"), padding="1.5rem"),
                    rx.cond(
                        PatientFormState.acct_picker_accounts.length() > 0,
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell(LanguageState.tr["col_account_name"]),
                                        rx.table.column_header_cell(LanguageState.tr["field_city"]),
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(PatientFormState.acct_picker_accounts, _account_picker_row)
                                ),
                                width="100%",
                                variant="surface",
                            ),
                            max_height="320px",
                            overflow_y="auto",
                            width="100%",
                        ),
                        rx.center(
                            rx.text(LanguageState.tr["no_accounts_found"], size="2", color="var(--gray-9)"),
                            padding="1.5rem",
                        ),
                    ),
                ),
                rx.hstack(
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="soft",
                        color_scheme="gray",
                        on_click=PatientFormState.close_account_picker,
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            on_interact_outside=PatientFormState.close_account_picker,
            on_escape_key_down=PatientFormState.close_account_picker,
            max_width="500px",
        ),
        open=PatientFormState.acct_picker_is_open,
    )



def _field(label: str, input_component: rx.Component) -> rx.Component:
    """Render a labeled form field."""
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _form_fields() -> rx.Component:
    """Build the form content with all patient fields."""
    return rx.vstack(
        # The account picker dialog is nested here so it lives inside the
        # outer form dialog's DOM tree — required for Radix nested dialogs.
        _account_picker_dialog(),
        rx.grid(
            _field(
                LanguageState.tr["field_last_name"],
                rx.input(
                    value=PatientFormState.form_last_name,
                    on_change=PatientFormState.set_form_last_name,
                    placeholder="DUPONT",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_first_name"],
                rx.input(
                    value=PatientFormState.form_first_name,
                    on_change=PatientFormState.set_form_first_name,
                    placeholder="Marie",
                    size="2",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        _field(
            LanguageState.tr["field_birth_name"],
            rx.input(
                value=PatientFormState.form_birth_name,
                on_change=PatientFormState.set_form_birth_name,
                placeholder=LanguageState.tr["birth_name_placeholder"],
                size="2",
                width="100%",
            ),
        ),
        rx.grid(
            _field(
                LanguageState.tr["field_dob"],
                rx.input(
                    value=PatientFormState.form_date_of_birth,
                    on_change=PatientFormState.set_form_date_of_birth,
                    type="date",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_gender"],
                rx.select.root(
                    rx.select.trigger(placeholder=LanguageState.tr["select_gender_placeholder"]),
                    rx.select.content(
                        rx.select.item(LanguageState.tr["gender_male"], value="M"),
                        rx.select.item(LanguageState.tr["gender_female"], value="F"),
                        rx.select.item(LanguageState.tr["gender_other"], value="Other"),
                    ),
                    value=PatientFormState.form_gender,
                    on_change=PatientFormState.set_form_gender,
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
        rx.grid(
            _field(
                LanguageState.tr["field_phone"],
                rx.input(
                    value=PatientFormState.form_phone,
                    on_change=PatientFormState.set_form_phone,
                    placeholder="+33 6 00 00 00 00",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_email"],
                rx.input(
                    value=PatientFormState.form_email,
                    on_change=PatientFormState.set_form_email,
                    placeholder="patient@email.com",
                    type="email",
                    size="2",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        _field(
            LanguageState.tr["field_address"],
            rx.input(
                value=PatientFormState.form_address,
                on_change=PatientFormState.set_form_address,
                placeholder="12 rue de la Paix",
                size="2",
                width="100%",
            ),
        ),
        rx.grid(
            _field(
                LanguageState.tr["field_postal_code"],
                rx.input(
                    value=PatientFormState.form_postal_code,
                    on_change=PatientFormState.set_form_postal_code,
                    placeholder="75001",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_city"],
                rx.input(
                    value=PatientFormState.form_city,
                    on_change=PatientFormState.set_form_city,
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
        rx.text(LanguageState.tr["section_primary_physician"], size="2", weight="bold", color="var(--gray-9)"),
        rx.grid(
            _field(
                LanguageState.tr["field_physician_name"],
                rx.input(
                    value=PatientFormState.form_primary_physician_name,
                    on_change=PatientFormState.set_form_primary_physician_name,
                    placeholder="Dr. Martin",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_physician_phone"],
                rx.input(
                    value=PatientFormState.form_primary_physician_phone,
                    on_change=PatientFormState.set_form_primary_physician_phone,
                    placeholder="+33 1 00 00 00 00",
                    size="2",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        rx.separator(width="100%"),
        rx.text(LanguageState.tr["section_account"], size="2", weight="bold", color="var(--gray-9)"),
        _field(
            LanguageState.tr["field_account_optional"],
            rx.hstack(
                rx.button(
                    rx.icon("building-2", size=14),
                    rx.cond(
                        PatientFormState.form_account_id != "",
                        rx.text(PatientFormState.form_account_name, size="2"),
                        rx.text(LanguageState.tr["select_account_placeholder"], size="2"),
                    ),
                    on_click=PatientFormState.open_account_picker,
                    variant=rx.cond(PatientFormState.form_account_id != "", "soft", "outline"),
                    size="2",
                    type="button",
                ),
                rx.cond(
                    PatientFormState.form_account_id != "",
                    rx.icon_button(
                        rx.icon("x", size=12),
                        on_click=PatientFormState.acct_picker_clear,
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                        type="button",
                    ),
                ),
                spacing="2",
                align="center",
            ),
        ),
        rx.separator(width="100%"),
        rx.text(LanguageState.tr["section_medical_info"], size="2", weight="bold", color="var(--gray-9)"),
        _field(
            LanguageState.tr["field_ssn"],
            rx.input(
                value=PatientFormState.form_social_security_number,
                on_change=PatientFormState.set_form_social_security_number,
                placeholder="1 85 07 75 123 456 78",
                size="2",
                width="100%",
            ),
        ),
        rx.grid(
            _field(
                LanguageState.tr["field_weight"],
                rx.input(
                    value=PatientFormState.form_weight,
                    on_change=PatientFormState.set_form_weight,
                    placeholder="70",
                    type="number",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_height"],
                rx.input(
                    value=PatientFormState.form_height,
                    on_change=PatientFormState.set_form_height,
                    placeholder="175",
                    type="number",
                    size="2",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        rx.vstack(
            rx.text(LanguageState.tr["field_notif_prefs"], size="2", weight="medium"),
            rx.hstack(
                rx.checkbox(
                    LanguageState.tr["notif_email"],
                    checked=PatientFormState.form_notif_email,
                    on_change=PatientFormState.set_form_notif_email,
                    size="2",
                ),
                spacing="4",
            ),
            width="100%",
            spacing="1",
        ),
        width="100%",
        spacing="3",
    )


def patient_form_dialog() -> rx.Component:
    """The patient create / edit dialog. Include once per page that needs it."""
    return form_dialog_component(
        state=PatientFormState,
        title=rx.cond(
            PatientFormState.is_create_mode,
            LanguageState.tr["new_patient_title"],
            LanguageState.tr["edit_patient_title"],
        ),
        description=rx.cond(
            PatientFormState.is_create_mode,
            LanguageState.tr["new_patient_desc"],
            LanguageState.tr["edit_patient_desc"],
        ),
        form_content=_form_fields(),
        max_width="680px",
    )
