"""Dashboard page component — key statistics at a glance."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .dashboard_state import (
    AccountOptionDTO,
    AppointmentStatusStat,
    DashboardState,
    ExamTypeStat,
    MonthlyExamStat,
)

_APPOINTMENT_STATUS_COLORS = {
    "SCHEDULED": "blue",
    "IN_PROGRESS": "orange",
    "DONE": "green",
    "CANCELLED": "gray",
}


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
    color = rx.match(
        stat.status,
        ("SCHEDULED", "blue"),
        ("IN_PROGRESS", "orange"),
        ("DONE", "green"),
        ("CANCELLED", "gray"),
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


def _account_filter_option(account: AccountOptionDTO) -> rx.Component:
    return rx.select.item(account.name, value=account.id)


def dashboard_page() -> rx.Component:
    """Main dashboard with aggregated statistics."""
    return main_component(
        page_layout(
            rx.hstack(
                rx.heading("Dashboard", size="6"),
                rx.spacer(),
                rx.select.root(
                    rx.select.trigger(placeholder="All Accounts"),
                    rx.select.content(
                        rx.select.item("All Accounts", value="ALL"),
                        rx.foreach(DashboardState.companies, _account_filter_option),
                    ),
                    value=DashboardState.filter_account_id,
                    on_change=DashboardState.set_filter_account,
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                DashboardState.error_message != "",
                rx.callout(
                    DashboardState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                DashboardState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.vstack(
                    # KPI row
                    rx.grid(
                        _kpi_card("Patients", DashboardState.total_patients, "users", "blue"),
                        _kpi_card("Exams", DashboardState.total_exams, "stethoscope", "violet"),
                        _kpi_card(
                            "Appointments",
                            DashboardState.total_appointments,
                            "calendar",
                            "orange",
                        ),
                        _kpi_card(
                            "Certificates",
                            DashboardState.total_certificates,
                            "file-check",
                            "green",
                        ),
                        columns="4",
                        spacing="4",
                        width="100%",
                    ),
                    # Charts row
                    rx.grid(
                        # Exams by type
                        _panel(
                            "Exams by Type",
                            "bar-chart-2",
                            rx.cond(
                                DashboardState.exams_by_type,
                                rx.vstack(
                                    rx.foreach(DashboardState.exams_by_type, _exam_type_row),
                                    width="100%",
                                    spacing="2",
                                ),
                                rx.text("No exams yet.", size="2", color="var(--gray-7)"),
                            ),
                        ),
                        # Appointments by status
                        _panel(
                            "Appointments by Status",
                            "pie-chart",
                            rx.cond(
                                DashboardState.appointments_by_status,
                                rx.vstack(
                                    rx.foreach(
                                        DashboardState.appointments_by_status,
                                        _appointment_status_row,
                                    ),
                                    width="100%",
                                    spacing="2",
                                ),
                                rx.text("No appointments yet.", size="2", color="var(--gray-7)"),
                            ),
                        ),
                        columns="2",
                        spacing="4",
                        width="100%",
                    ),
                    # Monthly trend
                    _panel(
                        "Monthly Exam Volume (last 12 months)",
                        "trending-up",
                        rx.cond(
                            DashboardState.monthly_exams,
                            rx.vstack(
                                rx.foreach(DashboardState.monthly_exams, _monthly_row),
                                width="100%",
                                spacing="2",
                            ),
                            rx.text("No data yet.", size="2", color="var(--gray-7)"),
                        ),
                    ),
                    width="100%",
                    spacing="5",
                ),
            ),
        )
    )
