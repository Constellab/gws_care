"""Patient portal Dashboard page component (/patient-dashboard).

Same visual layout as the admin dashboard_component.py but:
  - No account picker
  - KPIs scoped to the logged-in patient (exams, consultations, certificates, notifications)
  - Appointment status uses ConsultationVisitStatus values (lowercase)
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .patient_dashboard_state import (
    AppointmentStatusStat,
    ExamTypeStat,
    MonthlyExamStat,
    PatientDashboardState,
)


# ── Helpers — identical to admin dashboard_component.py ──────────────────────


def _kpi_card(label: str, value: rx.Var, icon: str, color: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=22, color=f"var(--{color}-9)"),
                rx.text(label, size="2", color="var(--gray-9)"),
                spacing="2",
                align="center",
            ),
            rx.text(value, size="8", weight="bold"),
            spacing="2",
            align_items="start",
        ),
        padding="1.25rem",
        border="1px solid var(--gray-4)",
        border_radius="10px",
        background="var(--gray-1)",
        width="100%",
    )


def _exam_type_row(stat: ExamTypeStat) -> rx.Component:
    return rx.hstack(
        rx.text(stat.label, size="2", flex="1"),
        rx.badge(stat.count, variant="soft", size="1"),
        rx.box(
            rx.box(
                height="8px",
                border_radius="4px",
                background="var(--accent-9)",
                width=f"{stat.count}px",
                max_width="200px",
            ),
            height="8px",
            background="var(--gray-4)",
            border_radius="4px",
            width="200px",
            overflow="hidden",
        ),
        width="100%",
        align="center",
        spacing="3",
    )


def _appointment_status_row(stat: AppointmentStatusStat) -> rx.Component:
    # ConsultationVisitStatus values: scheduled, in_progress, done, cancelled
    color = rx.match(
        stat.status,
        ("scheduled", "blue"),
        ("in_progress", "orange"),
        ("done", "green"),
        ("cancelled", "gray"),
        "gray",
    )
    return rx.hstack(
        rx.badge(stat.label, color_scheme=color, variant="soft", size="1", min_width="90px"),
        rx.text(stat.count, size="2", weight="bold"),
        spacing="3",
        align="center",
        width="100%",
    )


def _monthly_row(stat: MonthlyExamStat) -> rx.Component:
    return rx.hstack(
        rx.text(stat.month, size="2", color="var(--gray-9)", min_width="60px"),
        rx.box(
            rx.box(
                height="10px",
                border_radius="5px",
                background="var(--accent-9)",
                width=f"{stat.count * 20}px",
                max_width="300px",
            ),
            height="10px",
            background="var(--gray-4)",
            border_radius="5px",
            width="300px",
            overflow="hidden",
        ),
        rx.text(stat.count, size="2"),
        spacing="3",
        align="center",
        width="100%",
    )


def _panel(title: str, icon: str, *content: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon(icon, size=18, color="var(--accent-9)"),
            rx.heading(title, size="4"),
            spacing="2",
            align="center",
        ),
        rx.separator(width="100%"),
        *content,
        width="100%",
        padding="1.25rem",
        border="1px solid var(--gray-4)",
        border_radius="10px",
        background="var(--gray-1)",
        spacing="3",
    )


# ── Page ──────────────────────────────────────────────────────────────────────


def patient_dashboard_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.heading(LanguageState.tr["patient_dashboard_title"], size="6"),
            rx.cond(
                PatientDashboardState.error_message != "",
                rx.callout(
                    PatientDashboardState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                PatientDashboardState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.vstack(
                    # ── KPI row ───────────────────────────────────────────────
                    rx.grid(
                        _kpi_card(
                            LanguageState.tr["kpi_my_exams"],
                            PatientDashboardState.total_exams,
                            "stethoscope",
                            "violet",
                        ),
                        _kpi_card(
                            LanguageState.tr["kpi_my_consultations"],
                            PatientDashboardState.total_appointments,
                            "calendar",
                            "orange",
                        ),
                        _kpi_card(
                            LanguageState.tr["kpi_my_certificates"],
                            PatientDashboardState.total_certificates,
                            "file-check",
                            "green",
                        ),
                        _kpi_card(
                            LanguageState.tr["kpi_my_notifications"],
                            PatientDashboardState.total_notifications,
                            "bell",
                            "blue",
                        ),
                        columns="4",
                        spacing="4",
                        width="100%",
                    ),
                    # ── Charts row ────────────────────────────────────────────
                    rx.grid(
                        # Exams by type
                        _panel(
                            LanguageState.tr["panel_exams_by_type"],
                            "bar-chart-2",
                            rx.cond(
                                PatientDashboardState.exams_by_type,
                                rx.vstack(
                                    rx.foreach(PatientDashboardState.exams_by_type, _exam_type_row),
                                    width="100%",
                                    spacing="2",
                                ),
                                rx.text(LanguageState.tr["no_exams_yet"], size="2", color="var(--gray-7)"),
                            ),
                        ),
                        # Consultations by status
                        _panel(
                            LanguageState.tr["panel_appts_by_status"],
                            "pie-chart",
                            rx.cond(
                                PatientDashboardState.appointments_by_status,
                                rx.vstack(
                                    rx.foreach(
                                        PatientDashboardState.appointments_by_status,
                                        _appointment_status_row,
                                    ),
                                    width="100%",
                                    spacing="2",
                                ),
                                rx.text(LanguageState.tr["no_appts_yet"], size="2", color="var(--gray-7)"),
                            ),
                        ),
                        columns="2",
                        spacing="4",
                        width="100%",
                    ),
                    # ── Monthly trend ─────────────────────────────────────────
                    _panel(
                        LanguageState.tr["panel_monthly_exams"],
                        "trending-up",
                        rx.cond(
                            PatientDashboardState.monthly_exams,
                            rx.vstack(
                                rx.foreach(PatientDashboardState.monthly_exams, _monthly_row),
                                width="100%",
                                spacing="2",
                            ),
                            rx.text(LanguageState.tr["no_data_yet"], size="2", color="var(--gray-7)"),
                        ),
                    ),
                    width="100%",
                    spacing="5",
                ),
            ),
        )
    )
