"""Patient create / edit form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from ..common.language_state import LanguageState
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
            _field(
                LanguageState.tr["field_sex"],
                rx.select.root(
                    rx.select.trigger(placeholder=LanguageState.tr["select_sex_placeholder"]),
                    rx.select.content(
                        rx.select.item(LanguageState.tr["sex_male"], value="M"),
                        rx.select.item(LanguageState.tr["sex_female"], value="F"),
                        rx.select.item(LanguageState.tr["sex_other"], value="Autre"),
                    ),
                    value=PatientFormState.form_sex,
                    on_change=PatientFormState.set_form_sex,
                    size="2",
                    width="100%",
                ),
            ),
            columns="3",
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
                rx.checkbox(
                    LanguageState.tr["notif_sms"],
                    checked=PatientFormState.form_notif_sms,
                    on_change=PatientFormState.set_form_notif_sms,
                    size="2",
                ),
                rx.checkbox(
                    LanguageState.tr["notif_whatsapp"],
                    checked=PatientFormState.form_notif_whatsapp,
                    on_change=PatientFormState.set_form_notif_whatsapp,
                    size="2",
                ),
                spacing="4",
            ),
            width="100%",
            spacing="1",
        ),
        rx.hstack(
            rx.button(
                LanguageState.tr["cancel_btn"],
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
                        rx.text(LanguageState.tr["create_patient_btn"]),
                        rx.text(LanguageState.tr["save_changes_btn"]),
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
