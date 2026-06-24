"""Medical Doctors admin page — list and create/edit dialog."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.empty_state_component import empty_state
from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .doctor_list_state import DoctorListState, DoctorRowDTO


def _field(label: str, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _doctor_form_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    DoctorListState.is_edit_mode,
                    LanguageState.tr["edit_doctor_form_title"],
                    LanguageState.tr["new_doctor_form_title"],
                )
            ),
            rx.vstack(
                rx.grid(
                    _field(
                        LanguageState.tr["field_first_name"],
                        rx.input(
                            value=DoctorListState.form_first_name,
                            on_change=DoctorListState.set_form_first_name,
                            placeholder=LanguageState.tr["placeholder_first_name"],
                            size="2",
                            width="100%",
                        ),
                    ),
                    _field(
                        LanguageState.tr["field_last_name"],
                        rx.input(
                            value=DoctorListState.form_last_name,
                            on_change=DoctorListState.set_form_last_name,
                            placeholder=LanguageState.tr["placeholder_last_name"],
                            size="2",
                            width="100%",
                        ),
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),
                _field(
                    LanguageState.tr["field_specialization"],
                    rx.input(
                        value=DoctorListState.form_specialization,
                        on_change=DoctorListState.set_form_specialization,
                        placeholder="ex. Médecine générale",
                        size="2",
                        width="100%",
                    ),
                ),
                _field(
                    LanguageState.tr["field_phone"],
                    rx.hstack(
                        rx.select.root(
                            rx.select.trigger(width="110px"),
                            rx.select.content(
                                rx.select.item("🇫🇷 +33  France", value="+33"),
                                rx.select.item("🇲🇦 +212  Maroc", value="+212"),
                                rx.select.item("🇩🇿 +213  Algérie", value="+213"),
                                rx.select.item("🇹🇳 +216  Tunisie", value="+216"),
                                rx.select.item("🇸🇳 +221  Sénégal", value="+221"),
                                rx.select.item("🇨🇮 +225  Côte d'Ivoire", value="+225"),
                                rx.select.item("🇧🇪 +32  Belgique", value="+32"),
                                rx.select.item("🇨🇭 +41  Suisse", value="+41"),
                                rx.select.item("🇨🇦 +1  Canada", value="+1"),
                                rx.select.item("🇩🇪 +49  Allemagne", value="+49"),
                                rx.select.item("🇬🇧 +44  Royaume-Uni", value="+44"),
                                rx.select.item("🌐 Autre", value="other"),
                            ),
                            value=DoctorListState.form_phone_dial_code,
                            on_change=DoctorListState.set_form_phone_dial_code,
                            size="2",
                        ),
                        rx.input(
                            value=DoctorListState.form_phone,
                            on_change=DoctorListState.set_form_phone,
                            placeholder="6 00 00 00 00",
                            size="2",
                            flex="1",
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                    ),
                ),
                rx.grid(
                    _field(
                        LanguageState.tr["field_email"],
                        rx.input(
                            value=DoctorListState.form_email,
                            on_change=DoctorListState.set_form_email,
                            placeholder="medecin@cabinet.fr",
                            type="email",
                            size="2",
                            width="100%",
                        ),
                    ),
                    _field(
                        LanguageState.tr["field_rpps"],
                        rx.input(
                            value=DoctorListState.form_rpps,
                            on_change=DoctorListState.set_form_rpps,
                            placeholder="10 chiffres",
                            size="2",
                            width="100%",
                        ),
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),
                rx.cond(
                    DoctorListState.form_error != "",
                    rx.callout(
                        DoctorListState.form_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="outline",
                        on_click=DoctorListState.close_form_dialog,
                    ),
                    rx.button(
                        LanguageState.tr["save"],
                        on_click=DoctorListState.save_doctor,
                        loading=DoctorListState.form_is_saving,
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                width="100%",
                padding_top="0.5rem",
            ),
            on_interact_outside=DoctorListState.close_form_dialog,
            on_escape_key_down=DoctorListState.close_form_dialog,
            max_width="560px",
        ),
        open=DoctorListState.show_form_dialog,
    )


def _doctor_row(doctor: DoctorRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.text(doctor.full_name, size="2", weight="medium"),
                rx.cond(
                    ~doctor.is_active,
                    rx.badge(LanguageState.tr["inactive_badge"], color_scheme="gray", variant="soft", size="1"),
                ),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(
            rx.cond(
                doctor.specialization != "",
                rx.text(doctor.specialization, size="2"),
                rx.text("—", size="2", color="var(--gray-8)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                doctor.phone != "",
                rx.text(doctor.phone, size="2"),
                rx.text("—", size="2", color="var(--gray-8)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                doctor.rpps_number != "",
                rx.text(doctor.rpps_number, size="2", color="var(--gray-9)"),
                rx.text("—", size="2", color="var(--gray-8)"),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pencil", size=14),
                        on_click=lambda: DoctorListState.open_edit_dialog(doctor.id),
                        variant="ghost",
                        size="1",
                    ),
                    content=LanguageState.tr["edit_btn"],
                ),
                rx.cond(
                    doctor.is_active,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("user-x", size=14),
                            on_click=lambda: DoctorListState.deactivate_doctor(doctor.id),
                            variant="ghost",
                            color_scheme="red",
                            size="1",
                        ),
                        content=LanguageState.tr["tooltip_deactivate_account"],
                    ),
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def doctor_list_page() -> rx.Component:
    return main_component(
        page_layout(
            _doctor_form_dialog(),
            rx.hstack(
                rx.heading(LanguageState.tr["doctors_page_title"], size="6"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    LanguageState.tr["new_doctor_btn"],
                    on_click=DoctorListState.open_create_dialog,
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                DoctorListState.error_message != "",
                rx.callout(
                    DoctorListState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                    size="1",
                ),
            ),
            rx.cond(
                DoctorListState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    DoctorListState.doctors.length() > 0,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(LanguageState.tr["col_name"]),
                                rx.table.column_header_cell(LanguageState.tr["col_specialization"]),
                                rx.table.column_header_cell(LanguageState.tr["col_phone"]),
                                rx.table.column_header_cell(LanguageState.tr["col_rpps"]),
                                rx.table.column_header_cell(LanguageState.tr["col_actions"]),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(DoctorListState.doctors, _doctor_row),
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    empty_state("stethoscope", LanguageState.tr["no_doctors_found"]),
                ),
            ),
            spacing="4",
        )
    )
