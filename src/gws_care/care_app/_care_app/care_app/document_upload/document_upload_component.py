"""Document upload / annotation page."""

import reflex as rx
from gws_reflex_main import main_component, resource_select_button

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..common.patient_picker_component import (
    patient_picker_button,
    patient_picker_dialog,
)
from .document_upload_state import (
    DOC_TYPE_OPTIONS,
    DocumentAnnotationItemDTO,
    DocumentUploadState,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _doc_type_badge(doc_type: str) -> rx.Component:
    return rx.match(
        doc_type,
        ("prescription", rx.badge(LanguageState.tr["upload_doc_type_prescription"], color_scheme="blue", size="1")),
        ("medical_certificate", rx.badge(LanguageState.tr["upload_doc_type_medical_certificate"], color_scheme="green", size="1")),
        ("medical_report", rx.badge(LanguageState.tr["upload_doc_type_medical_report"], color_scheme="purple", size="1")),
        ("medical_analysis", rx.badge(LanguageState.tr["upload_doc_type_medical_analysis"], color_scheme="orange", size="1")),
        ("letter", rx.badge(LanguageState.tr["upload_doc_type_letter"], color_scheme="gray", size="1")),
        ("xray", rx.badge(LanguageState.tr["upload_doc_type_xray"], color_scheme="cyan", size="1")),
        ("ct_scan", rx.badge(LanguageState.tr["upload_doc_type_ct_scan"], color_scheme="cyan", size="1")),
        ("mri", rx.badge(LanguageState.tr["upload_doc_type_mri"], color_scheme="cyan", size="1")),
        ("ultrasound", rx.badge(LanguageState.tr["upload_doc_type_ultrasound"], color_scheme="cyan", size="1")),
        rx.cond(
            doc_type != "",
            rx.badge(doc_type, color_scheme="gray", size="1"),
            rx.text("—", size="1", color="var(--gray-7)"),
        ),
    )


def _status_badge(item: DocumentAnnotationItemDTO) -> rx.Component:
    return rx.cond(
        item.is_saved,
        rx.badge("Saved", color_scheme="green", variant="soft", size="1"),
        rx.badge("Pending", color_scheme="orange", variant="soft", size="1"),
    )


# ── Import section ────────────────────────────────────────────────────────────

def _upload_card() -> rx.Component:
    """Browser upload card — drag-and-drop or click to select."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("upload-cloud", size=20, color="var(--accent-9)"),
                rx.text(LanguageState.tr["upload_from_computer"], size="3", weight="medium"),
                spacing="2",
                align="center",
            ),
            rx.upload(
                rx.vstack(
                    rx.cond(
                        DocumentUploadState.is_uploading,
                        rx.hstack(
                            rx.spinner(size="2"),
                            rx.text(LanguageState.tr["upload_analyzing"], size="2", color="var(--gray-9)"),
                            spacing="2",
                            align="center",
                        ),
                        rx.vstack(
                            rx.icon("file-up", size=24, color="var(--gray-7)"),
                            rx.text(LanguageState.tr["upload_drop_hint"], size="2", color="var(--gray-8)"),
                            rx.text("PDF, PNG, JPG, TIFF…", size="1", color="var(--gray-6)"),
                            align="center",
                            spacing="1",
                        ),
                    ),
                    align="center",
                    justify="center",
                    width="100%",
                    min_height="90px",
                ),
                id="doc_file_upload",
                multiple=True,
                accept={
                    "application/pdf": [".pdf"],
                    "image/png": [".png"],
                    "image/jpeg": [".jpg", ".jpeg"],
                    "image/bmp": [".bmp"],
                    "image/tiff": [".tiff"],
                    "image/webp": [".webp"],
                },
                on_drop=DocumentUploadState.handle_upload(
                    rx.upload_files(upload_id="doc_file_upload")
                ),
                border="2px dashed var(--gray-5)",
                border_radius="8px",
                padding="1rem",
                width="100%",
                cursor="pointer",
                _hover={"border_color": "var(--accent-8)", "background": "var(--gray-1)"},
                disabled=DocumentUploadState.is_uploading,
            ),
            rx.cond(
                DocumentUploadState.upload_error != "",
                rx.callout(
                    DocumentUploadState.upload_error,
                    icon="triangle-alert",
                    color_scheme="red",
                    size="1",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def _folder_import_card() -> rx.Component:
    """Lab folder import card — opens the resource picker filtered to Folders."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("folder-open", size=20, color="var(--accent-9)"),
                rx.text(LanguageState.tr["upload_from_folder"], size="3", weight="medium"),
                spacing="2",
                align="center",
            ),
            rx.text(
                LanguageState.tr["upload_from_folder_desc"],
                size="2",
                color="var(--gray-9)",
            ),
            resource_select_button(DocumentUploadState),
            # Progress / error feedback
            rx.cond(
                DocumentUploadState.is_importing,
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text(DocumentUploadState.import_progress, size="2", color="var(--gray-9)"),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    DocumentUploadState.import_error != "",
                    rx.callout(
                        DocumentUploadState.import_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                    rx.cond(
                        DocumentUploadState.import_progress != "",
                        rx.hstack(
                            rx.icon("circle-check", size=14, color="var(--green-9)"),
                            rx.text(DocumentUploadState.import_progress, size="2", color="var(--green-9)"),
                            spacing="2",
                            align="center",
                        ),
                    ),
                ),
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


# ── Annotation table ──────────────────────────────────────────────────────────

def _doc_row(item: DocumentAnnotationItemDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                item.original_name, size="2", weight="medium",
                overflow="hidden", text_overflow="ellipsis",
                white_space="nowrap", max_width="220px",
            ),
        ),
        rx.table.cell(_doc_type_badge(item.detected_type)),
        rx.table.cell(
            rx.cond(
                item.detected_date != "",
                rx.text(item.detected_date, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                item.suggested_patient_label != "",
                rx.text(item.suggested_patient_label, size="2"),
                rx.cond(
                    item.detected_patient_name != "",
                    rx.text(item.detected_patient_name, size="2", color="var(--orange-9)"),
                    rx.text("—", size="2", color="var(--gray-7)"),
                ),
            )
        ),
        rx.table.cell(_status_badge(item)),
        rx.table.cell(
            rx.cond(
                item.save_error != "",
                rx.tooltip(
                    rx.icon("triangle-alert", size=14, color="var(--red-9)"),
                    content=item.save_error,
                ),
            )
        ),
        rx.table.cell(
            rx.button(
                rx.icon("pencil", size=14),
                LanguageState.tr["edit_btn"],
                variant="ghost",
                size="1",
                on_click=lambda: DocumentUploadState.open_annotation_dialog(item.index),
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _doc_list() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell(rx.text("File", size="2")),
                rx.table.column_header_cell(rx.text(LanguageState.tr["col_type"], size="2")),
                rx.table.column_header_cell(rx.text(LanguageState.tr["col_date"], size="2")),
                rx.table.column_header_cell(rx.text(LanguageState.tr["col_patient"], size="2")),
                rx.table.column_header_cell(rx.text(LanguageState.tr["col_status"], size="2")),
                rx.table.column_header_cell(""),
                rx.table.column_header_cell(""),
            )
        ),
        rx.table.body(
            rx.foreach(DocumentUploadState.annotation_items, _doc_row)
        ),
        width="100%",
        variant="surface",
    )


# ── Annotation dialog ─────────────────────────────────────────────────────────

def _annotation_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["upload_doc_page_title"]),
            rx.vstack(
                # Patient
                rx.vstack(
                    rx.text(LanguageState.tr["upload_field_patient"], size="2", weight="medium"),
                    patient_picker_button(DocumentUploadState),
                    spacing="1",
                    align_items="start",
                    width="100%",
                ),
                # Document type
                rx.vstack(
                    rx.text(LanguageState.tr["upload_field_doc_type"], size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder=LanguageState.tr["upload_field_doc_type"],
                            width="220px",
                        ),
                        rx.select.content(
                            *[
                                rx.select.item(LanguageState.tr[label_key], value=value)
                                for value, label_key in DOC_TYPE_OPTIONS
                            ],
                        ),
                        value=DocumentUploadState.form_doc_type,
                        on_change=DocumentUploadState.set_form_doc_type,
                        size="2",
                    ),
                    spacing="1",
                    align_items="start",
                    width="100%",
                ),
                # Date
                rx.vstack(
                    rx.text(LanguageState.tr["upload_field_date"], size="2", weight="medium"),
                    rx.input(
                        type="date",
                        value=DocumentUploadState.form_date,
                        on_change=DocumentUploadState.set_form_date,
                        size="2",
                        width="180px",
                    ),
                    spacing="1",
                    align_items="start",
                    width="100%",
                ),
                # Description
                rx.vstack(
                    rx.text(LanguageState.tr["upload_field_description"], size="2", weight="medium"),
                    rx.input(
                        value=DocumentUploadState.form_description,
                        on_change=DocumentUploadState.set_form_description,
                        placeholder=LanguageState.tr["upload_field_description"],
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    align_items="start",
                    width="100%",
                ),
                # Notes
                rx.vstack(
                    rx.text(LanguageState.tr["upload_field_notes"], size="2", weight="medium"),
                    rx.text_area(
                        value=DocumentUploadState.form_notes,
                        on_change=DocumentUploadState.set_form_notes,
                        placeholder=LanguageState.tr["upload_field_notes"],
                        size="2",
                        width="100%",
                        rows="3",
                    ),
                    spacing="1",
                    align_items="start",
                    width="100%",
                ),
                # Footer
                rx.hstack(
                    rx.button(
                        rx.cond(
                            DocumentUploadState.is_saving,
                            rx.hstack(rx.spinner(size="2"), rx.text(LanguageState.tr["upload_saving"]), spacing="2", align="center"),
                            rx.hstack(rx.icon("save", size=15), rx.text(LanguageState.tr["upload_save_btn"]), spacing="2", align="center"),
                        ),
                        on_click=DocumentUploadState.save_document,
                        disabled=DocumentUploadState.is_saving,
                        size="2",
                    ),
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        on_click=DocumentUploadState.close_annotation_dialog,
                        variant="outline",
                        color_scheme="gray",
                        size="2",
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            # Nested picker dialog — must be inside dialog.content so Radix focus trap allows interaction
            patient_picker_dialog(DocumentUploadState),
            on_interact_outside=DocumentUploadState.close_annotation_dialog,
            on_escape_key_down=DocumentUploadState.close_annotation_dialog,
            max_width="520px",
        ),
        open=DocumentUploadState.annotation_dialog_open,
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def document_upload_page() -> rx.Component:
    return main_component(
        page_layout(
            # Header
            rx.hstack(
                rx.button(
                    rx.icon("arrow-left", size=16),
                    LanguageState.tr["btn_back"],
                    on_click=DocumentUploadState.go_back,
                    variant="ghost",
                    size="2",
                ),
                rx.spacer(),
                width="100%",
                align="center",
            ),
            rx.vstack(
                rx.heading(LanguageState.tr["upload_doc_page_title"], size="6"),
                rx.text(LanguageState.tr["upload_doc_page_desc"], size="2", color="var(--gray-9)"),
                spacing="1",
            ),
            # Import section — two cards side by side
            rx.grid(
                _upload_card(),
                _folder_import_card(),
                columns="2",
                spacing="4",
                width="100%",
            ),
            # Annotation table (shown only when documents are loaded)
            rx.cond(
                DocumentUploadState.annotation_items.length() > 0,
                rx.vstack(
                    rx.separator(width="100%"),
                    _doc_list(),
                    spacing="3",
                    width="100%",
                ),
            ),
            # Dialogs
            _annotation_dialog(),
        )
    )
