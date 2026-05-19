"""MedicalProgram list page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.account_picker_component import (
    account_picker_button,
    account_picker_dialog,
    account_picker_widget,
)
from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .program_list_state import CampaignFormPickerState, CampaignListState, ProgramRowDTO

# ── Status color helper ────────────────────────────────────────────────────────

_STATUS_COLORS: dict[str, str] = {
    "draft": "gray",
    "validated": "blue",
    "in_progress": "amber",
    "lab_done": "orange",
    "doctor_clinic_validated": "violet",
    "doctor_company_validated": "green",
    "closed": "green",
    "archived": "gray",
}


def _status_badge(status: str, label: str) -> rx.Component:
    color = _STATUS_COLORS.get(status, "gray")
    return rx.badge(label, color_scheme=color, variant="soft", size="1")


def _campaign_row(program: ProgramRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(program.name, size="2", weight="medium"),
                rx.text(program.program_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(
            rx.cond(
                program.account_name != "",
                rx.text(program.account_name, size="2"),
                rx.text("—", size="2", color="var(--gray-8)"),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.text(program.start_date, size="2"),
                rx.text("→", size="2", color="var(--gray-8)"),
                rx.text(program.end_date, size="2"),
                spacing="1",
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.icon("users", size=13, color="var(--gray-9)"),
                rx.text(program.patient_count, size="2"),
                rx.text("|", size="2", color="var(--gray-6)"),
                rx.icon("test-tube", size=13, color="var(--gray-9)"),
                rx.text(program.exam_type_count, size="2"),
                spacing="1",
                align="center",
            )
        ),
        rx.table.cell(
            _status_badge(program.status, program.status_label)
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("chevron-right", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: CampaignListState.go_to_program(program.id),
                    ),
                    content=LanguageState.tr["tooltip_view_campaign"],
                ),
                rx.cond(
                    program.status != "archived",
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("archive", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="gray",
                            on_click=lambda: CampaignListState.archive_program(program.id),
                        ),
                        content=LanguageState.tr["tooltip_archive_program"],
                    ),
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}, "cursor": "pointer"},
        on_click=lambda: CampaignListState.go_to_program(program.id),
    )


def _sortable_header(label: str, column: str) -> rx.Component:
    """Column header cell with a sort-direction arrow."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                CampaignListState.sort_column == column,
                rx.cond(
                    CampaignListState.sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: CampaignListState.set_sort(column),
        style={"cursor": "pointer"},
    )


def _create_program_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["new_campaign_form_title"]),
            rx.form.root(
                rx.form.field(
                    rx.form.label(LanguageState.tr["field_campaign_name"]),
                    rx.input(
                        placeholder=LanguageState.tr["campaign_name_placeholder"],
                        value=CampaignListState.form_name,
                        on_change=CampaignListState.set_form_name,
                        size="2",
                    ),
                ),
                rx.form.field(
                    rx.form.label(LanguageState.tr["col_account"]),
                    account_picker_widget(CampaignFormPickerState),
                    width="100%",
                ),
                rx.grid(
                    rx.form.field(
                        rx.form.label(LanguageState.tr["field_start_date"]),
                        rx.input(
                            type="date",
                            value=CampaignListState.form_start_date,
                            on_change=CampaignListState.set_form_start_date,
                            size="2",
                        ),
                    ),
                    rx.form.field(
                        rx.form.label(LanguageState.tr["field_end_date"]),
                        rx.input(
                            type="date",
                            value=CampaignListState.form_end_date,
                            on_change=CampaignListState.set_form_end_date,
                            size="2",
                        ),
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),
                rx.cond(
                    CampaignListState.form_error != "",
                    rx.callout(
                        CampaignListState.form_error,
                        color_scheme="red",
                        size="1",
                        icon="triangle-alert",
                    ),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            LanguageState.tr["cancel_btn"],
                            variant="soft",
                            color_scheme="gray",
                            on_click=CampaignListState.close_create_dialog,
                        )
                    ),
                    rx.button(
                        LanguageState.tr["create_program_btn"],
                        on_click=CampaignListState.save_program,
                        loading=CampaignListState.is_saving,
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
                display="flex",
                flex_direction="column",
                gap="1rem",
                width="100%",
            ),
            on_interact_outside=CampaignListState.close_create_dialog,
            on_escape_key_down=CampaignListState.close_create_dialog,
            max_width="600px",
        ),
        open=CampaignListState.create_dialog_open,
    )


def program_list_page() -> rx.Component:
    return main_component(
        page_layout(
            account_picker_dialog(CampaignListState),
            rx.hstack(
                rx.heading(LanguageState.tr["campaigns_page_title"], size="6"),
                rx.spacer(),
                rx.cond(
                    CampaignListState.is_operator | CampaignListState.is_admin,
                    rx.button(
                        rx.icon("plus", size=16),
                        LanguageState.tr["new_campaign_btn"],
                        on_click=CampaignListState.open_create_dialog,
                        size="2",
                    ),
                ),
                width="100%",
                align="center",
            ),
            # Filters
            rx.hstack(
                rx.input(
                    rx.input.slot(rx.icon("search", size=14)),
                    placeholder=LanguageState.tr["search_by_name"],
                    value=CampaignListState.search_name,
                    on_change=CampaignListState.set_search_name,
                    size="2",
                    width="220px",
                ),
                rx.select.root(
                    rx.select.trigger(
                        placeholder=LanguageState.tr["all_program_statuses"],
                        width="180px",
                    ),
                    rx.select.content(
                        rx.select.item(LanguageState.tr["all_program_statuses"], value="ALL"),
                        rx.select.item(LanguageState.tr["status_draft"], value="draft"),
                        rx.select.item(LanguageState.tr["status_validated"], value="validated"),
                        rx.select.item(LanguageState.tr["status_in_progress"], value="in_progress"),
                        rx.select.item(LanguageState.tr["status_lab_done"], value="lab_done"),
                        rx.select.item(LanguageState.tr["status_doctor_clinic_validated"], value="doctor_clinic_validated"),
                        rx.select.item(LanguageState.tr["status_doctor_company_validated"], value="doctor_company_validated"),
                        rx.select.item(LanguageState.tr["status_closed"], value="closed"),
                        rx.select.item(LanguageState.tr["status_archived"], value="archived"),
                    ),
                    value=CampaignListState.filter_status,
                    on_change=CampaignListState.set_filter_status,
                ),
                account_picker_button(CampaignListState),
                spacing="2",
                wrap="wrap",
                width="100%",
            ),
            rx.cond(
                CampaignListState.error_message != "",
                rx.callout(
                    CampaignListState.error_message,
                    color_scheme="red",
                    size="2",
                    icon="triangle-alert",
                ),
            ),
            rx.cond(
                CampaignListState.is_loading,
                rx.center(rx.spinner(size="3"), padding="2rem"),
                rx.vstack(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                _sortable_header(LanguageState.tr["col_name"], "name"),
                                _sortable_header(LanguageState.tr["col_account"], "account_name"),
                                _sortable_header(LanguageState.tr["col_dates"], "start_date"),
                                rx.table.column_header_cell(LanguageState.tr["col_patients"] + " / " + LanguageState.tr["col_exam_types"]),
                                _sortable_header(LanguageState.tr["col_status"], "status_label"),
                                rx.table.column_header_cell(LanguageState.tr["col_actions"]),
                            )
                        ),
                        rx.table.body(
                            rx.cond(
                                CampaignListState.programs.length() == 0,
                                rx.table.row(
                                    rx.table.cell(
                                        rx.center(
                                            rx.text(LanguageState.tr["no_campaigns_found"], color="var(--gray-9)", size="2"),
                                            padding="1.5rem",
                                        ),
                                        col_span=6,
                                    )
                                ),
                                rx.foreach(CampaignListState.programs, _campaign_row),
                            )
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    rx.cond(
                        CampaignListState.has_more,
                        rx.center(
                            rx.button(
                                rx.cond(
                                    CampaignListState.is_loading_more,
                                    rx.hstack(rx.spinner(size="2"), rx.text("Loading..."), spacing="2"),
                                    rx.hstack(rx.icon("chevron-down", size=16), rx.text("Load more"), spacing="2"),
                                ),
                                variant="soft",
                                size="2",
                                on_click=CampaignListState.load_more_programs,
                                disabled=CampaignListState.is_loading_more,
                            ),
                            width="100%",
                            padding="1rem",
                        ),
                    ),
                    width="100%",
                    spacing="0",
                ),
            ),
            _create_program_dialog(),
        )
    )
