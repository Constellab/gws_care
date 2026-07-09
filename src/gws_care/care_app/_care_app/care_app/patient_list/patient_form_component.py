"""Patient create / edit form dialog component."""

import reflex as rx
from gws_reflex_base import dialog_header

from ..common.language_state import LanguageState
from ..common.shared_address_phone_components import address_section, phone_input_field
from .patient_form_state import AccountOption, PatientFormState


def _field(label: str, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


# ── Account picker ────────────────────────────────────────────────────────────

def _account_row(a: AccountOption) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.icon(
                    rx.cond(a.account_type == "COMPANY", "building-2", "user"),
                    size=12,
                    color="var(--gray-9)",
                ),
                rx.text(a.name, size="2"),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(rx.text(a.city, size="2", color="var(--gray-9)")),
        cursor="pointer",
        _hover={"background": "var(--accent-2)"},
        on_click=lambda: PatientFormState.select_account(a.id, a.name),
    )


def _account_picker_section() -> rx.Component:
    """Account linker — shown in create mode and when editing a draft patient."""
    return rx.cond(
        PatientFormState.show_account_section,
        rx.vstack(
            rx.separator(width="100%"),
            rx.hstack(
                rx.icon("link", size=14, color="var(--accent-9)"),
                rx.text(LanguageState.tr["section_link_account"], size="2", weight="bold", color="var(--gray-9)"),
                rx.badge(LanguageState.tr["required_badge"], color_scheme="red", variant="soft", size="1"),
                rx.spacer(),
                rx.cond(
                    PatientFormState.form_account_id != "",
                    rx.icon_button(
                        rx.icon("x", size=12),
                        on_click=PatientFormState.clear_account_selection,
                        type="button",
                        variant="ghost",
                        size="1",
                        color_scheme="gray",
                    ),
                ),
                rx.button(
                    rx.cond(
                        PatientFormState.show_account_picker,
                        rx.icon("chevron-up", size=13),
                        rx.icon("chevron-down", size=13),
                    ),
                    LanguageState.tr["btn_select_account"],
                    on_click=PatientFormState.toggle_account_picker,
                    type="button",
                    variant="outline",
                    size="1",
                    color_scheme="gray",
                ),
                rx.button(
                    rx.icon("plus", size=13),
                    "Create account",
                    on_click=PatientFormState.trigger_account_create,
                    type="button",
                    variant="soft",
                    size="1",
                    color_scheme="blue",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.cond(
                PatientFormState.form_account_id != "",
                rx.vstack(
                    rx.hstack(
                        rx.icon("check-circle", size=16, color="var(--green-9)"),
                        rx.text(PatientFormState.selected_account_label, size="2", color="var(--green-11)", weight="medium"),
                        spacing="2",
                        align="center",
                    ),
                    rx.cond(
                        PatientFormState.selected_account_contact_last_name != "",
                        rx.hstack(
                            rx.icon("user", size=13, color="var(--green-9)"),
                            rx.text(
                                PatientFormState.selected_account_contact_last_name,
                                " ",
                                PatientFormState.selected_account_contact_first_name,
                                size="2", color="var(--green-11)",
                            ),
                            spacing="1", align="center",
                        ),
                    ),
                    rx.cond(
                        PatientFormState.selected_account_address != "",
                        rx.hstack(
                            rx.icon("map-pin", size=13, color="var(--green-9)"),
                            rx.text(
                                PatientFormState.selected_account_address,
                                rx.cond(
                                    PatientFormState.selected_account_postal_code != "",
                                    " — " + PatientFormState.selected_account_postal_code + " " + PatientFormState.selected_account_city,
                                    rx.cond(PatientFormState.selected_account_city != "", " — " + PatientFormState.selected_account_city, ""),
                                ),
                                size="2", color="var(--green-11)",
                            ),
                            spacing="1", align="center",
                        ),
                    ),
                    rx.cond(
                        PatientFormState.selected_account_phone != "",
                        rx.hstack(
                            rx.icon("phone", size=13, color="var(--green-9)"),
                            rx.text(PatientFormState.selected_account_phone, size="2", color="var(--green-11)"),
                            spacing="1", align="center",
                        ),
                    ),
                    rx.cond(
                        PatientFormState.selected_account_email != "",
                        rx.hstack(
                            rx.icon("mail", size=13, color="var(--green-9)"),
                            rx.text(PatientFormState.selected_account_email, size="2", color="var(--green-11)"),
                            spacing="1", align="center",
                        ),
                    ),
                    padding="0.5rem 0.75rem",
                    border="1px solid var(--green-6)",
                    border_radius="var(--radius-2)",
                    background="var(--green-2)",
                    width="100%",
                    spacing="1",
                    align_items="start",
                ),
            ),
            rx.cond(
                PatientFormState.show_account_picker,
                rx.vstack(
                    rx.input(
                        placeholder=LanguageState.tr["search_account_placeholder"],
                        value=PatientFormState.account_filter,
                        on_change=PatientFormState.set_account_filter,
                        size="2",
                        width="100%",
                    ),
                    rx.cond(
                        PatientFormState.is_loading_accounts,
                        rx.center(rx.spinner(size="2"), padding="0.75rem"),
                        rx.cond(
                            PatientFormState.account_options.length() > 0,
                            rx.box(
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            rx.table.column_header_cell(rx.text("Account", size="1")),
                                            rx.table.column_header_cell(rx.text("City", size="1")),
                                        )
                                    ),
                                    rx.table.body(rx.foreach(PatientFormState.account_options, _account_row)),
                                    size="1",
                                    variant="surface",
                                    width="100%",
                                ),
                                max_height="200px",
                                overflow_y="auto",
                                width="100%",
                                border_radius="var(--radius-2)",
                            ),
                            rx.center(
                                rx.text(LanguageState.tr["no_accounts_found"], size="2", color="var(--gray-9)"),
                                padding="0.75rem",
                            ),
                        ),
                    ),
                    spacing="2",
                    width="100%",
                    padding="0.75rem",
                    border="1px solid var(--gray-4)",
                    border_radius="var(--radius-2)",
                    background="var(--gray-1)",
                ),
            ),
            width="100%",
            spacing="2",
        ),
    )


# ── Main form fields ──────────────────────────────────────────────────────────

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
                LanguageState.tr["field_gender"] + " *",
                rx.select.root(
                    rx.select.trigger(placeholder=LanguageState.tr["select_gender_placeholder"]),
                    rx.select.content(
                        rx.select.item(LanguageState.tr["gender_male"], value="M"),
                        rx.select.item(LanguageState.tr["gender_female"], value="F"),
                    ),
                    value=PatientFormState.form_gender,
                    on_change=PatientFormState.set_form_gender,
                    size="2", width="100%",
                ),
            ),
            columns="2", spacing="3", width="100%",
        ),
        # ── Address section (IGN autocomplete for France, manual for other countries) ──
        address_section(PatientFormState),
        # ── Contact ───────────────────────────────────────────────────────────
        rx.separator(width="100%"),
        rx.text(LanguageState.tr["section_contact"], size="2", weight="bold", color="var(--gray-9)"),
        rx.grid(
            phone_input_field(PatientFormState),
            _field(
                LanguageState.tr["field_email"],
                rx.input(
                    value=PatientFormState.form_email,
                    on_change=PatientFormState.set_form_email,
                    placeholder="patient@email.com",
                    type="email", size="2", width="100%",
                ),
            ),
            columns="2", spacing="3", width="100%",
        ),
        # ── Medical info ───────────────────────────────────────────────────────
        rx.separator(width="100%"),
        rx.text(LanguageState.tr["section_medical_info"], size="2", weight="bold", color="var(--gray-9)"),
        _field(
            LanguageState.tr["field_ssn"],
            rx.input(
                value=PatientFormState.form_social_security_number,
                on_change=PatientFormState.set_form_social_security_number,
                placeholder=rx.cond(
                    PatientFormState.form_country == "France",
                    "1 85 07 75 123 456 78",
                    "Social security number",
                ),
                size="2", width="100%",
            ),
        ),
        # ── Account linking (required) ─────────────────────────────────────────
        _account_picker_section(),
        # ── Inline error ─────────────────────────────────────────────────────
        rx.cond(
            PatientFormState.form_error != "",
            rx.callout(
                PatientFormState.form_error,
                icon="triangle-alert",
                color_scheme="red",
                size="1",
                width="100%",
            ),
            rx.fragment(),
        ),
        # ── Draft save button ─────────────────────────────────────────────────
        rx.cond(
            PatientFormState.is_create_mode,
            rx.hstack(
                rx.icon("save", size=14, color="var(--orange-9)"),
                rx.text(LanguageState.tr["save_as_draft_btn"], size="2", color="var(--orange-11)"),
                rx.text(LanguageState.tr["partial_data_hint"], size="1", color="var(--gray-9)"),
                spacing="2",
                align="center",
                padding="0.5rem 0.75rem",
                border="1px dashed var(--orange-6)",
                border_radius="var(--radius-2)",
                background="var(--orange-2)",
                cursor="pointer",
                width="100%",
                on_click=PatientFormState.save_as_draft,
            ),
        ),
        width="100%",
        spacing="3",
    )


def patient_form_dialog() -> rx.Component:
    """The patient create / edit dialog.

    Uses a manual rx.dialog.root instead of form_dialog_component to intentionally
    omit on_interact_outside. When the account creation dialog opens on top of this
    form, Radix UI would fire 'interact outside' on this dialog and silently close it,
    losing all form data and preventing the patient from being saved.
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                dialog_header(
                    rx.cond(
                        PatientFormState.is_create_mode,
                        LanguageState.tr["new_patient_title"],
                        LanguageState.tr["edit_patient_title"],
                    ),
                    close=PatientFormState.close_dialog,
                ),
                rx.dialog.description(
                    rx.cond(
                        PatientFormState.is_create_mode,
                        LanguageState.tr["new_patient_desc"],
                        LanguageState.tr["edit_patient_desc"],
                    ),
                    size="2",
                    margin_bottom="1rem",
                ),
                rx.form(
                    _form_fields(),
                    rx.hstack(
                        rx.button(
                            LanguageState.tr["cancel_btn"],
                            type="button",
                            variant="soft",
                            color_scheme="gray",
                            on_click=PatientFormState.close_dialog,
                            disabled=PatientFormState.is_loading,
                        ),
                        rx.button(
                            rx.spinner(loading=PatientFormState.is_loading),
                            rx.cond(
                                PatientFormState.is_create_mode,
                                LanguageState.tr["create_btn"],
                                LanguageState.tr["save_btn"],
                            ),
                            type="submit",
                            disabled=PatientFormState.is_loading,
                        ),
                        margin_top="1em",
                    ),
                    on_submit=PatientFormState.submit_form,
                ),
                width="100%",
            ),
            max_width="720px",
            on_escape_key_down=PatientFormState.close_dialog,
        ),
        open=PatientFormState.dialog_opened,
    )
