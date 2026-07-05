"""Visit detail page component (7.3)."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .visit_detail_state import ExamResultRowDTO, VisitCertificateRowDTO, VisitDetailState


def _visit_lifeline_step(step_idx: int, value: str, label: str, color: str) -> rx.Component:
    """Single step node for the visit workflow lifeline."""
    idx_var = VisitDetailState.visit_status_index
    return rx.vstack(
        rx.cond(
            idx_var > step_idx,
            # completed — filled circle with checkmark
            rx.box(
                rx.icon("check", size=14, color="white"),
                width="30px",
                height="30px",
                border_radius="50%",
                background=f"var(--{color}-9)",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.cond(
                idx_var == step_idx,
                # current — outlined circle with inner dot
                rx.box(
                    rx.box(
                        width="10px",
                        height="10px",
                        border_radius="50%",
                        background=f"var(--{color}-9)",
                    ),
                    width="30px",
                    height="30px",
                    border_radius="50%",
                    border=f"2px solid var(--{color}-9)",
                    background=f"var(--{color}-3)",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                # future — gray empty circle
                rx.box(
                    width="30px",
                    height="30px",
                    border_radius="50%",
                    border="2px solid var(--gray-5)",
                    background="var(--gray-2)",
                ),
            ),
        ),
        rx.text(
            label,
            size="1",
            color=rx.cond(
                idx_var > step_idx,
                f"var(--{color}-9)",
                rx.cond(
                    idx_var == step_idx,
                    f"var(--{color}-11)",
                    "var(--gray-8)",
                ),
            ),
            weight=rx.cond(idx_var == step_idx, "bold", "regular"),
            text_align="center",
            max_width="80px",
        ),
        align="center",
        spacing="1",
        flex_shrink="0",
    )


def _workflow_lifeline_visit() -> rx.Component:
    """Horizontal workflow progress lifeline for the visit detail page."""
    steps = [
        (0, "pending",                  "Pending",           "gray"),
        (1, "visit_done",               "Visit Done",        "amber"),
        (2, "lab_done",                 "Lab Done",          "blue"),
        (3, "doctor_clinic_validated",  "Clinic Validated",  "violet"),
        (4, "doctor_company_validated", "Company Validated", "green"),
    ]
    nodes = []
    for i, (idx, value, label, color) in enumerate(steps):
        nodes.append(_visit_lifeline_step(idx, value, label, color))
        if i < len(steps) - 1:
            nodes.append(
                rx.box(
                    flex="1",
                    height="2px",
                    background="var(--gray-4)",
                    align_self="flex-start",
                    margin_top="14px",
                    min_width="8px",
                )
            )
    return rx.card(
        rx.hstack(
            *nodes,
            align="start",
            width="100%",
            spacing="0",
        ),
        width="100%",
        padding="0.75rem 1rem",
    )



def _visit_status_badge() -> rx.Component:
    return rx.match(
        VisitDetailState.visit.campaign_visit_status,
        ("pending", rx.badge(VisitDetailState.visit.status_label, color_scheme="gray", size="2")),
        ("visit_done", rx.badge(VisitDetailState.visit.status_label, color_scheme="amber", size="2")),
        ("lab_done", rx.badge(VisitDetailState.visit.status_label, color_scheme="blue", size="2")),
        ("doctor_clinic_validated", rx.badge(VisitDetailState.visit.status_label, color_scheme="violet", size="2")),
        ("doctor_company_validated", rx.badge(VisitDetailState.visit.status_label, color_scheme="green", size="2")),
        rx.badge(VisitDetailState.visit.status_label, color_scheme="gray", size="2"),
    )


def _exam_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("todo", rx.badge(LanguageState.tr["exam_status_todo"], color_scheme="gray", variant="soft", size="1")),
        ("in_progress_results", rx.badge(LanguageState.tr["exam_status_in_progress_results"], color_scheme="orange", variant="soft", size="1")),
        ("in_progress_interpretation", rx.badge(LanguageState.tr["exam_status_in_progress_interpretation"], color_scheme="blue", variant="soft", size="1")),
        ("done", rx.badge(LanguageState.tr["exam_status_done"], color_scheme="green", variant="soft", size="1")),
        rx.badge("—", color_scheme="gray", variant="soft", size="1"),
    )


def _exam_result_row(row: ExamResultRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(row.exam_type_name, size="2", weight="medium"),
                rx.cond(
                    row.exam_type_code != "",
                    rx.text(row.exam_type_code, size="1", color="var(--gray-9)"),
                ),
                spacing="0",
            )
        ),
        rx.table.cell(
            rx.cond(
                row.exam_id != "",
                _exam_status_badge(row.status),
                rx.badge("À faire", color_scheme="gray", variant="soft", size="1"),
            )
        ),
    )


def _workflow_actions() -> rx.Component:
    """Show the next available workflow action button based on visit status."""
    return rx.hstack(
        rx.button(
            rx.icon("file-down", size=16),
            "Télécharger résultats PDF",
            variant="outline",
            size="2",
            color_scheme="gray",
            on_click=VisitDetailState.download_results_pdf,
        ),
        rx.cond(
            (VisitDetailState.visit.campaign_visit_status == "visit_done") & (VisitDetailState.is_operator | VisitDetailState.is_admin),
            rx.button(
                rx.icon("flask-conical", size=16),
                LanguageState.tr["btn_validate_lab_visit"],
                on_click=VisitDetailState.validate_lab,
                color_scheme="blue",
                size="2",
            ),
        ),
        rx.cond(
            (VisitDetailState.visit.campaign_visit_status == "lab_done") & (VisitDetailState.is_doctor | VisitDetailState.is_admin),
            rx.button(
                rx.icon("stethoscope", size=16),
                LanguageState.tr["btn_validate_clinic_visit"],
                on_click=VisitDetailState.validate_clinic,
                color_scheme="violet",
                size="2",
            ),
        ),
        rx.cond(
            (VisitDetailState.visit.campaign_visit_status == "doctor_clinic_validated") & (VisitDetailState.is_account_admin | VisitDetailState.is_admin),
            rx.button(
                rx.icon("building-2", size=16),
                LanguageState.tr["btn_validate_company_visit"],
                on_click=VisitDetailState.validate_company,
                color_scheme="green",
                size="2",
            ),
        ),
        spacing="2",
    )


def _section_card(title: str, content: rx.Component) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4"),
            content,
            width="100%",
            spacing="3",
        ),
        width="100%",
    )


def _certificate_card(cert: VisitCertificateRowDTO) -> rx.Component:
    """Card showing a single issued certificate with download button."""
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.cond(
                        cert.is_fit_for_work,
                        rx.badge(LanguageState.tr["cert_fit_for_work"], color_scheme="green", size="1"),
                        rx.badge(LanguageState.tr["cert_not_fit"], color_scheme="red", size="1"),
                    ),
                    rx.text(cert.issue_date, size="2", color="var(--gray-9)"),
                    spacing="2",
                    align="center",
                ),
                rx.text(cert.conclusion, size="2"),
                rx.cond(
                    cert.restrictions != "",
                    rx.text(
                        LanguageState.tr["cert_restrictions"] + " : " + cert.restrictions,
                        size="1",
                        color="var(--gray-9)",
                    ),
                ),
                rx.cond(
                    cert.issued_by_name != "",
                    rx.text(
                        LanguageState.tr["cert_issued_by"] + " : " + cert.issued_by_name,
                        size="1",
                        color="var(--gray-9)",
                    ),
                ),
                spacing="1",
                align_items="start",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("download", size=14),
                on_click=VisitDetailState.download_certificate_pdf(cert.id),
                variant="ghost",
                size="1",
            ),
            align="start",
            width="100%",
        ),
        width="100%",
    )


def _certificate_dialog() -> rx.Component:
    """Dialog for issuing a new medical certificate."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["dialog_issue_cert_title"]),
            rx.vstack(
                rx.vstack(
                    rx.text(LanguageState.tr["cert_issue_date"], size="2", weight="medium"),
                    rx.input(
                        type="date",
                        value=VisitDetailState.cert_form_issue_date,
                        on_change=VisitDetailState.set_cert_form_issue_date,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text(LanguageState.tr["cert_conclusion"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=LanguageState.tr["cert_conclusion"] + "…",
                        value=VisitDetailState.cert_form_conclusion,
                        on_change=VisitDetailState.set_cert_form_conclusion,
                        rows="4",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text(LanguageState.tr["cert_aptitude"], size="2", weight="medium"),
                    rx.radio_group(
                        ["Apte", "Inapte"],
                        value=rx.cond(VisitDetailState.cert_form_is_fit_for_work, "Apte", "Inapte"),
                        on_change=lambda v: VisitDetailState.set_cert_form_is_fit_for_work(v == "Apte"),
                        direction="row",
                        spacing="4",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text(LanguageState.tr["cert_restrictions"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=LanguageState.tr["cert_restrictions"] + "…",
                        value=VisitDetailState.cert_form_restrictions,
                        on_change=VisitDetailState.set_cert_form_restrictions,
                        rows="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Annuler",
                            variant="ghost",
                            on_click=VisitDetailState.close_certificate_dialog,
                        ),
                    ),
                    rx.button(
                        LanguageState.tr["btn_issue"],
                        on_click=VisitDetailState.submit_certificate,
                        loading=VisitDetailState.is_issuing_certificate,
                        color_scheme="purple",
                    ),
                    justify="end",
                    width="100%",
                    spacing="3",
                ),
                spacing="4",
                width="100%",
            ),
            on_interact_outside=VisitDetailState.close_certificate_dialog,
            on_escape_key_down=VisitDetailState.close_certificate_dialog,
            max_width="520px",
        ),
        open=VisitDetailState.cert_dialog_open,
    )


def visit_detail_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.cond(
                VisitDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    VisitDetailState.visit == None,  # noqa: E711
                    rx.center(
                        rx.callout(
                            LanguageState.tr["visit_not_found"],
                            color_scheme="red",
                            icon="triangle-alert",
                        ),
                        padding="4rem",
                    ),
                    rx.vstack(
                        # Back + download header
                        rx.hstack(
                            rx.button(
                                rx.icon("arrow-left", size=14),
                                LanguageState.tr["btn_back"],
                                variant="ghost",
                                size="2",
                                on_click=VisitDetailState.go_back,
                            ),
                            rx.spacer(),
                            rx.button(
                                rx.icon("file-down", size=16),
                                "Télécharger résultats PDF",
                                variant="outline",
                                size="2",
                                color_scheme="gray",
                                on_click=VisitDetailState.download_results_pdf,
                            ),
                            width="100%",
                            align="center",
                        ),
                        # Visit info card
                        rx.card(
                            rx.hstack(
                                rx.vstack(
                                    rx.hstack(
                                        rx.icon("calendar", size=20, color="var(--accent-9)"),
                                        rx.heading(VisitDetailState.visit.patient_name, size="5"),
                                        spacing="2",
                                        align="center",
                                    ),
                                    rx.hstack(
                                        rx.text(VisitDetailState.visit.visit_number, size="2", color="var(--gray-9)"),
                                        rx.separator(orientation="vertical"),
                                        rx.icon("folder-open", size=13, color="var(--gray-9)"),
                                        rx.text(VisitDetailState.visit.campaign_name, size="2", color="var(--gray-9)"),
                                        spacing="2",
                                        align="center",
                                    ),
                                    spacing="1",
                                    align_items="start",
                                ),
                                rx.spacer(),
                                _visit_status_badge(),
                                align="start",
                                width="100%",
                            ),
                            width="100%",
                        ),
                        # Workflow lifeline
                        _workflow_lifeline_visit(),
                        # Contextual workflow hint
                        rx.match(
                            VisitDetailState.visit.campaign_visit_status,
                            ("pending", rx.callout(
                                LanguageState.tr["hint_visit_pending"],
                                icon="info",
                                color_scheme="gray",
                                size="1",
                            )),
                            ("visit_done", rx.callout(
                                LanguageState.tr["hint_visit_done"],
                                icon="flask-conical",
                                color_scheme="amber",
                                size="1",
                            )),
                            ("lab_done", rx.callout(
                                LanguageState.tr["hint_visit_lab_done"],
                                icon="stethoscope",
                                color_scheme="blue",
                                size="1",
                            )),
                            ("doctor_clinic_validated", rx.callout(
                                LanguageState.tr["hint_visit_clinic_validated"],
                                icon="building-2",
                                color_scheme="violet",
                                size="1",
                            )),
                            ("doctor_company_validated", rx.callout(
                                LanguageState.tr["hint_visit_company_validated"],
                                icon="circle-check",
                                color_scheme="green",
                                size="1",
                            )),
                            rx.fragment(),
                        ),
                        # Alerts
                        rx.cond(
                            VisitDetailState.error_message != "",
                            rx.callout(
                                VisitDetailState.error_message,
                                color_scheme="red",
                                icon="triangle-alert",
                                size="2",
                            ),
                        ),
                        rx.cond(
                            VisitDetailState.success_message != "",
                            rx.callout(
                                VisitDetailState.success_message,
                                color_scheme="green",
                                icon="circle_check",
                                size="2",
                            ),
                        ),
                        # Exam Results section
                        rx.card(
                            rx.vstack(
                                rx.hstack(
                                    rx.heading(LanguageState.tr["section_exam_results"], size="4"),
                                    rx.spacer(),
                                    rx.cond(
                                        (
                                            (VisitDetailState.visit.campaign_visit_status == "visit_done")
                                            | (VisitDetailState.visit.campaign_visit_status == "pending")
                                        ) & (VisitDetailState.is_operator | VisitDetailState.is_admin),
                                        rx.button(
                                            rx.icon("pencil", size=14),
                                            "Saisir les résultats",
                                            variant="solid",
                                            color_scheme="blue",
                                            size="2",
                                            on_click=VisitDetailState.go_to_results_entry,
                                        ),
                                    ),
                                    align="center",
                                    width="100%",
                                ),
                                rx.cond(
                                    VisitDetailState.exam_results.length() == 0,
                                    rx.text(LanguageState.tr["no_results_entered"], size="2", color="var(--gray-9)"),
                                    rx.table.root(
                                        rx.table.header(
                                            rx.table.row(
                                                rx.table.column_header_cell(LanguageState.tr["col_exam_name"]),
                                                rx.table.column_header_cell(LanguageState.tr["col_status"]),
                                            )
                                        ),
                                        rx.table.body(
                                            rx.foreach(VisitDetailState.exam_results, _exam_result_row)
                                        ),
                                        width="100%",
                                    ),
                                ),
                                rx.cond(
                                    (VisitDetailState.visit.campaign_visit_status == "visit_done")
                                    & (VisitDetailState.is_operator | VisitDetailState.is_admin),
                                    rx.hstack(
                                        rx.button(
                                            rx.icon("flask-conical", size=16),
                                            LanguageState.tr["btn_validate_lab_visit"],
                                            on_click=VisitDetailState.validate_lab,
                                            color_scheme="blue",
                                            size="2",
                                            disabled=~VisitDetailState.all_exams_done,
                                        ),
                                        justify="end",
                                        width="100%",
                                    ),
                                ),
                                width="100%",
                                spacing="3",
                            ),
                            width="100%",
                        ),
                        # Clinic interpretation section
                        rx.card(
                            rx.vstack(
                                rx.heading(LanguageState.tr["section_clinic_interpretation"], size="4"),
                                rx.cond(
                                    VisitDetailState.visit.doctor_clinic_validated_at != "",
                                    # Already validated — read only
                                    rx.vstack(
                                        rx.hstack(
                                            rx.text(LanguageState.tr["validated_by_label"] + ":", size="2", color="var(--gray-9)"),
                                            rx.text(VisitDetailState.visit.doctor_clinic_validated_by, size="2"),
                                            rx.text(VisitDetailState.visit.doctor_clinic_validated_at, size="2", color="var(--gray-8)"),
                                            spacing="2",
                                        ),
                                        rx.cond(
                                            VisitDetailState.visit.doctor_clinic_interpretation != "",
                                            rx.box(
                                                rx.text(VisitDetailState.visit.doctor_clinic_interpretation, size="2"),
                                                padding="0.75rem",
                                                border_radius="var(--radius-2)",
                                                background="var(--gray-2)",
                                                width="100%",
                                            ),
                                        ),
                                        width="100%",
                                        spacing="2",
                                    ),
                                    # Not yet validated — show editable if doctor/admin
                                    rx.cond(
                                        VisitDetailState.is_doctor | VisitDetailState.is_admin,
                                        rx.vstack(
                                            rx.text(LanguageState.tr["clinic_interp_label"], size="2", color="var(--gray-9)"),
                                            rx.text_area(
                                                placeholder=LanguageState.tr["interpretation_placeholder"],
                                                value=VisitDetailState.clinic_interpretation,
                                                on_change=VisitDetailState.set_clinic_interpretation,
                                                rows="4",
                                                width="100%",
                                                disabled=(
                                                    (VisitDetailState.visit.campaign_visit_status != "lab_done")
                                                    & (VisitDetailState.visit.campaign_visit_status != "visit_done")
                                                ),
                                            ),
                                            rx.cond(
                                                (VisitDetailState.visit.campaign_visit_status == "visit_done"),
                                                rx.callout(
                                                    "Vous pouvez saisir votre interprétation dès maintenant. La validation sera possible une fois les résultats labo disponibles.",
                                                    icon="info", color_scheme="amber", size="1",
                                                ),
                                            ),
                                            rx.cond(
                                                (VisitDetailState.visit.campaign_visit_status == "lab_done")
                                                & (VisitDetailState.is_doctor | VisitDetailState.is_admin),
                                                rx.hstack(
                                                    rx.button(
                                                        rx.icon("stethoscope", size=16),
                                                        LanguageState.tr["btn_validate_clinic_visit"],
                                                        on_click=VisitDetailState.validate_clinic,
                                                        color_scheme="violet",
                                                        size="2",
                                                    ),
                                                    justify="end",
                                                    width="100%",
                                                ),
                                            ),
                                            spacing="2",
                                            width="100%",
                                        ),
                                        rx.text(
                                            LanguageState.tr["no_results_entered"],
                                            size="2",
                                            color="var(--gray-9)",
                                        ),
                                    ),
                                ),
                                width="100%",
                                spacing="3",
                            ),
                            width="100%",
                        ),
                        # Company interpretation section
                        rx.card(
                            rx.vstack(
                                rx.heading(LanguageState.tr["section_company_interpretation"], size="4"),
                                rx.cond(
                                    VisitDetailState.visit.doctor_company_validated_at != "",
                                    # Already validated — read only
                                    rx.vstack(
                                        rx.hstack(
                                            rx.text(LanguageState.tr["validated_by_label"] + ":", size="2", color="var(--gray-9)"),
                                            rx.text(VisitDetailState.visit.doctor_company_validated_by, size="2"),
                                            rx.text(VisitDetailState.visit.doctor_company_validated_at, size="2", color="var(--gray-8)"),
                                            spacing="2",
                                        ),
                                        rx.cond(
                                            VisitDetailState.visit.doctor_company_interpretation != "",
                                            rx.box(
                                                rx.text(VisitDetailState.visit.doctor_company_interpretation, size="2"),
                                                padding="0.75rem",
                                                border_radius="var(--radius-2)",
                                                background="var(--gray-2)",
                                                width="100%",
                                            ),
                                        ),
                                        rx.cond(
                                            VisitDetailState.visit.doctor_company_message != "",
                                            rx.vstack(
                                                rx.text(LanguageState.tr["patient_message_label"] + ":", size="2", color="var(--gray-9)"),
                                                rx.box(
                                                    rx.text(VisitDetailState.visit.doctor_company_message, size="2"),
                                                    padding="0.75rem",
                                                    border_radius="var(--radius-2)",
                                                    background="var(--accent-2)",
                                                    width="100%",
                                                ),
                                                spacing="1",
                                                width="100%",
                                            ),
                                        ),
                                        width="100%",
                                        spacing="2",
                                    ),
                                    # Not yet validated
                                    rx.cond(
                                        VisitDetailState.is_account_admin | VisitDetailState.is_admin,
                                        rx.vstack(
                                            rx.text(LanguageState.tr["company_interp_label"], size="2", color="var(--gray-9)"),
                                            rx.text_area(
                                                placeholder=LanguageState.tr["interpretation_placeholder"],
                                                value=VisitDetailState.company_interpretation,
                                                on_change=VisitDetailState.set_company_interpretation,
                                                rows="4",
                                                width="100%",
                                                disabled=(VisitDetailState.visit.campaign_visit_status != "doctor_clinic_validated"),
                                            ),
                                            rx.text(LanguageState.tr["patient_message_label"], size="2", color="var(--gray-9)"),
                                            rx.text_area(
                                                placeholder=LanguageState.tr["message_to_patient_placeholder"],
                                                value=VisitDetailState.company_message,
                                                on_change=VisitDetailState.set_company_message,
                                                rows="3",
                                                width="100%",
                                                disabled=(VisitDetailState.visit.campaign_visit_status != "doctor_clinic_validated"),
                                            ),
                                            rx.cond(
                                                (VisitDetailState.visit.campaign_visit_status == "doctor_clinic_validated")
                                                & (VisitDetailState.is_account_admin | VisitDetailState.is_admin),
                                                rx.hstack(
                                                    rx.button(
                                                        rx.icon("building-2", size=16),
                                                        LanguageState.tr["btn_validate_company_visit"],
                                                        on_click=VisitDetailState.validate_company,
                                                        color_scheme="green",
                                                        size="2",
                                                    ),
                                                    justify="end",
                                                    width="100%",
                                                ),
                                            ),
                                            spacing="2",
                                            width="100%",
                                        ),
                                        rx.text(
                                            LanguageState.tr["no_results_entered"],
                                            size="2",
                                            color="var(--gray-9)",
                                        ),
                                    ),
                                ),
                                width="100%",
                                spacing="3",
                            ),
                            width="100%",
                        ),
                        # Certificates section
                        _section_card(
                            LanguageState.tr["section_certificates"],
                            rx.vstack(
                                rx.cond(
                                    (VisitDetailState.is_account_admin | VisitDetailState.is_admin)
                                    & (VisitDetailState.visit.lab_validated_at != ""),
                                    rx.button(
                                        rx.icon("file-plus", size=14),
                                        LanguageState.tr["btn_issue_certificate"],
                                        on_click=VisitDetailState.open_certificate_dialog,
                                        size="2",
                                        color_scheme="purple",
                                        variant="soft",
                                    ),
                                ),
                                rx.cond(
                                    VisitDetailState.certificates.length() == 0,
                                    rx.text(
                                        LanguageState.tr["no_certificates_yet"],
                                        size="2",
                                        color="var(--gray-9)",
                                    ),
                                    rx.vstack(
                                        rx.foreach(VisitDetailState.certificates, _certificate_card),
                                        width="100%",
                                        spacing="2",
                                    ),
                                ),
                                width="100%",
                                spacing="3",
                            ),
                        ),
                        width="100%",
                        spacing="4",
                    ),
                ),
            ),
        ),
        _certificate_dialog(),
    )
