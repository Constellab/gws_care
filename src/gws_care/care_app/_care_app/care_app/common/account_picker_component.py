"""Reusable account-picker component (filter + table dialog) and trigger button."""

import reflex as rx

from .account_picker_state import AccountPickerRowDTO, AccountPickerState
from .language_state import LanguageState


def _account_type_badge(account_type: str) -> rx.Component:
    return rx.match(
        account_type,
        ("COMPANY", rx.badge(LanguageState.tr["account_company_badge"], color_scheme="blue", variant="soft", size="1")),
        ("INDIVIDUAL", rx.badge(LanguageState.tr["account_individual_badge"], color_scheme="purple", variant="soft", size="1")),
        rx.badge(account_type, color_scheme="gray", variant="soft", size="1"),
    )


def account_picker_dialog(state: type[AccountPickerState] = AccountPickerState) -> rx.Component:
    """Render the account picker dialog for *state*.

    Must be placed somewhere in the page component.
    Open it by calling ``state.open_account_picker``.
    """

    def _row(account: AccountPickerRowDTO) -> rx.Component:
        return rx.table.row(
            rx.table.cell(rx.text(account.name, size="2", weight="medium")),
            rx.table.cell(_account_type_badge(account.account_type)),
            rx.table.cell(
                rx.cond(account.city, rx.text(account.city, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
            ),
            rx.table.cell(
                rx.cond(account.phone, rx.text(account.phone, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
            ),
            _hover={"background_color": "var(--accent-2)", "cursor": "pointer"},
            on_click=lambda: state.acct_picker_confirm(account.id, account.name),
        )

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["acct_picker_title"]),
            rx.vstack(
                rx.input(
                    rx.input.slot(rx.icon("search", size=14)),
                    placeholder=LanguageState.tr["acct_picker_filter_placeholder"],
                    value=state.acct_picker_filter,
                    on_change=state.acct_picker_set_filter,
                    size="2",
                    width="100%",
                ),
                rx.cond(
                    state.acct_picker_error != "",
                    rx.callout(state.acct_picker_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.cond(
                    state.acct_picker_is_loading,
                    rx.center(rx.spinner(size="2"), padding="1.5rem"),
                    rx.cond(
                        state.acct_picker_accounts.length() > 0,
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell(LanguageState.tr["col_account_name"]),
                                        rx.table.column_header_cell(LanguageState.tr["field_account_type"]),
                                        rx.table.column_header_cell(LanguageState.tr["field_city"]),
                                        rx.table.column_header_cell(LanguageState.tr["field_phone"]),
                                    )
                                ),
                                rx.table.body(rx.foreach(state.acct_picker_accounts, _row)),
                                width="100%",
                                variant="surface",
                            ),
                            max_height="320px",
                            overflow_y="auto",
                            width="100%",
                        ),
                        rx.center(
                            rx.text(LanguageState.tr["no_accounts_found"], size="2", color="var(--gray-9)"),
                            padding="1.5rem",
                        ),
                    ),
                ),
                rx.hstack(
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="soft",
                        color_scheme="gray",
                        on_click=state.close_account_picker,
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            on_escape_key_down=state.close_account_picker,
            max_width="620px",
        ),
        open=state.acct_picker_is_open,
    )


def account_picker_widget(state: type[AccountPickerState] = AccountPickerState) -> rx.Component:
    """Render an inline account picker (filter bar + table) without a dialog.

    Use this when the picker should live directly inside another dialog or form.
    The selected account is stored in ``state.acct_picker_selected_id`` /
    ``state.acct_picker_selected_name``.  Clicking a row calls
    ``state.acct_picker_confirm``.
    """

    def _row(account: AccountPickerRowDTO) -> rx.Component:
        is_selected = state.acct_picker_selected_id == account.id
        return rx.table.row(
            rx.table.cell(rx.text(account.name, size="2", weight="medium")),
            rx.table.cell(_account_type_badge(account.account_type)),
            rx.table.cell(
                rx.cond(account.city, rx.text(account.city, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
            ),
            style=rx.cond(
                is_selected,
                {"background_color": "var(--accent-3)", "cursor": "pointer"},
                {"cursor": "pointer"},
            ),
            _hover={"background_color": "var(--accent-2)"},
            on_click=lambda: state.acct_picker_confirm(account.id, account.name),
        )

    return rx.vstack(
        rx.hstack(
            rx.input(
                rx.input.slot(rx.icon("search", size=14)),
                placeholder=LanguageState.tr["acct_picker_filter_placeholder"],
                value=state.acct_picker_filter,
                on_change=state.acct_picker_set_filter,
                size="2",
                flex="1",
            ),
            rx.cond(
                state.acct_picker_selected_id != "",
                rx.hstack(
                    rx.icon("building-2", size=14, color="var(--accent-9)"),
                    rx.text(state.acct_picker_selected_name, size="2", color="var(--accent-9)", weight="medium"),
                    rx.icon_button(
                        rx.icon("x", size=12),
                        on_click=state.acct_picker_clear,
                        variant="ghost",
                        color_scheme="gray",
                        size="1",
                    ),
                    spacing="1",
                    align="center",
                ),
            ),
            spacing="2",
            width="100%",
            align="center",
        ),
        rx.cond(
            state.acct_picker_error != "",
            rx.callout(state.acct_picker_error, icon="triangle-alert", color_scheme="red", size="1"),
        ),
        rx.cond(
            state.acct_picker_is_loading,
            rx.center(rx.spinner(size="2"), padding="1rem"),
            rx.cond(
                state.acct_picker_accounts.length() > 0,
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(LanguageState.tr["col_account_name"]),
                                rx.table.column_header_cell(LanguageState.tr["field_account_type"]),
                                rx.table.column_header_cell(LanguageState.tr["field_city"]),
                            )
                        ),
                        rx.table.body(rx.foreach(state.acct_picker_accounts, _row)),
                        width="100%",
                        variant="surface",
                    ),
                    max_height="260px",
                    overflow_y="auto",
                    width="100%",
                ),
                rx.center(
                    rx.text(LanguageState.tr["no_accounts_found"], size="2", color="var(--gray-9)"),
                    padding="1rem",
                ),
            ),
        ),
        spacing="2",
        width="100%",
    )


def account_picker_button(state: type[AccountPickerState] = AccountPickerState) -> rx.Component:
    """A button that shows the selected account (or 'All Accounts') and opens the picker.

    Pass the consuming state class so the correct substate vars are used.
    When an account is selected, also renders an x button to clear it.
    """
    return rx.hstack(
        rx.button(
            rx.icon("building-2", size=14),
            rx.cond(
                state.acct_picker_selected_id != "",
                rx.text(state.acct_picker_selected_name, size="2"),
                rx.text(LanguageState.tr["all_accounts"], size="2"),
            ),
            on_click=state.open_account_picker,
            variant=rx.cond(state.acct_picker_selected_id != "", "soft", "outline"),
            color_scheme=rx.cond(state.acct_picker_selected_id != "", "accent", "gray"),
            size="2",
        ),
        rx.cond(
            state.acct_picker_selected_id != "",
            rx.icon_button(
                rx.icon("x", size=13),
                on_click=state.acct_picker_clear,
                variant="ghost",
                color_scheme="gray",
                size="2",
                title=LanguageState.tr["acct_picker_clear_tooltip"],
            ),
        ),
        spacing="1",
        align="center",
    )
