"""Exam create form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from .exam_form_state import ExamFormState, StagedFile

_EXAM_TYPE_OPTIONS = [
    ("biology", "Biology"),
    ("radiology", "Radiology"),
    ("ophthalmology", "Ophthalmology"),
    ("orl", "ORL"),
    ("ecg", "ECG"),
    ("spirometry", "Spirometry"),
    ("clinical", "Clinical Exam"),
    ("hormones", "Hormones"),
    ("hematology", "Hematology"),
    ("bacteriology", "Bacteriology"),
    ("parasitology", "Parasitology"),
    ("drug_test", "Drug Test"),
    ("immunology", "Immunology"),
    ("hepatic_markers", "Hepatic Markers"),
    ("other", "Other"),
]

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


def _form_fields() -> rx.Component:
    return rx.vstack(
        rx.grid(
            _field(
                "Exam Date *",
                rx.input(
                    value=ExamFormState.form_exam_date,
                    on_change=ExamFormState.set_form_exam_date,
                    type="date",
                    size="2",
                    width="100%",
                ),
            ),
            _field(
                "Exam Type *",
                rx.select.root(
                    rx.select.trigger(width="100%"),
                    rx.select.content(
                        *[rx.select.item(label, value=value) for value, label in _EXAM_TYPE_OPTIONS],
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
            "Reason for visit",
            rx.text_area(
                value=ExamFormState.form_reason_for_visit,
                on_change=ExamFormState.set_form_reason_for_visit,
                placeholder="Reason for visit...",
                size="2",
                width="100%",
                rows="2",
            ),
        ),
        _field(
            "Medical history",
            rx.text_area(
                value=ExamFormState.form_medical_history,
                on_change=ExamFormState.set_form_medical_history,
                placeholder="Relevant medical history...",
                size="2",
                width="100%",
                rows="3",
            ),
        ),
        rx.vstack(
            rx.text("Physical examination", size="2", weight="medium"),
            rx.grid(
                _field(
                    "Weight (kg)",
                    rx.input(
                        value=ExamFormState.form_weight,
                        on_change=ExamFormState.set_form_weight,
                        placeholder="e.g. 70",
                        type="number",
                        size="2",
                        width="100%",
                    ),
                ),
                _field(
                    "Height (cm)",
                    rx.input(
                        value=ExamFormState.form_height,
                        on_change=ExamFormState.set_form_height,
                        placeholder="e.g. 175",
                        type="number",
                        size="2",
                        width="100%",
                    ),
                ),
                _field(
                    "BMI",
                    rx.input(
                        value=ExamFormState.form_bmi,
                        on_change=ExamFormState.set_form_bmi,
                        placeholder="e.g. 22.9",
                        type="number",
                        size="2",
                        width="100%",
                    ),
                ),
                _field(
                    "Blood pressure",
                    rx.input(
                        value=ExamFormState.form_blood_pressure,
                        on_change=ExamFormState.set_form_blood_pressure,
                        placeholder="e.g. 120/80",
                        size="2",
                        width="100%",
                    ),
                ),
                _field(
                    "Heart rate (bpm)",
                    rx.input(
                        value=ExamFormState.form_heart_rate,
                        on_change=ExamFormState.set_form_heart_rate,
                        placeholder="e.g. 72",
                        type="number",
                        size="2",
                        width="100%",
                    ),
                ),
                _field(
                    "Temperature (°C)",
                    rx.input(
                        value=ExamFormState.form_temperature,
                        on_change=ExamFormState.set_form_temperature,
                        placeholder="e.g. 37.0",
                        type="number",
                        size="2",
                        width="100%",
                    ),
                ),
                columns="3",
                spacing="3",
                width="100%",
            ),
            width="100%",
            spacing="2",
        ),
        _field(
            "Conclusion and recommendations",
            rx.text_area(
                value=ExamFormState.form_conclusion,
                on_change=ExamFormState.set_form_conclusion,
                placeholder="Conclusion and recommendations...",
                size="2",
                width="100%",
                rows="3",
            ),
        ),
        _field("Attachments", _upload_section()),
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
