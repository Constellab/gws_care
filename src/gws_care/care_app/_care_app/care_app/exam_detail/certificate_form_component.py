"""Medical certificate issue form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from .certificate_form_state import CertificateFormState


def _field(label: str, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _form_fields() -> rx.Component:
    return rx.vstack(
        _field(
            "Issue Date *",
            rx.input(
                value=CertificateFormState.form_issue_date,
                on_change=CertificateFormState.set_form_issue_date,
                type="date",
                size="2",
                width="100%",
            ),
        ),
        _field(
            "Conclusion *",
            rx.text_area(
                value=CertificateFormState.form_conclusion,
                on_change=CertificateFormState.set_form_conclusion,
                placeholder="Aptitude conclusion (e.g. Fit for work with no restrictions)...",
                size="2",
                width="100%",
                rows="4",
            ),
        ),
        rx.hstack(
            rx.checkbox(
                checked=CertificateFormState.form_is_fit_for_work,
                on_change=CertificateFormState.set_form_is_fit_for_work,
            ),
            rx.text("Fit for work", size="2"),
            spacing="2",
            align="center",
        ),
        rx.cond(
            CertificateFormState.form_is_fit_for_work == False,
            _field(
                "Restrictions",
                rx.text_area(
                    value=CertificateFormState.form_restrictions,
                    on_change=CertificateFormState.set_form_restrictions,
                    placeholder="Describe any work restrictions...",
                    size="2",
                    width="100%",
                    rows="3",
                ),
            ),
        ),
        width="100%",
        spacing="4",
    )


def certificate_form_dialog() -> rx.Component:
    """Render the certificate form dialog (place in component tree)."""
    return form_dialog_component(
        state=CertificateFormState,
        title="Issue Medical Certificate",
        form_content=_form_fields(),
    )
