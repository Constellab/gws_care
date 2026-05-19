"""Exam detail page component — Medical sections, Laboratory results, Medical Documents."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .exam_detail_state import (
    PREDEFINED_LAB_PARAMS,
    ExamDetailDTO,
    ExamDetailState,
    ExamFileRowDTO,
    LabResultRowDTO,
)

# Predefined parameter groups: (english_name, translation_key, [param_names])
_PREDEFINED_GROUPS: list[tuple[str, str, list[str]]] = [
    ("Complete Blood Count (CBC)", "lab_group_cbc", ["WBC", "RBC", "Hemoglobin", "Hematocrit", "MCV", "MCH", "MCHC", "Platelets"]),
    ("Metabolic Panel", "lab_group_metabolic", ["Glucose", "BUN", "Creatinine", "eGFR", "Sodium", "Potassium", "Chloride", "Bicarbonate", "Calcium"]),
    ("Liver Function (LFT)", "lab_group_lft", ["ALT", "AST", "ALP", "GGT", "Total Bilirubin", "Direct Bilirubin", "Total Protein", "Albumin"]),
    ("Lipid Panel", "lab_group_lipid", ["Total Cholesterol", "LDL", "HDL", "Triglycerides"]),
    ("Diabetes", "lab_group_diabetes", ["HbA1c", "Fasting Glucose", "Insulin"]),
    ("Thyroid", "lab_group_thyroid", ["TSH", "fT4", "fT3"]),
    ("Inflammation", "lab_group_inflammation", ["CRP", "ESR", "Ferritin"]),
    ("Coagulation", "lab_group_coagulation", ["PT", "INR", "aPTT"]),
]

# ── Document type options (value, translation_key) ───────────────────────────
_DOC_TYPE_OPTIONS = [
    ("medical_certificate", "doc_type_medical_certificate"),
    ("medical_report", "doc_type_medical_report"),
    ("letter", "doc_type_letter"),
    ("medical_analysis", "doc_type_medical_analysis"),
    ("prescription", "doc_type_prescription"),
    ("mri", "doc_type_mri"),
    ("ct_scan", "doc_type_ct_scan"),
    ("xray", "doc_type_xray"),
    ("ultrasound", "doc_type_ultrasound"),
    ("other", "doc_type_other"),
]



def _status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("draft", rx.badge(LanguageState.tr["exam_status_draft"], color_scheme="gray", variant="soft", size="2")),
        ("pending", rx.badge(LanguageState.tr["exam_status_pending"], color_scheme="orange", variant="soft", size="2")),
        ("interpreted", rx.badge(LanguageState.tr["exam_status_interpreted"], color_scheme="green", variant="soft", size="2")),
        rx.badge(status, color_scheme="gray", variant="soft", size="2"),
    )


# ── Header ────────────────────────────────────────────────────────────────────

def _mode_toggle() -> rx.Component:
    """View / Edit segmented control."""
    return rx.segmented_control.root(
        rx.segmented_control.item(
            rx.hstack(
                rx.icon("eye", size=13),
                rx.text(LanguageState.tr["mode_view"], size="1"),
                spacing="1",
                align="center",
            ),
            value="view",
        ),
        rx.segmented_control.item(
            rx.hstack(
                rx.icon("pencil", size=13),
                rx.text(LanguageState.tr["mode_edit"], size="1"),
                spacing="1",
                align="center",
            ),
            value="edit",
        ),
        value=rx.cond(ExamDetailState.is_edit_mode, "edit", "view"),
        on_change=lambda v: ExamDetailState.set_edit_mode(v == "edit"),
        size="1",
    )


def _exam_header(exam: ExamDetailDTO) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.heading(exam.exam_type_label, size="6"),
            rx.hstack(
                _status_badge(exam.status),
                rx.text(exam.exam_date, size="2", color="var(--gray-8)"),
                spacing="3",
                align="center",
            ),
            spacing="2",
            align_items="start",
        ),
        rx.spacer(),
        rx.text(
            LanguageState.tr["exam_patient_label"],
            exam.patient_name,
            size="2",
            color="var(--gray-9)",
        ),
        _mode_toggle(),
        width="100%",
        align="center",
    )


# ── Section 1: Medical sections ──────────────────────────────────────────────

def _section_card(heading: str, content: rx.Component) -> rx.Component:
    """Wrapper card for each section."""
    return rx.vstack(
        rx.heading(heading, size="4"),
        rx.separator(width="100%"),
        content,
        width="100%",
        spacing="3",
    )


def _text_field_edit(label: str, value, on_change, placeholder: str, rows: str = "3") -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        rx.text_area(
            value=value,
            on_change=on_change,
            placeholder=placeholder,
            size="2",
            width="100%",
            rows=rows,
        ),
        width="100%",
        spacing="1",
    )


def _text_field_view(value, empty_label: str) -> rx.Component:
    return rx.cond(
        value,
        rx.box(
            rx.text(value, size="2", color="var(--gray-11)"),
            padding="0.75rem 1rem",
            background="var(--gray-2)",
            border_radius="8px",
            width="100%",
        ),
        rx.text(empty_label, size="2", color="var(--gray-7)"),
    )


def _num_field_edit(label: str, value, on_change, placeholder: str) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        rx.input(
            value=value,
            on_change=on_change,
            placeholder=placeholder,
            type="number",
            size="2",
            width="100%",
        ),
        width="100%",
        spacing="1",
    )


def _str_field_edit(label: str, value, on_change, placeholder: str) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        rx.input(
            value=value,
            on_change=on_change,
            placeholder=placeholder,
            size="2",
            width="100%",
        ),
        width="100%",
        spacing="1",
    )


def _num_field_view(label: str, value, unit: str = "") -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", color="var(--gray-9)", weight="medium"),
        rx.cond(
            value,
            rx.text(
                rx.cond(unit != "", value.to_string() + " " + unit, value.to_string()),
                size="2",
            ),
            rx.text("—", size="2", color="var(--gray-6)"),
        ),
        spacing="1",
        align_items="start",
    )


def _str_field_view(label: str, value) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", color="var(--gray-9)", weight="medium"),
        rx.cond(
            value,
            rx.text(value, size="2"),
            rx.text("—", size="2", color="var(--gray-6)"),
        ),
        spacing="1",
        align_items="start",
    )


def _save_sections_button() -> rx.Component:
    return rx.hstack(
        rx.spacer(),
        rx.button(
            rx.cond(
                ExamDetailState.is_saving_sections,
                rx.spinner(size="2"),
                rx.icon("check", size=15),
            ),
            LanguageState.tr["save"],
            on_click=ExamDetailState.save_sections,
            disabled=ExamDetailState.is_saving_sections,
            size="2",
        ),
        width="100%",
        align="center",
    )


def _reasons_and_history_section() -> rx.Component:
    return rx.vstack(
        _section_card(
            LanguageState.tr["exam_section_reason"],
            rx.cond(
                ExamDetailState.is_edit_mode,
                rx.vstack(
                    _text_field_edit(
                        LanguageState.tr["exam_section_reason"],
                        ExamDetailState.form_reason_for_visit,
                        ExamDetailState.set_form_reason_for_visit,
                        LanguageState.tr["exam_reason_placeholder"],
                        rows="2",
                    ),
                    width="100%",
                    spacing="3",
                ),
                _text_field_view(
                    ExamDetailState.exam.reason_for_visit,
                    LanguageState.tr["exam_no_reason"],
                ),
            ),
        ),
        _section_card(
            LanguageState.tr["exam_section_history"],
            rx.cond(
                ExamDetailState.is_edit_mode,
                _text_field_edit(
                    LanguageState.tr["exam_section_history"],
                    ExamDetailState.form_medical_history,
                    ExamDetailState.set_form_medical_history,
                    LanguageState.tr["exam_history_placeholder"],
                    rows="3",
                ),
                _text_field_view(
                    ExamDetailState.exam.medical_history,
                    LanguageState.tr["exam_no_history"],
                ),
            ),
        ),
        width="100%",
        spacing="4",
    )


def _physical_exam_section() -> rx.Component:
    return _section_card(
        LanguageState.tr["exam_section_physical"],
        rx.cond(
            ExamDetailState.is_edit_mode,
            rx.vstack(
                rx.grid(
                    _num_field_edit(LanguageState.tr["exam_weight"], ExamDetailState.form_weight, ExamDetailState.set_form_weight, "e.g. 70"),
                    _num_field_edit(LanguageState.tr["exam_height"], ExamDetailState.form_height, ExamDetailState.set_form_height, "e.g. 175"),
                    _num_field_edit(LanguageState.tr["exam_bmi"], ExamDetailState.form_bmi, ExamDetailState.set_form_bmi, "e.g. 22.9"),
                    _str_field_edit(LanguageState.tr["exam_blood_pressure"], ExamDetailState.form_blood_pressure, ExamDetailState.set_form_blood_pressure, "e.g. 120/80"),
                    _num_field_edit(LanguageState.tr["exam_heart_rate"], ExamDetailState.form_heart_rate, ExamDetailState.set_form_heart_rate, "e.g. 72"),
                    _num_field_edit(LanguageState.tr["exam_temperature"], ExamDetailState.form_temperature, ExamDetailState.set_form_temperature, "e.g. 37.0"),
                    columns="3",
                    spacing="3",
                    width="100%",
                ),
                width="100%",
                spacing="3",
            ),
            rx.grid(
                _num_field_view(LanguageState.tr["exam_weight_view"], ExamDetailState.exam.weight, "kg"),
                _num_field_view(LanguageState.tr["exam_height_view"], ExamDetailState.exam.height, "cm"),
                _num_field_view(LanguageState.tr["exam_bmi"], ExamDetailState.exam.bmi),
                _str_field_view(LanguageState.tr["exam_blood_pressure"], ExamDetailState.exam.blood_pressure),
                _num_field_view(LanguageState.tr["exam_heart_rate_view"], ExamDetailState.exam.heart_rate, "bpm"),
                _num_field_view(LanguageState.tr["exam_temperature_view"], ExamDetailState.exam.temperature, "°C"),
                columns="3",
                spacing="4",
                width="100%",
            ),
        ),
    )


def _conclusion_section() -> rx.Component:
    return _section_card(
        LanguageState.tr["exam_section_conclusion"],
        rx.cond(
            ExamDetailState.is_edit_mode,
            rx.vstack(
                _text_field_edit(
                    LanguageState.tr["exam_section_conclusion"],
                    ExamDetailState.form_conclusion,
                    ExamDetailState.set_form_conclusion,
                    LanguageState.tr["exam_conclusion_placeholder"],
                    rows="3",
                ),
                _save_sections_button(),
                width="100%",
                spacing="3",
            ),
            _text_field_view(
                ExamDetailState.exam.conclusion,
                LanguageState.tr["exam_no_conclusion"],
            ),
        ),
    )


# ── Section: Laboratory results ───────────────────────────────────────────────

_LAB_STATUS_OPTIONS: list[tuple[str, str]] = [
    ("normal", "exam_lab_status_normal"),
    ("high", "exam_lab_status_high"),
    ("low", "exam_lab_status_low"),
    ("critical", "exam_lab_status_critical"),
]


def _lab_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("normal", rx.badge(
            rx.icon("check", size=11), LanguageState.tr["exam_lab_status_normal"],
            color_scheme="green", variant="soft", size="1",
        )),
        ("high", rx.badge(
            rx.icon("arrow-up", size=11), LanguageState.tr["exam_lab_status_high"],
            color_scheme="orange", variant="surface", size="1",
        )),
        ("low", rx.badge(
            rx.icon("arrow-down", size=11), LanguageState.tr["exam_lab_status_low"],
            color_scheme="blue", variant="surface", size="1",
        )),
        ("critical", rx.badge(
            rx.icon("triangle-alert", size=11), LanguageState.tr["exam_lab_status_critical"],
            color_scheme="red", variant="solid", size="1",
        )),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _lab_value_cell(row: LabResultRowDTO) -> rx.Component:
    """Display the result value with a color + arrow indicator if anomalous."""
    return rx.match(
        row.status,
        ("high", rx.hstack(
            rx.icon("triangle-alert", size=13, color="var(--orange-9)"),
            rx.text(row.value, size="2", weight="bold", color="var(--orange-9)"),
            spacing="1", align="center",
        )),
        ("low", rx.hstack(
            rx.icon("triangle-alert", size=13, color="var(--blue-9)"),
            rx.text(row.value, size="2", weight="bold", color="var(--blue-9)"),
            spacing="1", align="center",
        )),
        ("critical", rx.hstack(
            rx.icon("siren", size=13, color="var(--red-9)"),
            rx.text(row.value, size="2", weight="bold", color="var(--red-9)"),
            spacing="1", align="center",
        )),
        # normal or unknown — plain text
        rx.text(row.value, size="2"),
    )


def _lab_row_view(row: LabResultRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(row.parameter, size="2", weight="medium")),
        rx.table.cell(rx.text(row.unit, size="2", color="var(--gray-9)")),
        rx.table.cell(_lab_value_cell(row)),
        rx.table.cell(rx.text(row.reference_range, size="2", color="var(--gray-10)")),
        rx.table.cell(_lab_status_badge(row.status)),
        background=rx.match(
            row.status,
            ("high", "var(--orange-1)"),
            ("low", "var(--blue-1)"),
            ("critical", "var(--red-2)"),
            "transparent",
        ),
    )


def _lab_row_edit(row: LabResultRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(row.parameter, size="2", weight="medium")),
        rx.table.cell(rx.text(row.unit, size="2", color="var(--gray-9)")),
        rx.table.cell(_lab_value_cell(row)),
        rx.table.cell(rx.text(row.reference_range, size="2", color="var(--gray-10)")),
        rx.table.cell(_lab_status_badge(row.status)),
        rx.table.cell(
            rx.icon_button(
                rx.icon("trash-2", size=13),
                variant="ghost",
                size="1",
                color_scheme="red",
                on_click=lambda: ExamDetailState.remove_lab_row(row.id),
            ),
            padding="0",
        ),
    )


def _predefined_param_select() -> rx.Component:
    """Dropdown to quickly select a predefined lab parameter."""
    groups = []
    for _group_name, tr_key, param_names in _PREDEFINED_GROUPS:
        items = [rx.select.item(name, value=name) for name in param_names]
        groups.append(rx.select.group(rx.select.label(LanguageState.tr[tr_key]), *items))
    return rx.select.root(
        rx.select.trigger(placeholder=LanguageState.tr["exam_lab_select_preset"], size="2"),
        rx.select.content(
            rx.select.item(LanguageState.tr["exam_lab_custom_entry"], value="CUSTOM"),
            rx.select.separator(),
            *groups,
        ),
        value=ExamDetailState.new_lab_selected_preset,
        on_change=ExamDetailState.select_predefined_param,
        size="2",
        width="100%",
    )


def _lab_add_row_form() -> rx.Component:
    return rx.vstack(
        # Row 1: predefined selector (full width)
        _predefined_param_select(),
        # Row 2: parameter name + unit + value + reference range + status + add button
        rx.hstack(
            rx.input(
                value=ExamDetailState.new_lab_parameter,
                on_change=ExamDetailState.set_new_lab_parameter,
                placeholder=LanguageState.tr["exam_lab_param_name"],
                size="2",
                flex="3",
            ),
            rx.input(
                value=ExamDetailState.new_lab_unit,
                on_change=ExamDetailState.set_new_lab_unit,
                placeholder=LanguageState.tr["exam_lab_col_unit"],
                size="2",
                flex="1",
            ),
            rx.input(
                value=ExamDetailState.new_lab_value,
                on_change=ExamDetailState.set_new_lab_value,
                placeholder=LanguageState.tr["exam_lab_col_value"],
                size="2",
                flex="2",
            ),
            rx.input(
                value=ExamDetailState.new_lab_reference_range,
                on_change=ExamDetailState.set_new_lab_reference_range,
                placeholder=LanguageState.tr["exam_lab_col_ref"],
                size="2",
                flex="2",
            ),
            rx.select.root(
                rx.select.trigger(size="2"),
                rx.select.content(
                    *[rx.select.item(LanguageState.tr[tr_key], value=value) for value, tr_key in _LAB_STATUS_OPTIONS],
                ),
                value=ExamDetailState.new_lab_status,
                on_change=ExamDetailState.set_new_lab_status,
                size="2",
                flex="1",
            ),
            rx.icon_button(
                rx.icon("plus", size=15),
                on_click=ExamDetailState.add_lab_row,
                size="2",
                variant="soft",
            ),
            width="100%",
            spacing="2",
            align="center",
        ),
        width="100%",
        spacing="2",
        padding="0.75rem",
        background="var(--gray-2)",
        border_radius="8px",
    )


def _lab_results_section() -> rx.Component:
    return _section_card(
        LanguageState.tr["exam_section_lab"],
        rx.cond(
            ExamDetailState.is_edit_mode,
            rx.vstack(
                rx.cond(
                    ExamDetailState.lab_results,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(LanguageState.tr["exam_lab_col_param"]),
                                rx.table.column_header_cell(LanguageState.tr["exam_lab_col_unit"]),
                                rx.table.column_header_cell(LanguageState.tr["exam_lab_col_value"]),
                                rx.table.column_header_cell(LanguageState.tr["exam_lab_col_ref"]),
                                rx.table.column_header_cell(LanguageState.tr["col_status"]),
                                rx.table.column_header_cell(""),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(ExamDetailState.lab_results, _lab_row_edit),
                        ),
                        width="100%",
                        size="2",
                    ),
                ),
                _lab_add_row_form(),
                width="100%",
                spacing="3",
            ),
            # View mode
            rx.cond(
                ExamDetailState.lab_results,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(LanguageState.tr["exam_lab_col_param"]),
                            rx.table.column_header_cell(LanguageState.tr["exam_lab_col_unit"]),
                            rx.table.column_header_cell(LanguageState.tr["exam_lab_col_value"]),
                            rx.table.column_header_cell(LanguageState.tr["exam_lab_col_ref"]),
                            rx.table.column_header_cell(LanguageState.tr["col_status"]),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(ExamDetailState.lab_results, _lab_row_view),
                    ),
                    width="100%",
                    size="2",
                ),
                rx.text(LanguageState.tr["exam_lab_no_results"], size="2", color="var(--gray-7)"),
            ),
        ),
    )


# ── Section 3: Medical Documents ─────────────────────────────────────────────

def _doc_type_selector(ef: ExamFileRowDTO) -> rx.Component:
    """Compact document-type selector for a single file row."""
    return rx.select.root(
        rx.select.trigger(placeholder=LanguageState.tr["exam_docs_set_type"], size="1"),
        rx.select.content(
            *[rx.select.item(LanguageState.tr[tr_key], value=value) for value, tr_key in _DOC_TYPE_OPTIONS],
        ),
        value=ef.document_type,
        on_change=lambda v: ExamDetailState.set_file_document_type(ef.id, v),
        size="1",
    )


def _file_row(ef: ExamFileRowDTO) -> rx.Component:
    return rx.hstack(
        rx.icon("file", size=14, color="var(--gray-9)", flex_shrink="0"),
        rx.cond(
            ef.resource_download_url != "",
            rx.link(
                ef.original_name,
                href=ef.resource_download_url,
                target="_blank",
                size="2",
                flex="1",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
            rx.text(
                ef.original_name,
                size="2",
                flex="1",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
        ),
        rx.cond(
            ef.file_size_label != "",
            rx.text(ef.file_size_label, size="1", color="var(--gray-8)", flex_shrink="0"),
        ),
        rx.cond(
            ExamDetailState.is_edit_mode,
            _doc_type_selector(ef),
            rx.cond(
                ef.document_type != "",
                rx.badge(
                    rx.match(
                        ef.document_type,
                        *[(value, LanguageState.tr[tr_key]) for value, tr_key in _DOC_TYPE_OPTIONS],
                        ef.document_type,
                    ),
                    variant="soft",
                    color_scheme="blue",
                    size="1",
                    flex_shrink="0",
                ),
            ),
        ),
        rx.cond(
            ExamDetailState.is_edit_mode,
            rx.tooltip(
                rx.icon_button(
                    rx.icon("trash-2", size=13),
                    variant="ghost",
                    size="1",
                    color_scheme="red",
                    on_click=lambda: ExamDetailState.delete_file(ef.id),
                ),
                content=LanguageState.tr["exam_docs_delete_file"],
            ),
        ),
        padding_x="0.6rem",
        padding_y="0.4rem",
        align="center",
        spacing="2",
        border="1px solid var(--gray-4)",
        border_radius="6px",
        width="100%",
    )


def _documents_section() -> rx.Component:
    return rx.vstack(
        rx.heading(LanguageState.tr["exam_section_docs"], size="4"),
        rx.separator(width="100%"),
        rx.cond(
            ExamDetailState.exam_files,
            rx.vstack(
                rx.foreach(ExamDetailState.exam_files, _file_row),
                width="100%",
                spacing="1",
            ),
            rx.text(LanguageState.tr["exam_docs_no_docs"], size="2", color="var(--gray-7)"),
        ),
        # Upload drop zone — only in edit mode
        rx.cond(
            ExamDetailState.is_edit_mode,
            rx.upload(
                rx.vstack(
                    rx.cond(
                        ExamDetailState.is_uploading_file,
                        rx.hstack(
                            rx.spinner(size="2"),
                            rx.text(LanguageState.tr["exam_docs_uploading"], size="2", color="var(--gray-9)"),
                            spacing="2",
                            align="center",
                        ),
                        rx.vstack(
                            rx.icon("upload", size=18, color="var(--gray-7)"),
                            rx.text(
                                LanguageState.tr["exam_docs_drop_files"],
                                size="2",
                                color="var(--gray-7)",
                            ),
                            align="center",
                            spacing="1",
                        ),
                    ),
                    align="center",
                    justify="center",
                    width="100%",
                    height="68px",
                ),
                id="exam_detail_file_upload",
                multiple=True,
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
                on_drop=ExamDetailState.handle_file_upload(
                    rx.upload_files(upload_id="exam_detail_file_upload")
                ),
                border="2px dashed var(--gray-5)",
                border_radius="8px",
                padding="0.75rem",
                width="100%",
                cursor="pointer",
                _hover={"border_color": "var(--accent-8)", "background": "var(--gray-1)"},
            ),
        ),
        width="100%",
        spacing="3",
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def exam_detail_page() -> rx.Component:
    """Exam detail page: Medical sections, Doctor's Interpretation, Medical Documents."""
    return main_component(
        page_layout(
            rx.button(
                rx.icon("arrow-left", size=16),
                LanguageState.tr["back_to_patient_btn"],
                on_click=ExamDetailState.go_back,
                variant="ghost",
                size="2",
            ),
            rx.cond(
                ExamDetailState.error_message != "",
                rx.callout(
                    ExamDetailState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                ExamDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    ExamDetailState.exam,
                    rx.vstack(
                        _exam_header(ExamDetailState.exam),
                        _reasons_and_history_section(),
                        _physical_exam_section(),
                        _lab_results_section(),
                        _conclusion_section(),
                        _documents_section(),
                        width="100%",
                        spacing="6",
                    ),
                    rx.center(
                        rx.text(LanguageState.tr["exam_not_found"], color="var(--gray-9)"), padding="3rem"
                    ),
                ),
            ),
        )
    )
