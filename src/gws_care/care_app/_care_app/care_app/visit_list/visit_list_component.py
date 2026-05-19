"""Visit list / calendar page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.account_picker_component import account_picker_button, account_picker_dialog
from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..common.patient_picker_component import patient_picker_widget
from .visit_list_state import (
    AccountOptionDTO,
    CalendarDayDTO,
    CampaignVisitListState,
    PatientAccountOption,
    VisitRowDTO,
)


def _status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("pending", rx.badge(LanguageState.tr["status_pending"], color_scheme="gray", variant="soft", size="1")),
        ("visit_done", rx.badge(LanguageState.tr["status_visit_done"], color_scheme="amber", variant="soft", size="1")),
        ("lab_done", rx.badge(LanguageState.tr["status_lab_done"], color_scheme="blue", variant="soft", size="1")),
        ("doctor_clinic_validated", rx.badge(LanguageState.tr["status_doctor_clinic_validated"], color_scheme="purple", variant="soft", size="1")),
        ("doctor_company_validated", rx.badge(LanguageState.tr["status_doctor_company_validated"], color_scheme="green", variant="soft", size="1")),
        ("cancelled", rx.badge(LanguageState.tr["status_cancelled"], color_scheme="red", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _visit_row(visit: VisitRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.cond(
                visit.visit_number,
                rx.text(visit.visit_number, size="2", weight="medium"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.link(
                visit.patient_name,
                on_click=lambda: CampaignVisitListState.go_to_patient(visit.patient_id),
                cursor="pointer",
                size="2",
            )
        ),
        rx.table.cell(
            rx.cond(
                visit.campaign_name,
                rx.text(visit.campaign_name, size="2"),
                rx.cond(
                    visit.account_name,
                    rx.text(visit.account_name, size="2"),
                    rx.text("—", size="2", color="var(--gray-7)"),
                ),
            )
        ),
        rx.table.cell(
            rx.cond(
                visit.scheduled_at,
                rx.text(visit.scheduled_at[:16].replace("T", " "), size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(_status_badge(visit.status)),
        style={":hover": {"background_color": "var(--gray-2)", "cursor": "pointer"}},
        on_click=lambda: CampaignVisitListState.go_to_visit(visit.id),
    )


def _account_filter_option(account: AccountOptionDTO) -> rx.Component:
    return rx.select.item(account.name, value=account.id)


def _sortable_header(label: str, column: str) -> rx.Component:
    """Column header cell with a sort-direction arrow."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                CampaignVisitListState.sort_column == column,
                rx.cond(
                    CampaignVisitListState.sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: CampaignVisitListState.set_sort(column),
        style={"cursor": "pointer"},
    )


# ── Calendar view ─────────────────────────────────────────────────────────────

def _cal_visit_pill(visit: VisitRowDTO) -> rx.Component:
    """Compact visit chip for a calendar day cell."""
    bg = rx.match(
        visit.status,
        ("pending", "var(--gray-3)"),
        ("visit_done", "var(--amber-3)"),
        ("lab_done", "var(--blue-3)"),
        ("doctor_clinic_validated", "var(--purple-3)"),
        ("doctor_company_validated", "var(--green-3)"),
        ("cancelled", "var(--red-3)"),
        "var(--gray-3)",
    )
    color = rx.match(
        visit.status,
        ("pending", "var(--gray-11)"),
        ("visit_done", "var(--amber-11)"),
        ("lab_done", "var(--blue-11)"),
        ("doctor_clinic_validated", "var(--purple-11)"),
        ("doctor_company_validated", "var(--green-11)"),
        ("cancelled", "var(--red-11)"),
        "var(--gray-11)",
    )
    return rx.box(
        rx.text(
            visit.scheduled_at[11:16] + " " + visit.patient_name,
            size="1",
            color=color,
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        background=bg,
        border_radius="3px",
        padding="1px 4px",
        width="100%",
        overflow="hidden",
        cursor="pointer",
        on_click=lambda: CampaignVisitListState.go_to_visit(visit.id),
    )


def _cal_day_cell(day: CalendarDayDTO) -> rx.Component:
    """One cell in the monthly calendar grid."""
    return rx.box(
        rx.cond(
            day.day_num > 0,
            rx.vstack(
                rx.box(
                    rx.text(
                        day.day_num,
                        size="1",
                        weight=rx.cond(day.is_today, "bold", "regular"),
                        color=rx.cond(day.is_today, "white", "var(--gray-11)"),
                        text_align="center",
                        line_height="1.4rem",
                        width="1.4rem",
                    ),
                    border_radius="50%",
                    background=rx.cond(day.is_today, "var(--accent-9)", "transparent"),
                    width="fit-content",
                ),
                rx.vstack(
                    rx.foreach(day.visits, _cal_visit_pill),
                    spacing="1",
                    width="100%",
                    overflow="hidden",
                ),
                spacing="1",
                width="100%",
                align="start",
            ),
            rx.fragment(),
        ),
        min_height="90px",
        border="1px solid var(--gray-4)",
        padding="4px",
        background=rx.cond(day.is_current_month, "var(--gray-1)", "var(--gray-2)"),
        overflow="hidden",
    )


def _calendar_view() -> rx.Component:
    """Monthly calendar grid of scheduled visits."""
    return rx.vstack(
        # Month navigation
        rx.hstack(
            rx.icon_button(
                rx.icon("chevron-left", size=16),
                variant="ghost",
                size="2",
                on_click=CampaignVisitListState.calendar_prev_month,
            ),
            rx.text(
                CampaignVisitListState.calendar_month_label,
                size="4",
                weight="medium",
                min_width="180px",
                text_align="center",
            ),
            rx.icon_button(
                rx.icon("chevron-right", size=16),
                variant="ghost",
                size="2",
                on_click=CampaignVisitListState.calendar_next_month,
            ),
            spacing="2",
            align="center",
            justify="center",
            width="100%",
        ),
        # Weekday header row
        rx.grid(
            rx.text(LanguageState.tr["cal_mon"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_tue"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_wed"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_thu"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_fri"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_sat"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            rx.text(LanguageState.tr["cal_sun"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
            columns="7",
            width="100%",
        ),
        # Day cells
        rx.grid(
            rx.foreach(CampaignVisitListState.calendar_days, _cal_day_cell),
            columns="7",
            width="100%",
        ),
        width="100%",
        spacing="2",
    )


def _patient_account_option(option: PatientAccountOption) -> rx.Component:
    return rx.select.item(option.name, value=option.id)


def _new_visit_dialog() -> rx.Component:
    """Dialog for creating a new visit (auto-creates a Medical Program)."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["new_visit_form_title"]),
            rx.dialog.description(LanguageState.tr["new_visit_desc"]),
            rx.vstack(
                # Patient picker table
                rx.vstack(
                    rx.text(LanguageState.tr["field_patient_required"], size="2", weight="medium"),
                    patient_picker_widget(CampaignVisitListState),
                    spacing="1",
                    width="100%",
                ),
                # Date and time picker
                rx.vstack(
                    rx.text(LanguageState.tr["field_scheduled_datetime"], size="2", weight="medium"),
                    rx.input(
                        type="datetime-local",
                        value=CampaignVisitListState.new_visit_scheduled_at,
                        on_change=CampaignVisitListState.set_new_visit_scheduled_at,
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Account selector — only shown once a patient with accounts is selected
                rx.cond(
                    CampaignVisitListState.picker_selected_id != "",
                    rx.vstack(
                        rx.text(LanguageState.tr["col_account_name"], size="2", weight="medium"),
                        rx.cond(
                            CampaignVisitListState.new_visit_patient_accounts.length() > 0,
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder=LanguageState.tr["select_account_placeholder"]
                                ),
                                rx.select.content(
                                    rx.foreach(
                                        CampaignVisitListState.new_visit_patient_accounts,
                                        _patient_account_option,
                                    )
                                ),
                                value=CampaignVisitListState.new_visit_account_id,
                                on_change=CampaignVisitListState.set_new_visit_account_id,
                                size="2",
                                width="100%",
                            ),
                            # Patient has no accounts
                            rx.callout(
                                LanguageState.tr["no_account_alert_desc"],
                                icon="triangle-alert",
                                color_scheme="orange",
                                size="1",
                            ),
                        ),
                        spacing="1",
                        width="100%",
                    ),
                ),
                # Error
                rx.cond(
                    CampaignVisitListState.new_visit_error != "",
                    rx.callout(
                        CampaignVisitListState.new_visit_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                # Buttons
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="outline",
                        on_click=CampaignVisitListState.close_new_visit_dialog,
                    ),
                    rx.button(
                        LanguageState.tr["create_visit_btn"],
                        on_click=CampaignVisitListState.save_new_visit,
                        loading=CampaignVisitListState.new_visit_is_saving,
                        disabled=(
                            (CampaignVisitListState.picker_selected_id == "")
                            | (CampaignVisitListState.new_visit_account_id == "")
                        ),
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                padding_top="1rem",
            ),
            on_interact_outside=CampaignVisitListState.close_new_visit_dialog,
            on_escape_key_down=CampaignVisitListState.close_new_visit_dialog,
            max_width="700px",
        ),
        open=CampaignVisitListState.show_new_visit_dialog,
    )


def _no_account_alert() -> rx.Component:
    """Alert dialog shown when the selected patient has no linked account."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["no_account_alert_title"]),
            rx.dialog.description(
                LanguageState.tr["no_account_alert_desc"],
                size="2",
            ),
            rx.hstack(
                rx.spacer(),
                rx.button(
                    LanguageState.tr["cancel_btn"],
                    variant="outline",
                    color_scheme="gray",
                    on_click=CampaignVisitListState.close_no_account_alert,
                ),
                rx.button(
                    LanguageState.tr["go_to_patient_btn"],
                    on_click=lambda: CampaignVisitListState.go_to_patient(CampaignVisitListState.no_account_patient_id),
                ),
                spacing="2",
                width="100%",
                padding_top="1rem",
            ),
            on_interact_outside=CampaignVisitListState.close_no_account_alert,
            on_escape_key_down=CampaignVisitListState.close_no_account_alert,
            max_width="480px",
        ),
        open=CampaignVisitListState.show_no_account_alert,
    )


def visit_list_page() -> rx.Component:
    """Visit list page with filters, list and calendar views."""
    return main_component(
        page_layout(
            account_picker_dialog(CampaignVisitListState),
            rx.hstack(
                rx.heading(LanguageState.tr["visits_page_title"], size="6"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    LanguageState.tr["new_visit_btn"],
                    on_click=CampaignVisitListState.open_new_visit_dialog,
                    size="2",
                ),
                rx.segmented_control.root(
                    rx.segmented_control.item(rx.icon("list", size=15), value="list"),
                    rx.segmented_control.item(rx.icon("calendar-days", size=15), value="calendar"),
                    value=CampaignVisitListState.view_mode,
                    on_change=CampaignVisitListState.set_view_mode,
                    size="1",
                ),
                width="100%",
                align="center",
                spacing="3",
            ),
            _new_visit_dialog(),
            _no_account_alert(),
            # Filters
            rx.vstack(
                rx.hstack(
                    rx.input(
                        placeholder=LanguageState.tr["search_patient_placeholder"],
                        value=CampaignVisitListState.search,
                        on_change=CampaignVisitListState.set_search,
                        size="2",
                        max_width="260px",
                    ),
                    rx.select.root(
                        rx.select.trigger(placeholder=LanguageState.tr["all_statuses"]),
                        rx.select.content(
                            rx.select.item(LanguageState.tr["all_statuses"], value="ALL"),
                            rx.select.item(LanguageState.tr["status_pending"], value="pending"),
                            rx.select.item(LanguageState.tr["status_visit_done"], value="visit_done"),
                            rx.select.item(LanguageState.tr["status_lab_done"], value="lab_done"),
                            rx.select.item(LanguageState.tr["status_doctor_clinic_validated"], value="doctor_clinic_validated"),
                            rx.select.item(LanguageState.tr["status_doctor_company_validated"], value="doctor_company_validated"),
                            rx.select.item(LanguageState.tr["status_cancelled"], value="cancelled"),
                        ),
                        value=CampaignVisitListState.filter_status,
                        on_change=CampaignVisitListState.set_filter_status,
                        size="2",
                    ),
                    account_picker_button(CampaignVisitListState),
                    spacing="3",
                    wrap="wrap",
                    width="100%",
                ),
                # Date range — only relevant in list mode
                rx.cond(
                    CampaignVisitListState.view_mode == "list",
                    rx.hstack(
                        rx.text(LanguageState.tr["date_filter_label"], size="2", color="var(--gray-9)", white_space="nowrap"),
                        rx.input(
                            type="date",
                            value=CampaignVisitListState.filter_date_from,
                            on_change=CampaignVisitListState.set_filter_date_from,
                            size="2",
                        ),
                        rx.text(LanguageState.tr["date_range_arrow"], size="2", color="var(--gray-9)"),
                        rx.input(
                            type="date",
                            value=CampaignVisitListState.filter_date_to,
                            on_change=CampaignVisitListState.set_filter_date_to,
                            size="2",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=14),
                            LanguageState.tr["clear_btn"],
                            on_click=CampaignVisitListState.clear_filters,
                            variant="outline",
                            size="2",
                        ),
                        spacing="2",
                        align="center",
                        wrap="wrap",
                        width="100%",
                    ),
                    # Calendar mode: show clear button without date pickers
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=14),
                            LanguageState.tr["clear_btn"],
                            on_click=CampaignVisitListState.clear_filters,
                            variant="outline",
                            size="2",
                        ),
                        width="100%",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            # Error
            rx.cond(
                CampaignVisitListState.error_message != "",
                rx.callout(
                    CampaignVisitListState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            # List or Calendar
            rx.cond(
                CampaignVisitListState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    CampaignVisitListState.view_mode == "list",
                    # ── List view ──
                    rx.cond(
                        CampaignVisitListState.visits,
                        rx.vstack(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        _sortable_header(LanguageState.tr["col_visit_number"], "visit_number"),
                                        _sortable_header(LanguageState.tr["col_patient"], "patient_name"),
                                        _sortable_header(LanguageState.tr["col_campaign_account"], "campaign_name"),
                                        _sortable_header(LanguageState.tr["col_scheduled"], "scheduled_at"),
                                        _sortable_header(LanguageState.tr["col_status"], "status"),
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(CampaignVisitListState.visits, _visit_row),
                                ),
                                width="100%",
                                variant="surface",
                            ),
                            rx.cond(
                                CampaignVisitListState.has_more,
                                rx.center(
                                    rx.button(
                                        rx.cond(
                                            CampaignVisitListState.is_loading_more,
                                            rx.hstack(rx.spinner(size="2"), rx.text("Loading..."), spacing="2"),
                                            rx.hstack(rx.icon("chevron-down", size=16), rx.text("Load more"), spacing="2"),
                                        ),
                                        variant="soft",
                                        size="2",
                                        on_click=CampaignVisitListState.load_more_visits,
                                        disabled=CampaignVisitListState.is_loading_more,
                                    ),
                                    width="100%",
                                    padding="1rem",
                                ),
                            ),
                            width="100%",
                            spacing="0",
                        ),
                        rx.center(
                            rx.text(LanguageState.tr["no_visits_found"], size="2", color="var(--gray-8)"),
                            padding="3rem",
                        ),
                    ),
                    # ── Calendar view ──
                    _calendar_view(),
                ),
            ),
        )
    )
