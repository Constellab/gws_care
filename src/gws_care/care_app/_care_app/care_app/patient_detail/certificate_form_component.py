"""Certificate form dialog component — supports all 7 certificate types."""

import reflex as rx

from ..common.language_state import LanguageState
from .patient_detail_state import PatientDetailState


def _cert_type_options() -> rx.Component:
    """Select widget for certificate type."""
    return rx.select.root(
        rx.select.trigger(placeholder=LanguageState.tr["cert_form_type_label"]),
        rx.select.content(
            rx.select.item(LanguageState.tr["cert_type_aptitude"], value="APTITUDE"),
            rx.select.item(LanguageState.tr["cert_type_work_stoppage"], value="WORK_STOPPAGE"),
            rx.select.item(LanguageState.tr["cert_type_pre_employment"], value="PRE_EMPLOYMENT"),
            rx.select.item(LanguageState.tr["cert_type_periodic"], value="PERIODIC"),
            rx.select.item(LanguageState.tr["cert_type_work_accident"], value="WORK_ACCIDENT"),
            rx.select.item(LanguageState.tr["cert_type_sir"], value="SIR"),
            rx.select.item(LanguageState.tr["cert_type_vaccination"], value="VACCINATION"),
        ),
        value=PatientDetailState.cert_form_type,
        on_change=PatientDetailState.set_cert_form_type,
        size="2",
        width="100%",
    )


def _field(label_key: str, *controls) -> rx.Component:
    return rx.vstack(
        rx.text(LanguageState.tr[label_key], size="2", weight="medium"),
        *controls,
        spacing="1",
        width="100%",
    )


def _text_input(value_var, on_change, placeholder_key: str | None = None) -> rx.Component:
    kwargs = {"value": value_var, "on_change": on_change, "size": "2", "width": "100%"}
    if placeholder_key:
        kwargs["placeholder"] = LanguageState.tr[placeholder_key]
    return rx.input(**kwargs)


def _date_input(value_var, on_change) -> rx.Component:
    return rx.input(type="date", value=value_var, on_change=on_change, size="2", width="100%")


def _textarea_input(value_var, on_change) -> rx.Component:
    return rx.text_area(value=value_var, on_change=on_change, size="2", width="100%", rows="3")


# ── Type-specific field panels ────────────────────────────────────────────────

def _aptitude_fields() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.checkbox(
                checked=PatientDetailState.cert_form_is_fit_for_work,
                on_change=PatientDetailState.set_cert_form_is_fit_for_work,
            ),
            rx.text(LanguageState.tr["cert_form_fit_label"], size="2"),
            spacing="2",
            align="center",
        ),
        _field(
            "cert_form_restrictions_label",
            _textarea_input(PatientDetailState.cert_form_restrictions, PatientDetailState.set_cert_form_restrictions),
        ),
        spacing="3",
        width="100%",
    )


def _work_stoppage_fields() -> rx.Component:
    return rx.vstack(
        _field("cert_form_start_date_label", _date_input(PatientDetailState.cert_form_start_date, PatientDetailState.set_cert_form_start_date)),
        _field("cert_form_end_date_label", _date_input(PatientDetailState.cert_form_end_date, PatientDetailState.set_cert_form_end_date)),
        _field("cert_form_return_date_label", _date_input(PatientDetailState.cert_form_return_date, PatientDetailState.set_cert_form_return_date)),
        spacing="3",
        width="100%",
    )


def _visit_fields() -> rx.Component:
    """Shared fields for pre-employment and periodic visits."""
    return rx.vstack(
        _field("cert_form_visit_subtype_label", _text_input(PatientDetailState.cert_form_visit_subtype, PatientDetailState.set_cert_form_visit_subtype)),
        rx.hstack(
            rx.checkbox(
                checked=PatientDetailState.cert_form_is_fit_for_work,
                on_change=PatientDetailState.set_cert_form_is_fit_for_work,
            ),
            rx.text(LanguageState.tr["cert_form_fit_label"], size="2"),
            spacing="2",
            align="center",
        ),
        _field(
            "cert_form_restrictions_label",
            _textarea_input(PatientDetailState.cert_form_restrictions, PatientDetailState.set_cert_form_restrictions),
        ),
        spacing="3",
        width="100%",
    )


def _work_accident_fields() -> rx.Component:
    return rx.vstack(
        _field("cert_form_accident_date_label", _date_input(PatientDetailState.cert_form_accident_date, PatientDetailState.set_cert_form_accident_date)),
        _field("cert_form_body_part_label", _text_input(PatientDetailState.cert_form_body_part, PatientDetailState.set_cert_form_body_part)),
        spacing="3",
        width="100%",
    )


def _sir_fields() -> rx.Component:
    return rx.vstack(
        _field("cert_form_exposure_type_label", _text_input(PatientDetailState.cert_form_exposure_type, PatientDetailState.set_cert_form_exposure_type)),
        rx.hstack(
            rx.checkbox(
                checked=PatientDetailState.cert_form_is_fit_for_work,
                on_change=PatientDetailState.set_cert_form_is_fit_for_work,
            ),
            rx.text(LanguageState.tr["cert_form_fit_label"], size="2"),
            spacing="2",
            align="center",
        ),
        spacing="3",
        width="100%",
    )


def _vaccination_fields() -> rx.Component:
    return rx.vstack(
        _field("cert_form_vaccine_name_label", _text_input(PatientDetailState.cert_form_vaccine_name, PatientDetailState.set_cert_form_vaccine_name)),
        _field("cert_form_vaccine_lot_label", _text_input(PatientDetailState.cert_form_vaccine_lot, PatientDetailState.set_cert_form_vaccine_lot)),
        _field("cert_form_next_booster_label", _date_input(PatientDetailState.cert_form_next_booster, PatientDetailState.set_cert_form_next_booster)),
        spacing="3",
        width="100%",
    )


def _type_specific_fields() -> rx.Component:
    """Render the appropriate fields based on cert_form_type."""
    return rx.match(
        PatientDetailState.cert_form_type,
        ("APTITUDE", _aptitude_fields()),
        ("WORK_STOPPAGE", _work_stoppage_fields()),
        ("PRE_EMPLOYMENT", _visit_fields()),
        ("PERIODIC", _visit_fields()),
        ("WORK_ACCIDENT", _work_accident_fields()),
        ("SIR", _sir_fields()),
        ("VACCINATION", _vaccination_fields()),
        _aptitude_fields(),
    )


def certificate_form_dialog() -> rx.Component:
    """Modal dialog for creating a medical certificate of any type."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["new_certificate_title"]),
            rx.vstack(
                # Error banner
                rx.cond(
                    PatientDetailState.cert_form_error != "",
                    rx.callout(
                        PatientDetailState.cert_form_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                # Certificate type selector
                _field("cert_form_type_label", _cert_type_options()),
                # Issue date (always shown)
                _field("cert_form_date_label", _date_input(PatientDetailState.cert_form_date, PatientDetailState.set_cert_form_date)),
                # Type-specific fields
                _type_specific_fields(),
                # Conclusion (always shown)
                _field("cert_form_conclusion_label", _textarea_input(PatientDetailState.cert_form_conclusion, PatientDetailState.set_cert_form_conclusion)),
                # Action buttons
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        on_click=PatientDetailState.close_certificate_dialog,
                        variant="soft",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.button(
                        rx.cond(
                            PatientDetailState.is_saving_certificate,
                            rx.spinner(size="2"),
                            rx.icon("save", size=15),
                        ),
                        LanguageState.tr["save_certificate_btn"],
                        on_click=PatientDetailState.save_certificate,
                        loading=PatientDetailState.is_saving_certificate,
                        size="2",
                    ),
                    spacing="2",
                    width="100%",
                    padding_top="0.75rem",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="520px",
            on_interact_outside=PatientDetailState.close_certificate_dialog,
            on_escape_key_down=PatientDetailState.close_certificate_dialog,
        ),
        open=PatientDetailState.show_certificate_dialog,
    )
