"""Patient detail page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..account_list.account_form_component import account_form_dialog
from ..patient_list.patient_form_component import patient_form_dialog
from ..patient_list.patient_form_state import PatientFormState
from .certificate_form_component import certificate_form_dialog
from .patient_detail_state import (
    CertificateRowDTO,
    ExamRowDTO,
    PatientDetailDTO,
    PatientDetailState,
    PrescriptionRowDTO,
)
from .patient_account_tab_state import AccountPickerRowDTO, LinkedAccountRowDTO, PatientAccountTabState
from .patient_campaign_tab_state import PatientCampaignRowDTO, PatientCampaignTabState
from .patient_doctor_tab_state import DoctorPickerRowDTO, LinkedDoctorRowDTO, PatientDoctorTabState
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
        rx.flex(
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
                    rx.cond(
                        patient.sex != None,  # noqa: E711
                        rx.badge(
                            LanguageState.tr["field_sex_label"] + ": " + patient.sex,
                            color_scheme="violet", variant="soft", size="2",
                        ),
                    ),
                    rx.cond(
                        patient.is_archived,
                        rx.badge(
                            rx.hstack(rx.icon("archive", size=12), rx.text("Archivé"), spacing="1", align="center"),
                            color_scheme="orange", variant="solid", size="2",
                        ),
                    ),
                    spacing="2",
                    align="center",
                    flex_wrap="wrap",
                ),
                spacing="2",
                align_items="start",
                flex="1",
                min_width="0",
            ),
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
                rx.cond(
                    patient.is_archived,
                    rx.fragment(),
                    rx.button(
                        rx.icon("archive", size=15),
                        "Archiver",
                        on_click=PatientDetailState.open_archive_dialog,
                        variant="outline",
                        size="2",
                        color_scheme="orange",
                    ),
                ),
                rx.button(
                    rx.icon("trash-2", size=15),
                    "Supprimer",
                    on_click=PatientDetailState.open_delete_dialog,
                    variant="outline",
                    size="2",
                    color_scheme="red",
                ),
                spacing="2",
                flex_shrink="0",
                flex_wrap="wrap",
            ),
            width="100%",
            align="start",
            gap="3",
            wrap="wrap",
        ),
        rx.separator(width="100%"),
        rx.cond(
            patient.is_archived,
            rx.callout(
                rx.vstack(
                    rx.hstack(rx.icon("archive", size=14), rx.text("Patient archivé", weight="bold"), spacing="2", align="center"),
                    rx.cond(
                        patient.archived_reason,
                        rx.text("Motif : " + patient.archived_reason, size="2"),
                    ),
                    rx.cond(
                        patient.archived_at,
                        rx.text("Date : " + patient.archived_at, size="1", color="var(--gray-9)"),
                    ),
                    spacing="1",
                ),
                color_scheme="orange",
                variant="soft",
                width="100%",
            ),
        ),
        # Sections
        rx.grid(
            _section(
                LanguageState.tr["section_personal_info"],
                _info_row(LanguageState.tr["field_ssn"], patient.social_security_number),
                _info_row(LanguageState.tr["info_dob"], patient.date_of_birth),
                _info_row(LanguageState.tr["info_birth_name"], patient.birth_name),
                _info_row(LanguageState.tr["info_gender"], patient.gender),
                _info_row(LanguageState.tr["field_nationality"], patient.nationality),
            ),
            _section(
                LanguageState.tr["section_contact"],
                _info_row(LanguageState.tr["info_phone"], patient.phone),
                _info_row(LanguageState.tr["info_email"], patient.email),
                _info_row(LanguageState.tr["info_country"], patient.country),
                _info_row(LanguageState.tr["info_address"], patient.address),
                _info_row(LanguageState.tr["info_address_complement"], patient.address_complement),
                _info_row(LanguageState.tr["info_postal_code"], patient.postal_code),
                _info_row(LanguageState.tr["info_city"], patient.city),
            ),
            columns=rx.breakpoints(initial="1", sm="1", md="2"),
            spacing="4",
            width="100%",
        ),
        # Measurements section
        rx.cond(
            (patient.weight != None) | (patient.height != None),  # noqa: E711
            _section(
                LanguageState.tr["section_measurements"],
                rx.hstack(
                    # Weight
                    rx.cond(
                        patient.weight,
                        rx.vstack(
                            rx.text(LanguageState.tr["field_weight"], size="1", color="var(--gray-9)", weight="medium"),
                            rx.text(patient.weight.to_string() + " kg", size="3", weight="bold"),
                            spacing="0", align_items="start",
                        ),
                    ),
                    # Height
                    rx.cond(
                        patient.height,
                        rx.vstack(
                            rx.text(LanguageState.tr["field_height"], size="1", color="var(--gray-9)", weight="medium"),
                            rx.text(patient.height.to_string() + " cm", size="3", weight="bold"),
                            spacing="0", align_items="start",
                        ),
                    ),
                    # BMI badge
                    rx.cond(
                        PatientDetailState.patient_bmi,
                        rx.vstack(
                            rx.text(LanguageState.tr["bmi_label"], size="1", color="var(--gray-9)", weight="medium"),
                            rx.match(
                                PatientDetailState.patient_bmi_category,
                                ("underweight", rx.badge(
                                    PatientDetailState.patient_bmi.to_string() + " — " + LanguageState.tr["bmi_underweight"],
                                    color_scheme="blue", variant="soft", size="2")),
                                ("normal", rx.badge(
                                    PatientDetailState.patient_bmi.to_string() + " — " + LanguageState.tr["bmi_normal"],
                                    color_scheme="green", variant="soft", size="2")),
                                ("overweight", rx.badge(
                                    PatientDetailState.patient_bmi.to_string() + " — " + LanguageState.tr["bmi_overweight"],
                                    color_scheme="orange", variant="soft", size="2")),
                                ("obese", rx.badge(
                                    PatientDetailState.patient_bmi.to_string() + " — " + LanguageState.tr["bmi_obese"],
                                    color_scheme="red", variant="solid", size="2")),
                                rx.fragment(),
                            ),
                            rx.text(LanguageState.tr["bmi_auto"], size="1", color="var(--gray-7)"),
                            spacing="1", align_items="start",
                        ),
                    ),
                    spacing="6", align="end", flex_wrap="wrap",
                ),
                rx.text(LanguageState.tr["bmi_alert_desc"], size="1", color="var(--gray-7)", margin_top="0.5rem"),
                rx.text(LanguageState.tr["patient_measurements_from_exam"], size="1", color="var(--gray-6)"),
            ),
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
                    rx.icon("heart-pulse", size=16, color="var(--accent-9)"),
                    rx.text(
                        "CONSTELLAB CARE — PS CONSULTING",
                        size="1",
                        weight="bold",
                        color="var(--accent-9)",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.text(
                    PatientDetailState.patient.patient_number,
                    size="1",
                    color="var(--accent-9)",
                    weight="medium",
                ),
                width="100%",
                align="center",
            ),
            background="var(--accent-2)",
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
                    color="var(--accent-5)",
                ),
                rx.separator(width="100%", margin_y="0.4rem", color="var(--accent-5)"),
                # SSN
                rx.vstack(
                    rx.text(LanguageState.tr["field_ssn"], size="1", color="var(--accent-5)", weight="medium"),
                    rx.cond(
                        PatientDetailState.patient.social_security_number,
                        rx.text(
                            PatientDetailState.patient.social_security_number,
                            size="3",
                            color="white",
                            weight="bold",
                            font_family="monospace",
                        ),
                        rx.text("—", size="3", color="var(--accent-5)"),
                    ),
                    spacing="0",
                    align_items="start",
                ),
                # DOB
                rx.vstack(
                    rx.text(LanguageState.tr["info_dob"], size="1", color="var(--accent-5)", weight="medium"),
                    rx.text(PatientDetailState.patient.date_of_birth, size="3", color="white", weight="bold"),
                    spacing="0",
                    align_items="start",
                ),
                # Sex
                rx.vstack(
                    rx.text(LanguageState.tr["field_sex"], size="1", color="var(--accent-5)", weight="medium"),
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
                        rx.icon("qr-code", size=80, color="var(--accent-6)"),
                        padding="10px",
                    ),
                ),
                rx.text(LanguageState.tr["qr_code_label"], size="1", color="var(--accent-5)"),
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
                color="var(--accent-5)",
                text_align="center",
            ),
            background="var(--accent-12)",
            padding="0.25rem",
            border_radius="0 0 8px 8px",
        ),
        background="linear-gradient(135deg, var(--accent-10) 0%, var(--accent-8) 100%)",
        border_radius="8px",
        width="480px",
        box_shadow="0 8px 32px var(--accent-a8)",
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
                margin_top="1rem",
            ),
            max_width="560px",
            on_interact_outside=PatientDetailState.close_id_card,
            on_escape_key_down=PatientDetailState.close_id_card,
        ),
        open=PatientDetailState.show_id_card,
    )


def _exam_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("todo", rx.badge(LanguageState.tr["exam_status_todo"], color_scheme="gray", variant="soft", size="1")),
        ("in_progress_results", rx.badge(LanguageState.tr["exam_status_in_progress_results"], color_scheme="orange", variant="soft", size="1")),
        ("in_progress_interpretation", rx.badge(LanguageState.tr["exam_status_in_progress_interpretation"], color_scheme="blue", variant="soft", size="1")),
        ("done", rx.badge(LanguageState.tr["exam_status_done"], color_scheme="green", variant="soft", size="1")),
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
                on_click=lambda: PatientDetailState.go_to_exam_or_consultation(exam.id, exam.visit_id),
            ),
        ),
        _hover={"background": "var(--gray-2)"},
        cursor="pointer",
    )


def _exams_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading(LanguageState.tr["exams_section_title"], size="4"),
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
                placeholder=LanguageState.tr["placeholder_date_from"],
            ),
            rx.text("→", size="2", color="var(--gray-8)"),
            rx.input(
                type="date",
                value=PatientDetailState.exam_filter_to,
                on_change=PatientDetailState.set_exam_filter_to,
                size="1",
                width="130px",
                placeholder=LanguageState.tr["placeholder_date_to"],
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
            rx.select.root(
                rx.select.trigger(
                    placeholder=LanguageState.tr["filter_by_status_placeholder"],
                    size="1",
                    width="160px",
                ),
                rx.select.content(
                    rx.select.item(LanguageState.tr["all_statuses_option"], value="ALL"),
                    rx.select.item(LanguageState.tr["exam_status_todo"], value="todo"),
                    rx.select.item(LanguageState.tr["exam_status_in_progress_results"], value="in_progress_results"),
                    rx.select.item(LanguageState.tr["exam_status_in_progress_interpretation"], value="in_progress_interpretation"),
                    rx.select.item(LanguageState.tr["exam_status_done"], value="done"),
                ),
                value=rx.cond(PatientDetailState.exam_filter_status != "", PatientDetailState.exam_filter_status, "ALL"),
                on_change=PatientDetailState.set_exam_filter_status,
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
                rx.vstack(
                    rx.icon("flask-conical", size=40, color="var(--gray-6)"),
                    rx.text(LanguageState.tr["no_exams_recorded"], size="2", color="var(--gray-9)"),
                    align="center",
                    spacing="2",
                ),
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
                placeholder=LanguageState.tr["placeholder_date_from"],
            ),
            rx.text("→", size="2", color="var(--gray-8)"),
            rx.input(
                type="date",
                value=PatientDetailState.presc_filter_to,
                on_change=PatientDetailState.set_presc_filter_to,
                size="1",
                width="130px",
                placeholder=LanguageState.tr["placeholder_date_to"],
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
                    rx.icon("file-text", size=40, color="var(--gray-6)"),
                    rx.text(LanguageState.tr["no_prescriptions"], size="2", color="var(--gray-9)"),
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
        rx.table.cell(
            rx.match(
                cert.fitness_decision,
                ("FIT", rx.badge(LanguageState.tr["fit_for_work"], color_scheme="green", variant="soft", size="1")),
                ("UNFIT", rx.badge(LanguageState.tr["not_fit_for_work"], color_scheme="red", variant="soft", size="1")),
                ("PERMANENTLY_UNFIT", rx.badge("Inapte définitif", color_scheme="red", size="1")),
                rx.badge(LanguageState.tr["fit_for_work"], color_scheme="green", variant="soft", size="1"),
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
                placeholder=LanguageState.tr["placeholder_date_from"],
            ),
            rx.text("→", size="2", color="var(--gray-8)"),
            rx.input(
                type="date",
                value=PatientDetailState.cert_filter_to,
                on_change=PatientDetailState.set_cert_filter_to,
                size="1",
                width="130px",
                placeholder=LanguageState.tr["placeholder_date_to"],
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
                            rx.table.column_header_cell(
                                rx.text(LanguageState.tr["cert_fit_for_work"], size="2")
                            ),
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
                    rx.icon("award", size=40, color="var(--gray-6)"),
                    rx.text(LanguageState.tr["no_certificates"], size="2", color="var(--gray-9)"),
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


# ── Doctors tab ───────────────────────────────────────────────────────────────

def _doctor_picker_row(doctor: DoctorPickerRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(doctor.full_name, size="2", weight="medium")),
        rx.table.cell(
            rx.cond(doctor.specialization != "",
                    rx.text(doctor.specialization, size="2"),
                    rx.text("—", size="2", color="var(--gray-8)"))
        ),
        _hover={"background_color": "var(--accent-2)", "cursor": "pointer"},
        on_click=lambda: PatientDoctorTabState.link_doctor(doctor.id),
    )


def _doctor_picker_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["tab_doctors"]),
            rx.vstack(
                rx.input(
                    rx.input.slot(rx.icon("search", size=14)),
                    placeholder=LanguageState.tr["select_doctor_placeholder"],
                    value=PatientDoctorTabState.picker_filter,
                    on_change=PatientDoctorTabState.set_picker_filter,
                    size="2", width="100%",
                ),
                rx.cond(
                    PatientDoctorTabState.picker_is_loading,
                    rx.center(rx.spinner(size="2"), padding="1.5rem"),
                    rx.cond(
                        PatientDoctorTabState.picker_rows.length() > 0,
                        rx.box(
                            rx.table.root(
                                rx.table.header(rx.table.row(
                                    rx.table.column_header_cell(LanguageState.tr["col_name"]),
                                    rx.table.column_header_cell(LanguageState.tr["col_specialization"]),
                                )),
                                rx.table.body(rx.foreach(PatientDoctorTabState.picker_rows, _doctor_picker_row)),
                                width="100%", variant="surface",
                            ),
                            max_height="320px", overflow_y="auto", width="100%",
                        ),
                        rx.center(rx.text(LanguageState.tr["no_doctors_found"], size="2", color="var(--gray-9)"), padding="1.5rem"),
                    ),
                ),
                rx.hstack(
                    rx.button(LanguageState.tr["cancel_btn"], variant="soft", color_scheme="gray",
                              on_click=PatientDoctorTabState.close_picker),
                    justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            on_interact_outside=PatientDoctorTabState.close_picker,
            on_escape_key_down=PatientDoctorTabState.close_picker,
            max_width="500px",
        ),
        open=PatientDoctorTabState.picker_open,
    )


def _linked_doctor_row(doc: LinkedDoctorRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    doc.is_referent,
                    rx.tooltip(
                        rx.icon("star", size=14, color="var(--amber-9)"),
                        content=LanguageState.tr["doctor_referent_label"],
                    ),
                    rx.fragment(),
                ),
                rx.text(doc.full_name, size="2", weight="medium"),
                rx.cond(
                    doc.from_appointment,
                    rx.badge(doc.appointment_role_label, size="1", variant="soft", color_scheme="gray"),
                    rx.fragment(),
                ),
                spacing="2", align="center",
            )
        ),
        rx.table.cell(rx.cond(doc.specialization != "", rx.text(doc.specialization, size="2"), rx.text("—", size="2", color="var(--gray-8)"))),
        rx.table.cell(rx.cond(doc.phone != "", rx.text(doc.phone, size="2"), rx.text("—", size="2", color="var(--gray-8)"))),
        rx.table.cell(
            rx.cond(
                doc.from_appointment,
                rx.fragment(),
                rx.hstack(
                    rx.cond(
                        doc.is_referent,
                        rx.tooltip(
                            rx.icon_button(rx.icon("star-off", size=13), variant="ghost", color_scheme="amber", size="1",
                                           on_click=lambda: PatientDoctorTabState.open_confirm_clear_referent(doc.doctor_id, doc.full_name)),
                            content=LanguageState.tr["doctor_remove_referent_tooltip"],
                        ),
                        rx.tooltip(
                            rx.icon_button(rx.icon("star", size=13), variant="ghost", color_scheme="gray", size="1",
                                           on_click=lambda: PatientDoctorTabState.set_referent(doc.doctor_id)),
                            content=LanguageState.tr["doctor_set_referent_tooltip"],
                        ),
                    ),
                    rx.tooltip(
                        rx.icon_button(rx.icon("unlink", size=13), variant="ghost", color_scheme="red", size="1",
                                       on_click=lambda: PatientDoctorTabState.open_confirm_unlink(doc.doctor_id, doc.full_name)),
                        content=LanguageState.tr["doctor_unlink_tooltip"],
                    ),
                    spacing="1",
                ),
            )
        ),
    )


def _doctor_confirm_unlink_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(LanguageState.tr["doctor_unlink_tooltip"]),
            rx.alert_dialog.description(
                rx.text(
                    LanguageState.tr["confirm_unlink_doctor_msg"],
                    " ",
                    rx.text.strong(PatientDoctorTabState.confirm_unlink_doctor_name),
                    " ?",
                    size="2",
                ),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="outline", color_scheme="gray", size="2",
                        on_click=PatientDoctorTabState.close_confirm_unlink,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        LanguageState.tr["confirm_btn"],
                        color_scheme="red", size="2",
                        on_click=lambda: PatientDoctorTabState.unlink_doctor(PatientDoctorTabState.confirm_unlink_doctor_id),
                    ),
                ),
                spacing="3", justify="end", margin_top="1rem",
            ),
        ),
        open=PatientDoctorTabState.confirm_unlink_open,
    )


def _doctor_confirm_clear_referent_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(LanguageState.tr["doctor_remove_referent_tooltip"]),
            rx.alert_dialog.description(
                rx.text(
                    LanguageState.tr["confirm_clear_referent_msg"],
                    " ",
                    rx.text.strong(PatientDoctorTabState.confirm_clear_referent_doctor_name),
                    " ?",
                    size="2",
                ),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="outline", color_scheme="gray", size="2",
                        on_click=PatientDoctorTabState.close_confirm_clear_referent,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        LanguageState.tr["confirm_btn"],
                        color_scheme="amber", size="2",
                        on_click=lambda: PatientDoctorTabState.clear_referent(PatientDoctorTabState.confirm_clear_referent_doctor_id),
                    ),
                ),
                spacing="3", justify="end", margin_top="1rem",
            ),
        ),
        open=PatientDoctorTabState.confirm_clear_referent_open,
    )


def _doctors_tab() -> rx.Component:
    return rx.vstack(
        _doctor_picker_dialog(),
        _doctor_confirm_unlink_dialog(),
        _doctor_confirm_clear_referent_dialog(),
        rx.cond(
            PatientDoctorTabState.error_message != "",
            rx.callout(PatientDoctorTabState.error_message, icon="alert-circle", color_scheme="red", size="1"),
        ),
        rx.cond(
            PatientDoctorTabState.is_loading,
            rx.center(rx.spinner(size="2"), padding="2rem"),
            rx.cond(
                PatientDoctorTabState.linked_doctors.length() > 0,
                rx.table.root(
                    rx.table.header(rx.table.row(
                        rx.table.column_header_cell(LanguageState.tr["col_name"]),
                        rx.table.column_header_cell(LanguageState.tr["col_specialization"]),
                        rx.table.column_header_cell(LanguageState.tr["col_phone"]),
                        rx.table.column_header_cell(""),
                    )),
                    rx.table.body(rx.foreach(PatientDoctorTabState.linked_doctors, _linked_doctor_row)),
                    width="100%", variant="surface",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("user-round-x", size=40, color="var(--gray-6)"),
                        rx.text(LanguageState.tr["no_doctors_linked"], size="2", color="var(--gray-9)"),
                        spacing="2", align="center",
                    ),
                    padding="4rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="8px",
                    width="100%",
                ),
            ),
        ),
        width="100%", spacing="3",
    )


# ── Accounts tab ──────────────────────────────────────────────────────────────

def _account_picker_row_tab(account: AccountPickerRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(account.name, size="2", weight="medium")),
        rx.table.cell(rx.cond(account.city != "", rx.text(account.city, size="2"), rx.text("—", size="2", color="var(--gray-8)"))),
        _hover={"background_color": "var(--accent-2)", "cursor": "pointer"},
        on_click=lambda: PatientAccountTabState.link_account(account.id),
    )


def _account_picker_dialog_tab() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["acct_picker_title"]),
            rx.vstack(
                rx.input(
                    rx.input.slot(rx.icon("search", size=14)),
                    placeholder=LanguageState.tr["acct_picker_filter_placeholder"],
                    value=PatientAccountTabState.picker_filter,
                    on_change=PatientAccountTabState.set_picker_filter,
                    size="2", width="100%",
                ),
                rx.cond(
                    PatientAccountTabState.picker_error != "",
                    rx.callout(PatientAccountTabState.picker_error, icon="alert-circle", color_scheme="red", size="1"),
                ),
                rx.cond(
                    PatientAccountTabState.picker_is_loading,
                    rx.center(rx.spinner(size="2"), padding="1.5rem"),
                    rx.cond(
                        PatientAccountTabState.picker_rows.length() > 0,
                        rx.box(
                            rx.table.root(
                                rx.table.header(rx.table.row(
                                    rx.table.column_header_cell(LanguageState.tr["col_account_name"]),
                                    rx.table.column_header_cell(LanguageState.tr["field_city"]),
                                )),
                                rx.table.body(rx.foreach(PatientAccountTabState.picker_rows, _account_picker_row_tab)),
                                width="100%", variant="surface",
                            ),
                            max_height="320px", overflow_y="auto", width="100%",
                        ),
                        rx.center(rx.text(LanguageState.tr["no_accounts_found"], size="2", color="var(--gray-9)"), padding="1.5rem"),
                    ),
                ),
                rx.hstack(
                    rx.button(LanguageState.tr["cancel_btn"], variant="soft", color_scheme="gray",
                              on_click=PatientAccountTabState.close_picker),
                    justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            on_interact_outside=PatientAccountTabState.close_picker,
            on_escape_key_down=PatientAccountTabState.close_picker,
            max_width="500px",
        ),
        open=PatientAccountTabState.picker_open,
    )


def _linked_account_row(acct: LinkedAccountRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(acct.name, size="2", weight="medium")),
        rx.table.cell(
            rx.match(
                acct.account_type,
                ("COMPANY", rx.badge(LanguageState.tr["account_company_badge"], color_scheme="blue", variant="soft", size="1")),
                ("INDIVIDUAL", rx.badge(LanguageState.tr["account_individual_badge"], color_scheme="purple", variant="soft", size="1")),
                rx.badge(acct.account_type, color_scheme="gray", variant="soft", size="1"),
            )
        ),
        rx.table.cell(rx.cond(acct.city != "", rx.text(acct.city, size="2"), rx.text("—", size="2", color="var(--gray-8)"))),
        rx.table.cell(rx.cond(acct.phone != "", rx.text(acct.phone, size="2"), rx.text("—", size="2", color="var(--gray-8)"))),
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(rx.icon("unlink", size=13), variant="ghost", color_scheme="red", size="1",
                               on_click=lambda: PatientAccountTabState.open_confirm_unlink(acct.account_id, acct.name)),
                content=LanguageState.tr["account_unlink_tooltip"],
            )
        ),
    )


def _account_confirm_unlink_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(LanguageState.tr["account_unlink_tooltip"]),
            rx.alert_dialog.description(
                rx.text(
                    LanguageState.tr["confirm_unlink_account_msg"],
                    " ",
                    rx.text.strong(PatientAccountTabState.confirm_unlink_account_name),
                    " ?",
                    size="2",
                ),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="outline", color_scheme="gray", size="2",
                        on_click=PatientAccountTabState.close_confirm_unlink,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        LanguageState.tr["confirm_btn"],
                        color_scheme="red", size="2",
                        on_click=lambda: PatientAccountTabState.unlink_account(PatientAccountTabState.confirm_unlink_account_id),
                    ),
                ),
                spacing="3", justify="end", margin_top="1rem",
            ),
        ),
        open=PatientAccountTabState.confirm_unlink_open,
    )


def _campaign_row(c: PatientCampaignRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.link(c.name, on_click=lambda: PatientCampaignTabState.go_to_campaign(c.campaign_id), cursor="pointer", color="var(--accent-9)")),
        rx.table.cell(rx.text(c.campaign_number, size="2")),
        rx.table.cell(rx.text(c.start_date, size="2")),
        rx.table.cell(rx.badge(c.status_label, color_scheme=c.status_color, variant="soft", size="1")),
    )


def _campaigns_tab() -> rx.Component:
    return rx.vstack(
        rx.cond(
            PatientCampaignTabState.error_message != "",
            rx.callout(PatientCampaignTabState.error_message, icon="alert-circle", color_scheme="red", size="1"),
        ),
        rx.cond(
            PatientCampaignTabState.is_loading,
            rx.center(rx.spinner(size="2"), padding="2rem"),
            rx.cond(
                PatientCampaignTabState.campaigns.length() > 0,
                rx.table.root(
                    rx.table.header(rx.table.row(
                        rx.table.column_header_cell("Campagne"),
                        rx.table.column_header_cell("Numéro"),
                        rx.table.column_header_cell("Date début"),
                        rx.table.column_header_cell("Statut"),
                    )),
                    rx.table.body(rx.foreach(PatientCampaignTabState.campaigns, _campaign_row)),
                    width="100%", variant="surface",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("clipboard-x", size=40, color="var(--gray-6)"),
                        rx.text("Aucune campagne trouvée", size="2", color="var(--gray-9)"),
                        spacing="2", align="center",
                    ),
                    padding="4rem", border="1px dashed var(--gray-5)", border_radius="8px", width="100%",
                ),
            ),
        ),
        width="100%", spacing="3",
    )


def _accounts_tab() -> rx.Component:
    return rx.vstack(
        _account_picker_dialog_tab(),
        _account_confirm_unlink_dialog(),
        rx.cond(
            PatientAccountTabState.error_message != "",
            rx.callout(PatientAccountTabState.error_message, icon="alert-circle", color_scheme="red", size="1"),
        ),
        rx.cond(
            PatientAccountTabState.is_loading,
            rx.center(rx.spinner(size="2"), padding="2rem"),
            rx.cond(
                PatientAccountTabState.linked_accounts.length() > 0,
                rx.table.root(
                    rx.table.header(rx.table.row(
                        rx.table.column_header_cell(LanguageState.tr["col_account_name"]),
                        rx.table.column_header_cell(LanguageState.tr["col_type"]),
                        rx.table.column_header_cell(LanguageState.tr["col_city"]),
                        rx.table.column_header_cell(LanguageState.tr["col_phone"]),
                        rx.table.column_header_cell(""),
                    )),
                    rx.table.body(rx.foreach(PatientAccountTabState.linked_accounts, _linked_account_row)),
                    width="100%", variant="surface",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("building-x", size=40, color="var(--gray-6)"),
                        rx.text(LanguageState.tr["no_accounts_linked"], size="2", color="var(--gray-9)"),
                        spacing="2", align="center",
                    ),
                    padding="4rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="8px",
                    width="100%",
                ),
            ),
        ),
        width="100%", spacing="3",
    )


def _archive_dialog() -> rx.Component:
    """Confirmation dialog for archiving a patient."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(rx.icon("archive", size=18, color="var(--orange-9)"), rx.text("Archiver le patient"), spacing="2", align="center"),
            ),
            rx.dialog.description(
                "Le patient sera archivé et masqué des listes actives. Cette action est réversible. Un motif est obligatoire.",
                size="2",
                color="var(--gray-11)",
                margin_bottom="1rem",
            ),
            rx.vstack(
                rx.text("Motif d'archivage *", size="2", weight="medium"),
                rx.text_area(
                    value=PatientDetailState.archive_reason,
                    on_change=PatientDetailState.set_archive_reason,
                    placeholder="Indiquez le motif d'archivage (ex : départ de l'entreprise, doublon, erreur de saisie...)",
                    rows="3",
                    width="100%",
                ),
                rx.cond(
                    PatientDetailState.archive_error != "",
                    rx.callout(PatientDetailState.archive_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Annuler", variant="outline", size="2", on_click=PatientDetailState.close_archive_dialog),
                    ),
                    rx.button(
                        rx.cond(PatientDetailState.is_archiving, rx.spinner(size="2"), rx.icon("archive", size=15)),
                        "Confirmer l'archivage",
                        on_click=PatientDetailState.confirm_archive,
                        disabled=PatientDetailState.is_archiving,
                        color_scheme="orange",
                        size="2",
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                    margin_top="0.5rem",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="480px",
        ),
        open=PatientDetailState.show_archive_dialog,
        on_open_change=PatientDetailState.close_archive_dialog,
    )


def _delete_dialog() -> rx.Component:
    """Confirmation dialog for permanently deleting a patient."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(rx.icon("trash-2", size=18, color="var(--red-9)"), rx.text("Supprimer définitivement"), spacing="2", align="center"),
            ),
            rx.dialog.description(
                rx.vstack(
                    rx.text("⚠️ Cette action est irréversible.", size="2", weight="bold", color="var(--red-11)"),
                    rx.text("Toutes les données du patient seront supprimées définitivement. Un motif est obligatoire.", size="2", color="var(--gray-11)"),
                    spacing="1",
                ),
                margin_bottom="1rem",
            ),
            rx.vstack(
                rx.text("Motif de suppression *", size="2", weight="medium"),
                rx.text_area(
                    value=PatientDetailState.delete_reason,
                    on_change=PatientDetailState.set_delete_reason,
                    placeholder="Indiquez le motif de suppression (ex : doublon confirmé, demande RGPD, erreur de création...)",
                    rows="3",
                    width="100%",
                ),
                rx.cond(
                    PatientDetailState.delete_error != "",
                    rx.callout(PatientDetailState.delete_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Annuler", variant="outline", size="2", on_click=PatientDetailState.close_delete_dialog),
                    ),
                    rx.button(
                        rx.cond(PatientDetailState.is_deleting, rx.spinner(size="2"), rx.icon("trash-2", size=15)),
                        "Supprimer définitivement",
                        on_click=PatientDetailState.confirm_delete,
                        disabled=PatientDetailState.is_deleting,
                        color_scheme="red",
                        size="2",
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                    margin_top="0.5rem",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="480px",
        ),
        open=PatientDetailState.show_delete_dialog,
        on_open_change=PatientDetailState.close_delete_dialog,
    )


def patient_detail_page() -> rx.Component:
    """Patient detail page."""
    return main_component(
        page_layout(
            _archive_dialog(),
            _delete_dialog(),
            account_form_dialog(),
            patient_form_dialog(),
            prescription_form_dialog(),
            certificate_form_dialog(),
            id_card_dialog(),
            rx.button(
                rx.icon("arrow-left", size=16),
                LanguageState.tr["btn_back"],
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
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("user-round-check", size=15),
                                        rx.text(LanguageState.tr["tab_doctors"]),
                                        spacing="1",
                                        align="center",
                                    ),
                                    value="doctors",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("building-2", size=15),
                                        rx.text(LanguageState.tr["tab_accounts"]),
                                        spacing="1",
                                        align="center",
                                    ),
                                    value="accounts",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("clipboard-list", size=15),
                                        rx.text(LanguageState.tr["tab_campaigns"]),
                                        spacing="1",
                                        align="center",
                                    ),
                                    value="campaigns",
                                ),
                            ),
                            rx.tabs.content(_exams_section(), value="exams", padding_top="1rem"),
                            rx.tabs.content(_prescriptions_tab(), value="prescriptions", padding_top="1rem"),
                            rx.tabs.content(_certificates_tab(), value="certificates", padding_top="1rem"),
                            rx.tabs.content(_doctors_tab(), value="doctors", padding_top="1rem"),
                            rx.tabs.content(_accounts_tab(), value="accounts", padding_top="1rem"),
                            rx.tabs.content(_campaigns_tab(), value="campaigns", padding_top="1rem"),
                            default_value="exams",
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
