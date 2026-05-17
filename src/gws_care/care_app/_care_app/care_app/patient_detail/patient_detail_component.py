"""Patient detail page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..patient_list.patient_form_component import patient_form_dialog
from ..patient_list.patient_form_state import PatientFormState
from .certificate_form_component import certificate_form_dialog
from .exam_form_component import exam_form_dialog
from .exam_form_state import ExamFormState
from .patient_detail_state import (
    CertificateRowDTO,
    ExamRowDTO,
    PatientDetailDTO,
    PatientDetailState,
    PatientVisitRowDTO,
    PrescriptionRowDTO,
)
from .prescription_form_component import prescription_form_dialog


def _info_row(label: str, value: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="2", weight="medium", color="var(--gray-9)", min_width="180px", flex_shrink="0"),
        rx.cond(
            value,
            rx.text(value, size="2", overflow_wrap="break-word", word_break="break-word", min_width="0", flex="1"),
            rx.text("—", size="2", color="var(--gray-7)"),
        ),
        spacing="4",
        align="start",
        padding_y="0.4rem",
        width="100%",
    )


def _exam_sortable_header(label: str, column: str) -> rx.Component:
    """Column header cell with sort-direction arrow for the exams table."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                PatientDetailState.exam_sort_column == column,
                rx.cond(
                    PatientDetailState.exam_sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: PatientDetailState.set_exam_sort(column),
        style={"cursor": "pointer"},
    )


def _visit_sortable_header(label: str, column: str) -> rx.Component:
    """Column header cell with sort-direction arrow for the visits table."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                PatientDetailState.visit_sort_column == column,
                rx.cond(
                    PatientDetailState.visit_sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: PatientDetailState.set_visit_sort(column),
        style={"cursor": "pointer"},
    )


def _section(title: str, *rows: rx.Component) -> rx.Component:
    return rx.box(
        rx.text(title, size="2", weight="bold", color="var(--gray-9)", margin_bottom="0.5rem"),
        rx.separator(width="100%", margin_bottom="0.75rem"),
        rx.vstack(*rows, width="100%", spacing="1"),
        width="100%",
        padding="1rem",
        border="1px solid var(--gray-4)",
        border_radius="8px",
        background="var(--gray-1)",
        overflow="hidden",
    )


def _patient_card(patient: PatientDetailDTO) -> rx.Component:
    return rx.vstack(
        # Header
        rx.hstack(
            rx.vstack(
                rx.heading(f"{patient.first_name} {patient.last_name}", size="7"),
                rx.hstack(
                    rx.badge(patient.patient_number, variant="outline", size="2"),
                    rx.match(
                        patient.gender,
                        ("M", rx.badge(LanguageState.tr["gender_male_badge"], color_scheme="blue", variant="soft", size="2")),
                        ("F", rx.badge(LanguageState.tr["gender_female_badge"], color_scheme="pink", variant="soft", size="2")),
                        rx.badge(patient.gender, color_scheme="gray", variant="soft", size="2"),
                    ),
                    spacing="2",
                ),
                spacing="2",
                align_items="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("id-card", size=15),
                    LanguageState.tr["btn_id_card"],
                    on_click=PatientDetailState.open_id_card,
                    variant="outline",
                    size="2",
                ),
                rx.button(
                    rx.icon("download", size=15),
                    LanguageState.tr["export_csv"],
                    on_click=PatientDetailState.download_exam_history,
                    variant="outline",
                    size="2",
                ),
                rx.button(
                    rx.icon("pencil", size=15),
                    LanguageState.tr["edit_btn"],
                    on_click=lambda: PatientFormState.open_edit_dialog(patient.id),
                    variant="outline",
                    size="2",
                ),
                spacing="2",
            ),
            width="100%",
            align="center",
        ),
        rx.separator(width="100%"),
        # Sections
        rx.grid(
            _section(
                LanguageState.tr["section_personal_info"],
                _info_row(LanguageState.tr["field_ssn"], patient.social_security_number),
                _info_row(LanguageState.tr["info_dob"], patient.date_of_birth),
                _info_row(LanguageState.tr["info_birth_name"], patient.birth_name),
                _info_row(LanguageState.tr["info_gender"], patient.gender),
            ),
            _section(
                LanguageState.tr["section_contact"],
                _info_row(LanguageState.tr["info_phone"], patient.phone),
                _info_row(LanguageState.tr["info_email"], patient.email),
                _info_row(LanguageState.tr["info_address"], patient.address),
                _info_row(LanguageState.tr["info_postal_code"], patient.postal_code),
                _info_row(LanguageState.tr["info_city"], patient.city),
            ),
            _section(
                LanguageState.tr["section_primary_physician"],
                _info_row(LanguageState.tr["info_physician_name"], patient.primary_physician_name),
                _info_row(LanguageState.tr["info_physician_phone"], patient.primary_physician_phone),
            ),
            columns="2",
            spacing="4",
            width="100%",
        ),
        width="100%",
        spacing="4",
    )



def _id_card_visual() -> rx.Component:
    """The visual patient ID card rendered in the dialog."""
    sex_label = rx.match(
        PatientDetailState.patient.sex,
        ("M", LanguageState.tr["sex_male"]),
        ("F", LanguageState.tr["sex_female"]),
        ("Autre", LanguageState.tr["sex_other"]),
        "—",
    )
    return rx.box(
        # ── Top band ──────────────────────────────────────────────────────────
        rx.box(
            rx.hstack(
                rx.hstack(
                    rx.icon("heart-pulse", size=16, color="#166c5e"),
                    rx.text(
                        "CONSTELLAB CARE — PS CONSULTING",
                        size="1",
                        weight="bold",
                        color="#166c5e",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.text(
                    PatientDetailState.patient.patient_number,
                    size="1",
                    color="#166c5e",
                    weight="medium",
                ),
                width="100%",
                align="center",
            ),
            background="#d3f0eb",
            padding="0.5rem 1rem",
            border_radius="8px 8px 0 0",
        ),
        # ── Card body ─────────────────────────────────────────────────────────
        rx.hstack(
            # Left: patient info
            rx.vstack(
                rx.text(
                    rx.cond(
                        PatientDetailState.patient.last_name,
                        PatientDetailState.patient.last_name,
                        "",
                    ),
                    size="6",
                    weight="bold",
                    color="white",
                    letter_spacing="0.05em",
                ),
                rx.text(
                    rx.cond(
                        PatientDetailState.patient.first_name,
                        PatientDetailState.patient.first_name,
                        "",
                    ),
                    size="4",
                    color="#7cd2c4",
                ),
                rx.separator(width="100%", color_scheme="teal", margin_y="0.4rem"),
                # SSN
                rx.vstack(
                    rx.text(LanguageState.tr["field_ssn"], size="1", color="#7cd2c4", weight="medium"),
                    rx.cond(
                        PatientDetailState.patient.social_security_number,
                        rx.text(
                            PatientDetailState.patient.social_security_number,
                            size="3",
                            color="white",
                            weight="bold",
                            font_family="monospace",
                        ),
                        rx.text("—", size="3", color="#7cd2c4"),
                    ),
                    spacing="0",
                    align_items="start",
                ),
                # DOB
                rx.vstack(
                    rx.text(LanguageState.tr["info_dob"], size="1", color="#7cd2c4", weight="medium"),
                    rx.text(PatientDetailState.patient.date_of_birth, size="3", color="white", weight="bold"),
                    spacing="0",
                    align_items="start",
                ),
                # Sex
                rx.vstack(
                    rx.text(LanguageState.tr["field_sex"], size="1", color="#7cd2c4", weight="medium"),
                    rx.text(sex_label, size="3", color="white", weight="bold"),
                    spacing="0",
                    align_items="start",
                ),
                spacing="3",
                align_items="start",
                flex="1",
                padding="1.25rem",
            ),
            # Right: QR code
            rx.vstack(
                rx.cond(
                    PatientDetailState.patient.qr_code,
                    rx.box(
                        rx.image(
                            src=PatientDetailState.patient.qr_code,
                            width="120px",
                            height="120px",
                        ),
                        background="white",
                        padding="6px",
                        border_radius="6px",
                    ),
                    rx.box(
                        rx.icon("qr-code", size=80, color="#50c3b0"),
                        padding="10px",
                    ),
                ),
                rx.text(LanguageState.tr["qr_code_label"], size="1", color="#7cd2c4"),
                align="center",
                justify="center",
                padding="1rem",
            ),
            spacing="0",
            align="center",
            width="100%",
        ),
        # ── Footer strip ─────────────────────────────────────────────────────
        rx.box(
            rx.text(
                LanguageState.tr["id_card_footer"],
                size="1",
                color="#7cd2c4",
                text_align="center",
            ),
            background="#07241f",
            padding="0.25rem",
            border_radius="0 0 8px 8px",
        ),
        background="linear-gradient(135deg, #0e483e 0%, #1d907d 100%)",
        border_radius="8px",
        width="480px",
        box_shadow="0 8px 32px rgba(14,72,62,0.45)",
    )


def id_card_dialog() -> rx.Component:
    """Dialog showing the patient ID card with print and download actions."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["id_card_title"]),
            rx.dialog.description(LanguageState.tr["id_card_desc"]),
            rx.vstack(
                rx.cond(
                    PatientDetailState.patient,
                    _id_card_visual(),
                    rx.spinner(size="3"),
                ),
                rx.hstack(
                    rx.button(
                        rx.icon("printer", size=15),
                        LanguageState.tr["print_btn"],
                        on_click=rx.call_script("window.print()"),
                        variant="outline",
                        size="2",
                    ),
                    rx.button(
                        rx.icon("file-down", size=15),
                        LanguageState.tr["download_pdf_btn"],
                        on_click=PatientDetailState.download_id_card_pdf,
                        size="2",
                    ),
                    rx.button(
                        LanguageState.tr["close_btn"],
                        on_click=PatientDetailState.close_id_card,
                        variant="soft",
                        color_scheme="gray",
                        size="2",
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                    padding_top="0.75rem",
                ),
                spacing="4",
                align="center",
            ),
            max_width="560px",
            on_interact_outside=PatientDetailState.close_id_card,
            on_escape_key_down=PatientDetailState.close_id_card,
        ),
        open=PatientDetailState.show_id_card,
    )


def _visit_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("pending", rx.badge(LanguageState.tr["status_pending"], color_scheme="gray", variant="soft", size="1")),
        ("on-site_done", rx.badge(LanguageState.tr["status_on-site_done"], color_scheme="orange", variant="soft", size="1")),
        ("results_entered", rx.badge(LanguageState.tr["status_results_entered"], color_scheme="blue", variant="soft", size="1")),
        ("lab_validated", rx.badge(LanguageState.tr["status_lab_validated"], color_scheme="cyan", variant="soft", size="1")),
        ("doctor_clinic_validated", rx.badge(LanguageState.tr["status_doctor_clinic_validated"], color_scheme="purple", variant="soft", size="1")),
        ("doctor_company_validated", rx.badge(LanguageState.tr["status_doctor_company_validated"], color_scheme="green", variant="soft", size="1")),
        ("cancelled", rx.badge(LanguageState.tr["status_cancelled"], color_scheme="red", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _patient_visit_row(visit: PatientVisitRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(visit.visit_number, size="2")),
        rx.table.cell(
            rx.cond(
                visit.campaign_name,
                rx.link(
                    visit.campaign_name,
                    on_click=lambda: PatientDetailState.go_to_program(visit.program_id),
                    cursor="pointer",
                    size="2",
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                visit.scheduled_at,
                rx.text(visit.scheduled_at[:16].replace("T", " "), size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(_visit_status_badge(visit.status)),
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("external-link", size=14),
                    variant="ghost",
                    size="1",
                    on_click=lambda: PatientDetailState.go_to_visit(visit.id),
                ),
                content=LanguageState.tr["tooltip_view_visit"],
            ),
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _create_visit_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["new_visit_form_title"]),
            rx.dialog.description(LanguageState.tr["new_visit_desc"]),
            rx.vstack(
                rx.cond(
                    PatientDetailState.create_visit_error != "",
                    rx.callout(
                        PatientDetailState.create_visit_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                rx.vstack(
                    rx.text(LanguageState.tr["field_scheduled_datetime"], size="2", weight="medium"),
                    rx.input(
                        type="datetime-local",
                        value=PatientDetailState.create_visit_scheduled_at,
                        on_change=PatientDetailState.set_create_visit_scheduled_at,
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text(LanguageState.tr["col_account"], size="2", weight="medium"),
                    rx.cond(
                        PatientDetailState.patient_accounts.length() > 0,
                        rx.select.root(
                            rx.select.trigger(placeholder=LanguageState.tr["select_account_placeholder"]),
                            rx.select.content(
                                rx.foreach(
                                    PatientDetailState.patient_accounts,
                                    lambda a: rx.select.item(a.name, value=a.id),
                                ),
                            ),
                            value=PatientDetailState.create_visit_account_id,
                            on_change=PatientDetailState.set_create_visit_account_id,
                            size="2",
                            width="100%",
                        ),
                        rx.callout(
                            LanguageState.tr["no_account_alert_desc"],
                            icon="triangle-alert",
                            color_scheme="orange",
                            size="1",
                        ),
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        on_click=PatientDetailState.close_create_visit_dialog,
                        variant="soft",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.button(
                        LanguageState.tr["create_visit_btn"],
                        on_click=PatientDetailState.save_create_visit,
                        size="2",
                        disabled=PatientDetailState.patient_accounts.length() == 0,
                    ),
                    spacing="2",
                    width="100%",
                    padding_top="0.75rem",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="480px",
            on_interact_outside=PatientDetailState.close_create_visit_dialog,
            on_escape_key_down=PatientDetailState.close_create_visit_dialog,
        ),
        open=PatientDetailState.show_create_visit_dialog,
    )


def _visits_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading(LanguageState.tr["visits_section_title"], size="4"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=15),
                LanguageState.tr["new_visit_btn"],
                on_click=PatientDetailState.open_create_visit_dialog,
                size="2",
            ),
            width="100%",
            align="center",
        ),
        rx.cond(
            PatientDetailState.patient_visits,
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            _visit_sortable_header(LanguageState.tr["col_visit_number"], "visit_number"),
                            _visit_sortable_header(LanguageState.tr["nav_campaigns"], "campaign_name"),
                            _visit_sortable_header(LanguageState.tr["col_scheduled"], "scheduled_at"),
                            _visit_sortable_header(LanguageState.tr["col_status"], "status"),
                            rx.table.column_header_cell(""),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(PatientDetailState.sorted_visits, _patient_visit_row),
                    ),
                    width="100%",
                    variant="surface",
                ),
                overflow_x="auto",
                width="100%",
            ),
            rx.center(
                rx.text(LanguageState.tr["no_visits_section"], color="var(--gray-8)", size="2"),
                padding="2rem",
                border="1px dashed var(--gray-5)",
                border_radius="8px",
                width="100%",
            ),
        ),
        width="100%",
        spacing="3",
    )


def _exam_status_badge(status: str) -> rx.Component:    return rx.match(
        status,
        ("DRAFT", rx.badge(LanguageState.tr["exam_status_draft"], color_scheme="gray", variant="soft", size="1")),
        ("PENDING", rx.badge(LanguageState.tr["exam_status_pending"], color_scheme="orange", variant="soft", size="1")),
        ("INTERPRETED", rx.badge(LanguageState.tr["exam_status_interpreted"], color_scheme="green", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _exam_row(exam: ExamRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(exam.exam_date),
        rx.table.cell(exam.exam_type_label),
        rx.table.cell(_exam_status_badge(exam.status)),
        rx.table.cell(
            rx.button(
                rx.icon("eye", size=14),
                LanguageState.tr["view_btn"],
                variant="ghost",
                size="1",
                on_click=lambda: PatientDetailState.go_to_exam(exam.id),
            ),
        ),
        _hover={"background": "var(--gray-2)"},
        cursor="pointer",
    )


def _exams_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading(LanguageState.tr["exams_section_title"], size="4"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=15),
                LanguageState.tr["new_exam_btn"],
                on_click=lambda: ExamFormState.open_create_dialog(PatientDetailState.patient.id),
                size="2",
            ),
            width="100%",
            align="center",
        ),
        # Filter bar
        rx.hstack(
            rx.input(
                type="date",
                value=PatientDetailState.exam_filter_from,
                on_change=PatientDetailState.set_exam_filter_from,
                size="1",
                width="130px",
                placeholder="De",
            ),
            rx.text("→", size="2", color="var(--gray-8)"),
            rx.input(
                type="date",
                value=PatientDetailState.exam_filter_to,
                on_change=PatientDetailState.set_exam_filter_to,
                size="1",
                width="130px",
                placeholder="à",
            ),
            rx.select.root(
                rx.select.trigger(
                    placeholder=LanguageState.tr["filter_by_type_placeholder"],
                    size="1",
                    width="180px",
                ),
                rx.select.content(
                    rx.select.item(LanguageState.tr["all_types_option"], value="ALL"),
                    rx.foreach(
                        PatientDetailState.exam_type_options,
                        lambda t: rx.select.item(t, value=t),
                    ),
                ),
                value=rx.cond(PatientDetailState.exam_filter_type != "", PatientDetailState.exam_filter_type, "ALL"),
                on_change=PatientDetailState.set_exam_filter_type,
            ),
            width="100%",
            align="center",
            spacing="2",
        ),
        rx.cond(
            PatientDetailState.filtered_sorted_exams,
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            _exam_sortable_header(LanguageState.tr["col_date"], "exam_date"),
                            _exam_sortable_header(LanguageState.tr["col_type"], "exam_type_label"),
                            _exam_sortable_header(LanguageState.tr["col_status"], "status"),
                            rx.table.column_header_cell(""),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(PatientDetailState.filtered_sorted_exams, _exam_row),
                    ),
                    width="100%",
                    variant="surface",
                ),
                overflow_x="auto",
                width="100%",
            ),
            rx.center(
                rx.text(LanguageState.tr["no_exams_recorded"], color="var(--gray-8)", size="2"),
                padding="2rem",
                border="1px dashed var(--gray-5)",
                border_radius="8px",
                width="100%",
            ),
        ),
        width="100%",
        spacing="3",
    )




def _presc_sortable_header(label: str, column: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                PatientDetailState.presc_sort_column == column,
                rx.cond(
                    PatientDetailState.presc_sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: PatientDetailState.set_presc_sort(column),
        style={"cursor": "pointer"},
    )


def _prescription_row(presc: PrescriptionRowDTO) -> rx.Component:
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
        rx.table.cell(rx.text(presc.prescribed_by_name, size="2", color="var(--gray-9)")),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    presc.is_archived,
                    rx.badge("α", color_scheme="gray", variant="soft", size="1"),
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("eye", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: PatientDetailState.go_to_prescription(presc.id),
                    ),
                    content=LanguageState.tr["view_btn"],
                ),
                spacing="1",
            )
        ),
        _hover={"background": "var(--gray-2)"},
        style={"opacity": rx.cond(presc.is_archived, "0.6", "1")},
    )


def _prescriptions_tab() -> rx.Component:
    return rx.vstack(
        # Filter bar
        rx.hstack(
            rx.input(
                type="date",
                value=PatientDetailState.presc_filter_from,
                on_change=PatientDetailState.set_presc_filter_from,
                size="1",
                width="130px",
                placeholder="De",
            ),
            rx.text("→", size="2", color="var(--gray-8)"),
            rx.input(
                type="date",
                value=PatientDetailState.presc_filter_to,
                on_change=PatientDetailState.set_presc_filter_to,
                size="1",
                width="130px",
                placeholder="à",
            ),
            rx.tooltip(
                rx.icon_button(
                    rx.icon(
                        rx.cond(PatientDetailState.presc_show_archived, "archive", "archive-x"),
                        size=14,
                    ),
                    on_click=PatientDetailState.toggle_presc_show_archived,
                    variant=rx.cond(PatientDetailState.presc_show_archived, "soft", "ghost"),
                    color_scheme=rx.cond(PatientDetailState.presc_show_archived, "accent", "gray"),
                    size="1",
                ),
                content=LanguageState.tr["show_archived_tooltip"],
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=15),
                LanguageState.tr["new_prescription_btn"],
                on_click=PatientDetailState.open_prescription_dialog,
                size="2",
            ),
            width="100%",
            align="center",
            spacing="2",
        ),
        rx.cond(
            PatientDetailState.filtered_sorted_prescriptions,
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            _presc_sortable_header(LanguageState.tr["prescription_date_label"], "prescription_date"),
                            _presc_sortable_header(LanguageState.tr["prescription_diagnosis_label"], "diagnosis"),
                            _presc_sortable_header(LanguageState.tr["prescription_drugs_count"], "drug_count"),
                            _presc_sortable_header(LanguageState.tr["col_prescribed_by"], "prescribed_by_name"),
                            rx.table.column_header_cell(""),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(PatientDetailState.filtered_sorted_prescriptions, _prescription_row),
                    ),
                    width="100%",
                    variant="surface",
                ),
                overflow_x="auto",
                width="100%",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("file-text", size=36, color="var(--gray-6)"),
                    rx.text(LanguageState.tr["no_prescriptions"], color="var(--gray-8)", size="2"),
                    align="center",
                    spacing="2",
                ),
                padding="2.5rem",
                border="1px dashed var(--gray-5)",
                border_radius="8px",
                width="100%",
            ),
        ),
        width="100%",
        spacing="3",
    )


def _cert_sortable_header(label: str, column: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, size="2"),
            rx.cond(
                PatientDetailState.cert_sort_column == column,
                rx.cond(
                    PatientDetailState.cert_sort_ascending,
                    rx.icon("chevron-up", size=13, color="var(--accent-9)"),
                    rx.icon("chevron-down", size=13, color="var(--accent-9)"),
                ),
                rx.icon("chevrons-up-down", size=13, color="var(--gray-7)"),
            ),
            spacing="1",
            align="center",
        ),
        on_click=lambda: PatientDetailState.set_cert_sort(column),
        style={"cursor": "pointer"},
    )


def _certificate_row(cert: CertificateRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(cert.issue_date, size="2")),
        rx.table.cell(rx.badge(cert.certificate_type_label, variant="soft", color_scheme="teal", size="1")),
        rx.table.cell(
            rx.cond(
                cert.conclusion != "",
                rx.text(cert.conclusion, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(rx.text(cert.issued_by_name, size="2", color="var(--gray-9)")),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    cert.is_archived,
                    rx.badge("α", color_scheme="gray", variant="soft", size="1"),
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("eye", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: PatientDetailState.go_to_certificate(cert.id),
                    ),
                    content=LanguageState.tr["view_btn"],
                ),
                spacing="1",
            )
        ),
        _hover={"background": "var(--gray-2)"},
        style={"opacity": rx.cond(cert.is_archived, "0.6", "1")},
    )


def _certificates_tab() -> rx.Component:
    return rx.vstack(
        # Filter bar
        rx.hstack(
            rx.input(
                type="date",
                value=PatientDetailState.cert_filter_from,
                on_change=PatientDetailState.set_cert_filter_from,
                size="1",
                width="130px",
                placeholder="De",
            ),
            rx.text("→", size="2", color="var(--gray-8)"),
            rx.input(
                type="date",
                value=PatientDetailState.cert_filter_to,
                on_change=PatientDetailState.set_cert_filter_to,
                size="1",
                width="130px",
                placeholder="à",
            ),
            rx.tooltip(
                rx.icon_button(
                    rx.icon(
                        rx.cond(PatientDetailState.cert_show_archived, "archive", "archive-x"),
                        size=14,
                    ),
                    on_click=PatientDetailState.toggle_cert_show_archived,
                    variant=rx.cond(PatientDetailState.cert_show_archived, "soft", "ghost"),
                    color_scheme=rx.cond(PatientDetailState.cert_show_archived, "accent", "gray"),
                    size="1",
                ),
                content=LanguageState.tr["show_archived_tooltip"],
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=15),
                LanguageState.tr["new_certificate_btn"],
                on_click=PatientDetailState.open_certificate_dialog,
                size="2",
            ),
            width="100%",
            align="center",
            spacing="2",
        ),
        rx.cond(
            PatientDetailState.filtered_sorted_certificates,
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            _cert_sortable_header(LanguageState.tr["cert_form_date_label"], "issue_date"),
                            _cert_sortable_header(LanguageState.tr["col_cert_type"], "certificate_type_label"),
                            _cert_sortable_header(LanguageState.tr["cert_form_conclusion_label"], "conclusion"),
                            _cert_sortable_header(LanguageState.tr["col_issued_by"], "issued_by_name"),
                            rx.table.column_header_cell(""),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(PatientDetailState.filtered_sorted_certificates, _certificate_row),
                    ),
                    width="100%",
                    variant="surface",
                ),
                overflow_x="auto",
                width="100%",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("award", size=36, color="var(--gray-6)"),
                    rx.text(LanguageState.tr["no_certificates"], color="var(--gray-8)", size="2"),
                    align="center",
                    spacing="2",
                ),
                padding="2.5rem",
                border="1px dashed var(--gray-5)",
                border_radius="8px",
                width="100%",
            ),
        ),
        width="100%",
        spacing="3",
    )


def patient_detail_page() -> rx.Component:
    """Patient detail page."""
    return main_component(
        page_layout(
            patient_form_dialog(),
            exam_form_dialog(),
            prescription_form_dialog(),
            certificate_form_dialog(),
            id_card_dialog(),
            _create_visit_dialog(),
            rx.button(
                rx.icon("arrow-left", size=16),
                LanguageState.tr["back_to_patients"],
                on_click=PatientDetailState.go_back,
                variant="ghost",
                size="2",
            ),
            rx.cond(
                PatientDetailState.error_message != "",
                rx.callout(
                    PatientDetailState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                PatientDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    PatientDetailState.patient,
                    rx.vstack(
                        _patient_card(PatientDetailState.patient),
                        rx.tabs.root(
                            rx.tabs.list(
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("stethoscope", size=15),
                                        rx.text(LanguageState.tr["tab_visits"]),
                                        spacing="1",
                                        align="center",
                                    ),
                                    value="visits",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("flask-conical", size=15),
                                        rx.text(LanguageState.tr["tab_exams"]),
                                        spacing="1",
                                        align="center",
                                    ),
                                    value="exams",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("file-text", size=15),
                                        rx.text(LanguageState.tr["tab_prescriptions"]),
                                        spacing="1",
                                        align="center",
                                    ),
                                    value="prescriptions",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("award", size=15),
                                        rx.text(LanguageState.tr["tab_certificates"]),
                                        spacing="1",
                                        align="center",
                                    ),
                                    value="certificates",
                                ),
                            ),
                            rx.tabs.content(_visits_section(), value="visits", padding_top="1rem"),
                            rx.tabs.content(_exams_section(), value="exams", padding_top="1rem"),
                            rx.tabs.content(_prescriptions_tab(), value="prescriptions", padding_top="1rem"),
                            rx.tabs.content(_certificates_tab(), value="certificates", padding_top="1rem"),
                            default_value="visits",
                            width="100%",
                        ),
                        width="100%",
                        spacing="6",
                    ),
                    rx.center(rx.text(LanguageState.tr["patient_not_found"], color="var(--gray-9)"), padding="3rem"),
                ),
            ),
        )
    )
