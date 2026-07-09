import reflex as rx
from gws_reflex_base import form_dialog_component

from ..common.language_state import LanguageState
from .certificate_form_state import CertificateFormState


def _field(label, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        label if not isinstance(label, str) else rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _form_fields() -> rx.Component:
    return rx.vstack(
        _field(
            LanguageState.tr["cert_form_date_label"],
            rx.input(
                value=CertificateFormState.form_issue_date,
                on_change=CertificateFormState.set_form_issue_date,
                type="date",
                size="2",
                width="100%",
            ),
        ),
        _field(
            LanguageState.tr["cert_form_conclusion_label"],
            rx.text_area(
                value=CertificateFormState.form_conclusion,
                on_change=CertificateFormState.set_form_conclusion,
                placeholder=LanguageState.tr["placeholder_cert_conclusion"],
                size="2",
                width="100%",
                rows="4",
            ),
        ),
        rx.radio_group.root(
            rx.hstack(
                rx.hstack(rx.radio_group.item(value="FIT"), rx.text(LanguageState.tr["cert_fit_yes"], size="2"), spacing="1", align="center"),
                rx.hstack(rx.radio_group.item(value="UNFIT"), rx.text(LanguageState.tr["cert_fit_no"], size="2"), spacing="1", align="center"),
                rx.hstack(rx.radio_group.item(value="PERMANENTLY_UNFIT"), rx.text(LanguageState.tr["cert_fit_permanently_unfit"], size="2"), spacing="1", align="center"),
                spacing="4",
            ),
            value=CertificateFormState.form_fitness_decision,
            on_change=CertificateFormState.set_form_fitness_decision,
        ),
        rx.cond(
            CertificateFormState.form_fitness_decision == "UNFIT",
            _field(
                LanguageState.tr["cert_form_restrictions_label"],
                rx.text_area(
                    value=CertificateFormState.form_restrictions,
                    on_change=CertificateFormState.set_form_restrictions,
                    placeholder=LanguageState.tr["placeholder_cert_restrictions"],
                    size="2",
                    width="100%",
                    rows="3",
                ),
            ),
        ),
        rx.cond(
            CertificateFormState.form_error != "",
            rx.callout(
                CertificateFormState.form_error,
                icon="triangle-alert",
                color_scheme="red",
                size="1",
            ),
            rx.fragment(),
        ),
        width="100%",
        spacing="4",
    )


def certificate_form_dialog() -> rx.Component:
    """Render the certificate form dialog (place in component tree)."""
    return form_dialog_component(
        state=CertificateFormState,
        title=LanguageState.tr["dialog_issue_cert_title"],
        form_content=_form_fields(),
    )
