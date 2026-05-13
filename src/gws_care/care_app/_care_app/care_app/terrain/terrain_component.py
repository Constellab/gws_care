"""Terrain page component (Phase 7.4).

Mobile-optimised layout for the Opérateur Terrain (OT).
Route: /on-site/[program_id_param]
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .qr_scanner_component import qr_scanner_component
from .terrain_state import TerrainExamDTO, TerrainPatientDTO, TerrainState

# ── Patient card ──────────────────────────────────────────────────────────────


def _terrain_status_badge(p: TerrainPatientDTO) -> rx.Component:
    return rx.match(
        p.visit_status,
        ("pending", rx.badge("Pending", color_scheme="gray", variant="soft", size="1")),
        ("on-site_done", rx.badge("Terrain ✓", color_scheme="green", variant="solid", size="1")),
        ("results_entered", rx.badge("Results Entered", color_scheme="orange", variant="soft", size="1")),
        ("lab_validated", rx.badge("Lab Validated", color_scheme="blue", variant="soft", size="1")),
        ("doctor_clinic_validated", rx.badge("Clinic Doctor Validated", color_scheme="violet", variant="soft", size="1")),
        ("doctor_company_validated", rx.badge("Company Doctor Validated", color_scheme="green", variant="soft", size="1")),
        rx.badge(p.visit_status_label, color_scheme="gray", variant="soft", size="1"),
    )


def _exam_row(e: TerrainExamDTO) -> rx.Component:
    """Single exam row in the patient's checklist."""
    return rx.hstack(
        rx.cond(
            e.is_done_on_site,
            rx.icon("circle_check_big", size=18, color="var(--green-9)"),
            rx.icon("circle", size=18, color="var(--gray-7)"),
        ),
        rx.vstack(
            rx.text(e.exam_type_name, size="2", weight="medium"),
            rx.cond(
                e.tube_qr_code != "",
                rx.text(e.tube_qr_code, size="1", color="var(--gray-9)"),
            ),
            spacing="0",
            align_items="start",
        ),
        rx.spacer(),
        rx.cond(
            ~e.is_done_on_site,
            rx.button(
                rx.icon("check", size=12),
                "Fait",
                variant="soft",
                color_scheme="green",
                size="1",
                on_click=lambda: TerrainState.mark_exam_done(e.id, e.patient_id, e.visit_id, e.exam_type_code),
            ),
        ),
        align="center",
        width="100%",
        spacing="2",
        padding="4px 0",
    )


def _patient_card(p: TerrainPatientDTO) -> rx.Component:
    return rx.card(
        rx.vstack(
            # Patient header row
            rx.hstack(
                # QR code
                rx.cond(
                    p.qr_code != "",
                    rx.image(
                        src=p.qr_code,
                        width="72px",
                        height="72px",
                        border_radius="4px",
                        flex_shrink="0",
                    ),
                    rx.box(
                        rx.icon("qr-code", size=36, color="var(--gray-7)"),
                        width="72px",
                        height="72px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        background="var(--gray-2)",
                        border_radius="4px",
                        flex_shrink="0",
                    ),
                ),
                # Info
                rx.vstack(
                    rx.hstack(
                        rx.text(p.full_name, size="3", weight="bold"),
                        rx.spacer(),
                        _terrain_status_badge(p),
                        align="center",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.text(p.patient_number, size="2", color="var(--gray-9)"),
                        rx.separator(orientation="vertical"),
                        rx.text("Né(e) le " + p.date_of_birth, size="2", color="var(--gray-9)"),
                        spacing="2",
                        align="center",
                    ),
                    # Exam progress summary
                    rx.cond(
                        p.exams_total > 0,
                        rx.hstack(
                            rx.icon("circle_check", size=13, color="var(--green-9)"),
                            rx.text(
                                p.exams_done.to_string() + " / " + p.exams_total.to_string() + " exams done",
                                size="2",
                                color="var(--gray-9)",
                            ),
                            spacing="1",
                            align="center",
                        ),
                    ),
                    width="100%",
                    spacing="1",
                    align_items="start",
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            # Exam checklist
            rx.cond(
                p.exams_total > 0,
                rx.vstack(
                    rx.separator(width="100%"),
                    rx.foreach(p.exams, _exam_row),
                    width="100%",
                    spacing="1",
                ),
            ),
            # Mark all on-site done (if visit is still pending)
            rx.cond(
                p.visit_status == "pending",
                rx.button(
                    rx.icon("check-check", size=14),
                    "Mark on-site visit as done",
                    variant="solid",
                    color_scheme="green",
                    size="2",
                    width="100%",
                    on_click=lambda: TerrainState.mark_terrain_done(p.id),
                ),
            ),
            width="100%",
            spacing="2",
        ),
        width="100%",
    )


def terrain_page() -> rx.Component:
    return main_component(
        page_layout(
            # Back + header
            rx.hstack(
                rx.button(
                    rx.icon("arrow-left", size=14),
                    "Retour à la campagne",
                    variant="ghost",
                    size="2",
                    on_click=TerrainState.go_back,
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("download", size=14),
                    "PDF QR Codes",
                    variant="soft",
                    size="2",
                    loading=TerrainState.is_downloading_pdf,
                    on_click=TerrainState.download_pdf,
                ),
                width="100%",
                align="center",
            ),
            # MedicalProgram info
            rx.card(
                rx.vstack(
                    rx.heading(TerrainState.campaign_name, size="5"),
                    rx.hstack(
                        rx.text(TerrainState.program_number, size="2", color="var(--gray-9)"),
                        rx.separator(orientation="vertical"),
                        rx.text(TerrainState.account_name, size="2", color="var(--gray-9)"),
                        rx.separator(orientation="vertical"),
                        rx.icon("calendar", size=13, color="var(--gray-9)"),
                        rx.text(
                            TerrainState.campaign_start_date + " → " + TerrainState.campaign_end_date,
                            size="2",
                            color="var(--gray-9)",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    width="100%",
                    spacing="1",
                )
            ),
            # Scanner section
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Scanner un QR code", size="4"),
                        rx.spacer(),
                        rx.button(
                            rx.cond(
                                TerrainState.scanner_active,
                                rx.hstack(rx.icon("camera-off", size=14), rx.text("Arrêter caméra"), spacing="1"),
                                rx.hstack(rx.icon("camera", size=14), rx.text("Scanner caméra"), spacing="1"),
                            ),
                            variant=rx.cond(TerrainState.scanner_active, "solid", "soft"),
                            color_scheme=rx.cond(TerrainState.scanner_active, "red", "blue"),
                            size="2",
                            on_click=TerrainState.toggle_scanner,
                        ),
                        align="center",
                        width="100%",
                    ),
                    # Camera scanner (shown when active)
                    rx.cond(
                        TerrainState.scanner_active,
                        rx.vstack(
                            qr_scanner_component(
                                active=TerrainState.scanner_active,
                                on_scan=TerrainState.on_scan_detected,
                                on_error=TerrainState.on_scan_error,
                                width="100%",
                            ),
                            rx.text(
                                "Pointez la caméra vers un QR code patient ou tube.",
                                size="2",
                                color="var(--gray-9)",
                                text_align="center",
                            ),
                            width="100%",
                            spacing="2",
                        ),
                    ),
                    # Manual entry fallback
                    rx.hstack(
                        rx.input(
                            placeholder="Ou saisir manuellement (n° patient, code tube)…",
                            value=TerrainState.scan_result,
                            on_change=TerrainState.set_scan_result,
                            size="3",
                            flex="1",
                        ),
                        rx.button(
                            rx.icon("search", size=16),
                            "Rechercher",
                            on_click=TerrainState.process_scan,
                            size="3",
                        ),
                        rx.cond(
                            TerrainState.scan_result != "",
                            rx.button(
                                rx.icon("x", size=14),
                                variant="ghost",
                                size="3",
                                on_click=TerrainState.clear_scan,
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.cond(
                        TerrainState.scan_error != "",
                        rx.callout(
                            TerrainState.scan_error,
                            color_scheme="red",
                            icon="triangle-alert",
                            size="1",
                        ),
                    ),
                    rx.cond(
                        TerrainState.scan_found_patient != None,  # noqa: E711
                        rx.callout(
                            "Patient trouvé : " + TerrainState.scan_found_patient.full_name,
                            color_scheme="green",
                            icon="circle_check",
                            size="1",
                        ),
                    ),
                    width="100%",
                    spacing="3",
                )
            ),
            # Alerts
            rx.cond(
                TerrainState.error_message != "",
                rx.callout(
                    TerrainState.error_message,
                    color_scheme="red",
                    icon="triangle-alert",
                    size="2",
                ),
            ),
            rx.cond(
                TerrainState.success_message != "",
                rx.callout(
                    TerrainState.success_message,
                    color_scheme="green",
                    icon="circle_check",
                    size="2",
                ),
            ),
            # Search filter
            rx.hstack(
                rx.input(
                    rx.input.slot(rx.icon("search", size=13)),
                    placeholder="Rechercher par nom ou n° dossier…",
                    value=TerrainState.search_query,
                    on_change=TerrainState.set_search_query,
                    size="2",
                    flex="1",
                ),
                rx.text(
                    TerrainState.filtered_patients.length().to_string() + " patients",
                    size="2",
                    color="var(--gray-9)",
                    white_space="nowrap",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            # Patient cards
            rx.cond(
                TerrainState.is_loading,
                rx.center(rx.spinner(size="3"), padding="4rem"),
                rx.cond(
                    TerrainState.filtered_patients.length() == 0,
                    rx.center(
                        rx.vstack(
                            rx.icon("users", size=40, color="var(--gray-7)"),
                            rx.text("Aucun patient trouvé.", size="3", color="var(--gray-9)"),
                            spacing="3",
                            align="center",
                        ),
                        padding="3rem",
                    ),
                    rx.vstack(
                        rx.foreach(TerrainState.filtered_patients, _patient_card),
                        width="100%",
                        spacing="3",
                    ),
                ),
            ),
            width="100%",
            spacing="4",
            max_width="800px",
            margin="0 auto",
        )
    )
