"""My Accounts page component for the patient portal (/my-patient-accounts).

Table-based view matching the admin account list style.
Patients can create or edit personal (INDIVIDUAL) accounts.
Enterprise (COMPANY) accounts are read-only.
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .patient_accounts_state import PatientAccountRowDTO, PatientAccountsState


# ── Sortable column header ─────────────────────────────────────────────────────


def _sortable_header(label: rx.Var | str, column: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                PatientAccountsState.sort_column == column,
                rx.cond(
                    PatientAccountsState.sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: PatientAccountsState.set_sort(column),
        style={"cursor": "pointer"},
    )


# ── Badge helpers ──────────────────────────────────────────────────────────────


def _account_type_badge(account_type: str) -> rx.Component:
    return rx.match(
        account_type,
        ("COMPANY", rx.badge(LanguageState.tr["account_company_badge"], color_scheme="blue", variant="soft", size="1")),
        ("INDIVIDUAL", rx.badge(LanguageState.tr["account_individual_badge"], color_scheme="purple", variant="soft", size="1")),
        rx.badge(account_type, color_scheme="gray", variant="soft", size="1"),
    )


# ── Table row ──────────────────────────────────────────────────────────────────


def _account_row(acct: PatientAccountRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.text(acct.name, size="2", weight="medium"),
                _account_type_badge(acct.account_type),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(
            rx.cond(acct.city != "", rx.text(acct.city, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(acct.phone != "", rx.text(acct.phone, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(acct.email != "", rx.text(acct.email, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(
                acct.is_active,
                rx.badge(LanguageState.tr["active_badge"], color_scheme="green", variant="soft", size="1"),
                rx.badge(LanguageState.tr["inactive_badge"], color_scheme="gray", variant="soft", size="1"),
            )
        ),
        # Edit button — only for INDIVIDUAL accounts
        rx.table.cell(
            rx.cond(
                acct.account_type == "INDIVIDUAL",
                rx.box(
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("pencil", size=14),
                            variant="ghost",
                            size="1",
                            on_click=lambda: PatientAccountsState.open_edit_dialog(acct.id),
                        ),
                        content=LanguageState.tr["tooltip_edit_personal_account"],
                    ),
                    on_click=rx.stop_propagation,
                ),
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


# ── Create / Edit dialog ───────────────────────────────────────────────────────


def _field(label: str | rx.Component, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        label if not isinstance(label, str) else rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _account_form_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    PatientAccountsState.form_is_edit_mode,
                    LanguageState.tr["edit_personal_account_form_title"],
                    LanguageState.tr["new_personal_account_form_title"],
                )
            ),
            rx.dialog.description(
                rx.cond(
                    PatientAccountsState.form_is_edit_mode,
                    LanguageState.tr["edit_personal_account_desc"],
                    LanguageState.tr["new_personal_account_desc"],
                ),
                size="2",
                color="var(--gray-9)",
            ),
            rx.separator(width="100%", margin_y="0.75rem"),
            rx.form.root(
                rx.vstack(
                    # Account type locked to INDIVIDUAL (read-only indicator)
                    rx.hstack(
                        rx.icon("user", size=14, color="var(--accent-9)"),
                        rx.text(LanguageState.tr["account_type_individual"], size="2", weight="medium", color="var(--accent-9)"),
                        rx.badge(LanguageState.tr["account_individual_badge"], color_scheme="purple", variant="soft", size="1"),
                        spacing="2",
                        align="center",
                        padding="0.5rem 0.75rem",
                        border="1px solid var(--accent-6)",
                        border_radius="var(--radius-2)",
                        background="var(--accent-2)",
                        width="100%",
                    ),
                    rx.separator(width="100%"),
                    _field(
                        LanguageState.tr["field_full_name"],
                        rx.input(
                            value=PatientAccountsState.form_name,
                            on_change=PatientAccountsState.set_form_name,
                            placeholder="Jean Dupont",
                            size="2",
                            width="100%",
                        ),
                    ),
                    rx.separator(width="100%"),
                    rx.text(LanguageState.tr["section_address"], size="2", weight="bold", color="var(--gray-9)"),
                    _field(
                        LanguageState.tr["field_street_address"],
                        rx.input(
                            value=PatientAccountsState.form_address,
                            on_change=PatientAccountsState.set_form_address,
                            placeholder="12 rue de la Paix",
                            size="2",
                            width="100%",
                        ),
                    ),
                    rx.grid(
                        _field(
                            LanguageState.tr["field_postal_code"],
                            rx.input(
                                value=PatientAccountsState.form_postal_code,
                                on_change=PatientAccountsState.set_form_postal_code,
                                placeholder="75001",
                                size="2",
                                width="100%",
                            ),
                        ),
                        _field(
                            LanguageState.tr["field_city"],
                            rx.input(
                                value=PatientAccountsState.form_city,
                                on_change=PatientAccountsState.set_form_city,
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
                    rx.text(LanguageState.tr["section_contact"], size="2", weight="bold", color="var(--gray-9)"),
                    rx.grid(
                        _field(
                            LanguageState.tr["field_phone"],
                            rx.input(
                                value=PatientAccountsState.form_phone,
                                on_change=PatientAccountsState.set_form_phone,
                                placeholder="+33 1 00 00 00 00",
                                size="2",
                                width="100%",
                            ),
                        ),
                        _field(
                            LanguageState.tr["field_email"],
                            rx.input(
                                value=PatientAccountsState.form_email,
                                on_change=PatientAccountsState.set_form_email,
                                placeholder="contact@example.com",
                                type="email",
                                size="2",
                                width="100%",
                            ),
                        ),
                        columns="2",
                        spacing="3",
                        width="100%",
                    ),
                    rx.cond(
                        PatientAccountsState.form_error_message != "",
                        rx.callout(
                            PatientAccountsState.form_error_message,
                            icon="triangle-alert",
                            color_scheme="red",
                            size="1",
                        ),
                    ),
                    rx.hstack(
                        rx.button(
                            LanguageState.tr["cancel_btn"],
                            variant="soft",
                            color_scheme="gray",
                            on_click=PatientAccountsState.close_dialog,
                            disabled=PatientAccountsState.form_is_loading,
                            type="button",
                        ),
                        rx.button(
                            rx.cond(
                                PatientAccountsState.form_is_loading,
                                rx.spinner(size="2"),
                                rx.cond(
                                    PatientAccountsState.form_is_edit_mode,
                                    rx.text(LanguageState.tr["save_personal_account_btn"]),
                                    rx.text(LanguageState.tr["create_personal_account_btn"]),
                                ),
                            ),
                            type="submit",
                            disabled=PatientAccountsState.form_is_loading,
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                        padding_top="0.5rem",
                    ),
                    width="100%",
                    spacing="3",
                ),
                on_submit=PatientAccountsState.submit_account_form,
                width="100%",
            ),
            on_interact_outside=PatientAccountsState.close_dialog,
            on_escape_key_down=PatientAccountsState.close_dialog,
            max_width="520px",
        ),
        open=PatientAccountsState.form_dialog_open,
    )


# ── Reusable accounts section (embedded in My Details) ───────────────────────


def accounts_section_for_details() -> rx.Component:
    """Account list + create/edit dialog, embeddable in any page that has
    PatientAccountsState loaded as part of its on_load chain."""
    return rx.vstack(
        rx.hstack(
            rx.text(LanguageState.tr["my_patient_accounts_title"], size="3", weight="bold", color="var(--gray-9)"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                LanguageState.tr["new_personal_account_btn"],
                on_click=PatientAccountsState.open_create_dialog,
                size="1",
                variant="outline",
            ),
            width="100%",
            align="center",
        ),
        _account_form_dialog(),
        rx.cond(
            PatientAccountsState.is_loading,
            rx.center(rx.spinner(size="2"), padding="2rem"),
            rx.cond(
                PatientAccountsState.accounts.length() == 0,
                rx.center(
                    rx.vstack(
                        rx.icon("building-2", size=40, color="var(--gray-6)"),
                        rx.text(LanguageState.tr["no_patient_accounts"], size="2", color="var(--gray-9)"),
                        align="center",
                        spacing="2",
                    ),
                    padding="4rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="8px",
                    width="100%",
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            _sortable_header(LanguageState.tr["col_account_name"], "name"),
                            _sortable_header(LanguageState.tr["col_city"], "city"),
                            _sortable_header(LanguageState.tr["col_phone"], "phone"),
                            _sortable_header(LanguageState.tr["col_email"], "email"),
                            _sortable_header(LanguageState.tr["col_status"], "is_active"),
                            rx.table.column_header_cell(""),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(PatientAccountsState.accounts, _account_row)
                    ),
                    width="100%",
                    variant="surface",
                    size="1",
                ),
            ),
        ),
        width="100%",
        spacing="3",
        padding="1rem",
        border="1px solid var(--gray-4)",
        border_radius="8px",
        background="var(--gray-1)",
    )


# ── Page ──────────────────────────────────────────────────────────────────────


def patient_accounts_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.hstack(
                rx.heading(LanguageState.tr["my_patient_accounts_title"], size="6"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    LanguageState.tr["new_personal_account_btn"],
                    on_click=PatientAccountsState.open_create_dialog,
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            _account_form_dialog(),
            rx.cond(
                PatientAccountsState.error_message != "",
                rx.callout(
                    PatientAccountsState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                PatientAccountsState.is_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    PatientAccountsState.accounts.length() == 0,
                    rx.center(
                        rx.vstack(
                            rx.icon("building-2", size=40, color="var(--gray-7)"),
                            rx.text(LanguageState.tr["no_patient_accounts"], size="3", color="var(--gray-9)"),
                            spacing="3",
                            align="center",
                        ),
                        padding="4rem",
                    ),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                _sortable_header(LanguageState.tr["col_account_name"], "name"),
                                _sortable_header(LanguageState.tr["col_city"], "city"),
                                _sortable_header(LanguageState.tr["col_phone"], "phone"),
                                _sortable_header(LanguageState.tr["col_email"], "email"),
                                _sortable_header(LanguageState.tr["col_status"], "is_active"),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(PatientAccountsState.accounts, _account_row)
                        ),
                        width="100%",
                        variant="surface",
                    ),
                ),
            ),
        )
    )
