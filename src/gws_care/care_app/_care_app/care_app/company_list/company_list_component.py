"""Company list page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .company_form_component import company_form_dialog
from .company_form_state import CompanyFormState
from .company_list_state import CompanyListState, CompanyRowDTO


def _company_row(company: CompanyRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(company.name, size="2", weight="medium")),
        rx.table.cell(
            rx.cond(company.city, rx.text(company.city, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(company.contact_name, rx.text(company.contact_name, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(company.phone, rx.text(company.phone, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(company.email, rx.text(company.email, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(
                company.is_active,
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
                        on_click=lambda: CompanyListState.go_to_company(company.id),
                    ),
                    content=LanguageState.tr["tooltip_view_account"],
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pencil", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: CompanyFormState.open_edit_dialog(company.id),
                    ),
                    content=LanguageState.tr["tooltip_edit_account"],
                ),
                rx.cond(
                    company.is_active,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("ban", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="red",
                            on_click=lambda: CompanyListState.deactivate_company(company.id),
                        ),
                        content=LanguageState.tr["tooltip_deactivate_account"],
                    ),
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}, "cursor": "pointer"},
        on_click=lambda: CompanyListState.go_to_company(company.id),
    )


def company_list_page() -> rx.Component:
    """Company list page."""
    return main_component(
        page_layout(
            rx.hstack(
                rx.heading(LanguageState.tr["accounts_page_title"], size="6"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    LanguageState.tr["new_account_page_btn"],
                    on_click=CompanyFormState.open_create_dialog,
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            company_form_dialog(),
            rx.hstack(
                rx.input(
                    placeholder=LanguageState.tr["search_by_name"],
                    value=CompanyListState.search_name,
                    on_change=CompanyListState.handle_name_change,
                    min_width="260px",
                    size="2",
                ),
                rx.button(
                    rx.icon("x", size=14),
                    LanguageState.tr["clear_btn"],
                    on_click=CompanyListState.clear_filters,
                    variant="outline",
                    size="2",
                ),
                spacing="3",
                width="100%",
            ),
            rx.cond(
                CompanyListState.error_message != "",
                rx.callout(
                    CompanyListState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                CompanyListState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    CompanyListState.companies.length() > 0,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(LanguageState.tr["col_company_name"]),
                                rx.table.column_header_cell(LanguageState.tr["col_city"]),
                                rx.table.column_header_cell(LanguageState.tr["col_contact"]),
                                rx.table.column_header_cell(LanguageState.tr["col_phone"]),
                                rx.table.column_header_cell(LanguageState.tr["col_email"]),
                                rx.table.column_header_cell(LanguageState.tr["col_status"]),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(CompanyListState.companies, _company_row)
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("building-2", size=40, color="var(--gray-7)"),
                            rx.text(LanguageState.tr["no_companies_found"], color="var(--gray-9)"),
                            align="center",
                            spacing="2",
                        ),
                        padding="3rem",
                    ),
                ),
            ),
        )
    )
