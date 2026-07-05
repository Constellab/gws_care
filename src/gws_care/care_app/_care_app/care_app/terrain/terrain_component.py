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
        ("pending", rx.badge("En attente", color_scheme="gray", variant="soft", size="1")),
        ("visit_done", rx.badge(rx.icon("user-check", size=11), "Présent(e)", color_scheme="green", variant="solid", size="1")),
        ("cancelled", rx.badge(rx.icon("user-x", size=11), "Absent(e)", color_scheme="red", variant="solid", size="1")),
        ("lab_done", rx.badge(LanguageState.tr["status_lab_done"], color_scheme="blue", variant="soft", size="1")),
        ("doctor_clinic_validated", rx.badge(LanguageState.tr["status_doctor_clinic_validated"], color_scheme="violet", variant="soft", size="1")),
        ("doctor_company_validated", rx.badge(LanguageState.tr["status_doctor_company_validated"], color_scheme="green", variant="soft", size="1")),
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
                LanguageState.tr["terrain_done_btn"],
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
                        rx.text(LanguageState.tr["terrain_born_on"] + p.date_of_birth, size="2", color="var(--gray-9)"),
                        spacing="2",
                        align="center",
                    ),
                    # Exam progress summary
                    rx.cond(
                        p.exams_total > 0,
                        rx.hstack(
                            rx.icon("circle_check", size=13, color="var(--green-9)"),
                            rx.text(
                                p.exams_done.to_string() + " / " + p.exams_total.to_string() + LanguageState.tr["terrain_exams_done_suffix"],
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
            # Exam checklist — hidden when visit is cancelled
            rx.cond(
                (p.exams_total > 0) & (p.visit_status != "cancelled"),
                rx.vstack(
                    rx.separator(width="100%"),
                    rx.foreach(p.exams, _exam_row),
                    width="100%",
                    spacing="1",
                ),
            ),
            # Action buttons — depend on visit status
            rx.cond(
                (p.visit_status == "pending") | (p.visit_status == ""),
                # Pending: declare PRESENT or ABSENT — no result entry yet
                rx.vstack(
                    rx.text(
                        "Le patient est-il présent ?",
                        size="2", color="var(--gray-9)", weight="medium",
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon("user-check", size=14),
                            LanguageState.tr["terrain_mark_visit_done_btn"],
                            variant="solid",
                            color_scheme="green",
                            size="2",
                            flex="1",
                            on_click=lambda: TerrainState.mark_terrain_done(p.id),
                        ),
                        rx.button(
                            rx.icon("user-x", size=14),
                            LanguageState.tr["terrain_cancel_visit_btn"],
                            variant="soft",
                            color_scheme="red",
                            size="2",
                            flex="1",
                            on_click=lambda: TerrainState.cancel_visit(p.id),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    spacing="2",
                    width="100%",
                ),
            ),
            rx.cond(
                p.visit_status == "visit_done",
                # Present: result entry is now unlocked
                rx.vstack(
                    rx.hstack(
                        rx.icon("circle-check", size=14, color="var(--green-9)"),
                        rx.text(
                            "Patient présent — saisie des résultats disponible",
                            size="2", color="var(--green-11)",
                        ),
                        spacing="2", align="center",
                    ),
                    rx.button(
                        rx.icon("pencil", size=14),
                        "Saisir les résultats",
                        variant="solid",
                        color_scheme="blue",
                        size="2",
                        width="100%",
                        on_click=lambda: TerrainState.go_to_patient_results(p.id),
                    ),
                    spacing="2",
                    width="100%",
                ),
            ),
            rx.cond(
                p.visit_status == "cancelled",
                # Absent: reactivate button
                rx.hstack(
                    rx.icon("user-x", size=14, color="var(--red-9)"),
                    rx.text("Patient absent", size="2", color="var(--red-10)", weight="medium"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("rotate-ccw", size=14),
                        LanguageState.tr["terrain_reactivate_visit_btn"],
                        variant="soft",
                        color_scheme="gray",
                        size="2",
                        on_click=lambda: TerrainState.reactivate_visit(p.id),
                    ),
                    spacing="2", align="center", width="100%",
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
                    LanguageState.tr["btn_back"],
                    variant="ghost",
                    size="2",
                    on_click=TerrainState.go_back,
                ),
                rx.spacer(),
                rx.cond(
                    TerrainState.is_operator | TerrainState.is_admin,
                    rx.button(
                        rx.icon("check-check", size=14),
                        LanguageState.tr["btn_complete_terrain"],
                        variant="solid",
                        color_scheme="orange",
                        size="2",
                        disabled=~TerrainState.all_visits_closeable,
                        on_click=TerrainState.complete_terrain,
                    ),
                ),
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
                spacing="2",
            ),
            # Campaign info
            rx.card(
                rx.vstack(
                    rx.heading(TerrainState.campaign_name, size="5"),
                    rx.hstack(
                        rx.text(TerrainState.campaign_number, size="2", color="var(--gray-9)"),
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
                        flex_wrap="wrap",
                    ),
                    width="100%",
                    spacing="1",
                ),
                width="100%",
            ),
            # Scanner section
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.heading(LanguageState.tr["terrain_scan_title"], size="4"),
                        rx.spacer(),
                        rx.button(
                            rx.cond(
                                TerrainState.scanner_active,
                                rx.hstack(rx.icon("camera-off", size=14), rx.text(LanguageState.tr["terrain_stop_camera"]), spacing="1"),
                                rx.hstack(rx.icon("camera", size=14), rx.text(LanguageState.tr["terrain_scan_camera"]), spacing="1"),
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
                                LanguageState.tr["terrain_camera_hint"],
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
                            placeholder=LanguageState.tr["terrain_manual_input_placeholder"],
                            value=TerrainState.scan_result,
                            on_change=TerrainState.set_scan_result,
                            size="3",
                            flex="1",
                        ),
                        rx.button(
                            rx.icon("search", size=16),
                            LanguageState.tr["terrain_search_btn"],
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
                        rx.vstack(
                            rx.callout(
                                TerrainState.scan_error,
                                color_scheme="red",
                                icon="triangle-alert",
                                size="1",
                                width="100%",
                            ),
                            rx.button(
                                rx.icon("refresh-cw", size=13),
                                "Réessayer",
                                variant="soft",
                                size="1",
                                on_click=TerrainState.toggle_scanner,
                            ),
                            spacing="2",
                            width="100%",
                        ),
                    ),
                    rx.cond(
                        TerrainState.scan_found_patient != None,  # noqa: E711
                        rx.callout(
                            LanguageState.tr["terrain_patient_found_prefix"] + TerrainState.scan_found_patient.full_name,
                            color_scheme="green",
                            icon="circle_check",
                            size="1",
                        ),
                    ),
                    width="100%",
                    spacing="3",
                ),
                width="100%",
            ),
            # Help message
            rx.callout(
                LanguageState.tr["terrain_help_message"],
                icon="info",
                color_scheme="blue",
                size="1",
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
            # Search + status filter
            rx.hstack(
                rx.input(
                    rx.input.slot(rx.icon("search", size=13)),
                    placeholder=LanguageState.tr["terrain_search_placeholder"],
                    value=TerrainState.search_query,
                    on_change=TerrainState.set_search_query,
                    size="2",
                    flex="1",
                ),
                rx.select.root(
                    rx.select.trigger(size="2", width="180px"),
                    rx.select.content(
                        rx.select.item(LanguageState.tr["terrain_status_all"], value="__all__"),
                        rx.select.item(LanguageState.tr["status_pending"], value="pending"),
                        rx.select.item(LanguageState.tr["status_visit_done"], value="visit_done"),
                        rx.select.item(LanguageState.tr["status_lab_done"], value="lab_done"),
                        rx.select.item(LanguageState.tr["status_doctor_clinic_validated"], value="doctor_clinic_validated"),
                        rx.select.item(LanguageState.tr["status_doctor_company_validated"], value="doctor_company_validated"),
                    ),
                    value=TerrainState.visit_status_filter,
                    on_change=TerrainState.set_visit_status_filter,
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
                            rx.text(LanguageState.tr["terrain_no_patients"], size="3", color="var(--gray-9)"),
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
