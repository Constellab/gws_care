"""Uploaded document detail page (/document/[doc_id])."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..common.patient_picker_component import patient_picker_button, patient_picker_dialog
from ..document_upload.document_upload_state import DOC_TYPE_OPTIONS
from .uploaded_document_detail_state import UploadedDocumentDetailState


def _info_row(label: str, value: rx.Component) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="2", weight="medium", color="var(--gray-9)", min_width="180px", flex_shrink="0"),
        value,
        spacing="4",
        align="start",
        padding_y="0.3rem",
        width="100%",
    )


def _edit_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["upload_doc_page_title"]),
            rx.vstack(
                # Patient
                rx.vstack(
                    rx.text(LanguageState.tr["upload_field_patient"], size="2", weight="medium"),
                    patient_picker_button(UploadedDocumentDetailState),
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
                        value=UploadedDocumentDetailState.edit_form_doc_type,
                        on_change=UploadedDocumentDetailState.set_edit_form_doc_type,
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
                        value=UploadedDocumentDetailState.edit_form_date,
                        on_change=UploadedDocumentDetailState.set_edit_form_date,
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
                        value=UploadedDocumentDetailState.edit_form_description,
                        on_change=UploadedDocumentDetailState.set_edit_form_description,
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
                        value=UploadedDocumentDetailState.edit_form_notes,
                        on_change=UploadedDocumentDetailState.set_edit_form_notes,
                        placeholder=LanguageState.tr["upload_field_notes"],
                        size="2",
                        width="100%",
                        rows="3",
                    ),
                    spacing="1",
                    align_items="start",
                    width="100%",
                ),
                # Error
                rx.cond(
                    UploadedDocumentDetailState.edit_error != "",
                    rx.callout(
                        UploadedDocumentDetailState.edit_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                # Footer
                rx.hstack(
                    rx.button(
                        rx.cond(
                            UploadedDocumentDetailState.edit_is_saving,
                            rx.hstack(rx.spinner(size="2"), rx.text(LanguageState.tr["upload_saving"]), spacing="2", align="center"),
                            rx.hstack(rx.icon("save", size=15), rx.text(LanguageState.tr["upload_save_btn"]), spacing="2", align="center"),
                        ),
                        on_click=UploadedDocumentDetailState.save_edit,
                        disabled=UploadedDocumentDetailState.edit_is_saving,
                        size="2",
                    ),
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        on_click=UploadedDocumentDetailState.close_edit,
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
            # Nested picker dialog inside dialog.content so Radix focus trap allows interaction
            patient_picker_dialog(UploadedDocumentDetailState),
            on_interact_outside=UploadedDocumentDetailState.close_edit,
            on_escape_key_down=UploadedDocumentDetailState.close_edit,
            max_width="520px",
        ),
        open=UploadedDocumentDetailState.edit_open,
    )


def uploaded_document_detail_page() -> rx.Component:
    return main_component(
        page_layout(
            # ── Header ──────────────────────────────────────────────────────
            rx.hstack(
                rx.icon_button(
                    rx.icon("arrow-left", size=16),
                    on_click=UploadedDocumentDetailState.go_back,
                    variant="ghost",
                    size="2",
                ),
                rx.vstack(
                    rx.heading(
                        rx.cond(
                            UploadedDocumentDetailState.original_name != "",
                            UploadedDocumentDetailState.original_name,
                            "Document importé",
                        ),
                        size="5",
                    ),
                    rx.cond(
                        UploadedDocumentDetailState.patient_name != "",
                        rx.text(
                            UploadedDocumentDetailState.patient_name,
                            size="2",
                            color="var(--gray-9)",
                        ),
                    ),
                    spacing="0",
                ),
                rx.spacer(),
                # Action buttons
                rx.hstack(
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("pencil", size=16),
                            on_click=UploadedDocumentDetailState.open_edit,
                            variant="outline",
                            size="2",
                        ),
                        content="Modifier",
                    ),
                    rx.cond(
                        UploadedDocumentDetailState.has_file,
                        rx.hstack(
                            rx.tooltip(
                                rx.icon_button(
                                    rx.icon("eye", size=16),
                                    on_click=UploadedDocumentDetailState.open_file,
                                    variant="outline",
                                    size="2",
                                ),
                                content=LanguageState.tr["view_pdf_btn"],
                            ),
                            rx.tooltip(
                                rx.icon_button(
                                    rx.icon("download", size=16),
                                    on_click=UploadedDocumentDetailState.open_file,
                                    variant="outline",
                                    size="2",
                                ),
                                content=LanguageState.tr["download_pdf_btn"],
                            ),
                            spacing="2",
                        ),
                    ),
                    spacing="2",
                ),
                width="100%",
                align="center",
                padding_bottom="1rem",
            ),

            # ── Error ────────────────────────────────────────────────────────
            rx.cond(
                UploadedDocumentDetailState.error_message != "",
                rx.callout(
                    UploadedDocumentDetailState.error_message,
                    color_scheme="red",
                    size="2",
                    icon="triangle-alert",
                    margin_bottom="1rem",
                ),
            ),

            # ── Loading / content ────────────────────────────────────────────
            rx.cond(
                UploadedDocumentDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    UploadedDocumentDetailState.not_found,
                    rx.center(
                        rx.vstack(
                            rx.icon("file-x", size=40, color="var(--gray-6)"),
                            rx.text("Document introuvable.", color="var(--gray-8)", size="2"),
                            align="center",
                            spacing="2",
                        ),
                        padding="3rem",
                    ),
                    rx.card(
                        rx.vstack(
                            rx.text(
                                "Informations",
                                size="2",
                                weight="bold",
                                color="var(--gray-11)",
                                margin_bottom="0.5rem",
                            ),
                            rx.cond(
                                UploadedDocumentDetailState.doc_type_label != "",
                                _info_row(
                                    LanguageState.tr["upload_field_doc_type"],
                                    rx.text(UploadedDocumentDetailState.doc_type_label, size="2"),
                                ),
                            ),
                            rx.cond(
                                UploadedDocumentDetailState.doc_date != "",
                                _info_row(
                                    LanguageState.tr["upload_field_date"],
                                    rx.text(UploadedDocumentDetailState.doc_date, size="2"),
                                ),
                            ),
                            rx.cond(
                                UploadedDocumentDetailState.patient_name != "",
                                _info_row(
                                    "Patient",
                                    rx.link(
                                        UploadedDocumentDetailState.patient_name,
                                        on_click=UploadedDocumentDetailState.go_to_patient,
                                        cursor="pointer",
                                        color="var(--accent-9)",
                                        size="2",
                                    ),
                                ),
                            ),
                            rx.cond(
                                UploadedDocumentDetailState.description != "",
                                _info_row(
                                    LanguageState.tr["upload_field_description"],
                                    rx.text(UploadedDocumentDetailState.description, size="2"),
                                ),
                            ),
                            rx.cond(
                                UploadedDocumentDetailState.notes != "",
                                _info_row(
                                    LanguageState.tr["upload_field_notes"],
                                    rx.text(UploadedDocumentDetailState.notes, size="2", white_space="pre-wrap"),
                                ),
                            ),
                            width="100%",
                            spacing="0",
                        ),
                        width="100%",
                    ),
                ),
            ),
        ),
        _edit_dialog(),
    )
