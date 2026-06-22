"""Admin documents page component — Gestion des documents.

Reuses stateless helpers from patient_documents_component (date filter,
sortable column header, empty state, type badge). The all-doc row is
re-implemented here as _admin_doc_row so it can include an Edit button
for uploaded documents (calling AdminDocumentsState events).
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..common.patient_picker_component import (
    patient_picker_button,
    patient_picker_dialog,
)
from ..patient_portal.patient_documents_component import (
    _date_range_filter,
    _doc_type_badge,
    _empty_state,
    _sortable_col,
)
from ..patient_portal.patient_documents_state import AllDocumentRowDTO
from ..document_upload.document_upload_state import DOC_TYPE_OPTIONS
from .admin_documents_state import AdminDocumentsState


# ── Admin-specific doc row (adds Edit button for uploaded docs) ───────────────

def _admin_doc_row(doc: AllDocumentRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.icon(doc.icon, size=16, color="var(--gray-10)"),
                _doc_type_badge(doc.doc_type),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(rx.text(doc.date, size="2")),
        rx.table.cell(
            rx.cond(
                doc.description != "",
                rx.text(doc.description, size="2", weight="medium"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                doc.sub_label != "",
                rx.text(doc.sub_label, size="2", color="var(--gray-9)"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                doc.extra != "",
                rx.text(doc.extra, size="2", color="var(--gray-9)"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        _hover={"background": "var(--gray-2)", "cursor": "pointer"},
        on_click=lambda: AdminDocumentsState.navigate_to_document(doc.id, doc.doc_type),
    )


# ── Edit uploaded document dialog ─────────────────────────────────────────────

def _edit_uploaded_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["upload_doc_page_title"]),
            rx.vstack(
                # Patient
                rx.vstack(
                    rx.text(LanguageState.tr["upload_field_patient"], size="2", weight="medium"),
                    patient_picker_button(AdminDocumentsState),
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
                        value=AdminDocumentsState.edit_form_doc_type,
                        on_change=AdminDocumentsState.set_edit_form_doc_type,
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
                        value=AdminDocumentsState.edit_form_date,
                        on_change=AdminDocumentsState.set_edit_form_date,
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
                        value=AdminDocumentsState.edit_form_description,
                        on_change=AdminDocumentsState.set_edit_form_description,
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
                        value=AdminDocumentsState.edit_form_notes,
                        on_change=AdminDocumentsState.set_edit_form_notes,
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
                    AdminDocumentsState.edit_uploaded_error != "",
                    rx.callout(
                        AdminDocumentsState.edit_uploaded_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                # Footer
                rx.hstack(
                    rx.button(
                        rx.cond(
                            AdminDocumentsState.edit_uploaded_is_saving,
                            rx.hstack(rx.spinner(size="2"), rx.text(LanguageState.tr["upload_saving"]), spacing="2", align="center"),
                            rx.hstack(rx.icon("save", size=15), rx.text(LanguageState.tr["upload_save_btn"]), spacing="2", align="center"),
                        ),
                        on_click=AdminDocumentsState.save_edit_uploaded,
                        disabled=AdminDocumentsState.edit_uploaded_is_saving,
                        size="2",
                    ),
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        on_click=AdminDocumentsState.close_edit_uploaded,
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
            patient_picker_dialog(AdminDocumentsState),
            on_interact_outside=AdminDocumentsState.close_edit_uploaded,
            on_escape_key_down=AdminDocumentsState.close_edit_uploaded,
            max_width="520px",
        ),
        open=AdminDocumentsState.edit_uploaded_open,
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def admin_documents_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.hstack(
                rx.heading(LanguageState.tr["admin_documents_title"], size="6"),
                rx.spacer(),
                rx.button(
                    rx.icon("upload", size=15),
                    LanguageState.tr["upload_doc_btn"],
                    on_click=rx.redirect("/documents/upload"),
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                AdminDocumentsState.all_docs_error != "",
                rx.callout(AdminDocumentsState.all_docs_error, icon="triangle-alert", color_scheme="red"),
            ),
            # ── Filter bar ─────────────────────────────────────────────────────
            rx.hstack(
                rx.input(
                    placeholder=LanguageState.tr["admin_filter_patient_placeholder"],
                    value=AdminDocumentsState.admin_filter_patient_name,
                    on_change=AdminDocumentsState.set_admin_filter_patient_name,
                    size="2",
                    width="200px",
                ),
                rx.select.root(
                    rx.select.trigger(
                        placeholder=LanguageState.tr["doc_type_all"],
                        width="170px",
                    ),
                    rx.select.content(
                        rx.select.item(LanguageState.tr["doc_type_all"], value="ALL"),
                        rx.select.item(LanguageState.tr["doc_type_exam"], value="exam"),
                        rx.select.item(LanguageState.tr["doc_type_prescription"], value="prescription"),
                        rx.select.item(LanguageState.tr["doc_type_certificate"], value="certificate"),
                        rx.select.item(LanguageState.tr["upload_doc_type_uploaded"], value="uploaded"),
                    ),
                    value=AdminDocumentsState.all_docs_filter_type,
                    on_change=AdminDocumentsState.set_all_docs_filter_type,
                    size="2",
                ),
                _date_range_filter(
                    AdminDocumentsState.all_docs_filter_from,
                    AdminDocumentsState.all_docs_filter_to,
                    AdminDocumentsState.set_all_docs_filter_from,
                    AdminDocumentsState.set_all_docs_filter_to,
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14),
                    LanguageState.tr["clear_btn"],
                    variant="outline",
                    size="2",
                    on_click=AdminDocumentsState.clear_admin_docs_filters,
                ),
                spacing="3",
                align="center",
                wrap="wrap",
                width="100%",
            ),
            # ── Table ──────────────────────────────────────────────────────────
            rx.cond(
                AdminDocumentsState.all_docs_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    AdminDocumentsState.admin_filtered_documents.length() == 0,
                    _empty_state("folder-open", LanguageState.tr["no_admin_documents"]),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                _sortable_col(
                                    LanguageState.tr["col_source"],
                                    AdminDocumentsState.all_docs_sort_column,
                                    AdminDocumentsState.all_docs_sort_ascending,
                                    "doc_type",
                                    lambda: AdminDocumentsState.set_all_docs_sort("doc_type"),
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_date"],
                                    AdminDocumentsState.all_docs_sort_column,
                                    AdminDocumentsState.all_docs_sort_ascending,
                                    "date",
                                    lambda: AdminDocumentsState.set_all_docs_sort("date"),
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_name"],
                                    AdminDocumentsState.all_docs_sort_column,
                                    AdminDocumentsState.all_docs_sort_ascending,
                                    "description",
                                    lambda: AdminDocumentsState.set_all_docs_sort("description"),
                                ),
                                rx.table.column_header_cell(
                                    rx.text(LanguageState.tr["col_details"], size="2")
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_patient"],
                                    AdminDocumentsState.all_docs_sort_column,
                                    AdminDocumentsState.all_docs_sort_ascending,
                                    "extra",
                                    lambda: AdminDocumentsState.set_all_docs_sort("extra"),
                                ),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(AdminDocumentsState.admin_filtered_documents, _admin_doc_row)
                        ),
                        width="100%",
                        variant="surface",
                    ),
                ),
            ),
        ),
        _edit_uploaded_dialog(),
    )
