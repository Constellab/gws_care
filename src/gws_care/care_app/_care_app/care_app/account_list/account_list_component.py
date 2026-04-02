"""Account list page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .account_form_component import account_form_dialog
from .account_form_state import AccountFormState
from .account_list_state import AccountListState, AccountRowDTO


def _account_row(account: AccountRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(account.name, size="2", weight="medium")),
        rx.table.cell(
            rx.cond(account.city, rx.text(account.city, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(account.contact_name, rx.text(account.contact_name, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(account.phone, rx.text(account.phone, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(account.email, rx.text(account.email, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(
                account.is_active,
                rx.badge("Active", color_scheme="green", variant="soft", size="1"),
                rx.badge("Inactive", color_scheme="gray", variant="soft", size="1"),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("chevron-right", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: AccountListState.go_to_account(account.id),
                    ),
                    content="View account",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pencil", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: AccountFormState.open_edit_dialog(account.id),
                    ),
                    content="Edit account",
                ),
                rx.cond(
                    account.is_active,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("ban", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="red",
                            on_click=lambda: AccountListState.deactivate_account(account.id),
                        ),
                        content="Deactivate account",
                    ),
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}, "cursor": "pointer"},
        on_click=lambda: AccountListState.go_to_account(account.id),
    )


def account_list_page() -> rx.Component:
    """Account list page."""
    return main_component(
        page_layout(
            rx.hstack(
                rx.heading("Accounts", size="6"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    "New Account",
                    on_click=AccountFormState.open_create_dialog,
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            account_form_dialog(),
            rx.hstack(
                rx.input(
                    placeholder="Search by name…",
                    value=AccountListState.search_name,
                    on_change=AccountListState.handle_name_change,
                    min_width="260px",
                    size="2",
                ),
                rx.button(
                    rx.icon("x", size=14),
                    "Clear",
                    on_click=AccountListState.clear_filters,
                    variant="outline",
                    size="2",
                ),
                spacing="3",
                width="100%",
            ),
            rx.cond(
                AccountListState.error_message != "",
                rx.callout(
                    AccountListState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                AccountListState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    AccountListState.accounts.length() > 0,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Account Name"),
                                rx.table.column_header_cell("City"),
                                rx.table.column_header_cell("Contact"),
                                rx.table.column_header_cell("Phone"),
                                rx.table.column_header_cell("Email"),
                                rx.table.column_header_cell("Status"),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(AccountListState.accounts, _account_row)
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("building-2", size=40, color="var(--gray-7)"),
                            rx.text("No accounts found", color="var(--gray-9)"),
                            align="center",
                            spacing="2",
                        ),
                        padding="3rem",
                    ),
                ),
            ),
        )
    )
