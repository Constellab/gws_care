"""Patient create / edit form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from .patient_form_state import PatientFormState


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
        rx.grid(
            _field(
                "Last Name *",
                rx.input(
                    value=PatientFormState.form_last_name,
                    on_change=PatientFormState.set_form_last_name,
                    placeholder="DUPONT",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "First Name *",
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
            "Birth Name",
            rx.input(
                value=PatientFormState.form_birth_name,
                on_change=PatientFormState.set_form_birth_name,
                placeholder="Maiden name (if different)",
                size="2",
                width="100%",
            ),
        ),
        rx.grid(
            _field(
                "Date of Birth *",
                rx.input(
                    value=PatientFormState.form_date_of_birth,
                    on_change=PatientFormState.set_form_date_of_birth,
                    type="date",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "Gender *",
                rx.select.root(
                    rx.select.trigger(placeholder="Select gender"),
                    rx.select.content(
                        rx.select.item("Male", value="M"),
                        rx.select.item("Female", value="F"),
                        rx.select.item("Other", value="Other"),
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
        rx.text("Contact", size="2", weight="bold", color="var(--gray-9)"),
        rx.grid(
            _field(
                "Phone",
                rx.input(
                    value=PatientFormState.form_phone,
                    on_change=PatientFormState.set_form_phone,
                    placeholder="+33 6 00 00 00 00",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "Email",
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
            "Address",
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
                "Postal Code",
                rx.input(
                    value=PatientFormState.form_postal_code,
                    on_change=PatientFormState.set_form_postal_code,
                    placeholder="75001",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "City",
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
        rx.text("Primary Care Physician", size="2", weight="bold", color="var(--gray-9)"),
        rx.grid(
            _field(
                "Physician Name",
                rx.input(
                    value=PatientFormState.form_primary_physician_name,
                    on_change=PatientFormState.set_form_primary_physician_name,
                    placeholder="Dr. Martin",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "Physician Phone",
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
        rx.hstack(
            rx.button(
                "Cancel",
                variant="soft",
                color_scheme="gray",
                on_click=PatientFormState.close_dialog,
                disabled=PatientFormState.is_loading,
            ),
            rx.button(
                rx.cond(
                    PatientFormState.is_loading,
                    rx.spinner(size="2"),
                    rx.cond(
                        PatientFormState.is_create_mode,
                        rx.text("Create Patient"),
                        rx.text("Save Changes"),
                    ),
                ),
                type="submit",
                disabled=PatientFormState.is_loading,
            ),
            spacing="3",
            justify="end",
            width="100%",
            padding_top="0.5rem",
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
            "New Patient",
            "Edit Patient",
        ),
        description=rx.cond(
            PatientFormState.is_create_mode,
            "Fill in the details to create a new patient file. A unique patient number will be generated automatically.",
            "Update the patient's information.",
        ),
        form_content=_form_fields(),
        max_width="680px",
    )
