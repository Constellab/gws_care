"""Company create / edit form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from .company_form_state import CompanyFormState


def _field(label: str, input_component: rx.Component) -> rx.Component:
    """Render a labeled form field."""
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _form_fields() -> rx.Component:
    """Build the form content with all company fields."""
    return rx.vstack(
        _field(
            "Company Name *",
            rx.input(
                value=CompanyFormState.form_name,
                on_change=CompanyFormState.set_form_name,
                placeholder="PS CONSULTING",
                size="2",
                width="100%",
            ),
        ),
        _field(
            "Registration Number",
            rx.input(
                value=CompanyFormState.form_registration_number,
                on_change=CompanyFormState.set_form_registration_number,
                placeholder="SIRET / Company ID",
                size="2",
                width="100%",
            ),
        ),
        rx.separator(width="100%"),
        rx.text("Address", size="2", weight="bold", color="var(--gray-9)"),
        _field(
            "Street Address",
            rx.input(
                value=CompanyFormState.form_address,
                on_change=CompanyFormState.set_form_address,
                placeholder="12 rue de la Paix",
                size="2",
                width="100%",
            ),
        ),
        rx.grid(
            _field(
                "Postal Code",
                rx.input(
                    value=CompanyFormState.form_postal_code,
                    on_change=CompanyFormState.set_form_postal_code,
                    placeholder="75001",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "City",
                rx.input(
                    value=CompanyFormState.form_city,
                    on_change=CompanyFormState.set_form_city,
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
                value=CompanyFormState.form_contact_name,
                on_change=CompanyFormState.set_form_contact_name,
                placeholder="Jean Dupont",
                size="2",
                width="100%",
            ),
        ),
        rx.grid(
            _field(
                "Phone",
                rx.input(
                    value=CompanyFormState.form_phone,
                    on_change=CompanyFormState.set_form_phone,
                    placeholder="+33 1 00 00 00 00",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "Email",
                rx.input(
                    value=CompanyFormState.form_email,
                    on_change=CompanyFormState.set_form_email,
                    placeholder="contact@company.com",
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
                on_click=CompanyFormState.close_dialog,
                disabled=CompanyFormState.is_loading,
            ),
            rx.button(
                rx.cond(
                    CompanyFormState.is_loading,
                    rx.spinner(size="2"),
                    rx.cond(
                        CompanyFormState.is_create_mode,
                        rx.text("Create Company"),
                        rx.text("Save Changes"),
                    ),
                ),
                type="submit",
                disabled=CompanyFormState.is_loading,
            ),
            spacing="3",
            justify="end",
            width="100%",
            padding_top="0.5rem",
        ),
        width="100%",
        spacing="3",
    )


def company_form_dialog() -> rx.Component:
    """The company create / edit dialog. Include once per page that needs it."""
    return form_dialog_component(
        state=CompanyFormState,
        title=rx.cond(
            CompanyFormState.is_create_mode,
            "New Company",
            "Edit Company",
        ),
        description=rx.cond(
            CompanyFormState.is_create_mode,
            "Register a new client company.",
            "Update the company's information.",
        ),
        form_content=_form_fields(),
        max_width="600px",
    )
