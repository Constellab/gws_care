"""Patient detail page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..appointment_list.appointment_form_component import appointment_form_dialog
from ..appointment_list.appointment_form_state import AppointmentFormState
from ..common.page_layout import page_layout
from ..patient_list.patient_form_component import patient_form_dialog
from ..patient_list.patient_form_state import PatientFormState
from .exam_form_component import exam_form_dialog
from .exam_form_state import ExamFormState
from .patient_detail_state import (
    AppointmentRowDTO,
    ExamRowDTO,
    PatientDetailDTO,
    PatientDetailState,
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
                        ("M", rx.badge("Male", color_scheme="blue", variant="soft", size="2")),
                        ("F", rx.badge("Female", color_scheme="pink", variant="soft", size="2")),
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
                    "Export CSV",
                    on_click=PatientDetailState.download_exam_history,
                    variant="ghost",
                    size="2",
                ),
                rx.button(
                    rx.icon("pencil", size=15),
                    "Edit",
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
                "Personal Information",
                _info_row("Date of Birth", patient.date_of_birth),
                _info_row("Birth Name", patient.birth_name),
                _info_row("Gender", patient.gender),
            ),
            _section(
                "Contact",
                _info_row("Phone", patient.phone),
                _info_row("Email", patient.email),
                _info_row("Address", patient.address),
                _info_row("Postal Code", patient.postal_code),
                _info_row("City", patient.city),
            ),
            _section(
                "Primary Care Physician",
                _info_row("Name", patient.primary_physician_name),
                _info_row("Phone", patient.primary_physician_phone),
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
        ("DRAFT", rx.badge("Draft", color_scheme="gray", variant="soft", size="1")),
        ("PENDING", rx.badge("Pending", color_scheme="orange", variant="soft", size="1")),
        ("INTERPRETED", rx.badge("Interpreted", color_scheme="green", variant="soft", size="1")),
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
                "View",
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
            rx.heading("Exams", size="4"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=15),
                "New Exam",
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
                        rx.table.column_header_cell("Date"),
                        rx.table.column_header_cell("Type"),
                        rx.table.column_header_cell("Status"),
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
                rx.text("No exams recorded yet.", color="var(--gray-8)", size="2"),
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
        ("SCHEDULED", rx.badge("Scheduled", color_scheme="blue", variant="soft", size="1")),
        ("IN_PROGRESS", rx.badge("In Progress", color_scheme="orange", variant="soft", size="1")),
        ("DONE", rx.badge("Done", color_scheme="green", variant="soft", size="1")),
        ("CANCELLED", rx.badge("Cancelled", color_scheme="gray", variant="soft", size="1")),
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


def _appointments_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Appointments", size="4"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=15),
                "New Appointment",
                on_click=lambda: AppointmentFormState.open_create_dialog(
                    PatientDetailState.patient.id,
                    f"{PatientDetailState.patient.first_name} {PatientDetailState.patient.last_name}",
                ),
                size="2",
            ),
            rx.button(
                "View All",
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
                        rx.table.column_header_cell("Scheduled"),
                        rx.table.column_header_cell("Exam Type"),
                        rx.table.column_header_cell("Account"),
                        rx.table.column_header_cell("Status"),
                    )
                ),
                rx.table.body(
                    rx.foreach(PatientDetailState.appointments, _appointment_row),
                ),
                width="100%",
                variant="surface",
            ),
            rx.center(
                rx.text("No appointments yet.", color="var(--gray-8)", size="2"),
                padding="2rem",
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
            appointment_form_dialog(),
            rx.button(
                rx.icon("arrow-left", size=16),
                "Back to patients",
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
                        _appointments_section(),
                        _exams_section(),
                        width="100%",
                        spacing="6",
                    ),
                    rx.center(rx.text("Patient not found", color="var(--gray-9)"), padding="3rem"),
                ),
            ),
        )
    )
