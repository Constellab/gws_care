"""Exam detail page component — Medical sections, Laboratory results, Medical Documents."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .exam_detail_state import (
    AvailableParamOption,
    ConsultationContextDTO,
    ExamDetailDTO,
    ExamDetailState,
    ExamFileRowDTO,
    FollowUpExamOption,
    FollowUpExamRowDTO,
    FollowUpParamOption,
    LabResultRowDTO,
    RequestedParamDTO,
)


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
    return rx.vstack(
        rx.hstack(
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
            # Notify doctor button — shown when exam has prescribed params (independent patient workflow)
            rx.cond(
                ExamDetailState.requested_params,
                rx.tooltip(
                    rx.button(
                        rx.icon("bell", size=14),
                        "Notifier le médecin",
                        on_click=ExamDetailState.notify_doctor_results_ready,
                        size="2",
                        variant="soft",
                        color_scheme="blue",
                    ),
                    content="Notifier le médecin que les résultats sont prêts",
                ),
            ),
            _mode_toggle(),
            width="100%",
            align="center",
        ),
        # DRAFT banner: shown when exam is still a draft — invite doctor to submit
        rx.cond(
            exam.status == "draft",
            rx.callout(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "Cet examen est en mode brouillon.",
                            size="2",
                            weight="medium",
                        ),
                        rx.text(
                            "Remplissez les informations cliniques, puis cliquez sur «\u00a0Soumettre\u00a0» "
                            "pour envoyer au laboratoire.",
                            size="1",
                            color="var(--gray-9)",
                        ),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.cond(
                            ExamDetailState.is_submitting,
                            rx.spinner(size="2"),
                            rx.icon("send", size=15),
                        ),
                        "Soumettre",
                        on_click=ExamDetailState.submit_exam,
                        disabled=ExamDetailState.is_submitting,
                        color_scheme="blue",
                        size="2",
                    ),
                    width="100%",
                    align="center",
                    spacing="3",
                ),
                icon="pencil",
                color_scheme="gray",
                width="100%",
            ),
            rx.fragment(),
        ),
        width="100%",
        spacing="3",
    )


# ── Section 1: Medical sections ──────────────────────────────────────────────


def _vitals_item(label: str, value: rx.Var, unit: str = "") -> rx.Component:
    return rx.cond(
        value,
        rx.hstack(
            rx.text(label, size="1", color="var(--gray-9)", min_width="80px"),
            rx.text(value, size="1", weight="medium"),
            rx.text(unit, size="1", color="var(--gray-8)") if unit else rx.fragment(),
            spacing="1",
        ),
    )


def _consultation_context_banner(ctx: ConsultationContextDTO) -> rx.Component:
    """Read-only banner showing the shared clinical context from the parent consultation."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("stethoscope", size=14, color="var(--blue-9)"),
                rx.text(
                    "Contexte de consultation du\u00a0",
                    rx.text.strong(ctx.consultation_date),
                    size="2",
                ),
                rx.spacer(),
                rx.tooltip(
                    rx.badge("Vue consultation", color_scheme="blue", variant="soft", size="1"),
                    content="Ce contexte clinique est partagé avec tous les examens de cette consultation.",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.cond(
                ctx.reason_for_visit != "",
                rx.hstack(
                    rx.text("Motif\u00a0:", size="2", weight="medium", color="var(--gray-9)"),
                    rx.text(ctx.reason_for_visit, size="2"),
                    spacing="2",
                ),
            ),
            rx.cond(
                ctx.medical_history != "",
                rx.hstack(
                    rx.text("Antécédents\u00a0:", size="2", weight="medium", color="var(--gray-9)"),
                    rx.text(ctx.medical_history, size="2"),
                    spacing="2",
                ),
            ),
            # Vitals compact row
            rx.hstack(
                _vitals_item("Poids", rx.cond(ctx.weight, ctx.weight.to_string(), ""), "kg"),
                _vitals_item("Taille", rx.cond(ctx.height, ctx.height.to_string(), ""), "cm"),
                _vitals_item("IMC", rx.cond(ctx.bmi, ctx.bmi.to_string(), "")),
                _vitals_item("Tension", rx.cond(ctx.blood_pressure != "", ctx.blood_pressure, "")),
                _vitals_item("FC", rx.cond(ctx.heart_rate, ctx.heart_rate.to_string(), ""), "bpm"),
                _vitals_item("Temp.", rx.cond(ctx.temperature, ctx.temperature.to_string(), ""), "°C"),
                spacing="4",
                wrap="wrap",
            ),
            spacing="2",
            width="100%",
        ),
        background="var(--blue-2)",
        border="1px solid var(--blue-5)",
        width="100%",
        padding="0.75rem 1rem",
    )


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
                rx.icon("save", size=15),
            ),
            rx.cond(
                ExamDetailState.exam.status == "draft",
                "Sauvegarder (brouillon)",
                LanguageState.tr["save"],
            ),
            on_click=ExamDetailState.save_sections,
            disabled=ExamDetailState.is_saving_sections,
            variant=rx.cond(ExamDetailState.exam.status == "draft", "soft", "solid"),
            color_scheme=rx.cond(ExamDetailState.exam.status == "draft", "gray", "blue"),
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
    """In edit mode each row exposes a value input directly. Status is auto-computed."""
    return rx.table.row(
        rx.table.cell(rx.text(row.parameter, size="2", weight="medium")),
        rx.table.cell(rx.text(row.unit, size="2", color="var(--gray-9)")),
        rx.table.cell(
            rx.input(
                value=row.value,
                on_change=lambda v: ExamDetailState.set_lab_row_value(row.id, v),
                placeholder="Valeur...",
                size="2",
                width="100%",
            ),
            padding="0.25rem",
        ),
        rx.table.cell(rx.text(row.reference_range, size="2", color="var(--gray-10)")),
        rx.table.cell(
            rx.cond(
                row.value == "",
                rx.badge("À saisir", color_scheme="orange", variant="soft", size="1"),
                _lab_status_badge(row.status),
            )
        ),
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
        background=rx.cond(row.value == "", "var(--orange-2)", "transparent"),
    )


def _available_param_select() -> rx.Component:
    """Dropdown to quickly select a parameter from the exam type referential."""
    return rx.cond(
        ExamDetailState.available_params,
        rx.vstack(
            rx.text("Sélectionner depuis le référentiel", size="1", color="var(--gray-10)", weight="medium"),
            rx.select.root(
                rx.select.trigger(placeholder="Choisir un paramètre du référentiel...", size="2"),
                rx.select.content(
                    rx.foreach(
                        ExamDetailState.available_params,
                        lambda p: rx.select.item(p.name, value=p.id),
                    ),
                ),
                value=ExamDetailState.new_lab_selected_preset,
                on_change=ExamDetailState.select_available_param,
                size="2",
                width="100%",
            ),
            width="100%",
            spacing="1",
        ),
        rx.fragment(),
    )


def _lab_add_row_form() -> rx.Component:
    return rx.vstack(
        # Row 1: referential parameter selector (full width, only if available)
        _available_param_select(),
        # Row 2: parameter name + unit + value + reference range + add button (status is auto-computed)
        rx.text("Ou saisir manuellement", size="1", color="var(--gray-10)", weight="medium"),
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


def _prescribed_param_row(param: RequestedParamDTO) -> rx.Component:
    """One row for a prescribed lab parameter — shows completion status."""
    return rx.hstack(
        rx.cond(
            param.is_resulted,
            rx.icon("circle-check", size=14, color="var(--green-9)"),
            rx.icon("clock", size=14, color="var(--orange-9)"),
        ),
        rx.text(param.name, size="2", flex="1"),
        rx.cond(
            param.unit != "",
            rx.text(param.unit, size="1", color="var(--gray-9)"),
        ),
        rx.cond(
            param.is_resulted,
            rx.badge("Saisi", color_scheme="green", variant="soft", size="1"),
            rx.badge("En attente", color_scheme="orange", variant="soft", size="1"),
        ),
        spacing="2",
        align="center",
        width="100%",
        padding_y="0.25rem",
    )


def _prescribed_tests_section() -> rx.Component:
    """Section showing which lab tests were requested by the doctor.

    Always shown when exam has an exam type ref (so doctor can add/edit).
    """
    return rx.cond(
        ExamDetailState.available_params,
        _section_card(
            "Tests prescrits par le médecin",
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "Sélectionnez les analyses spécifiques à effectuer pour cet examen.",
                            size="2",
                            color="var(--gray-9)",
                        ),
                        rx.cond(
                            ExamDetailState.requested_params,
                            rx.hstack(
                                rx.icon("flask-conical", size=14, color="var(--blue-9)"),
                                rx.text(
                                    ExamDetailState.requested_params.length().to(str)
                                    + " analyse(s) prescrite(s)",
                                    size="2",
                                    color="var(--blue-9)",
                                    weight="medium",
                                ),
                                spacing="1",
                                align="center",
                            ),
                            rx.text(
                                "Aucune analyse prescrite pour l'instant.",
                                size="2",
                                color="var(--gray-7)",
                                font_style="italic",
                            ),
                        ),
                        spacing="1",
                        flex="1",
                    ),
                    rx.button(
                        rx.icon("list-checks", size=14),
                        "Prescrire les analyses",
                        on_click=ExamDetailState.open_request_params_dialog,
                        variant="soft",
                        color_scheme="blue",
                        size="2",
                    ),
                    width="100%",
                    align="start",
                    spacing="3",
                ),
                rx.cond(
                    ExamDetailState.requested_params,
                    rx.box(
                        rx.foreach(ExamDetailState.requested_params, _prescribed_param_row),
                        width="100%",
                        padding="0.5rem",
                        background="var(--blue-2)",
                        border_radius="6px",
                    ),
                ),
                width="100%",
                spacing="3",
            ),
        ),
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


# ── Request parameters dialog (doctor selects tests for current exam) ─────────

def _request_param_option_row(param: AvailableParamOption) -> rx.Component:
    """One row in the request-parameters dialog: checkbox + parameter name + unit."""
    is_checked = ExamDetailState.request_params_selected_ids.contains(param.id)
    return rx.hstack(
        rx.checkbox(
            checked=is_checked,
            on_change=lambda _: ExamDetailState.toggle_request_param(param.id),
            size="2",
        ),
        rx.vstack(
            rx.text(param.name, size="2", weight="medium"),
            rx.cond(
                param.unit != "",
                rx.text(param.unit, size="1", color="var(--gray-9)"),
            ),
            spacing="0",
        ),
        rx.spacer(),
        rx.cond(
            param.ref_range != "",
            rx.text(param.ref_range, size="1", color="var(--gray-8)"),
        ),
        spacing="3",
        align="center",
        width="100%",
        padding_y="0.25rem",
        cursor="pointer",
        on_click=ExamDetailState.toggle_request_param(param.id),
    )


def _request_params_dialog() -> rx.Component:
    """Modal dialog for doctor to select which parameters to test in this exam."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("list-checks", size=18, color="var(--accent-9)"),
                    rx.text("Analyses à prescrire"),
                    spacing="2",
                    align="center",
                )
            ),
            rx.text(
                "Cochez les analyses spécifiques que le laboratoire doit effectuer pour cet examen.",
                size="2",
                color="var(--gray-9)",
                margin_bottom="0.75rem",
            ),
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(ExamDetailState.available_params, _request_param_option_row),
                    spacing="1",
                    width="100%",
                ),
                max_height="360px",
                width="100%",
            ),
            rx.cond(
                ExamDetailState.request_params_selected_ids.length() > 0,
                rx.callout(
                    ExamDetailState.request_params_selected_ids.length().to(str)
                    + " analyse(s) sélectionnée(s)",
                    icon="flask-conical",
                    color_scheme="blue",
                    size="1",
                    margin_top="0.75rem",
                ),
                rx.fragment(),
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Annuler",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ExamDetailState.close_request_params_dialog,
                    ),
                ),
                rx.button(
                    rx.cond(
                        ExamDetailState.is_saving_requested_params,
                        rx.spinner(size="2"),
                        rx.icon("save", size=15),
                    ),
                    "Enregistrer",
                    on_click=ExamDetailState.save_requested_params,
                    color_scheme="blue",
                    disabled=ExamDetailState.is_saving_requested_params,
                ),
                spacing="2",
                justify="end",
                margin_top="1rem",
                width="100%",
            ),
            max_width="520px",
        ),
        open=ExamDetailState.request_params_form_open,
        on_open_change=lambda _: ExamDetailState.close_request_params_dialog(),
    )


# ── Prescribe follow-up exams ─────────────────────────────────────────────────

def _prescribe_param_row(opt_id: str):
    """Factory — returns a foreach-compatible renderer for one param checkbox row."""
    def _render(p: FollowUpParamOption) -> rx.Component:
        return rx.hstack(
            rx.checkbox(
                checked=p.is_selected,
                on_change=lambda _: ExamDetailState.toggle_prescribe_param(opt_id, p.id),
                size="1",
            ),
            rx.text(p.name, size="2", flex="1"),
            rx.cond(
                p.unit != "",
                rx.text(p.unit, size="1", color="var(--gray-8)", min_width="40px"),
                rx.fragment(),
            ),
            rx.cond(
                p.ref_range != "",
                rx.text(p.ref_range, size="1", color="var(--gray-8)", min_width="60px"),
                rx.fragment(),
            ),
            spacing="2",
            align="center",
            padding_y="0.15rem",
            padding_left="1rem",
            cursor="pointer",
            on_click=ExamDetailState.toggle_prescribe_param(opt_id, p.id),
            width="100%",
        )
    return _render


def _prescribe_exam_option_row(opt: FollowUpExamOption) -> rx.Component:
    """One row in the prescribe dialog: checkbox + exam type name + expandable params."""
    is_checked = ExamDetailState.prescribe_selected_ids.contains(opt.id)
    return rx.vstack(
        rx.hstack(
            rx.checkbox(
                checked=is_checked,
                on_change=lambda _: ExamDetailState.toggle_prescribe_exam(opt.id),
                size="2",
            ),
            rx.vstack(
                rx.text(opt.name, size="2", weight="medium"),
                rx.text(
                    opt.category_label + " · " + opt.params.length().to(str) + " paramètre(s)",
                    size="1", color="var(--gray-9)",
                ),
                spacing="0",
                flex="1",
                align_items="start",
            ),
            rx.cond(
                is_checked & opt.params,
                rx.icon_button(
                    rx.cond(opt.params_expanded, rx.icon("chevron-up", size=13), rx.icon("chevron-down", size=13)),
                    variant="ghost",
                    size="1",
                    color_scheme="gray",
                    on_click=ExamDetailState.toggle_prescribe_params_expanded(opt.id),
                ),
                rx.fragment(),
            ),
            spacing="3",
            align="center",
            width="100%",
            padding_y="0.35rem",
            cursor="pointer",
            on_click=ExamDetailState.toggle_prescribe_exam(opt.id),
        ),
        rx.cond(
            is_checked & opt.params_expanded & opt.params,
            rx.vstack(
                rx.hstack(
                    rx.text("Tout sélectionner", size="1", color="var(--accent-9)", cursor="pointer",
                            on_click=ExamDetailState.select_all_prescribe_params(opt.id)),
                    width="100%",
                    padding_left="1rem",
                ),
                rx.foreach(opt.params, _prescribe_param_row(opt.id)),
                spacing="0",
                width="100%",
                background="var(--gray-2)",
                border_radius="6px",
                padding="0.5rem",
            ),
            rx.fragment(),
        ),
        spacing="0",
        width="100%",
    )


def _prescribe_dialog() -> rx.Component:
    """Modal dialog for doctor to prescribe follow-up exams with parameter selection."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("clipboard-plus", size=18, color="var(--accent-9)"),
                    rx.text("Prescrire des examens de suivi"),
                    spacing="2",
                    align="center",
                )
            ),
            rx.text(
                "Sélectionnez les examens et les tests spécifiques à prescrire.",
                size="2",
                color="var(--gray-9)",
                margin_bottom="0.75rem",
            ),
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(ExamDetailState.prescribe_exam_options, _prescribe_exam_option_row),
                    spacing="1",
                    width="100%",
                ),
                max_height="400px",
                width="100%",
            ),
            rx.cond(
                ExamDetailState.prescribe_selected_ids.length() > 0,
                rx.callout(
                    ExamDetailState.prescribe_selected_ids.length().to(str)
                    + " examen(s) sélectionné(s) — cochez les tests souhaités",
                    icon="check",
                    color_scheme="blue",
                    size="1",
                    margin_top="0.75rem",
                ),
                rx.fragment(),
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Annuler",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ExamDetailState.close_prescribe_dialog,
                    ),
                ),
                rx.button(
                    rx.cond(
                        ExamDetailState.is_saving_prescription,
                        rx.spinner(size="2"),
                        rx.icon("save", size=15),
                    ),
                    "Enregistrer l'ordonnance",
                    on_click=ExamDetailState.save_prescribed_exams,
                    color_scheme="blue",
                    disabled=ExamDetailState.is_saving_prescription,
                ),
                spacing="2",
                justify="end",
                margin_top="1rem",
                width="100%",
            ),
            max_width="560px",
        ),
        open=ExamDetailState.prescribe_form_open,
        on_open_change=lambda _: ExamDetailState.close_prescribe_dialog(),
    )


def _followup_exam_row(row: FollowUpExamRowDTO) -> rx.Component:
    """One clickable row for a prescribed follow-up exam."""
    status_color = rx.cond(
        row.status == "draft",
        "var(--amber-9)",
        rx.cond(row.status == "pending", "var(--blue-9)", "var(--green-9)"),
    )
    status_label = rx.cond(
        row.status == "draft",
        "En attente",
        rx.cond(row.status == "pending", "Résultats en cours", "Complété"),
    )
    return rx.link(
        rx.hstack(
            rx.icon("flask-conical", size=14, color="var(--blue-9)"),
            rx.text(row.exam_type_label, size="2", weight="medium", flex="1"),
            rx.badge(status_label, color_scheme=rx.cond(
                row.status == "draft", "amber",
                rx.cond(row.status == "pending", "blue", "green"),
            ), size="1"),
            rx.icon("chevron-right", size=12, color="var(--gray-8)"),
            spacing="2",
            align="center",
            width="100%",
            padding="0.5rem 0.75rem",
            border_radius="6px",
            background="var(--gray-2)",
            _hover={"background": "var(--blue-2)", "cursor": "pointer"},
        ),
        href=row.link_url,
        text_decoration="none",
        width="100%",
    )


def _followup_exams_section(exam: ExamDetailDTO) -> rx.Component:
    """Section showing prescribed follow-up exams and the 'Prescrire' button (edit mode)."""
    return _section_card(
        "Examens de suivi prescrits",
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Le médecin peut prescrire des examens complémentaires au patient.",
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.cond(
                        ExamDetailState.follow_up_exams.length() > 0,
                        rx.vstack(
                            rx.hstack(
                                rx.icon("check-check", size=14, color="var(--green-9)"),
                                rx.text(
                                    ExamDetailState.follow_up_exams.length().to(str)
                                    + " examen(s) prescrit(s)",
                                    size="2",
                                    color="var(--green-9)",
                                    weight="medium",
                                ),
                                spacing="1",
                                align="center",
                            ),
                            rx.vstack(
                                rx.foreach(
                                    ExamDetailState.follow_up_exams,
                                    _followup_exam_row,
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        rx.cond(
                            exam.prescribed_exam_ref_ids.length() > 0,
                            # Prescriptions saved but no follow-up records yet (legacy data)
                            rx.hstack(
                                rx.icon("check-check", size=14, color="var(--green-9)"),
                                rx.text(
                                    exam.prescribed_exam_ref_ids.length().to(str)
                                    + " examen(s) prescrit(s)",
                                    size="2",
                                    color="var(--green-9)",
                                    weight="medium",
                                ),
                                spacing="1",
                                align="center",
                            ),
                            rx.text(
                                "Aucun examen prescrit pour l'instant.",
                                size="2",
                                color="var(--gray-7)",
                                font_style="italic",
                            ),
                        ),
                    ),
                    spacing="2",
                    flex="1",
                ),
                rx.button(
                    rx.icon("clipboard-plus", size=14),
                    "Prescrire des examens",
                    on_click=ExamDetailState.open_prescribe_dialog,
                    variant="soft",
                    color_scheme="blue",
                    size="2",
                ),
                width="100%",
                align="start",
                spacing="3",
            ),
            width="100%",
            spacing="2",
        ),
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def exam_detail_page() -> rx.Component:
    """Exam detail page: Medical sections, Doctor's Interpretation, Medical Documents."""
    return main_component(
        page_layout(
            _prescribe_dialog(),
            _request_params_dialog(),
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
                    rx.cond(
                        ExamDetailState.exam.is_follow_up,
                        # ── Simplified view: follow-up prescribed exam (lab tech fills results) ──
                        rx.vstack(
                            _exam_header(ExamDetailState.exam),
                            _prescribed_tests_section(),
                            _lab_results_section(),
                            _documents_section(),
                            _section_card(
                                "Interprétation médicale",
                                rx.vstack(
                                    rx.text_area(
                                        placeholder="Interprétation et commentaires du médecin...",
                                        value=ExamDetailState.form_conclusion,
                                        on_change=ExamDetailState.set_form_conclusion,
                                        rows="4",
                                        width="100%",
                                    ),
                                    rx.button(
                                        rx.icon("save", size=15),
                                        "Sauvegarder",
                                        on_click=ExamDetailState.save_sections,
                                        disabled=ExamDetailState.is_saving_sections,
                                        size="2",
                                    ),
                                    spacing="3",
                                    width="100%",
                                ),
                            ),
                            width="100%",
                            spacing="6",
                        ),
                        # ── Full view: standard exam detail page ──
                        rx.vstack(
                            _exam_header(ExamDetailState.exam),
                            # When exam belongs to a consultation: show shared context banner
                            # and hide the per-exam medical sections (they live on the consultation)
                            rx.cond(
                                ExamDetailState.consultation_context,
                                _consultation_context_banner(ExamDetailState.consultation_context),
                                rx.fragment(),
                            ),
                            rx.cond(
                                ~ExamDetailState.exam.consultation_id,
                                rx.vstack(
                                    _reasons_and_history_section(),
                                    _physical_exam_section(),
                                    width="100%",
                                    spacing="6",
                                ),
                                rx.fragment(),
                            ),
                            _prescribed_tests_section(),
                            _lab_results_section(),
                            rx.cond(
                                ~ExamDetailState.exam.consultation_id,
                                _conclusion_section(),
                                rx.fragment(),
                            ),
                            _followup_exams_section(ExamDetailState.exam),
                            _documents_section(),
                            width="100%",
                            spacing="6",
                        ),
                    ),
                    rx.center(
                        rx.text(LanguageState.tr["exam_not_found"], color="var(--gray-9)"), padding="3rem"
                    ),
                ),
            ),
        )
    )
