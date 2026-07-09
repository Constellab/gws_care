"""Account list page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.empty_state_component import empty_state
from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .account_form_component import account_form_dialog
from .account_form_state import AccountFormState
from .account_list_state import AccountListState, AccountRowDTO


def _sortable_header(label: str, column: str) -> rx.Component:
    """Column header cell with a sort-direction arrow."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                AccountListState.sort_column == column,
                rx.cond(
                    AccountListState.sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: AccountListState.set_sort(column),
        style={"cursor": "pointer"},
    )


def _account_row(account: AccountRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.text(account.name, size="2", weight="medium"),
                rx.cond(
                    account.account_type == "INDIVIDUAL",
                    rx.badge(LanguageState.tr["account_individual_badge"], color_scheme="purple", variant="soft", size="1"),
                    rx.badge(LanguageState.tr["account_company_badge"], color_scheme="blue", variant="soft", size="1"),
                ),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(
            rx.cond(account.city, rx.text(account.city, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
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
                rx.badge(LanguageState.tr["active_badge"], color_scheme="green", variant="soft", size="1"),
                rx.badge(LanguageState.tr["inactive_badge"], color_scheme="gray", variant="soft", size="1"),
            )
        ),
        rx.table.cell(
            rx.box(
                rx.hstack(
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("chevron-right", size=14),
                            variant="ghost",
                            size="1",
                            on_click=lambda: AccountListState.go_to_account(account.id),
                        ),
                        content=LanguageState.tr["tooltip_view_account"],
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("pencil", size=14),
                            variant="ghost",
                            size="1",
                            on_click=lambda: AccountFormState.open_edit_dialog(account.id),
                        ),
                        content=LanguageState.tr["tooltip_edit_account"],
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
                            content=LanguageState.tr["tooltip_deactivate_account"],
                        ),
                    ),
                    spacing="1",
                ),
                on_click=rx.stop_propagation,
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
                rx.heading(LanguageState.tr["accounts_page_title"], size="6"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    LanguageState.tr["new_account_page_btn"],
                    on_click=AccountFormState.open_create_dialog,
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            account_form_dialog(),
            rx.hstack(
                rx.input(
                    placeholder=LanguageState.tr["search_by_name"],
                    value=AccountListState.search_name,
                    on_change=AccountListState.handle_name_change,
                    min_width="260px",
                    size="2",
                ),
                rx.select.root(
                    rx.select.trigger(
                        placeholder=LanguageState.tr["all_account_types"],
                        width="180px",
                    ),
                    rx.select.content(
                        rx.select.item(LanguageState.tr["all_account_types"], value="ALL"),
                        rx.select.item(LanguageState.tr["account_company_badge"], value="COMPANY"),
                        rx.select.item(LanguageState.tr["account_individual_badge"], value="INDIVIDUAL"),
                    ),
                    value=AccountListState.filter_account_type,
                    on_change=AccountListState.set_filter_account_type,
                    size="2",
                ),
                rx.button(
                    rx.icon("x", size=14),
                    LanguageState.tr["clear_btn"],
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
                    rx.vstack(
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
                                rx.foreach(AccountListState.accounts, _account_row)
                            ),
                            width="100%",
                            variant="surface",
                        ),
                        rx.cond(
                            AccountListState.has_more,
                            rx.center(
                                rx.button(
                                    rx.cond(
                                        AccountListState.is_loading_more,
                                        rx.hstack(rx.spinner(size="2"), rx.text(LanguageState.tr["loading_text"]), spacing="2"),
                                        rx.hstack(rx.icon("chevron-down", size=16), rx.text(LanguageState.tr["load_more_btn"]), spacing="2"),
                                    ),
                                    variant="soft",
                                    size="2",
                                    on_click=AccountListState.load_more_accounts,
                                    disabled=AccountListState.is_loading_more,
                                ),
                                width="100%",
                                padding="1rem",
                            ),
                        ),
                        width="100%",
                        spacing="0",
                    ),
                    empty_state("building-2", LanguageState.tr["no_accounts_found"]),
                ),
            ),
        )
    )
