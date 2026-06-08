"""Patient document page components for the patient portal.

Four pages:
  /my-exams           — PatientDocumentsState.on_load_exams
  /my-prescriptions   — PatientDocumentsState.on_load_prescriptions
  /my-certificates    — PatientDocumentsState.on_load_certificates
  /my-all-documents   — PatientDocumentsState.on_load_all_documents
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .patient_documents_state import (
    AllDocumentRowDTO,
    PatientCertificateRowDTO,
    PatientDocumentsState,
    PatientExamRowDTO,
    PatientPrescriptionRowDTO,
)


# ── Shared helpers ─────────────────────────────────────────────────────────────


def _empty_state(icon: str, message: rx.Var) -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon(icon, size=40, color="var(--gray-7)"),
            rx.text(message, size="3", color="var(--gray-9)"),
            spacing="3",
            align="center",
        ),
        padding="4rem",
    )


def _date_range_filter(from_val: rx.Var, to_val: rx.Var,
                       on_from, on_to) -> rx.Component:
    return rx.hstack(
        rx.input(
            type="date",
            value=from_val,
            on_change=on_from,
            size="2",
        ),
        rx.text(LanguageState.tr["date_range_arrow"], size="2", color="var(--gray-8)"),
        rx.input(
            type="date",
            value=to_val,
            on_change=on_to,
            size="2",
        ),
        spacing="2",
        align="center",
    )


def _sortable_col(label: rx.Var | str, sort_col_var: rx.Var, sort_asc_var: rx.Var, column: str, on_click) -> rx.Component:
    """Sortable column header cell."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                sort_col_var == column,
                rx.cond(
                    sort_asc_var,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=on_click,
        style={"cursor": "pointer"},
    )


# ── My Exams ───────────────────────────────────────────────────────────────────


def _exam_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("todo", rx.badge(LanguageState.tr["exam_status_todo"], color_scheme="gray", variant="soft", size="1")),
        ("in_progress_results", rx.badge(LanguageState.tr["exam_status_in_progress_results"], color_scheme="orange", variant="soft", size="1")),
        ("in_progress_interpretation", rx.badge(LanguageState.tr["exam_status_in_progress_interpretation"], color_scheme="blue", variant="soft", size="1")),
        ("done", rx.badge(LanguageState.tr["exam_status_done"], color_scheme="green", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _exam_row(exam: PatientExamRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(exam.exam_date, size="2")),
        rx.table.cell(rx.text(exam.exam_type_label, size="2")),
        rx.table.cell(_exam_status_badge(exam.status)),
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("eye", size=14),
                    variant="ghost",
                    size="1",
                    on_click=lambda: PatientDocumentsState.go_to_exam(exam.id),
                ),
                content=LanguageState.tr["view_btn"],
            )
        ),
        _hover={"background": "var(--gray-2)"},
        cursor="pointer",
        on_click=lambda: PatientDocumentsState.go_to_exam(exam.id),
    )


def my_exams_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.heading(LanguageState.tr["my_exams_title"], size="6"),
            # Filter bar
            rx.hstack(
                _date_range_filter(
                    PatientDocumentsState.exam_filter_from,
                    PatientDocumentsState.exam_filter_to,
                    PatientDocumentsState.set_exam_filter_from,
                    PatientDocumentsState.set_exam_filter_to,
                ),
                rx.select.root(
                    rx.select.trigger(
                        placeholder=LanguageState.tr["filter_by_type_placeholder"],
                        width="180px",
                    ),
                    rx.select.content(
                        rx.select.item(LanguageState.tr["all_types_option"], value="ALL"),
                        rx.foreach(
                            PatientDocumentsState.exam_type_options,
                            lambda t: rx.select.item(t, value=t),
                        ),
                    ),
                    value=rx.cond(
                        PatientDocumentsState.exam_filter_type != "",
                        PatientDocumentsState.exam_filter_type,
                        "ALL",
                    ),
                    on_change=PatientDocumentsState.set_exam_filter_type,
                    size="2",
                ),
                rx.select.root(
                    rx.select.trigger(
                        placeholder=LanguageState.tr["all_statuses"],
                        width="180px",
                    ),
                    rx.select.content(
                        rx.select.item(LanguageState.tr["all_statuses"], value="ALL"),
                        rx.select.item(LanguageState.tr["exam_status_todo"], value="todo"),
                        rx.select.item(LanguageState.tr["exam_status_in_progress_results"], value="in_progress_results"),
                        rx.select.item(LanguageState.tr["exam_status_in_progress_interpretation"], value="in_progress_interpretation"),
                        rx.select.item(LanguageState.tr["exam_status_done"], value="done"),
                    ),
                    value=rx.cond(
                        PatientDocumentsState.exam_filter_status != "",
                        PatientDocumentsState.exam_filter_status,
                        "ALL",
                    ),
                    on_change=PatientDocumentsState.set_exam_filter_status,
                    size="2",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14),
                    LanguageState.tr["clear_btn"],
                    variant="outline",
                    size="2",
                    on_click=PatientDocumentsState.clear_exam_filters,
                ),
                spacing="3",
                align="center",
                wrap="wrap",
                width="100%",
            ),
            rx.cond(
                PatientDocumentsState.exams_error != "",
                rx.callout(PatientDocumentsState.exams_error, icon="triangle-alert", color_scheme="red"),
            ),
            rx.cond(
                PatientDocumentsState.exams_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    PatientDocumentsState.filtered_exams.length() == 0,
                    _empty_state("flask-conical", LanguageState.tr["no_my_exams"]),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                _sortable_col(
                                    LanguageState.tr["col_date"],
                                    PatientDocumentsState.exam_sort_column,
                                    PatientDocumentsState.exam_sort_ascending,
                                    "exam_date",
                                    lambda: PatientDocumentsState.set_exam_sort("exam_date"),
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_exam_type"],
                                    PatientDocumentsState.exam_sort_column,
                                    PatientDocumentsState.exam_sort_ascending,
                                    "exam_type_label",
                                    lambda: PatientDocumentsState.set_exam_sort("exam_type_label"),
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_status"],
                                    PatientDocumentsState.exam_sort_column,
                                    PatientDocumentsState.exam_sort_ascending,
                                    "status",
                                    lambda: PatientDocumentsState.set_exam_sort("status"),
                                ),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(rx.foreach(PatientDocumentsState.filtered_exams, _exam_row)),
                        width="100%",
                        variant="surface",
                    ),
                ),
            ),
        )
    )


# ── My Prescriptions ───────────────────────────────────────────────────────────


def _prescription_row(presc: PatientPrescriptionRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(presc.prescription_date, size="2")),
        rx.table.cell(
            rx.cond(
                presc.diagnosis != "",
                rx.text(presc.diagnosis, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(rx.text(presc.drug_count.to_string(), size="2")),
        rx.table.cell(
            rx.cond(
                presc.prescribed_by_name != "",
                rx.text(presc.prescribed_by_name, size="2", color="var(--gray-9)"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    presc.is_archived,
                    rx.badge(LanguageState.tr["archived_badge"], color_scheme="gray", variant="soft", size="1"),
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("eye", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: PatientDocumentsState.go_to_prescription(presc.id),
                    ),
                    content=LanguageState.tr["view_btn"],
                ),
                spacing="1",
            )
        ),
        _hover={"background": "var(--gray-2)"},
        style={"opacity": rx.cond(presc.is_archived, "0.6", "1")},
    )


def my_prescriptions_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.heading(LanguageState.tr["my_prescriptions_title"], size="6"),
            # Filter bar
            rx.hstack(
                _date_range_filter(
                    PatientDocumentsState.presc_filter_from,
                    PatientDocumentsState.presc_filter_to,
                    PatientDocumentsState.set_presc_filter_from,
                    PatientDocumentsState.set_presc_filter_to,
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon(
                            rx.cond(PatientDocumentsState.presc_show_archived, "archive", "archive-x"),
                            size=14,
                        ),
                        on_click=PatientDocumentsState.toggle_presc_show_archived,
                        variant=rx.cond(PatientDocumentsState.presc_show_archived, "soft", "ghost"),
                        color_scheme=rx.cond(PatientDocumentsState.presc_show_archived, "accent", "gray"),
                        size="2",
                    ),
                    content=LanguageState.tr["show_archived_tooltip"],
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14),
                    LanguageState.tr["clear_btn"],
                    variant="outline",
                    size="2",
                    on_click=PatientDocumentsState.clear_presc_filters,
                ),
                spacing="3",
                align="center",
                wrap="wrap",
                width="100%",
            ),
            rx.cond(
                PatientDocumentsState.prescriptions_error != "",
                rx.callout(PatientDocumentsState.prescriptions_error, icon="triangle-alert", color_scheme="red"),
            ),
            rx.cond(
                PatientDocumentsState.prescriptions_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    PatientDocumentsState.filtered_prescriptions.length() == 0,
                    _empty_state("file-text", LanguageState.tr["no_my_prescriptions"]),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                _sortable_col(
                                    LanguageState.tr["prescription_date_label"],
                                    PatientDocumentsState.presc_sort_column,
                                    PatientDocumentsState.presc_sort_ascending,
                                    "prescription_date",
                                    lambda: PatientDocumentsState.set_presc_sort("prescription_date"),
                                ),
                                _sortable_col(
                                    LanguageState.tr["prescription_diagnosis_label"],
                                    PatientDocumentsState.presc_sort_column,
                                    PatientDocumentsState.presc_sort_ascending,
                                    "diagnosis",
                                    lambda: PatientDocumentsState.set_presc_sort("diagnosis"),
                                ),
                                rx.table.column_header_cell(
                                    rx.text(LanguageState.tr["prescription_drugs_count"], size="2")
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_prescribed_by"],
                                    PatientDocumentsState.presc_sort_column,
                                    PatientDocumentsState.presc_sort_ascending,
                                    "prescribed_by_name",
                                    lambda: PatientDocumentsState.set_presc_sort("prescribed_by_name"),
                                ),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(PatientDocumentsState.filtered_prescriptions, _prescription_row)
                        ),
                        width="100%",
                        variant="surface",
                    ),
                ),
            ),
        )
    )


# ── My Certificates ────────────────────────────────────────────────────────────


def _certificate_row(cert: PatientCertificateRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(cert.issue_date, size="2")),
        rx.table.cell(rx.badge(cert.certificate_type_label, variant="soft", color_scheme="teal", size="1")),
        rx.table.cell(
            rx.cond(
                cert.conclusion != "",
                rx.text(cert.conclusion, size="2", max_width="280px", overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                cert.is_fit_for_work,
                rx.badge(LanguageState.tr["fit_for_work"], color_scheme="green", variant="soft", size="1"),
                rx.badge(LanguageState.tr["not_fit_for_work"], color_scheme="red", variant="soft", size="1"),
            )
        ),
        rx.table.cell(
            rx.cond(
                cert.issued_by_name != "",
                rx.text(cert.issued_by_name, size="2", color="var(--gray-9)"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    cert.is_archived,
                    rx.badge(LanguageState.tr["archived_badge"], color_scheme="gray", variant="soft", size="1"),
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("file-down", size=14),
                        variant="ghost",
                        color_scheme="blue",
                        size="1",
                        on_click=lambda: PatientDocumentsState.download_certificate_pdf(cert.id),
                    ),
                    content=LanguageState.tr["download_cert_pdf"],
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("eye", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: PatientDocumentsState.go_to_certificate(cert.id),
                    ),
                    content=LanguageState.tr["view_btn"],
                ),
                spacing="1",
            )
        ),
        _hover={"background": "var(--gray-2)"},
        style={"opacity": rx.cond(cert.is_archived, "0.6", "1")},
    )


def my_certificates_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.heading(LanguageState.tr["my_certificates_title"], size="6"),
            rx.cond(
                PatientDocumentsState.pdf_error != "",
                rx.callout(PatientDocumentsState.pdf_error, icon="triangle-alert", color_scheme="red"),
            ),
            # Filter bar
            rx.hstack(
                _date_range_filter(
                    PatientDocumentsState.cert_filter_from,
                    PatientDocumentsState.cert_filter_to,
                    PatientDocumentsState.set_cert_filter_from,
                    PatientDocumentsState.set_cert_filter_to,
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon(
                            rx.cond(PatientDocumentsState.cert_show_archived, "archive", "archive-x"),
                            size=14,
                        ),
                        on_click=PatientDocumentsState.toggle_cert_show_archived,
                        variant=rx.cond(PatientDocumentsState.cert_show_archived, "soft", "ghost"),
                        color_scheme=rx.cond(PatientDocumentsState.cert_show_archived, "accent", "gray"),
                        size="2",
                    ),
                    content=LanguageState.tr["show_archived_tooltip"],
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14),
                    LanguageState.tr["clear_btn"],
                    variant="outline",
                    size="2",
                    on_click=PatientDocumentsState.clear_cert_filters,
                ),
                spacing="3",
                align="center",
                wrap="wrap",
                width="100%",
            ),
            rx.cond(
                PatientDocumentsState.certificates_error != "",
                rx.callout(PatientDocumentsState.certificates_error, icon="triangle-alert", color_scheme="red"),
            ),
            rx.cond(
                PatientDocumentsState.certificates_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    PatientDocumentsState.filtered_certificates.length() == 0,
                    _empty_state("award", LanguageState.tr["no_my_certificates"]),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                _sortable_col(
                                    LanguageState.tr["cert_form_date_label"],
                                    PatientDocumentsState.cert_sort_column,
                                    PatientDocumentsState.cert_sort_ascending,
                                    "issue_date",
                                    lambda: PatientDocumentsState.set_cert_sort("issue_date"),
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_cert_type"],
                                    PatientDocumentsState.cert_sort_column,
                                    PatientDocumentsState.cert_sort_ascending,
                                    "certificate_type_label",
                                    lambda: PatientDocumentsState.set_cert_sort("certificate_type_label"),
                                ),
                                rx.table.column_header_cell(
                                    rx.text(LanguageState.tr["cert_form_conclusion_label"], size="2")
                                ),
                                rx.table.column_header_cell(
                                    rx.text(LanguageState.tr["cert_fit_for_work"], size="2")
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_issued_by"],
                                    PatientDocumentsState.cert_sort_column,
                                    PatientDocumentsState.cert_sort_ascending,
                                    "issued_by_name",
                                    lambda: PatientDocumentsState.set_cert_sort("issued_by_name"),
                                ),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(PatientDocumentsState.filtered_certificates, _certificate_row)
                        ),
                        width="100%",
                        variant="surface",
                    ),
                ),
            ),
        )
    )


# ── All Documents ──────────────────────────────────────────────────────────────


def _doc_type_badge(doc_type: str) -> rx.Component:
    return rx.match(
        doc_type,
        ("exam", rx.badge(LanguageState.tr["doc_type_exam"], color_scheme="blue", variant="soft", size="1")),
        ("prescription", rx.badge(LanguageState.tr["doc_type_prescription"], color_scheme="green", variant="soft", size="1")),
        ("certificate", rx.badge(LanguageState.tr["doc_type_certificate"], color_scheme="teal", variant="soft", size="1")),
        ("uploaded", rx.badge(LanguageState.tr["upload_doc_type_uploaded"], color_scheme="orange", variant="soft", size="1")),
        rx.badge(doc_type, color_scheme="gray", variant="soft", size="1"),
    )


def _all_doc_row(doc: AllDocumentRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(_doc_type_badge(doc.doc_type)),
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
        rx.table.cell(
            rx.match(
                doc.doc_type,
                ("exam", rx.tooltip(
                    rx.icon_button(
                        rx.icon("eye", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: PatientDocumentsState.go_to_exam(doc.id),
                    ),
                    content=LanguageState.tr["view_btn"],
                )),
                ("prescription", rx.tooltip(
                    rx.icon_button(
                        rx.icon("eye", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: PatientDocumentsState.go_to_prescription(doc.id),
                    ),
                    content=LanguageState.tr["view_btn"],
                )),
                ("certificate", rx.hstack(
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("file-down", size=14),
                            variant="ghost",
                            color_scheme="blue",
                            size="1",
                            on_click=lambda: PatientDocumentsState.download_certificate_pdf(doc.id),
                        ),
                        content=LanguageState.tr["download_cert_pdf"],
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("eye", size=14),
                            variant="ghost",
                            size="1",
                            on_click=lambda: PatientDocumentsState.go_to_certificate(doc.id),
                        ),
                        content=LanguageState.tr["view_btn"],
                    ),
                    spacing="1",
                )),
                rx.fragment(),
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def my_all_documents_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.heading(LanguageState.tr["my_all_documents_title"], size="6"),
            rx.cond(
                PatientDocumentsState.pdf_error != "",
                rx.callout(PatientDocumentsState.pdf_error, icon="triangle-alert", color_scheme="red"),
            ),
            # Filter bar
            rx.hstack(
                rx.select.root(
                    rx.select.trigger(
                        placeholder=LanguageState.tr["doc_type_all"],
                        width="180px",
                    ),
                    rx.select.content(
                        rx.select.item(LanguageState.tr["doc_type_all"], value="ALL"),
                        rx.select.item(LanguageState.tr["doc_type_exam"], value="exam"),
                        rx.select.item(LanguageState.tr["doc_type_prescription"], value="prescription"),
                        rx.select.item(LanguageState.tr["doc_type_certificate"], value="certificate"),
                    ),
                    value=PatientDocumentsState.all_docs_filter_type,
                    on_change=PatientDocumentsState.set_all_docs_filter_type,
                    size="2",
                ),
                _date_range_filter(
                    PatientDocumentsState.all_docs_filter_from,
                    PatientDocumentsState.all_docs_filter_to,
                    PatientDocumentsState.set_all_docs_filter_from,
                    PatientDocumentsState.set_all_docs_filter_to,
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14),
                    LanguageState.tr["clear_btn"],
                    variant="outline",
                    size="2",
                    on_click=PatientDocumentsState.clear_all_docs_filters,
                ),
                spacing="3",
                align="center",
                wrap="wrap",
                width="100%",
            ),
            rx.cond(
                PatientDocumentsState.all_docs_error != "",
                rx.callout(PatientDocumentsState.all_docs_error, icon="triangle-alert", color_scheme="red"),
            ),
            rx.cond(
                PatientDocumentsState.all_docs_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    PatientDocumentsState.filtered_all_documents.length() == 0,
                    _empty_state("folder-open", LanguageState.tr["no_my_all_documents"]),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                _sortable_col(
                                    LanguageState.tr["col_type"],
                                    PatientDocumentsState.all_docs_sort_column,
                                    PatientDocumentsState.all_docs_sort_ascending,
                                    "doc_type",
                                    lambda: PatientDocumentsState.set_all_docs_sort("doc_type"),
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_date"],
                                    PatientDocumentsState.all_docs_sort_column,
                                    PatientDocumentsState.all_docs_sort_ascending,
                                    "date",
                                    lambda: PatientDocumentsState.set_all_docs_sort("date"),
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_name"],
                                    PatientDocumentsState.all_docs_sort_column,
                                    PatientDocumentsState.all_docs_sort_ascending,
                                    "description",
                                    lambda: PatientDocumentsState.set_all_docs_sort("description"),
                                ),
                                rx.table.column_header_cell(
                                    rx.text(LanguageState.tr["col_status"], size="2")
                                ),
                                _sortable_col(
                                    LanguageState.tr["col_sent_by"],
                                    PatientDocumentsState.all_docs_sort_column,
                                    PatientDocumentsState.all_docs_sort_ascending,
                                    "extra",
                                    lambda: PatientDocumentsState.set_all_docs_sort("extra"),
                                ),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(PatientDocumentsState.filtered_all_documents, _all_doc_row)
                        ),
                        width="100%",
                        variant="surface",
                    ),
                ),
            ),
        )
    )
