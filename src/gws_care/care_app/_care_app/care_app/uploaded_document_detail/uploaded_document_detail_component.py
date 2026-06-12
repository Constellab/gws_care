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


def _doc_info_card() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("file-text", size=20, color="var(--accent-9)"),
                    rx.heading(
                        rx.cond(
                            UploadedDocumentDetailState.original_name != "",
                            UploadedDocumentDetailState.original_name,
                            "Document importé",
                        ),
                        size="5",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    UploadedDocumentDetailState.patient_name != "",
                    rx.hstack(
                        rx.icon("user", size=13, color="var(--gray-9)"),
                        rx.text(UploadedDocumentDetailState.patient_name, size="2", color="var(--gray-9)"),
                        spacing="1",
                        align="center",
                    ),
                ),
                spacing="1",
                align_items="start",
            ),
            width="100%",
            align="start",
        ),
        width="100%",
    )


def _edit_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["edit_doc_info_title"]),
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


def _viewer_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.dialog.title(UploadedDocumentDetailState.original_name),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("x", size=16),
                    on_click=UploadedDocumentDetailState.close_viewer,
                    variant="ghost",
                    size="2",
                ),
                width="100%",
                align="center",
                margin_bottom="1rem",
            ),
            rx.match(
                UploadedDocumentDetailState.viewer_type,
                ("image", rx.box(
                    rx.image(
                        src=UploadedDocumentDetailState.download_url,
                        max_width="100%",
                        max_height="70vh",
                        object_fit="contain",
                        border_radius="8px",
                    ),
                    width="100%",
                    overflow="auto",
                )),
                rx.vstack(
                    rx.icon("file-down", size=40, color="var(--gray-6)"),
                    rx.text(
                        "Veuillez télécharger le document pour l'ouvrir sur votre ordinateur.",
                        size="2",
                        color="var(--gray-9)",
                        text_align="center",
                        max_width="320px",
                    ),
                    rx.button(
                        rx.icon("download", size=14),
                        LanguageState.tr["download_pdf_btn"],
                        on_click=UploadedDocumentDetailState.open_file,
                        variant="soft",
                        size="2",
                    ),
                    align="center",
                    spacing="4",
                    padding="2rem",
                    width="100%",
                ),
            ),
            on_interact_outside=UploadedDocumentDetailState.close_viewer,
            on_escape_key_down=UploadedDocumentDetailState.close_viewer,
            max_width="900px",
            width="90vw",
        ),
        open=UploadedDocumentDetailState.viewer_open,
    )


def uploaded_document_detail_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                # ── Back button ───────────────────────────────────────────────
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=14),
                        LanguageState.tr["btn_back"],
                        on_click=UploadedDocumentDetailState.go_back,
                        variant="ghost",
                        size="2",
                    ),
                    width="100%",
                    align="center",
                ),

                # ── Error ─────────────────────────────────────────────────────
                rx.cond(
                    UploadedDocumentDetailState.error_message != "",
                    rx.callout(
                        UploadedDocumentDetailState.error_message,
                        color_scheme="red",
                        size="2",
                        icon="triangle-alert",
                    ),
                ),

                # ── Loading / content ─────────────────────────────────────────
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
                        rx.vstack(
                            # ── Info card ─────────────────────────────────────
                            _doc_info_card(),

                            # ── Action buttons ────────────────────────────────
                            rx.hstack(
                                rx.button(
                                    rx.icon("pencil", size=14),
                                    LanguageState.tr["edit_doc_info_btn"],
                                    on_click=UploadedDocumentDetailState.open_edit,
                                    variant="soft",
                                    size="2",
                                ),
                                rx.button(
                                    rx.icon("eye", size=14),
                                    LanguageState.tr["view_pdf_btn"],
                                    on_click=UploadedDocumentDetailState.open_viewer,
                                    variant="soft",
                                    size="2",
                                    disabled=~UploadedDocumentDetailState.has_file,
                                ),
                                rx.button(
                                    rx.icon("download", size=14),
                                    LanguageState.tr["download_pdf_btn"],
                                    on_click=UploadedDocumentDetailState.open_file,
                                    variant="soft",
                                    size="2",
                                    disabled=~UploadedDocumentDetailState.has_file,
                                ),
                                spacing="2",
                                width="100%",
                            ),

                            # ── Details card ──────────────────────────────────
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
                                            rx.hstack(
                                                rx.icon("user", size=13, color="var(--gray-9)"),
                                                rx.link(
                                                    UploadedDocumentDetailState.patient_name,
                                                    on_click=UploadedDocumentDetailState.go_to_patient,
                                                    cursor="pointer",
                                                    color="var(--accent-9)",
                                                    size="2",
                                                ),
                                                spacing="1",
                                                align="center",
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

                            width="100%",
                            spacing="4",
                        ),
                    ),
                ),

                width="100%",
                spacing="4",
            ),
        ),
        _edit_dialog(),
        _viewer_dialog(),
    )
