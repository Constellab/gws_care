"""Admin documents page component — Gestion des documents.

Reuses stateless helpers from patient_documents_component (date filter,
sortable column header, empty state, type badge, and the all-doc row renderer).
The row renderer displays doc.extra as the patient name column because
AdminDocumentsState._load_all_documents populates extra with patient full name.
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..patient_portal.patient_documents_component import (
    _all_doc_row,
    _date_range_filter,
    _doc_type_badge,  # noqa: F401 — imported for re-export if needed
    _empty_state,
    _sortable_col,
)
from .admin_documents_state import AdminDocumentsState


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
                                    LanguageState.tr["col_type"],
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
                                    rx.text(LanguageState.tr["col_status"], size="2")
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_patient"],
                                    AdminDocumentsState.all_docs_sort_column,
                                    AdminDocumentsState.all_docs_sort_ascending,
                                    "extra",
                                    lambda: AdminDocumentsState.set_all_docs_sort("extra"),
                                ),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(AdminDocumentsState.admin_filtered_documents, _all_doc_row)
                        ),
                        width="100%",
                        variant="surface",
                    ),
                ),
            ),
        )
    )
