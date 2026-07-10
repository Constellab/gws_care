"""Exam detail page — three-tab layout: Details | Results | Interpretation."""

import reflex as rx
from gws_reflex_main import main_component, plotly_fullscreen_dialog, plotly_with_fullscreen

_TABLE_PREVIEW_MAX_ROWS = 50

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .exam_detail_state import (
    ExamDetailDTO,
    ExamDetailState,
    ExamFileRowDTO,
    LabResultRowDTO,
    SiblingExamDTO,
)

_DOC_TYPE_OPTIONS = [
    ("medical_certificate", "Medical Certificate"),
    ("medical_report", "Medical Report"),
    ("letter", "Letter"),
    ("medical_analysis", "Medical Analysis"),
    ("prescription", "Prescription"),
    ("mri", "MRI"),
    ("ct_scan", "CT Scan"),
    ("xray", "X-Ray"),
    ("ultrasound", "Ultrasound"),
    ("other", "Other"),
]

_LAB_STATUS_OPTIONS = [
    ("normal", "Normal"),
    ("high", "High"),
    ("low", "Low"),
    ("critical", "Critical"),
]


# ── Sibling exam navigation ───────────────────────────────────────────────────

def _sibling_exam_pill(sibling: SiblingExamDTO) -> rx.Component:
    is_current = sibling.id == ExamDetailState.exam.id
    return rx.button(
        sibling.exam_type_label,
        variant=rx.cond(is_current, "solid", "outline"),
        color_scheme=rx.cond(is_current, "accent", "gray"),
        size="1",
        on_click=lambda: ExamDetailState.navigate_to_sibling(sibling.id),
        cursor="pointer",
    )


def _sibling_exams_nav() -> rx.Component:
    return rx.cond(
        ExamDetailState.sibling_exams.length() > 1,
        rx.card(
            rx.hstack(
                rx.icon("stethoscope", size=13, color="var(--gray-9)"),
                rx.text(
                    LanguageState.tr["visit_exams_nav"],
                    size="2", color="var(--gray-9)", weight="medium",
                ),
                rx.foreach(ExamDetailState.sibling_exams, _sibling_exam_pill),
                spacing="2", align="center", flex_wrap="wrap",
            ),
            padding="0.5rem 1rem", width="100%",
        ),
    )


# ── Exam workflow lifeline ────────────────────────────────────────────────────

def _exam_step(step_idx: int, label: rx.Component, color: str) -> rx.Component:
    idx = ExamDetailState.exam_status_index
    return rx.vstack(
        rx.cond(
            idx > step_idx,
            rx.box(
                rx.icon("check", size=14, color="white"),
                width="28px", height="28px", border_radius="50%",
                background=f"var(--{color}-9)",
                display="flex", align_items="center", justify_content="center",
            ),
            rx.cond(
                idx == step_idx,
                rx.box(
                    rx.box(width="10px", height="10px", border_radius="50%",
                           background=f"var(--{color}-9)"),
                    width="28px", height="28px", border_radius="50%",
                    border=f"2px solid var(--{color}-9)",
                    background=f"var(--{color}-3)",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.box(
                    width="28px", height="28px", border_radius="50%",
                    border="2px solid var(--gray-5)", background="var(--gray-2)",
                ),
            ),
        ),
        rx.text(
            label, size="1",
            color=rx.cond(
                idx > step_idx, f"var(--{color}-9)",
                rx.cond(idx == step_idx, f"var(--{color}-11)", "var(--gray-8)"),
            ),
            weight=rx.cond(idx == step_idx, "bold", "regular"),
            text_align="center", max_width="80px",
        ),
        align="center", spacing="1", flex_shrink="0",
    )


def _exam_workflow_lifeline() -> rx.Component:
    connector = rx.box(
        flex="1", height="2px", background="var(--gray-4)",
        align_self="flex-start", margin_top="13px", min_width="10px",
    )
    return rx.card(
        rx.hstack(
            _exam_step(0, LanguageState.tr["tab_details"], "blue"),
            connector,
            _exam_step(1, LanguageState.tr["tab_results"], "orange"),
            connector,
            _exam_step(2, LanguageState.tr["tab_interpretation"], "green"),
            connector,
            _exam_step(3, LanguageState.tr["exam_step_done"], "teal"),
            align="start", width="100%", spacing="0",
        ),
        width="100%", padding="0.75rem 1.5rem",
    )


def _exam_help_banner() -> rx.Component:
    return rx.match(
        ExamDetailState.exam.status,
        ("todo", rx.callout(
            LanguageState.tr["hint_exam_draft"],
            icon="info", color_scheme="blue", size="1",
        )),
        ("in_progress_results", rx.callout(
            LanguageState.tr["hint_exam_in_progress_results"],
            icon="flask-conical", color_scheme="orange", size="1",
        )),
        ("in_progress_interpretation", rx.callout(
            LanguageState.tr["hint_exam_pending"],
            icon="clock", color_scheme="orange", size="1",
        )),
        ("done", rx.callout(
            LanguageState.tr["hint_exam_interpreted"],
            icon="circle-check", color_scheme="green", size="1",
        )),
        rx.fragment(),
    )


# ── Status badge ──────────────────────────────────────────────────────────────

def _status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("todo", rx.badge(LanguageState.tr["exam_status_todo"], color_scheme="gray", variant="soft", size="2")),
        ("in_progress_results", rx.badge(LanguageState.tr["exam_status_in_progress_results"], color_scheme="orange", variant="soft", size="2")),
        ("in_progress_interpretation", rx.badge(LanguageState.tr["exam_status_in_progress_interpretation"], color_scheme="blue", variant="soft", size="2")),
        ("done", rx.badge(LanguageState.tr["exam_status_done"], color_scheme="green", variant="soft", size="2")),
        rx.badge(status, color_scheme="gray", variant="soft", size="2"),
    )


# ── Header ────────────────────────────────────────────────────────────────────

def _exam_info_card() -> rx.Component:
    exam = ExamDetailState.exam
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("stethoscope", size=20, color="var(--accent-9)"),
                    rx.heading(exam.exam_type_label, size="5"),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.icon("calendar", size=13, color="var(--gray-9)"),
                    rx.text(exam.exam_date, size="2", color="var(--gray-9)"),
                    rx.separator(orientation="vertical"),
                    rx.icon("user", size=13, color="var(--gray-9)"),
                    rx.text(exam.patient_name, size="2", color="var(--gray-9)"),
                    spacing="1", align="center",
                ),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            _status_badge(exam.status),
            rx.icon_button(
                rx.icon("trash-2", size=14),
                variant="soft", color_scheme="red", size="2",
                on_click=ExamDetailState.open_delete_exam_dialog,
                title="Supprimer l'examen",
            ),
            align="center", width="100%",
        ),
        width="100%",
    )


# ── Shared helpers ────────────────────────────────────────────────────────────

def _section_card(heading: str, content: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.heading(heading, size="4"),
        rx.separator(width="100%"),
        content,
        width="100%",
        spacing="3",
    )


def _text_field_edit(label, value, on_change, placeholder, rows="3") -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        rx.text_area(value=value, on_change=on_change, placeholder=placeholder, size="2", width="100%", rows=rows),
        width="100%", spacing="1",
    )


def _text_field_view(value, empty_label="—") -> rx.Component:
    return rx.cond(
        value,
        rx.box(rx.text(value, size="2", color="var(--gray-11)"),
               padding="0.75rem 1rem", background="var(--gray-2)", border_radius="8px", width="100%"),
        rx.text(empty_label, size="2", color="var(--gray-7)"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Details
# ══════════════════════════════════════════════════════════════════════════════

def _tab_details() -> rx.Component:
    return rx.vstack(
        _section_card(
            LanguageState.tr["exam_section_reason"],
            rx.cond(
                ExamDetailState.is_sections_editable,
                _text_field_edit(
                    LanguageState.tr["exam_section_reason"],
                    ExamDetailState.form_reason_for_visit,
                    ExamDetailState.set_form_reason_for_visit,
                    LanguageState.tr["exam_section_reason"] + "...",
                    rows="2",
                ),
                _text_field_view(ExamDetailState.exam.reason_for_visit),
            ),
        ),
        _section_card(
            LanguageState.tr["exam_section_history"],
            rx.cond(
                ExamDetailState.is_sections_editable,
                _text_field_edit(
                    LanguageState.tr["exam_section_history"],
                    ExamDetailState.form_medical_history,
                    ExamDetailState.set_form_medical_history,
                    LanguageState.tr["exam_section_history"] + "...",
                    rows="3",
                ),
                _text_field_view(ExamDetailState.exam.medical_history),
            ),
        ),
        rx.cond(
            ExamDetailState.is_sections_editable,
            rx.hstack(
                rx.spacer(),
                rx.button(
                    rx.cond(
                        ExamDetailState.is_saving_reason,
                        rx.spinner(size="2"),
                        rx.icon("check", size=15),
                    ),
                    LanguageState.tr["exam_btn_save_informations"],
                    on_click=ExamDetailState.save_informations,
                    size="2",
                ),
                width="100%", align="center",
            ),
        ),
        width="100%", spacing="6",
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Results
# ══════════════════════════════════════════════════════════════════════════════

def _lab_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("normal", rx.badge("Normal", color_scheme="green", variant="soft", size="1")),
        ("high", rx.badge("High", color_scheme="orange", variant="soft", size="1")),
        ("low", rx.badge("Low", color_scheme="blue", variant="soft", size="1")),
        ("critical", rx.badge("Critical", color_scheme="red", variant="solid", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _lab_row_view(row: LabResultRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(row.parameter, size="2")),
        rx.table.cell(rx.text(row.unit, size="2", color="var(--gray-9)")),
        rx.table.cell(rx.text(row.value, size="2")),
        rx.table.cell(rx.text(row.reference_range, size="2")),
        rx.table.cell(_lab_status_badge(row.status)),
    )


def _lab_row_edit(row: LabResultRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(row.parameter, size="2")),
        rx.table.cell(rx.text(row.unit, size="2", color="var(--gray-9)")),
        rx.table.cell(rx.text(row.value, size="2")),
        rx.table.cell(rx.text(row.reference_range, size="2")),
        rx.table.cell(_lab_status_badge(row.status)),
        rx.table.cell(
            rx.icon_button(
                rx.icon("trash-2", size=13),
                variant="ghost", size="1", color_scheme="red",
                on_click=lambda: ExamDetailState.open_delete_lab_row_dialog(row.id),
            ),
            padding="0",
            vertical_align="middle",
        ),
    )


def _lab_add_row_form() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.input(value=ExamDetailState.new_lab_parameter, on_change=ExamDetailState.set_new_lab_parameter,
                     placeholder=LanguageState.tr["placeholder_param_name"], size="2", flex="3"),
            rx.input(value=ExamDetailState.new_lab_unit, on_change=ExamDetailState.set_new_lab_unit,
                     placeholder=LanguageState.tr["placeholder_unit"], size="2", flex="1"),
            rx.input(value=ExamDetailState.new_lab_value, on_change=ExamDetailState.set_new_lab_value,
                     placeholder=LanguageState.tr["placeholder_value"], size="2", flex="2"),
            rx.input(value=ExamDetailState.new_lab_reference_range, on_change=ExamDetailState.set_new_lab_reference_range,
                     placeholder=LanguageState.tr["placeholder_ref_range"], size="2", flex="2"),
            rx.select.root(
                rx.select.trigger(size="2"),
                rx.select.content(*[rx.select.item(label, value=value) for value, label in _LAB_STATUS_OPTIONS]),
                value=ExamDetailState.new_lab_status, on_change=ExamDetailState.set_new_lab_status,
                size="2", flex="1",
            ),
            rx.icon_button(rx.icon("plus", size=15), on_click=ExamDetailState.add_lab_row, size="2", variant="soft"),
            width="100%", spacing="2", align="center",
        ),
        width="100%", spacing="2", padding="0.75rem",
        background="var(--gray-2)", border_radius="8px",
    )


def _lab_results_section() -> rx.Component:
    return _section_card(
        LanguageState.tr["exam_section_lab"],
        rx.cond(
            ExamDetailState.is_results_editable,
            rx.vstack(
                rx.cond(
                    ExamDetailState.lab_results,
                    rx.table.root(
                        rx.table.header(rx.table.row(
                            rx.table.column_header_cell(LanguageState.tr["col_parameter"]),
                            rx.table.column_header_cell(LanguageState.tr["col_unit"]),
                            rx.table.column_header_cell(LanguageState.tr["col_value"]),
                            rx.table.column_header_cell(LanguageState.tr["col_ref_range"]),
                            rx.table.column_header_cell(LanguageState.tr["col_status"]),
                            rx.table.column_header_cell(""),
                        )),
                        rx.table.body(rx.foreach(ExamDetailState.lab_results, _lab_row_edit)),
                        width="100%", size="2",
                    ),
                ),
                _lab_add_row_form(),
                width="100%", spacing="3",
            ),
            rx.cond(
                ExamDetailState.lab_results,
                rx.table.root(
                    rx.table.header(rx.table.row(
                        rx.table.column_header_cell(LanguageState.tr["col_parameter"]),
                        rx.table.column_header_cell(LanguageState.tr["col_unit"]),
                        rx.table.column_header_cell(LanguageState.tr["col_value"]),
                        rx.table.column_header_cell(LanguageState.tr["col_ref_range"]),
                        rx.table.column_header_cell(LanguageState.tr["col_status"]),
                    )),
                    rx.table.body(rx.foreach(ExamDetailState.lab_results, _lab_row_view)),
                    width="100%", size="2",
                ),
                rx.text("No laboratory results recorded.", size="2", color="var(--gray-7)"),
            ),
        ),
    )


# ── Document preview helpers ──────────────────────────────────────────────────

def _doc_type_selector(ef: ExamFileRowDTO) -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder="Set type…", size="1"),
        rx.select.content(*[rx.select.item(label, value=value) for value, label in _DOC_TYPE_OPTIONS]),
        value=ef.document_type,
        on_change=lambda v: ExamDetailState.set_file_document_type(ef.id, v),
        size="1",
    )


def _delete_file_confirm_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete document"),
            rx.alert_dialog.description(
                "Are you sure you want to delete this document? This action cannot be undone.",
                size="2",
            ),
            rx.flex(
                rx.button(
                    "Cancel",
                    variant="soft", color_scheme="gray", size="2",
                    on_click=ExamDetailState.close_delete_file_confirm,
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    "Delete",
                    color_scheme="red", size="2",
                    on_click=ExamDetailState.delete_file_confirmed,
                ),
                spacing="3", justify="end", margin_top="1rem",
            ),
        ),
        open=ExamDetailState.file_delete_confirm_open,
    )


def _delete_exam_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete exam"),
            rx.alert_dialog.description(
                "This action is irreversible. Please enter a mandatory comment before confirming.",
                size="2",
            ),
            rx.vstack(
                rx.text_area(
                    value=ExamDetailState.delete_exam_comment,
                    on_change=ExamDetailState.set_delete_exam_comment,
                    placeholder="Deletion reason (required)...",
                    size="2", width="100%", rows="3",
                ),
                rx.flex(
                    rx.button(
                        "Cancel",
                        variant="soft", color_scheme="gray", size="2",
                        on_click=ExamDetailState.close_delete_exam_dialog,
                    ),
                    rx.button(
                        rx.icon("trash-2", size=14),
                        "Delete exam",
                        color_scheme="red", size="2",
                        on_click=ExamDetailState.confirm_delete_exam,
                        disabled=ExamDetailState.delete_exam_comment.length() == 0,
                    ),
                    spacing="3", justify="end",
                ),
                spacing="3", margin_top="0.75rem", width="100%",
            ),
        ),
        open=ExamDetailState.delete_exam_confirm_open,
    )


def _delete_lab_row_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete result"),
            rx.alert_dialog.description(
                "Please enter a mandatory comment before deleting this result.",
                size="2",
            ),
            rx.vstack(
                rx.text_area(
                    value=ExamDetailState.delete_lab_comment,
                    on_change=ExamDetailState.set_delete_lab_comment,
                    placeholder="Deletion reason (required)...",
                    size="2", width="100%", rows="3",
                ),
                rx.flex(
                    rx.button(
                        "Cancel",
                        variant="soft", color_scheme="gray", size="2",
                        on_click=ExamDetailState.close_delete_lab_row_dialog,
                    ),
                    rx.button(
                        rx.icon("trash-2", size=14),
                        "Delete",
                        color_scheme="red", size="2",
                        on_click=ExamDetailState.confirm_delete_lab_row,
                        disabled=ExamDetailState.delete_lab_comment.length() == 0,
                    ),
                    spacing="3", justify="end",
                ),
                spacing="3", margin_top="0.75rem", width="100%",
            ),
        ),
        open=ExamDetailState.delete_lab_confirm_open,
    )


def _file_list_row(ef: ExamFileRowDTO) -> rx.Component:
    return rx.hstack(
        rx.icon("file", size=14, color="var(--gray-9)", flex_shrink="0"),
        rx.vstack(
            rx.text(
                ef.original_name, size="2", weight="medium",
                overflow="hidden", text_overflow="ellipsis", white_space="nowrap",
            ),
            rx.cond(
                ef.file_size_label != "",
                rx.text(ef.file_size_label, size="1", color="var(--gray-8)"),
            ),
            spacing="0", align_items="start", flex="1", min_width="0",
        ),
        rx.cond(
            ExamDetailState.is_results_editable,
            rx.hstack(
                _doc_type_selector(ef),
                rx.icon_button(
                    rx.icon("trash-2", size=13),
                    variant="ghost", size="1", color_scheme="red",
                    on_click=lambda: ExamDetailState.confirm_delete_file(ef.id),
                ),
                spacing="3", align="center",
            ),
            rx.cond(
                ef.document_type != "",
                rx.badge(
                    rx.match(ef.document_type, *[(v, l) for v, l in _DOC_TYPE_OPTIONS], ef.document_type),
                    variant="soft", color_scheme="blue", size="1", flex_shrink="0",
                ),
            ),
        ),
        rx.separator(orientation="vertical", size="2"),
        rx.icon_button(
            rx.icon("eye", size=14),
            variant="ghost", size="1", color_scheme="blue",
            on_click=lambda: ExamDetailState.open_preview_dialog(ef.id),
        ),
        padding_x="0.6rem", padding_y="0.4rem",
        align="center", spacing="2",
        border="1px solid var(--gray-4)",
        border_radius="6px", width="100%",
        cursor="pointer",
    )


def _table_row(row: list) -> rx.Component:
    return rx.table.row(
        rx.foreach(row, lambda cell: rx.table.cell(rx.text(cell, size="1"))),
    )


def _table_preview_content() -> rx.Component:
    return rx.vstack(
        # Truncation notice
        rx.cond(
            ExamDetailState.table_preview_total_rows > _TABLE_PREVIEW_MAX_ROWS,
            rx.text(
                f"Showing first {_TABLE_PREVIEW_MAX_ROWS} rows of " + ExamDetailState.table_preview_total_rows.to_string(),
                size="1", color="var(--gray-8)", style={"font_style": "italic"},
            ),
        ),
        # Table
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.foreach(
                            ExamDetailState.table_preview_columns,
                            lambda col: rx.table.column_header_cell(rx.text(col, size="1", weight="medium")),
                        ),
                    ),
                ),
                rx.table.body(
                    rx.foreach(ExamDetailState.table_preview_rows, _table_row),
                ),
                size="1", width="100%",
            ),
            overflow_x="auto", width="100%",
            max_height="300px", overflow_y="auto",
            border="1px solid var(--gray-4)", border_radius="6px",
        ),
        # Chart (shown above prompt after generation)
        rx.cond(
            ExamDetailState.plot_chart,
            rx.box(
                plotly_with_fullscreen(
                    ExamDetailState.plot_chart["figure"],
                    ExamDetailState.plot_chart["name"],
                ),
                width="100%",
                border="1px solid var(--gray-4)", border_radius="8px",
                padding="0.5rem",
            ),
        ),
        rx.cond(
            ExamDetailState.plot_generation_error != "",
            rx.callout(ExamDetailState.plot_generation_error, icon="triangle-alert", color_scheme="red", size="1"),
        ),
        # Prompt area
        rx.hstack(
            rx.input(
                value=ExamDetailState.plot_prompt,
                on_change=ExamDetailState.set_plot_prompt,
                placeholder=LanguageState.tr["plot_prompt_placeholder"],
                size="2",
                flex="1",
            ),
            rx.button(
                rx.cond(
                    ExamDetailState.is_generating_plot,
                    rx.spinner(size="2"),
                    rx.icon("bar-chart-2", size=15),
                ),
                LanguageState.tr["plot_btn_generate"],
                on_click=ExamDetailState.generate_plot_from_prompt,
                disabled=ExamDetailState.is_generating_plot,
                size="2",
                variant="soft",
            ),
            width="100%", spacing="2", align="center",
        ),
        rx.cond(
            ExamDetailState.plot_chart,
            rx.fragment(),
            rx.text(LanguageState.tr["plot_no_chart_yet"], size="1", color="var(--gray-7)", style={"font_style": "italic"}),
        ),
        width="100%", spacing="3",
    )


def _preview_dialog_content() -> rx.Component:
    return rx.cond(
        ExamDetailState.is_loading_preview,
        rx.center(rx.spinner(size="3"), padding="3rem"),
        rx.cond(
            ExamDetailState.preview_error != "",
            rx.callout(ExamDetailState.preview_error, icon="triangle-alert", color_scheme="red", size="1"),
            rx.match(
                ExamDetailState.selected_file_type,
                ("image", rx.box(
                    rx.image(src=ExamDetailState.selected_file_preview_url, max_width="100%", border_radius="8px"),
                    width="100%",
                )),
                ("pdf", rx.html(
                    '<iframe src="' + ExamDetailState.selected_file_preview_url + '" width="100%" height="600px" style="border:none;border-radius:8px;"></iframe>'
                )),
                ("table", _table_preview_content()),
                ("other", rx.vstack(
                    rx.icon("file-down", size=32, color="var(--gray-6)"),
                    rx.link(
                        LanguageState.tr["preview_download"],
                        href=ExamDetailState.selected_file_preview_url,
                        target="_blank",
                        size="2",
                    ),
                    spacing="2", align="center", padding="2rem",
                )),
                rx.text(LanguageState.tr["preview_unsupported"], size="2", color="var(--gray-7)"),
            ),
        ),
    )


def _file_preview_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(ExamDetailState.selected_file_name),
            rx.dialog.description(""),
            _preview_dialog_content(),
            rx.flex(
                rx.dialog.close(
                    rx.button("Close", variant="soft", color_scheme="gray", size="2"),
                ),
                justify="end",
                margin_top="1rem",
            ),
            on_interact_outside=ExamDetailState.close_preview_dialog,
            on_escape_key_down=ExamDetailState.close_preview_dialog,
            max_width="90vw",
            width="860px",
        ),
        open=ExamDetailState.preview_dialog_open,
    )


def _documents_section() -> rx.Component:
    return rx.vstack(
        rx.heading(LanguageState.tr["exam_section_documents"], size="4"),
        rx.separator(width="100%"),
        rx.cond(
            ExamDetailState.exam_files,
            rx.vstack(
                rx.foreach(ExamDetailState.exam_files, _file_list_row),
                width="100%", spacing="1",
            ),
            rx.text("No documents attached yet.", size="2", color="var(--gray-7)"),
        ),
        rx.cond(
            ExamDetailState.is_results_editable,
            rx.upload(
                rx.vstack(
                    rx.cond(
                        ExamDetailState.is_uploading_file,
                        rx.hstack(rx.spinner(size="2"), rx.text("Uploading…", size="2"), spacing="2", align="center"),
                        rx.vstack(
                            rx.icon("upload", size=18, color="var(--gray-7)"),
                            rx.text("Drop files here or click to add", size="2", color="var(--gray-7)"),
                            align="center", spacing="1",
                        ),
                    ),
                    align="center", justify="center", width="100%", height="68px",
                ),
                id="exam_detail_file_upload", multiple=True,
                accept={
                    "image/*": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"],
                    "application/pdf": [".pdf"],
                    "application/msword": [".doc"],
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
                    "application/vnd.ms-excel": [".xls"],
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                    "text/csv": [".csv"],
                    "text/plain": [".txt"],
                },
                on_drop=ExamDetailState.handle_file_upload(rx.upload_files(upload_id="exam_detail_file_upload")),
                border="2px dashed var(--gray-5)", border_radius="8px", padding="0.75rem",
                width="100%", cursor="pointer",
                _hover={"border_color": "var(--accent-8)", "background": "var(--gray-1)"},
            ),
        ),
        width="100%", spacing="3",
    )


def _tab_results() -> rx.Component:
    return rx.vstack(
        _documents_section(),
        _lab_results_section(),
        rx.cond(
            ExamDetailState.exam.status != "done",
            rx.hstack(
                rx.spacer(),
                rx.button(
                    rx.cond(ExamDetailState.is_submitting_review, rx.spinner(size="2"), rx.icon("send", size=15)),
                    LanguageState.tr["exam_btn_submit_review"],
                    on_click=ExamDetailState.submit_for_review,
                    loading=ExamDetailState.is_submitting_review,
                    color_scheme="orange", size="2",
                ),
                width="100%", align="center",
            ),
        ),
        width="100%", spacing="6",
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Interpretation
# ══════════════════════════════════════════════════════════════════════════════

def _tab_interpretation() -> rx.Component:
    return _section_card(
        LanguageState.tr["exam_section_interpretation"],
        rx.match(
            ExamDetailState.exam.status,
            ("done",
                rx.vstack(
                    rx.cond(
                        ExamDetailState.exam.interpretation,
                        rx.box(
                            rx.text(ExamDetailState.exam.interpretation, size="2"),
                            padding="0.75rem 1rem",
                            background="var(--green-2)",
                            border="1px solid var(--green-6)",
                            border_radius="8px", width="100%",
                        ),
                        rx.text("—", size="2", color="var(--gray-7)"),
                    ),
                    rx.cond(
                        ExamDetailState.exam.interpreted_by_name != "",
                        rx.hstack(
                            rx.icon("user-check", size=13, color="var(--green-9)"),
                            rx.text(
                                "Interpreted by " + ExamDetailState.exam.interpreted_by_name,
                                size="1", color="var(--green-9)",
                            ),
                            spacing="1", align="center",
                        ),
                    ),
                    spacing="2", width="100%",
                ),
            ),
            ("in_progress_interpretation",
                rx.cond(
                    ExamDetailState.is_doctor | ExamDetailState.is_admin,
                    rx.vstack(
                        rx.text(LanguageState.tr["exam_hint_doctor_interpretation"], size="2", color="var(--gray-9)"),
                        rx.text_area(
                            value=ExamDetailState.form_interpretation,
                            on_change=ExamDetailState.set_form_interpretation,
                            placeholder=LanguageState.tr["exam_section_interpretation"] + "…",
                            size="2", width="100%", rows="6",
                        ),
                        rx.hstack(
                            rx.spacer(),
                            rx.button(
                                rx.cond(ExamDetailState.is_submitting_interpretation, rx.spinner(size="2"), rx.icon("check-circle", size=15)),
                                LanguageState.tr["exam_btn_submit_interpretation"],
                                on_click=ExamDetailState.submit_interpretation,
                                disabled=ExamDetailState.is_submitting_interpretation,
                                color_scheme="green", size="2",
                            ),
                            width="100%", align="center",
                        ),
                        spacing="3", width="100%",
                    ),
                    rx.callout(LanguageState.tr["exam_hint_awaiting_interpretation"], icon="clock", color_scheme="orange", size="1"),
                ),
            ),
            rx.callout(LanguageState.tr["exam_hint_not_yet_unlocked"], icon="info", color_scheme="gray", size="1"),
        ),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Page
# ══════════════════════════════════════════════════════════════════════════════

def exam_detail_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.cond(
                ExamDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    ExamDetailState.exam,
                    rx.vstack(
                        # ── Header row: back ─────────────────────────────────
                        rx.hstack(
                            rx.button(
                                rx.icon("arrow-left", size=14),
                                LanguageState.tr["btn_back"],
                                on_click=ExamDetailState.go_back,
                                variant="ghost", size="2",
                            ),
                            width="100%", align="center",
                        ),
                        # ── Sibling exam navigation ───────────────────────────
                        _sibling_exams_nav(),
                        # ── Error alert ───────────────────────────────────────
                        rx.cond(
                            ExamDetailState.error_message != "",
                            rx.callout(
                                ExamDetailState.error_message,
                                icon="triangle-alert", color_scheme="red", size="2",
                            ),
                        ),
                        # ── Exam info card ────────────────────────────────────
                        _exam_info_card(),
                        # ── Workflow lifeline ─────────────────────────────────
                        _exam_workflow_lifeline(),
                        # ── Contextual hint (after lifeline, like campaign) ───
                        _exam_help_banner(),
                        # ── Tabs ──────────────────────────────────────────────
                        rx.tabs.root(
                            rx.tabs.list(
                                rx.tabs.trigger(
                                    rx.hstack(rx.icon("file-text", size=13), LanguageState.tr["tab_details"], spacing="1", align="center"),
                                    value="informations",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(rx.icon("flask-conical", size=13), LanguageState.tr["tab_results"], spacing="1", align="center"),
                                    value="results",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(rx.icon("brain", size=13), LanguageState.tr["tab_interpretation"], spacing="1", align="center"),
                                    value="interpretation",
                                ),
                            ),
                            rx.tabs.content(_tab_details(), value="informations", padding_top="1.25rem"),
                            rx.tabs.content(_tab_results(), value="results", padding_top="1.25rem"),
                            rx.tabs.content(_tab_interpretation(), value="interpretation", padding_top="1.25rem"),
                            value=ExamDetailState.active_tab,
                            on_change=ExamDetailState.set_active_tab,
                            width="100%",
                        ),
                        width="100%", spacing="4", padding_bottom="6",
                    ),
                    rx.center(
                        rx.callout("Exam not found.", icon="triangle-alert", color_scheme="red"),
                        padding="4rem",
                    ),
                ),
            ),
            # Dialogs — must be mounted once in the page
            plotly_fullscreen_dialog(),
            _file_preview_dialog(),
            _delete_file_confirm_dialog(),
            _delete_exam_dialog(),
            _delete_lab_row_dialog(),
        )
    )
