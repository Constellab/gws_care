"""Account create / edit form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from .account_form_state import AccountFormState


def _field(label: str, input_component: rx.Component) -> rx.Component:
    """Render a labeled form field."""
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _form_fields() -> rx.Component:
    """Build the form content with all account fields."""
    return rx.vstack(
        _field(
            "Account Name *",
            rx.input(
                value=AccountFormState.form_name,
                on_change=AccountFormState.set_form_name,
                placeholder="PS CONSULTING",
                size="2",
                width="100%",
            ),
        ),
        _field(
            "Registration Number",
            rx.input(
                value=AccountFormState.form_registration_number,
                on_change=AccountFormState.set_form_registration_number,
                placeholder="SIRET / Registration ID",
                size="2",
                width="100%",
            ),
        ),
        rx.separator(width="100%"),
        rx.text("Address", size="2", weight="bold", color="var(--gray-9)"),
        _field(
            "Street Address",
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
                "Postal Code",
                rx.input(
                    value=AccountFormState.form_postal_code,
                    on_change=AccountFormState.set_form_postal_code,
                    placeholder="75001",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "City",
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
        rx.text("Contact", size="2", weight="bold", color="var(--gray-9)"),
        _field(
            "Contact Name",
            rx.input(
                value=AccountFormState.form_contact_name,
                on_change=AccountFormState.set_form_contact_name,
                placeholder="Jean Dupont",
                size="2",
                width="100%",
            ),
        ),
        rx.grid(
            _field(
                "Phone",
                rx.input(
                    value=AccountFormState.form_phone,
                    on_change=AccountFormState.set_form_phone,
                    placeholder="+33 1 00 00 00 00",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "Email",
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
        rx.hstack(
            rx.button(
                "Cancel",
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
                        rx.text("Create Account"),
                        rx.text("Save Changes"),
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
            "New Account",
            "Edit Account",
        ),
        description=rx.cond(
            AccountFormState.is_create_mode,
            "Register a new client account.",
            "Update the account's information.",
        ),
        form_content=_form_fields(),
        max_width="600px",
    )
