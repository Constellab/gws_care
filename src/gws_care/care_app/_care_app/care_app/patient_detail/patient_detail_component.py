"""Patient detail page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..appointment_list.appointment_form_component import appointment_form_dialog
from ..appointment_list.appointment_form_state import AppointmentFormState
from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..patient_list.patient_form_component import patient_form_dialog
from ..patient_list.patient_form_state import PatientFormState
from .exam_form_component import exam_form_dialog
from .exam_form_state import ExamFormState
from .patient_detail_state import (
    AppointmentRowDTO,
    CampaignEnrollmentDTO,
    ExamRowDTO,
    PatientDetailDTO,
    PatientDetailState,
)
from .patient_dossier_state import (
    PATIENT_DOC_TYPE_OPTIONS,
    PatientDocRowDTO,
    PatientDossierState,
    PatientNoteRowDTO,
)


def _info_row(label: str, value: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="2", weight="medium", color="var(--gray-9)", min_width="180px"),
        rx.cond(value, rx.text(value, size="2"), rx.text("—", size="2", color="var(--gray-7)")),
        spacing="4",
        align="start",
        padding_y="0.4rem",
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
                    rx.icon("download", size=15),
                    LanguageState.tr["export_csv"],
                    on_click=PatientDetailState.download_exam_history,
                    variant="ghost",
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


def _exam_status_badge(status: str) -> rx.Component:
    return rx.match(
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
        rx.cond(
            PatientDetailState.exams,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(LanguageState.tr["col_date"]),
                        rx.table.column_header_cell(LanguageState.tr["col_type"]),
                        rx.table.column_header_cell(LanguageState.tr["col_status"]),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(PatientDetailState.exams, _exam_row),
                ),
                width="100%",
                variant="surface",
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


def _appointment_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("SCHEDULED", rx.badge(LanguageState.tr["status_scheduled"], color_scheme="blue", variant="soft", size="1")),
        ("IN_PROGRESS", rx.badge(LanguageState.tr["status_in_progress"], color_scheme="orange", variant="soft", size="1")),
        ("DONE", rx.badge(LanguageState.tr["status_done"], color_scheme="green", variant="soft", size="1")),
        ("CANCELLED", rx.badge(LanguageState.tr["status_cancelled"], color_scheme="gray", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _appointment_row(appt: AppointmentRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(appt.scheduled_at[:16].replace("T", " "), size="2")),
        rx.table.cell(rx.text(appt.exam_type_label, size="2")),
        rx.table.cell(
            rx.cond(
                appt.account_name,
                rx.text(appt.account_name, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(_appointment_status_badge(appt.status)),
        _hover={"background": "var(--gray-2)"},
    )


def _campaigns_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Campagnes de santé", size="4"),
            rx.spacer(),
            width="100%",
            align="center",
        ),
        rx.cond(
            PatientDetailState.campaign_enrollments,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Campagne"),
                        rx.table.column_header_cell("Compte"),
                        rx.table.column_header_cell("Date"),
                        rx.table.column_header_cell("Statut médical"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(PatientDetailState.campaign_enrollments, _campaign_enrollment_row),
                ),
                width="100%",
                variant="surface",
            ),
            rx.center(
                rx.text("Ce patient ne participe à aucune campagne.",
                        color="var(--gray-8)", size="2"),
                padding="2rem",
                border="1px dashed var(--gray-5)",
                border_radius="8px",
                width="100%",
            ),
        ),
        width="100%",
        spacing="3",
    )


def _campaign_enrollment_row(e: CampaignEnrollmentDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(e.campaign_name, size="2", weight="medium")),
        rx.table.cell(
            rx.cond(
                e.account_name != "",
                rx.text(e.account_name, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                e.start_date != "",
                rx.text(e.start_date, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.badge(e.status_label, color_scheme="blue", variant="soft", size="1"),
        ),
        rx.table.cell(
            rx.button(
                rx.icon("chevron-right", size=14),
                variant="ghost",
                size="1",
                on_click=rx.redirect("/campaign/" + e.campaign_id),
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _appointments_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading(LanguageState.tr["appointments_section_title"], size="4"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=15),
                LanguageState.tr["new_appointment_btn"],
                on_click=lambda: AppointmentFormState.open_create_dialog(
                    PatientDetailState.patient.id,
                    f"{PatientDetailState.patient.first_name} {PatientDetailState.patient.last_name}",
                ),
                size="2",
            ),
            rx.button(
                LanguageState.tr["view_all_btn"],
                on_click=PatientDetailState.go_to_appointments,
                variant="ghost",
                size="2",
            ),
            width="100%",
            align="center",
            spacing="2",
        ),
        rx.cond(
            PatientDetailState.appointments,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(LanguageState.tr["col_scheduled"]),
                        rx.table.column_header_cell(LanguageState.tr["col_exam_type"]),
                        rx.table.column_header_cell(LanguageState.tr["col_account"]),
                        rx.table.column_header_cell(LanguageState.tr["col_status"]),
                    )
                ),
                rx.table.body(
                    rx.foreach(PatientDetailState.appointments, _appointment_row),
                ),
                width="100%",
                variant="surface",
            ),
            rx.center(
                rx.text(LanguageState.tr["no_appts_section"], color="var(--gray-8)", size="2"),
                padding="2rem",
                border="1px dashed var(--gray-5)",
                border_radius="8px",
                width="100%",
            ),
        ),
        width="100%",
        spacing="3",
    )


# ── Document types dropdown options ──────────────────────────────────────────
_DOC_TYPE_ITEMS = [rx.select.item(label, value=value) for value, label in PATIENT_DOC_TYPE_OPTIONS]


def _doc_row(doc: PatientDocRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.icon("file", size=14, color="var(--gray-8)"),
                rx.link(
                    doc.original_name,
                    href=rx.get_upload_url(doc.stored_filename),
                    target="_blank",
                    size="2",
                ),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(rx.badge(doc.type_label, variant="soft", size="1")),
        rx.table.cell(rx.text(doc.uploaded_by_name, size="2", color="var(--gray-9)")),
        rx.table.cell(rx.text(doc.created_at, size="2", color="var(--gray-8)")),
        rx.table.cell(rx.text(doc.file_size_kb, size="2", color="var(--gray-7)")),
        rx.table.cell(
            rx.icon_button(
                rx.icon("trash-2", size=13),
                color_scheme="red",
                variant="ghost",
                size="1",
                on_click=PatientDossierState.delete_patient_doc(doc.id),
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _documents_section() -> rx.Component:
    """Document upload and list section for the patient dossier."""
    return rx.vstack(
        rx.hstack(
            rx.icon("folder-open", size=18, color="var(--blue-9)"),
            rx.heading("Documents du dossier", size="4"),
            rx.spacer(),
            width="100%",
            align="center",
        ),
        # Upload bar
        rx.hstack(
            rx.select.root(
                rx.select.trigger(size="2", width="200px"),
                rx.select.content(
                    *_DOC_TYPE_ITEMS,
                ),
                value=PatientDossierState.selected_doc_type,
                on_change=PatientDossierState.set_selected_doc_type,
                size="2",
            ),
            rx.upload(
                rx.button(
                    rx.cond(
                        PatientDossierState.is_uploading_doc,
                        rx.spinner(size="2"),
                        rx.icon("upload", size=15),
                    ),
                    "Ajouter un document",
                    size="2",
                    variant="outline",
                    disabled=PatientDossierState.is_uploading_doc,
                ),
                id="patient_doc_upload",
                accept={
                    "application/pdf": [".pdf"],
                    "image/jpeg": [".jpg", ".jpeg"],
                    "image/png": [".png"],
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
                },
                multiple=True,
                on_drop=PatientDossierState.handle_doc_upload(
                    rx.upload_files(upload_id="patient_doc_upload")
                ),
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        # Document list
        rx.cond(
            PatientDossierState.patient_docs,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Fichier"),
                        rx.table.column_header_cell("Type"),
                        rx.table.column_header_cell("Ajouté par"),
                        rx.table.column_header_cell("Date"),
                        rx.table.column_header_cell("Taille"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(PatientDossierState.patient_docs, _doc_row),
                ),
                width="100%",
                variant="surface",
            ),
            rx.center(
                rx.text(
                    "Aucun document dans le dossier.",
                    size="2", color="var(--gray-7)",
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


def _note_card(note: PatientNoteRowDTO) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.icon("user-round", size=14, color="var(--blue-9)"),
                rx.text(note.author_name, size="2", weight="medium"),
                spacing="1",
                align="center",
            ),
            rx.spacer(),
            rx.text(note.created_at, size="1", color="var(--gray-7)"),
            rx.icon_button(
                rx.icon("trash-2", size=12),
                color_scheme="red",
                variant="ghost",
                size="1",
                on_click=PatientDossierState.delete_patient_note(note.id),
            ),
            width="100%",
            align="center",
        ),
        rx.separator(width="100%", my="2"),
        rx.text(note.content, size="2", color="var(--gray-12)", white_space="pre-wrap"),
        padding="0.75rem 1rem",
        border="1px solid var(--gray-4)",
        border_radius="8px",
        background="var(--gray-1)",
        width="100%",
    )


def _notes_section() -> rx.Component:
    """Doctor notes section for the patient dossier."""
    return rx.vstack(
        rx.hstack(
            rx.icon("notebook-pen", size=18, color="var(--green-9)"),
            rx.heading("Notes médicales", size="4"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=15),
                "Ajouter une note",
                on_click=PatientDossierState.toggle_note_input,
                size="2",
                variant="outline",
                color_scheme="green",
            ),
            width="100%",
            align="center",
        ),
        # Inline note input (toggled)
        rx.cond(
            PatientDossierState.show_note_input,
            rx.vstack(
                rx.text_area(
                    value=PatientDossierState.new_note_text,
                    on_change=PatientDossierState.set_new_note_text,
                    placeholder="Rédigez votre note médicale ici…",
                    rows="5",
                    width="100%",
                    resize="vertical",
                ),
                rx.hstack(
                    rx.button(
                        rx.cond(
                            PatientDossierState.is_saving_note,
                            rx.spinner(size="2"),
                            rx.icon("save", size=14),
                        ),
                        "Enregistrer la note",
                        on_click=PatientDossierState.add_patient_note,
                        disabled=PatientDossierState.is_saving_note,
                        size="2",
                        color_scheme="green",
                    ),
                    rx.button(
                        "Annuler",
                        on_click=PatientDossierState.toggle_note_input,
                        variant="ghost",
                        size="2",
                    ),
                    spacing="2",
                ),
                width="100%",
                spacing="2",
                padding="1rem",
                border="1px solid var(--green-6)",
                border_radius="8px",
                background="var(--green-1)",
            ),
        ),
        # Notes list
        rx.cond(
            PatientDossierState.patient_notes,
            rx.vstack(
                rx.foreach(PatientDossierState.patient_notes, _note_card),
                width="100%",
                spacing="2",
            ),
            rx.cond(
                ~PatientDossierState.show_note_input,
                rx.center(
                    rx.text(
                        "Aucune note médicale pour ce patient.",
                        size="2", color="var(--gray-7)",
                    ),
                    padding="2rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="8px",
                    width="100%",
                ),
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
            appointment_form_dialog(),
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
                        _campaigns_section(),
                        _appointments_section(),
                        _exams_section(),
                        _documents_section(),
                        _notes_section(),
                        width="100%",
                        spacing="6",
                    ),
                    rx.center(rx.text(LanguageState.tr["patient_not_found"], color="var(--gray-9)"), padding="3rem"),
                ),
            ),
        )
    )
