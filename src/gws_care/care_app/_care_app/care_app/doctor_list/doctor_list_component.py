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
                    rx.box(
                        rx.input(
                            value=DoctorListState.form_specialization,
                            on_change=DoctorListState.set_form_specialization,
                            on_focus=DoctorListState.focus_specialty_input,
                            on_blur=DoctorListState.hide_specialty_suggestions,
                            placeholder="ex. General Medicine",
                            size="2",
                            width="100%",
                        ),
                        rx.cond(
                            DoctorListState.show_specialty_suggestions
                            & (DoctorListState.filtered_specialty_suggestions.length() > 0),
                            rx.box(
                                rx.foreach(
                                    DoctorListState.filtered_specialty_suggestions,
                                    lambda s: rx.box(
                                        rx.text(s, size="2"),
                                        padding="6px 10px",
                                        cursor="pointer",
                                        border_bottom="1px solid var(--gray-3)",
                                        _hover={"background": "var(--accent-2)"},
                                        on_mouse_down=lambda: DoctorListState.pick_specialty_suggestion(s),
                                    ),
                                ),
                                position="absolute",
                                top="100%",
                                left="0",
                                right="0",
                                background="white",
                                border="1px solid var(--gray-5)",
                                border_radius="6px",
                                box_shadow="0 4px 12px rgba(0,0,0,0.12)",
                                z_index="200",
                                max_height="180px",
                                overflow_y="auto",
                            ),
                            rx.fragment(),
                        ),
                        position="relative",
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
                                rx.select.item("🇲🇦 +212  Morocco", value="+212"),
                                rx.select.item("🇩🇿 +213  Algeria", value="+213"),
                                rx.select.item("🇹🇳 +216  Tunisia", value="+216"),
                                rx.select.item("🇸🇳 +221  Senegal", value="+221"),
                                rx.select.item("🇨🇮 +225  Ivory Coast", value="+225"),
                                rx.select.item("🇧🇪 +32  Belgium", value="+32"),
                                rx.select.item("🇨🇭 +41  Switzerland", value="+41"),
                                rx.select.item("🇨🇦 +1  Canada", value="+1"),
                                rx.select.item("🇩🇪 +49  Germany", value="+49"),
                                rx.select.item("🇬🇧 +44  United Kingdom", value="+44"),
                                rx.select.item("🌐 Other", value="other"),
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


def _action_confirm_dialog() -> rx.Component:
    """Unified confirmation dialog for deactivate / archive / delete / reactivate."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.cond(
                        DoctorListState.action_confirm_is_red,
                        rx.icon("triangle-alert", size=20, color="var(--red-9)"),
                        rx.icon("info", size=20, color="var(--accent-9)"),
                    ),
                    rx.dialog.title(DoctorListState.action_confirm_title, margin="0"),
                    spacing="2", align="center",
                ),
                rx.text(DoctorListState.action_confirm_desc, size="2", color="var(--gray-11)"),
                rx.cond(
                    DoctorListState.action_confirm_show_reason,
                    rx.vstack(
                        rx.text("Reason *", size="2", weight="medium"),
                        rx.text_area(
                            placeholder="Enter the reason for this action…",
                            value=DoctorListState.action_reason,
                            on_change=DoctorListState.set_action_reason,
                            rows="3",
                            width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="outline",
                        color_scheme="gray",
                        on_click=DoctorListState.close_action_confirm,
                    ),
                    rx.cond(
                        DoctorListState.action_confirm_is_red,
                        rx.button(
                            rx.icon("trash-2", size=14),
                            DoctorListState.action_confirm_btn_label,
                            color_scheme="red",
                            loading=DoctorListState.action_is_saving,
                            on_click=DoctorListState.confirm_action,
                        ),
                        rx.button(
                            DoctorListState.action_confirm_btn_label,
                            loading=DoctorListState.action_is_saving,
                            on_click=DoctorListState.confirm_action,
                        ),
                    ),
                    spacing="2", width="100%", padding_top="0.5rem",
                ),
                spacing="3", width="100%",
            ),
            on_interact_outside=DoctorListState.close_action_confirm,
            on_escape_key_down=DoctorListState.close_action_confirm,
            max_width="460px",
        ),
        open=DoctorListState.show_action_confirm,
    )


def _doctor_row(doctor: DoctorRowDTO) -> rx.Component:
    return rx.table.row(
        # Name + status badges + reason
        rx.table.cell(
            rx.vstack(
                rx.hstack(
                    rx.text(doctor.full_name, size="2", weight="medium"),
                    rx.cond(
                        doctor.is_archived,
                        rx.badge(LanguageState.tr["archived_badge"], color_scheme="orange", variant="soft", size="1"),
                        rx.cond(
                            ~doctor.is_active,
                            rx.badge(LanguageState.tr["inactive_badge"], color_scheme="gray", variant="soft", size="1"),
                            rx.fragment(),
                        ),
                    ),
                    spacing="2", align="center",
                ),
                rx.cond(
                    (~doctor.is_active | doctor.is_archived) & (doctor.status_reason != ""),
                    rx.text(
                        doctor.status_reason,
                        size="1",
                        color="var(--gray-9)",
                        font_style="italic",
                    ),
                    rx.fragment(),
                ),
                spacing="1", align_items="start",
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
        # Actions dropdown
        rx.table.cell(
            rx.cond(
                doctor.is_archived,
                # Archived: reactivate or delete only
                rx.dropdown_menu.root(
                    rx.dropdown_menu.trigger(
                        rx.icon_button(rx.icon("ellipsis-vertical", size=14), variant="ghost", size="1")
                    ),
                    rx.dropdown_menu.content(
                        rx.dropdown_menu.item(
                            rx.icon("circle-check", size=14), LanguageState.tr["reactivate_tooltip"],
                            on_click=lambda: DoctorListState.open_action_confirm(doctor.id, doctor.full_name, "reactivate"),
                        ),
                        rx.dropdown_menu.separator(),
                        rx.dropdown_menu.item(
                            rx.icon("trash-2", size=14), LanguageState.tr["delete_btn"],
                            color_scheme="red",
                            on_click=lambda: DoctorListState.open_action_confirm(doctor.id, doctor.full_name, "delete"),
                        ),
                    ),
                ),
                # Active or inactive
                rx.dropdown_menu.root(
                    rx.dropdown_menu.trigger(
                        rx.icon_button(rx.icon("ellipsis-vertical", size=14), variant="ghost", size="1")
                    ),
                    rx.dropdown_menu.content(
                        rx.dropdown_menu.item(
                            rx.icon("pencil", size=14), LanguageState.tr["edit_btn"],
                            on_click=lambda: DoctorListState.open_edit_dialog(doctor.id),
                        ),
                        rx.dropdown_menu.separator(),
                        rx.cond(
                            doctor.is_active,
                            rx.dropdown_menu.item(
                                rx.icon("user-x", size=14), LanguageState.tr["deactivate_tooltip"],
                                on_click=lambda: DoctorListState.open_action_confirm(doctor.id, doctor.full_name, "deactivate"),
                            ),
                            rx.dropdown_menu.item(
                                rx.icon("circle-check", size=14), LanguageState.tr["reactivate_tooltip"],
                                on_click=lambda: DoctorListState.open_action_confirm(doctor.id, doctor.full_name, "reactivate"),
                            ),
                        ),
                        rx.dropdown_menu.item(
                            rx.icon("archive", size=14), LanguageState.tr["archive_btn"],
                            on_click=lambda: DoctorListState.open_action_confirm(doctor.id, doctor.full_name, "archive"),
                        ),
                        rx.dropdown_menu.separator(),
                        rx.dropdown_menu.item(
                            rx.icon("trash-2", size=14), LanguageState.tr["delete_btn"],
                            color_scheme="red",
                            on_click=lambda: DoctorListState.open_action_confirm(doctor.id, doctor.full_name, "delete"),
                        ),
                    ),
                ),
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def doctor_list_page() -> rx.Component:
    return main_component(
        page_layout(
            _doctor_form_dialog(),
            _action_confirm_dialog(),
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
