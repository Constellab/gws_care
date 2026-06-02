"""Exam create form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from .exam_form_state import ExamFormState, ExamParamOption, StagedFile

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


def _field(label: str, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _staged_file_row(sf: StagedFile) -> rx.Component:
    """One row in the staged-file list."""
    return rx.hstack(
        rx.icon("file", size=14, color="var(--gray-9)", flex_shrink="0"),
        rx.text(
            sf.original_name,
            size="2",
            flex="1",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Set type…", size="1"),
            rx.select.content(
                *[rx.select.item(label, value=value) for value, label in _DOC_TYPE_OPTIONS],
            ),
            value=sf.document_type,
            on_change=lambda v: ExamFormState.set_staged_file_document_type(
                sf.stored_filename, v
            ),
            size="1",
        ),
        rx.tooltip(
            rx.icon_button(
                rx.icon("x", size=12),
                variant="ghost",
                size="1",
                color_scheme="red",
                on_click=lambda: ExamFormState.remove_staged_file(sf.stored_filename),
            ),
            content="Remove file",
        ),
        padding_x="0.5rem",
        padding_y="0.25rem",
        align="center",
        spacing="2",
        border="1px solid var(--gray-4)",
        border_radius="6px",
        width="100%",
    )


def _upload_section() -> rx.Component:
    """Drag-and-drop / click-to-select file upload area."""
    return rx.vstack(
        # Drop zone
        rx.upload(
            rx.vstack(
                rx.cond(
                    ExamFormState.is_uploading,
                    rx.hstack(
                        rx.spinner(size="2"),
                        rx.text("Uploading…", size="2", color="var(--gray-9)"),
                        spacing="2",
                        align="center",
                    ),
                    rx.vstack(
                        rx.icon("upload", size=20, color="var(--gray-8)"),
                        rx.text("Drop files here or click to browse", size="2", color="var(--gray-8)"),
                        rx.text(
                            "Images, PDF, Word, Excel and more",
                            size="1",
                            color="var(--gray-6)",
                        ),
                        align="center",
                        spacing="1",
                    ),
                ),
                align="center",
                justify="center",
                width="100%",
                height="80px",
            ),
            id="exam_file_upload",
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
            on_drop=ExamFormState.handle_file_upload(
                rx.upload_files(upload_id="exam_file_upload")
            ),
            border="2px dashed var(--gray-5)",
            border_radius="8px",
            padding="1rem",
            width="100%",
            cursor="pointer",
            _hover={"border_color": "var(--accent-8)", "background": "var(--gray-1)"},
        ),
        # Staged files list
        rx.cond(
            ExamFormState.staged_files,
            rx.vstack(
                rx.foreach(ExamFormState.staged_files, _staged_file_row),
                width="100%",
                spacing="1",
            ),
        ),
        width="100%",
        spacing="2",
    )


def _param_checkbox_row(param: ExamParamOption) -> rx.Component:
    """One checkbox row for a requested lab parameter."""
    return rx.hstack(
        rx.checkbox(
            checked=ExamFormState.selected_param_ids.contains(param.id),
            on_change=lambda _: ExamFormState.toggle_param_selection(param.id),
            size="2",
        ),
        rx.text(param.name, size="2", flex="1"),
        rx.cond(
            param.unit != "",
            rx.text(param.unit, size="1", color="var(--gray-9)"),
        ),
        spacing="2",
        align="center",
        width="100%",
    )


def _params_section() -> rx.Component:
    """Parameter selection section — shown only when the selected exam type has ExamParameters."""
    return rx.cond(
        ExamFormState.available_exam_params,
        rx.vstack(
            rx.hstack(
                rx.icon("flask-conical", size=14, color="var(--blue-9)"),
                rx.text("Analyses à prescrire", size="2", weight="medium"),
                spacing="2",
                align="center",
            ),
            rx.box(
                rx.foreach(ExamFormState.available_exam_params, _param_checkbox_row),
                padding="0.75rem",
                background="var(--blue-2)",
                border_radius="8px",
                width="100%",
            ),
            rx.text(
                rx.icon("info", size=11, display="inline"),
                " Le laborantin sera notifié et recevra la liste des analyses à effectuer.",
                size="1",
                color="var(--gray-8)",
            ),
            width="100%",
            spacing="2",
        ),
    )


def _form_fields() -> rx.Component:
    return rx.vstack(
        rx.grid(
            _field(
                "Date *",
                rx.input(
                    value=ExamFormState.form_exam_date,
                    on_change=ExamFormState.set_form_exam_date,
                    type="date",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "Type d'examen *",
                rx.select.root(
                    rx.select.trigger(width="100%", placeholder="Sélectionner un examen..."),
                    rx.select.content(
                        rx.foreach(
                            ExamFormState.exam_type_options,
                            lambda o: rx.select.item(
                                o.name + " (" + o.category_label + ")",
                                value=o.id,
                            ),
                        ),
                    ),
                    value=ExamFormState.form_exam_type,
                    on_change=ExamFormState.set_form_exam_type,
                    size="2",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        _field(
            "Motif",
            rx.text_area(
                value=ExamFormState.form_reason_for_visit,
                on_change=ExamFormState.set_form_reason_for_visit,
                placeholder="Motif de la consultation...",
                size="2",
                width="100%",
                rows="2",
            ),
        ),
        _params_section(),
        rx.cond(
            ExamFormState.load_error != "",
            rx.callout(
                ExamFormState.load_error,
                icon="triangle-alert",
                color_scheme="red",
                size="1",
            ),
            rx.fragment(),
        ),
        _field("Pièces jointes", _upload_section()),
        rx.cond(
            ExamFormState.form_error != "",
            rx.callout(
                ExamFormState.form_error,
                icon="triangle-alert",
                color_scheme="red",
                size="1",
            ),
            rx.fragment(),
        ),
        rx.text(
            rx.icon("info", size=12, display="inline"),
            " Les données cliniques (poids, tension, résultats…) se saisissent depuis la fiche de l'examen.",
            size="1",
            color="var(--gray-8)",
        ),
        width="100%",
        spacing="4",
    )


def exam_form_dialog() -> rx.Component:
    """Render the create exam dialog (must be placed in the component tree)."""
    return form_dialog_component(
        state=ExamFormState,
        title="New Exam",
        form_content=_form_fields(),
    )
