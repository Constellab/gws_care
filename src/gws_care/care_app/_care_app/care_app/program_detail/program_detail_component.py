"""MedicalProgram detail page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..common.patient_picker_component import patient_picker_widget
from .program_detail_state import (
    ExamTypeOptionDTO,
    ExamTypeRowDTO,
    PatientRowDTO,
    ProgramDetailState,
    VisitRowDTO,
)


def _exam_type_option_item(opt: ExamTypeOptionDTO) -> rx.Component:
    return rx.select.item(opt.label, value=opt.id)


def _prog_lifeline_step(step_idx: int, value: str, label: str, color: str) -> rx.Component:
    """Single step node for the program workflow lifeline."""
    idx_var = ProgramDetailState.program_status_index
    return rx.vstack(
        rx.cond(
            idx_var > step_idx,
            # completed — filled circle with checkmark
            rx.box(
                rx.icon("check", size=14, color="white"),
                width="30px",
                height="30px",
                border_radius="50%",
                background=f"var(--{color}-9)",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.cond(
                idx_var == step_idx,
                # current — outlined circle with inner dot
                rx.box(
                    rx.box(
                        width="10px",
                        height="10px",
                        border_radius="50%",
                        background=f"var(--{color}-9)",
                    ),
                    width="30px",
                    height="30px",
                    border_radius="50%",
                    border=f"2px solid var(--{color}-9)",
                    background=f"var(--{color}-3)",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                # future — gray empty circle
                rx.box(
                    width="30px",
                    height="30px",
                    border_radius="50%",
                    border="2px solid var(--gray-5)",
                    background="var(--gray-2)",
                ),
            ),
        ),
        rx.text(
            label,
            size="1",
            color=rx.cond(
                idx_var > step_idx,
                f"var(--{color}-9)",
                rx.cond(
                    idx_var == step_idx,
                    f"var(--{color}-11)",
                    "var(--gray-8)",
                ),
            ),
            weight=rx.cond(idx_var == step_idx, "bold", "regular"),
            text_align="center",
            max_width="80px",
        ),
        align="center",
        spacing="1",
        cursor="pointer",
        on_click=lambda: ProgramDetailState.set_workflow_status(value),
        flex_shrink="0",
    )


def _workflow_lifeline_program() -> rx.Component:
    """Horizontal workflow progress lifeline for the program detail page."""
    steps = [
        (0, "draft",                    "Draft",             "gray"),
        (1, "validated",               "Validated",          "blue"),
        (2, "in_progress",             "In Progress",        "amber"),
        (3, "lab_done",                "Lab Done",           "orange"),
        (4, "doctor_clinic_validated", "Clinic Validated",   "violet"),
        (5, "doctor_company_validated","Company Validated",  "green"),
    ]
    nodes = []
    for i, (idx, value, label, color) in enumerate(steps):
        nodes.append(_prog_lifeline_step(idx, value, label, color))
        if i < len(steps) - 1:
            nodes.append(
                rx.box(
                    flex="1",
                    height="2px",
                    background="var(--gray-4)",
                    align_self="flex-start",
                    margin_top="14px",
                    min_width="8px",
                )
            )
    return rx.card(
        rx.hstack(
            *nodes,
            align="start",
            width="100%",
            spacing="0",
        ),
        width="100%",
        padding="0.75rem 1rem",
    )


_STATUS_COLORS: dict[str, str] = {
    "draft": "gray",
    "validated": "blue",
    "in_progress": "amber",
    "lab_done": "orange",
    "doctor_clinic_validated": "violet",
    "doctor_company_validated": "green",
    "archived": "gray",
}

_VISIT_STATUS_COLORS: dict[str, str] = {
    "pending": "gray",
    "on-site_done": "amber",
    "results_entered": "orange",
    "lab_validated": "blue",
    "doctor_clinic_validated": "violet",
    "doctor_company_validated": "green",
}


def _visit_status_badge(v: VisitRowDTO) -> rx.Component:
    return rx.match(
        v.status,
        ("pending", rx.badge(v.status_label, color_scheme="gray", variant="soft", size="1")),
        ("on-site_done", rx.badge(v.status_label, color_scheme="amber", variant="soft", size="1")),
        ("results_entered", rx.badge(v.status_label, color_scheme="orange", variant="soft", size="1")),
        ("lab_validated", rx.badge(v.status_label, color_scheme="blue", variant="soft", size="1")),
        ("doctor_clinic_validated", rx.badge(v.status_label, color_scheme="violet", variant="soft", size="1")),
        ("doctor_company_validated", rx.badge(v.status_label, color_scheme="green", variant="soft", size="1")),
        rx.badge(v.status_label, color_scheme="gray", variant="soft", size="1"),
    )


def _workflow_buttons() -> rx.Component:
    """Show the correct workflow action button based on current program status."""
    return rx.hstack(
        rx.cond(
            (ProgramDetailState.program.status == "draft") & (ProgramDetailState.is_doctor | ProgramDetailState.is_admin),
            rx.button(
                rx.icon("circle_check", size=16),
                LanguageState.tr["btn_validate_program"],
                on_click=ProgramDetailState.validate_program,
                color_scheme="blue",
                size="2",
            ),
        ),
        rx.cond(
            (ProgramDetailState.program.status == "validated") & (ProgramDetailState.is_operator | ProgramDetailState.is_admin),
            rx.button(
                rx.icon("play", size=16),
                LanguageState.tr["btn_start_campaign"],
                on_click=ProgramDetailState.start_campaign,
                color_scheme="amber",
                size="2",
            ),
        ),
        rx.cond(
            (ProgramDetailState.program.status == "in_progress") & (ProgramDetailState.is_operator | ProgramDetailState.is_admin),
            rx.button(
                rx.icon("flask-conical", size=16),
                LanguageState.tr["btn_validate_lab"],
                on_click=ProgramDetailState.validate_lab,
                color_scheme="orange",
                size="2",
            ),
        ),
        rx.cond(
            (ProgramDetailState.program.status == "lab_done") & (ProgramDetailState.is_doctor | ProgramDetailState.is_admin),
            rx.button(
                rx.icon("stethoscope", size=16),
                LanguageState.tr["btn_validate_clinic"],
                on_click=ProgramDetailState.validate_clinic,
                color_scheme="violet",
                size="2",
            ),
        ),
        # Terrain page shortcut (for in_progress/lab_done)
        rx.cond(
            (ProgramDetailState.is_operator | ProgramDetailState.is_admin) &
            (
                (ProgramDetailState.program.status == "in_progress") |
                (ProgramDetailState.program.status == "lab_done")
            ),
            rx.link(
                rx.button(
                    rx.icon("map-pin", size=16),
                    "Terrain",
                    variant="soft",
                    color_scheme="green",
                    size="2",
                ),
                href="/on-site/" + ProgramDetailState.program.id,
            ),
        ),
        # PDF QR Grid download
        rx.cond(
            ProgramDetailState.is_operator | ProgramDetailState.is_admin,
            rx.button(
                rx.icon("qr-code", size=16),
                "PDF QR Codes",
                on_click=ProgramDetailState.download_tube_qr_pdf,
                variant="soft",
                size="2",
                loading=ProgramDetailState.is_downloading_pdf,
            ),
        ),
        # MedicalProgram report PDF
        rx.button(
            rx.icon("file-bar-chart", size=16),
            "Rapport PDF",
            on_click=ProgramDetailState.download_campaign_report_pdf,
            variant="soft",
            color_scheme="gray",
            size="2",
            loading=ProgramDetailState.is_downloading_pdf,
        ),
        spacing="2",
    )


def _patient_row(patient: PatientRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(patient.full_name, size="2", weight="medium")),
        rx.table.cell(rx.text(patient.patient_number, size="2", color="var(--gray-9)")),
        rx.table.cell(
            rx.cond(
                ProgramDetailState.program.is_individual
                | (ProgramDetailState.program.status == "draft")
                | (ProgramDetailState.program.status == "validated"),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("x", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="red",
                        on_click=lambda: ProgramDetailState.remove_patient(patient.id),
                    ),
                    content=LanguageState.tr["tooltip_remove_patient"],
                ),
            )
        ),
    )


def _exam_type_row(et: ExamTypeRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(et.name, size="2", weight="medium")),
        rx.table.cell(rx.text(et.code, size="2", color="var(--gray-9)")),
        rx.table.cell(rx.text(et.category, size="2", color="var(--gray-8)")),
        rx.table.cell(
            rx.cond(
                (ProgramDetailState.program.status == "draft") | (ProgramDetailState.program.status == "validated"),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("x", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="red",
                        on_click=lambda: ProgramDetailState.remove_exam_type(et.id),
                    ),
                    content=LanguageState.tr["tooltip_remove_exam_type"],
                ),
            )
        ),
    )


def _visit_row(visit: VisitRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(visit.patient_name, size="2", weight="medium"),
                rx.text(visit.patient_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(rx.text(visit.visit_number, size="2", color="var(--gray-9)")),
        rx.table.cell(_visit_status_badge(visit)),
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("chevron-right", size=14),
                    variant="ghost",
                    size="1",
                    on_click=lambda: ProgramDetailState.go_to_visit(visit.id),
                ),
                content=LanguageState.tr["tooltip_view_visit"],
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}, "cursor": "pointer"},
        on_click=lambda: ProgramDetailState.go_to_visit(visit.id),
    )


def _add_patient_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["add_patient_btn"]),
            rx.vstack(
                patient_picker_widget(ProgramDetailState),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            LanguageState.tr["cancel_btn"],
                            variant="soft",
                            color_scheme="gray",
                            on_click=ProgramDetailState.close_add_patient_dialog,
                        )
                    ),
                    rx.button(
                        LanguageState.tr["add"],
                        on_click=ProgramDetailState.confirm_add_patient,
                        loading=ProgramDetailState.is_adding_patient,
                        disabled=ProgramDetailState.picker_selected_id == "",
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            on_escape_key_down=ProgramDetailState.close_add_patient_dialog,
            on_interact_outside=ProgramDetailState.close_add_patient_dialog,
            max_width="700px",
        ),
        open=ProgramDetailState.add_patient_dialog_open,
    )


def _add_exam_type_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["add_exam_type_btn"]),
            rx.vstack(
                rx.select.root(
                    rx.select.trigger(
                        placeholder=LanguageState.tr["select_exam_type_to_add"],
                        width="100%",
                    ),
                    rx.select.content(
                        rx.foreach(
                            ProgramDetailState.exam_type_options,
                            _exam_type_option_item,
                        )
                    ),
                    value=ProgramDetailState.selected_exam_type_id,
                    on_change=ProgramDetailState.set_selected_exam_type,
                ),
                rx.cond(
                    ProgramDetailState.error_message != "",
                    rx.callout(
                        ProgramDetailState.error_message,
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
                            on_click=ProgramDetailState.close_add_exam_type_dialog,
                        )
                    ),
                    rx.button(
                        LanguageState.tr["add"],
                        on_click=ProgramDetailState.confirm_add_exam_type,
                        loading=ProgramDetailState.is_adding_exam_type,
                        disabled=ProgramDetailState.selected_exam_type_id == "",
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            on_escape_key_down=ProgramDetailState.close_add_exam_type_dialog,
            max_width="440px",
        ),
        open=ProgramDetailState.add_exam_type_dialog_open,
    )


def program_detail_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.cond(
                ProgramDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    ProgramDetailState.program == None,  # noqa: E711
                    rx.center(
                        rx.callout(
                            LanguageState.tr["campaign_not_found"],
                            color_scheme="red",
                            icon="triangle-alert",
                        ),
                        padding="4rem",
                    ),
                    rx.vstack(
                        # Header
                        rx.hstack(
                            rx.button(
                                rx.icon("arrow-left", size=14),
                                LanguageState.tr["back_to_campaigns"],
                                variant="ghost",
                                size="2",
                                on_click=ProgramDetailState.go_back,
                            ),
                            rx.spacer(),
                            _workflow_buttons(),
                            width="100%",
                            align="center",
                        ),
                        # MedicalProgram info card
                        rx.card(
                            rx.hstack(
                                rx.vstack(
                                    rx.hstack(
                                        rx.icon("clipboard-list", size=20, color="var(--accent-9)"),
                                        rx.heading(ProgramDetailState.program.name, size="5"),
                                        spacing="2",
                                        align="center",
                                    ),
                                    rx.hstack(
                                        rx.text(ProgramDetailState.program.program_number, size="2", color="var(--gray-9)"),
                                        rx.separator(orientation="vertical"),
                                        rx.text(ProgramDetailState.program.account_name, size="2"),
                                        spacing="2",
                                        align="center",
                                    ),
                                    rx.hstack(
                                        rx.icon("calendar", size=13, color="var(--gray-9)"),
                                        rx.text(
                                            ProgramDetailState.program.start_date + " → " + ProgramDetailState.program.end_date,
                                            size="2",
                                            color="var(--gray-9)",
                                        ),
                                        spacing="1",
                                        align="center",
                                    ),
                                    spacing="1",
                                    align_items="start",
                                ),
                                rx.spacer(),
                                rx.vstack(
                                    rx.cond(
                                        ProgramDetailState.program.is_individual,
                                        rx.badge(
                                            rx.icon("user", size=11),
                                            "Individual",
                                            color_scheme="purple",
                                            variant="soft",
                                            size="1",
                                        ),
                                    ),
                                    rx.match(
                                        ProgramDetailState.program.status,
                                        ("draft", rx.badge(ProgramDetailState.program.status_label, color_scheme="gray", size="2")),
                                        ("validated", rx.badge(ProgramDetailState.program.status_label, color_scheme="blue", size="2")),
                                        ("in_progress", rx.badge(ProgramDetailState.program.status_label, color_scheme="amber", size="2")),
                                        ("lab_done", rx.badge(ProgramDetailState.program.status_label, color_scheme="orange", size="2")),
                                        ("doctor_clinic_validated", rx.badge(ProgramDetailState.program.status_label, color_scheme="violet", size="2")),
                                        ("doctor_company_validated", rx.badge(ProgramDetailState.program.status_label, color_scheme="green", size="2")),
                                        rx.badge(ProgramDetailState.program.status_label, color_scheme="gray", size="2"),
                                    ),
                                    spacing="1",
                                    align="end",
                                ),
                                align="start",
                                width="100%",
                            ),
                            width="100%",
                        ),
                        # Workflow lifeline
                        _workflow_lifeline_program(),
                        # Alerts
                        rx.cond(
                            ProgramDetailState.error_message != "",
                            rx.callout(
                                ProgramDetailState.error_message,
                                color_scheme="red",
                                icon="triangle-alert",
                                size="2",
                            ),
                        ),
                        rx.cond(
                            ProgramDetailState.success_message != "",
                            rx.callout(
                                ProgramDetailState.success_message,
                                color_scheme="green",
                                icon="circle_check",
                                size="2",
                            ),
                        ),
                        # Two-column layout for patients + exam types
                        rx.grid(
                            # Patients section
                            rx.card(
                                rx.vstack(
                                    rx.hstack(
                                        rx.heading(LanguageState.tr["section_patients"], size="4"),
                                        rx.spacer(),
                                        rx.cond(
                                            ~ProgramDetailState.program.is_individual
                                            & (ProgramDetailState.is_operator | ProgramDetailState.is_admin)
                                            & (
                                                (ProgramDetailState.program.status == "draft")
                                                | (ProgramDetailState.program.status == "validated")
                                            ),
                                            rx.button(
                                                rx.icon("user-plus", size=14),
                                                LanguageState.tr["add_patient_btn"],
                                                variant="soft",
                                                size="1",
                                                on_click=ProgramDetailState.open_add_patient_dialog,
                                            ),
                                        ),
                                        width="100%",
                                        align="center",
                                    ),
                                    rx.cond(
                                        ProgramDetailState.patients.length() == 0,
                                        rx.text(LanguageState.tr["no_patients_in_campaign"], size="2", color="var(--gray-9)"),
                                        rx.table.root(
                                            rx.table.header(
                                                rx.table.row(
                                                    rx.table.column_header_cell(LanguageState.tr["col_name"]),
                                                    rx.table.column_header_cell(LanguageState.tr["col_patient_number"] if "col_patient_number" in ["col_patient_number"] else "N° Dossier"),
                                                    rx.table.column_header_cell(""),
                                                )
                                            ),
                                            rx.table.body(
                                                rx.foreach(ProgramDetailState.patients, _patient_row)
                                            ),
                                            width="100%",
                                            size="1",
                                        ),
                                    ),
                                    width="100%",
                                    spacing="3",
                                )
                            ),
                            # Exam types section
                            rx.card(
                                rx.vstack(
                                    rx.hstack(
                                        rx.heading(LanguageState.tr["section_exam_types"], size="4"),
                                        rx.spacer(),
                                        rx.cond(
                                            (ProgramDetailState.is_operator | ProgramDetailState.is_admin)
                                            & (
                                                (ProgramDetailState.program.status == "draft")
                                                | (ProgramDetailState.program.status == "validated")
                                            ),
                                            rx.button(
                                                rx.icon("plus", size=14),
                                                LanguageState.tr["add_exam_type_btn"],
                                                variant="soft",
                                                size="1",
                                                on_click=ProgramDetailState.open_add_exam_type_dialog,
                                            ),
                                        ),
                                        width="100%",
                                        align="center",
                                    ),
                                    rx.cond(
                                        ProgramDetailState.exam_types.length() == 0,
                                        rx.text(LanguageState.tr["no_exam_types_in_campaign"], size="2", color="var(--gray-9)"),
                                        rx.table.root(
                                            rx.table.header(
                                                rx.table.row(
                                                    rx.table.column_header_cell(LanguageState.tr["col_name"]),
                                                    rx.table.column_header_cell("Code"),
                                                    rx.table.column_header_cell(LanguageState.tr["col_type"]),
                                                    rx.table.column_header_cell(""),
                                                )
                                            ),
                                            rx.table.body(
                                                rx.foreach(ProgramDetailState.exam_types, _exam_type_row)
                                            ),
                                            width="100%",
                                            size="1",
                                        ),
                                    ),
                                    width="100%",
                                    spacing="3",
                                )
                            ),
                            columns="2",
                            spacing="4",
                            width="100%",
                        ),
                        # Visits progress section
                        rx.card(
                            rx.vstack(
                                rx.heading(LanguageState.tr["section_visits"], size="4"),
                                rx.cond(
                                    ProgramDetailState.visits.length() == 0,
                                    rx.text(LanguageState.tr["no_visits_in_campaign"], size="2", color="var(--gray-9)"),
                                    rx.table.root(
                                        rx.table.header(
                                            rx.table.row(
                                                rx.table.column_header_cell(LanguageState.tr["col_patient"]),
                                                rx.table.column_header_cell(LanguageState.tr["col_visit_number"]),
                                                rx.table.column_header_cell(LanguageState.tr["col_visit_status"]),
                                                rx.table.column_header_cell(LanguageState.tr["col_actions"]),
                                            )
                                        ),
                                        rx.table.body(
                                            rx.foreach(ProgramDetailState.visits, _visit_row)
                                        ),
                                        width="100%",
                                    ),
                                ),
                                width="100%",
                                spacing="3",
                            )
                        ),
                        width="100%",
                        spacing="4",
                    ),
                ),
            ),
            _add_patient_dialog(),
            _add_exam_type_dialog(),
        )
    )
