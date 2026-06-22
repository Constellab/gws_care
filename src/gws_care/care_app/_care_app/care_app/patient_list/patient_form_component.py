"""Patient create / edit form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from ..common.language_state import LanguageState
from .patient_form_state import PatientFormState


def _field(label: str, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _form_fields() -> rx.Component:
    return rx.vstack(
        rx.grid(
            _field(
                LanguageState.tr["field_last_name"],
                rx.input(
                    value=PatientFormState.form_last_name,
                    on_change=PatientFormState.set_form_last_name,
                    placeholder=LanguageState.tr["placeholder_last_name"],
                    size="2", width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_first_name"],
                rx.input(
                    value=PatientFormState.form_first_name,
                    on_change=PatientFormState.set_form_first_name,
                    placeholder=LanguageState.tr["placeholder_first_name"],
                    size="2", width="100%",
                ),
            ),
            columns="2", spacing="3", width="100%",
        ),
        _field(
            LanguageState.tr["field_birth_name"],
            rx.input(
                value=PatientFormState.form_birth_name,
                on_change=PatientFormState.set_form_birth_name,
                placeholder=LanguageState.tr["birth_name_placeholder"],
                size="2", width="100%",
            ),
        ),
        rx.grid(
            _field(
                LanguageState.tr["field_dob"],
                rx.input(
                    value=PatientFormState.form_date_of_birth,
                    on_change=PatientFormState.set_form_date_of_birth,
                    type="date", size="2", width="100%",
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
                    size="2", width="100%",
                ),
            ),
            columns="2", spacing="3", width="100%",
        ),
        _field(
            LanguageState.tr["field_nationality"],
            rx.input(
                value=PatientFormState.form_nationality,
                on_change=PatientFormState.set_form_nationality,
                placeholder=LanguageState.tr["placeholder_nationality"],
                size="2", width="100%",
            ),
        ),
        rx.separator(width="100%"),
        rx.text(LanguageState.tr["section_contact"], size="2", weight="bold", color="var(--gray-9)"),
        rx.grid(
            _field(
                LanguageState.tr["field_phone_country"],
                rx.select.root(
                    rx.select.trigger(placeholder=LanguageState.tr["field_phone_country"]),
                    rx.select.content(
                        rx.select.item(LanguageState.tr["phone_country_fr"], value="+33"),
                        rx.select.item(LanguageState.tr["phone_country_ma"], value="+212"),
                        rx.select.item(LanguageState.tr["phone_country_dz"], value="+213"),
                        rx.select.item(LanguageState.tr["phone_country_tn"], value="+216"),
                        rx.select.item(LanguageState.tr["phone_country_sn"], value="+221"),
                        rx.select.item(LanguageState.tr["phone_country_other"], value=""),
                    ),
                    value=PatientFormState.form_phone_country,
                    on_change=PatientFormState.set_form_phone_country,
                    size="2", width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_phone"],
                rx.input(
                    value=PatientFormState.form_phone,
                    on_change=PatientFormState.set_form_phone,
                    placeholder="06 00 00 00 00",
                    size="2", width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_email"],
                rx.input(
                    value=PatientFormState.form_email,
                    on_change=PatientFormState.set_form_email,
                    placeholder="patient@email.com",
                    type="email", size="2", width="100%",
                ),
            ),
            columns="3", spacing="3", width="100%",
        ),
        _field(
            LanguageState.tr["field_address"],
            rx.input(
                value=PatientFormState.form_address,
                on_change=PatientFormState.set_form_address,
                placeholder="12 rue de la Paix",
                size="2", width="100%",
            ),
        ),
        rx.grid(
            _field(
                LanguageState.tr["field_postal_code"],
                rx.input(
                    value=PatientFormState.form_postal_code,
                    on_change=PatientFormState.set_form_postal_code,
                    placeholder="75001",
                    size="2", width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_city"],
                rx.input(
                    value=PatientFormState.form_city,
                    on_change=PatientFormState.set_form_city,
                    placeholder=LanguageState.tr["placeholder_city"],
                    size="2", width="100%",
                ),
            ),
            columns="2", spacing="3", width="100%",
        ),
        rx.separator(width="100%"),
        rx.text(LanguageState.tr["section_medical_info"], size="2", weight="bold", color="var(--gray-9)"),
        _field(
            LanguageState.tr["field_ssn"],
            rx.input(
                value=PatientFormState.form_social_security_number,
                on_change=PatientFormState.set_form_social_security_number,
                placeholder="1 85 07 75 123 456 78",
                size="2", width="100%",
            ),
        ),
        rx.grid(
            _field(
                LanguageState.tr["field_weight"],
                rx.input(
                    value=PatientFormState.form_weight,
                    on_change=PatientFormState.set_form_weight,
                    placeholder="70", type="number",
                    size="2", width="100%",
                ),
            ),
            _field(
                LanguageState.tr["field_height"],
                rx.input(
                    value=PatientFormState.form_height,
                    on_change=PatientFormState.set_form_height,
                    placeholder="175", type="number",
                    size="2", width="100%",
                ),
            ),
            columns="2", spacing="3", width="100%",
        ),
        width="100%",
        spacing="3",
    )


def patient_form_dialog() -> rx.Component:
    """The patient create / edit dialog."""
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
