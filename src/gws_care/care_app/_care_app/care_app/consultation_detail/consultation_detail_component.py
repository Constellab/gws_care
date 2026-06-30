"""Consultation detail page — single page with all exam types as tabs.

Layout:
  ┌── Header card (visit number, patient, status, actions) ──────────────┐
  │                                                                        │
  │  [Informations]  [Constantes vitales ●]  [NFS ⏳]  [+ Ajouter]        │
  │  ─────────────────────────────────────────────────────────────────── │
  │                                                                        │
  │  (Tab content — Informations OR selected exam param table)            │
  └────────────────────────────────────────────────────────────────────────┘
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .consultation_detail_state import (
    CertificateRowDTO,
    ConsultationDetailState,
    ConsultationDTO,
    DrugLineDTO,
    ExamAuditEntryVM,
    ExamParamOption,
    ExamParamRowVM,
    ExamRowDTO,
    ExamTabHeaderVM,
    ExamTypeRefOption,
    PrescriptionRowDTO,
)


# ── Status helpers ────────────────────────────────────────────────────────────

def _visit_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("scheduled", rx.badge("Planifiée", color_scheme="blue", variant="soft", size="1")),
        ("in_progress", rx.badge("En cours", color_scheme="amber", variant="soft", size="1")),
        ("done", rx.badge("Terminée", color_scheme="green", variant="soft", size="1")),
        ("cancelled", rx.badge("Annulée", color_scheme="red", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _exam_status_dot(status: str) -> rx.Component:
    """Small colored circle indicating exam status — used in tab headers."""
    return rx.match(
        status,
        ("todo", rx.box(
            width="7px", height="7px", border_radius="50%",
            background="var(--gray-7)", flex_shrink="0",
        )),
        ("in_progress_results", rx.box(
            width="7px", height="7px", border_radius="50%",
            background="var(--orange-9)", flex_shrink="0",
        )),
        ("in_progress_interpretation", rx.box(
            width="7px", height="7px", border_radius="50%",
            background="var(--blue-9)", flex_shrink="0",
        )),
        ("done", rx.box(
            width="7px", height="7px", border_radius="50%",
            background="var(--green-9)", flex_shrink="0",
        )),
        rx.box(width="7px", height="7px", border_radius="50%", background="var(--gray-5)"),
    )


def _param_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("NORMAL", rx.badge("Normal", color_scheme="green", variant="soft", size="1")),
        ("NEGATIVE", rx.badge("Négatif", color_scheme="green", variant="soft", size="1")),
        ("LOW", rx.badge("Bas", color_scheme="orange", variant="soft", size="1")),
        ("HIGH", rx.badge("Élevé", color_scheme="orange", variant="soft", size="1")),
        ("CRITICAL_LOW", rx.badge("Critique bas", color_scheme="red", variant="solid", size="1")),
        ("CRITICAL_HIGH", rx.badge("Critique élevé", color_scheme="red", variant="solid", size="1")),
        ("POSITIVE", rx.badge("Positif", color_scheme="red", variant="solid", size="1")),
        ("PENDING", rx.badge("—", color_scheme="gray", variant="surface", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


# ── Header card ───────────────────────────────────────────────────────────────

def _info_card(label: str, value: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", color="var(--gray-9)", weight="medium"),
        value,
        spacing="1",
        align="start",
    )


def _consultation_header(c: ConsultationDTO) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.text(c.visit_number, size="5", weight="bold"),
                        _visit_status_badge(c.status),
                        spacing="2",
                        align="center",
                    ),
                    rx.text("Consultation", size="2", color="var(--gray-9)"),
                    spacing="1",
                ),
                rx.spacer(),
                rx.cond(
                    ~ConsultationDetailState.is_patient_user,
                    rx.hstack(
                        rx.cond(
                            c.status == "scheduled",
                            rx.button(
                                rx.icon("play", size=14),
                                "Démarrer",
                                on_click=ConsultationDetailState.start_consultation,
                                loading=ConsultationDetailState.is_starting,
                                size="2",
                                color_scheme="teal",
                            ),
                            rx.fragment(),
                        ),
                        rx.cond(
                            (c.status == "scheduled") | (c.status == "in_progress"),
                            rx.button(
                                rx.icon("check", size=14),
                                "Clôturer",
                                on_click=ConsultationDetailState.open_close_dialog,
                                size="2",
                                color_scheme="green",
                                variant="soft",
                            ),
                            rx.fragment(),
                        ),
                        rx.cond(
                            (c.status == "scheduled") | (c.status == "in_progress"),
                            rx.button(
                                rx.icon("x", size=14),
                                "Annuler",
                                on_click=ConsultationDetailState.open_cancel_dialog,
                                size="2",
                                color_scheme="red",
                                variant="soft",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                    ),
                ),
                width="100%",
                align="start",
            ),
            rx.separator(width="100%"),
            rx.cond(
                c.status == "cancelled",
                rx.callout.root(
                    rx.callout.icon(rx.icon("ban", size=16)),
                    rx.callout.text(
                        rx.vstack(
                            rx.text("Rendez-vous annulé", weight="bold", size="2"),
                            rx.cond(
                                c.cancellation_reason != "",
                                rx.text("Motif : " + c.cancellation_reason, size="2"),
                                rx.fragment(),
                            ),
                            spacing="0",
                        )
                    ),
                    color_scheme="red",
                    width="100%",
                ),
                rx.fragment(),
            ),
            rx.grid(
                _info_card(
                    "Patient",
                    rx.link(
                        c.patient_name,
                        on_click=ConsultationDetailState.go_back,
                        cursor="pointer",
                        size="2",
                        weight="medium",
                    ),
                ),
                _info_card(
                    "Compte",
                    rx.cond(
                        c.account_name != "",
                        rx.text(c.account_name, size="2"),
                        rx.text("—", size="2", color="var(--gray-7)"),
                    ),
                ),
                _info_card(
                    "Date prévue",
                    rx.cond(
                        c.scheduled_at != "",
                        rx.text(c.scheduled_at[:10], size="2"),
                        rx.text("—", size="2", color="var(--gray-7)"),
                    ),
                ),
                columns="3",
                spacing="4",
                width="100%",
            ),
            spacing="3",
        ),
        width="100%",
    )


# ── Tab bar ───────────────────────────────────────────────────────────────────

def _tab_btn_informations() -> rx.Component:
    is_active = ConsultationDetailState.active_tab == "informations"
    return rx.box(
        rx.hstack(
            rx.icon("file-text", size=13, color=rx.cond(is_active, "var(--accent-9)", "var(--gray-9)")),
            rx.text(
                "Informations",
                size="2",
                weight=rx.cond(is_active, "medium", "regular"),
                color=rx.cond(is_active, "var(--accent-11)", "var(--gray-11)"),
            ),
            spacing="1",
            align="center",
        ),
        padding="0.5rem 0.875rem",
        cursor="pointer",
        border_bottom=rx.cond(is_active, "2px solid var(--accent-9)", "2px solid transparent"),
        on_click=ConsultationDetailState.set_active_tab("informations"),
        _hover={"background": rx.cond(is_active, "transparent", "var(--gray-2)")},
        border_radius="4px 4px 0 0",
        flex_shrink="0",
    )


def _exam_tab_btn(tab: ExamTabHeaderVM) -> rx.Component:
    is_active = ConsultationDetailState.active_tab == tab.exam_id
    return rx.box(
        rx.hstack(
            _exam_status_dot(tab.status),
            rx.text(
                tab.exam_type_label,
                size="2",
                weight=rx.cond(is_active, "medium", "regular"),
                color=rx.cond(is_active, "var(--accent-11)", "var(--gray-11)"),
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
                max_width="140px",
            ),
            spacing="2",
            align="center",
        ),
        padding="0.5rem 0.875rem",
        cursor="pointer",
        border_bottom=rx.cond(is_active, "2px solid var(--accent-9)", "2px solid transparent"),
        on_click=lambda: ConsultationDetailState.set_active_tab(tab.exam_id),
        _hover={"background": rx.cond(is_active, "transparent", "var(--gray-2)")},
        border_radius="4px 4px 0 0",
        flex_shrink="0",
    )


def _tab_bar() -> rx.Component:
    return rx.box(
        rx.hstack(
            _tab_btn_informations(),
            rx.foreach(ConsultationDetailState.exam_tab_headers, _exam_tab_btn),
            rx.cond(
                ~ConsultationDetailState.is_patient_user
                & (ConsultationDetailState.consultation.status != "cancelled"),
                rx.box(
                    rx.hstack(
                        rx.icon("plus", size=13, color="var(--gray-9)"),
                        rx.text("Ajouter", size="2", color="var(--gray-9)"),
                        spacing="1",
                        align="center",
                    ),
                    padding="0.5rem 0.875rem",
                    cursor="pointer",
                    border_bottom="2px solid transparent",
                    on_click=ConsultationDetailState.open_new_exam_dialog,
                    _hover={"background": "var(--gray-2)"},
                    border_radius="4px 4px 0 0",
                    flex_shrink="0",
                ),
            ),
            spacing="0",
            align="end",
            overflow_x="auto",
            width="100%",
        ),
        border_bottom="1px solid var(--gray-4)",
        width="100%",
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB: Informations
# ══════════════════════════════════════════════════════════════════════════════

def _exam_summary_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("todo", rx.badge("En attente", color_scheme="gray", variant="soft", size="1")),
        ("in_progress_results", rx.badge("Saisie en cours", color_scheme="orange", variant="soft", size="1")),
        ("in_progress_interpretation", rx.badge("Interprétation", color_scheme="blue", variant="soft", size="1")),
        ("done", rx.badge("Terminé", color_scheme="green", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _exam_summary_row(exam: ExamRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(exam.exam_date[:10], size="2")),
        rx.table.cell(rx.text(exam.exam_type_label, size="2", weight="medium")),
        rx.table.cell(_exam_summary_status_badge(exam.status)),
        rx.table.cell(
            rx.link(
                "Voir",
                on_click=lambda: ConsultationDetailState.set_active_tab(exam.id),
                size="2",
                cursor="pointer",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _prescription_row(p: PrescriptionRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p.prescription_date, size="2")),
        rx.table.cell(
            rx.cond(
                p.diagnosis != "",
                rx.text(p.diagnosis, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(rx.text(p.prescribed_by_name, size="2")),
        rx.table.cell(
            rx.link(
                "Voir",
                on_click=lambda: rx.redirect(f"/prescription/{p.id}"),
                size="2",
                cursor="pointer",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _certificate_row(c: CertificateRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(c.issue_date, size="2")),
        rx.table.cell(
            rx.cond(
                c.is_fit_for_work,
                rx.badge("Apte", color_scheme="green", variant="soft", size="1"),
                rx.badge("Inapte", color_scheme="red", variant="soft", size="1"),
            )
        ),
        rx.table.cell(rx.text(c.issued_by_name, size="2")),
        rx.table.cell(
            rx.link(
                "Voir",
                on_click=lambda: rx.redirect(f"/certificate/{c.id}"),
                size="2",
                cursor="pointer",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _tab_informations() -> rx.Component:
    can_edit = (
        ~ConsultationDetailState.is_patient_user
        & (ConsultationDetailState.consultation.status != "cancelled")
        & (ConsultationDetailState.consultation.status != "done")
    )
    return rx.vstack(
        # ── Motif ─────────────────────────────────────────────────────────────
        rx.vstack(
            rx.hstack(
                rx.icon("clipboard-list", size=16, color="var(--accent-9)"),
                rx.heading("Motif de la consultation", size="4"),
                spacing="2",
                align="center",
            ),
            rx.separator(width="100%"),
            rx.cond(
                can_edit,
                rx.text_area(
                    value=ConsultationDetailState.form_reason,
                    on_change=ConsultationDetailState.set_form_reason,
                    placeholder="Décrivez le motif de la consultation…",
                    size="2",
                    width="100%",
                    rows="3",
                ),
                rx.cond(
                    ConsultationDetailState.form_reason != "",
                    rx.box(
                        rx.text(ConsultationDetailState.form_reason, size="2"),
                        padding="0.75rem 1rem",
                        background="var(--gray-2)",
                        border_radius="8px",
                        width="100%",
                    ),
                    rx.text("—", size="2", color="var(--gray-7)"),
                ),
            ),
            width="100%",
            spacing="3",
        ),
        # ── Antécédents ───────────────────────────────────────────────────────
        rx.vstack(
            rx.hstack(
                rx.icon("history", size=16, color="var(--accent-9)"),
                rx.heading("Antécédents médicaux", size="4"),
                spacing="2",
                align="center",
            ),
            rx.separator(width="100%"),
            rx.cond(
                can_edit,
                rx.text_area(
                    value=ConsultationDetailState.form_history,
                    on_change=ConsultationDetailState.set_form_history,
                    placeholder="Antécédents médicaux, traitements en cours, allergies…",
                    size="2",
                    width="100%",
                    rows="4",
                ),
                rx.cond(
                    ConsultationDetailState.form_history != "",
                    rx.box(
                        rx.text(ConsultationDetailState.form_history, size="2"),
                        padding="0.75rem 1rem",
                        background="var(--gray-2)",
                        border_radius="8px",
                        width="100%",
                    ),
                    rx.text("—", size="2", color="var(--gray-7)"),
                ),
            ),
            width="100%",
            spacing="3",
        ),
        # ── Save button ───────────────────────────────────────────────────────
        rx.cond(
            can_edit,
            rx.hstack(
                rx.spacer(),
                rx.button(
                    rx.cond(
                        ConsultationDetailState.is_saving_info,
                        rx.spinner(size="2"),
                        rx.icon("check", size=14),
                    ),
                    "Enregistrer les informations",
                    on_click=ConsultationDetailState.save_consultation_info,
                    loading=ConsultationDetailState.is_saving_info,
                    size="2",
                ),
                width="100%",
                align="center",
            ),
        ),
        rx.separator(width="100%"),
        # ── Examens ───────────────────────────────────────────────────────────
        rx.vstack(
            rx.hstack(
                rx.icon("flask-conical", size=16, color="var(--accent-9)"),
                rx.heading("Examens", size="4"),
                rx.spacer(),
                rx.cond(
                    (~ConsultationDetailState.is_patient_user)
                    & (ConsultationDetailState.consultation.status != "cancelled"),
                    rx.button(
                        rx.icon("plus", size=14),
                        "Ajouter",
                        on_click=ConsultationDetailState.open_new_exam_dialog,
                        size="1",
                        variant="soft",
                    ),
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.cond(
                ConsultationDetailState.exams.length() == 0,
                rx.text("Aucun examen lié à cette consultation.", size="2", color="var(--gray-8)"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(rx.text("Date", size="2")),
                            rx.table.column_header_cell(rx.text("Type d'examen", size="2")),
                            rx.table.column_header_cell(rx.text("Statut", size="2")),
                            rx.table.column_header_cell(rx.text("", size="2")),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(ConsultationDetailState.exams, _exam_summary_row)
                    ),
                    width="100%",
                    variant="surface",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        rx.separator(width="100%"),
        # ── Ordonnances ───────────────────────────────────────────────────────
        rx.vstack(
            rx.hstack(
                rx.icon("pill", size=16, color="var(--accent-9)"),
                rx.heading("Ordonnances", size="4"),
                rx.spacer(),
                rx.cond(
                    (~ConsultationDetailState.is_patient_user)
                    & (ConsultationDetailState.consultation.status != "cancelled"),
                    rx.button(
                        rx.icon("plus", size=14),
                        "Ajouter",
                        on_click=ConsultationDetailState.open_new_prescription_dialog,
                        size="1",
                        variant="soft",
                    ),
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.cond(
                ConsultationDetailState.prescriptions.length() == 0,
                rx.text("Aucune ordonnance liée à cette consultation.", size="2", color="var(--gray-8)"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(rx.text("Date", size="2")),
                            rx.table.column_header_cell(rx.text("Diagnostic", size="2")),
                            rx.table.column_header_cell(rx.text("Médecin", size="2")),
                            rx.table.column_header_cell(rx.text("", size="2")),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(ConsultationDetailState.prescriptions, _prescription_row)
                    ),
                    width="100%",
                    variant="surface",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        # ── Certificats ───────────────────────────────────────────────────────
        rx.vstack(
            rx.hstack(
                rx.icon("file-check", size=16, color="var(--accent-9)"),
                rx.heading("Certificats médicaux", size="4"),
                rx.spacer(),
                rx.cond(
                    (~ConsultationDetailState.is_patient_user)
                    & (ConsultationDetailState.consultation.status != "cancelled"),
                    rx.button(
                        rx.icon("plus", size=14),
                        "Émettre",
                        on_click=ConsultationDetailState.open_new_certificate_dialog,
                        size="1",
                        variant="soft",
                    ),
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.cond(
                ConsultationDetailState.certificates.length() == 0,
                rx.text("Aucun certificat lié à cette consultation.", size="2", color="var(--gray-8)"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(rx.text("Date", size="2")),
                            rx.table.column_header_cell(rx.text("Aptitude", size="2")),
                            rx.table.column_header_cell(rx.text("Émis par", size="2")),
                            rx.table.column_header_cell(rx.text("", size="2")),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(ConsultationDetailState.certificates, _certificate_row)
                    ),
                    width="100%",
                    variant="surface",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        spacing="5",
        width="100%",
        padding_top="1.25rem",
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB: Exam parameters
# ══════════════════════════════════════════════════════════════════════════════

def _exam_status_banner(status: str) -> rx.Component:
    return rx.match(
        status,
        ("todo", rx.callout(
            "Examen en attente de saisie. Renseignez les résultats ci-dessous.",
            icon="info", color_scheme="gray", size="1",
        )),
        ("in_progress_results", rx.callout(
            "Saisie des résultats en cours.",
            icon="flask-conical", color_scheme="orange", size="1",
        )),
        ("in_progress_interpretation", rx.callout(
            "Résultats transmis — en attente d'interprétation médicale.",
            icon="clock", color_scheme="blue", size="1",
        )),
        ("done", rx.callout(
            "Examen terminé et interprété.",
            icon="circle-check", color_scheme="green", size="1",
        )),
        rx.fragment(),
    )


def _param_input_cell(p: ExamParamRowVM) -> rx.Component:
    """Input cell — numeric, text area, or boolean switch."""
    return rx.cond(
        p.is_computed,
        # Computed: read-only, show current value
        rx.cond(
            p.value_numeric != "",
            rx.text(p.value_numeric, size="2", color="var(--gray-11)", weight="medium"),
            rx.text("auto", size="1", color="var(--gray-7)", style={"font_style": "italic"}),
        ),
        rx.match(
            p.value_type,
            ("BOOLEAN",
                rx.select.root(
                    rx.select.trigger(placeholder="—", size="1", width="90px"),
                    rx.select.content(
                        rx.select.item("Positif", value="true"),
                        rx.select.item("Négatif", value="false"),
                    ),
                    value=p.value_boolean,
                    on_change=lambda v: ConsultationDetailState.set_param_boolean(p.param_id, v),
                    size="1",
                ),
            ),
            ("TEXT",
                rx.input(
                    value=p.value_text,
                    on_change=lambda v: ConsultationDetailState.set_param_text(p.param_id, v),
                    placeholder="—",
                    size="1",
                    width="160px",
                ),
            ),
            # Default: NUMERIC
            rx.input(
                value=p.value_numeric,
                on_change=lambda v: ConsultationDetailState.set_param_numeric(p.param_id, v),
                placeholder="—",
                type="text",
                size="1",
                width="90px",
                text_align="right",
            ),
        ),
    )


def _param_row(p: ExamParamRowVM) -> rx.Component:
    can_delete_row = (
        ~ConsultationDetailState.is_patient_user
        & (ConsultationDetailState.active_exam_status != "done")
        & (ConsultationDetailState.active_exam_status != "in_progress_interpretation")
        & ~p.is_computed
    )
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    p.is_required,
                    rx.text("*", color="var(--red-9)", size="1"),
                    rx.fragment(),
                ),
                rx.cond(
                    p.is_computed,
                    rx.hstack(
                        rx.text(p.param_name, size="2"),
                        rx.badge("calc.", size="1", color_scheme="violet", variant="soft"),
                        spacing="1",
                        align="center",
                    ),
                    rx.text(p.param_name, size="2"),
                ),
                spacing="1",
                align="center",
            )
        ),
        rx.table.cell(
            _param_input_cell(p),
            vertical_align="middle",
        ),
        rx.table.cell(
            rx.text(p.unit, size="1", color="var(--gray-9)"),
            vertical_align="middle",
        ),
        rx.table.cell(
            rx.cond(
                p.ref_range_label != "",
                rx.text(p.ref_range_label, size="1", color="var(--gray-9)"),
                rx.text("—", size="1", color="var(--gray-6)"),
            ),
            vertical_align="middle",
        ),
        rx.table.cell(
            rx.cond(
                (p.status != "PENDING") & (p.status != "NOT_EVALUATED"),
                _param_status_badge(p.status),
                rx.fragment(),
            ),
            vertical_align="middle",
        ),
        rx.table.cell(
            rx.cond(
                can_delete_row,
                rx.icon_button(
                    rx.icon("trash-2", size=13),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=lambda: ConsultationDetailState.open_delete_param_dialog(
                        p.param_id, p.param_name
                    ),
                ),
                rx.fragment(),
            ),
            vertical_align="middle",
        ),
    )


def _audit_entry_row(e: ExamAuditEntryVM) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.badge(e.action_label, size="1", variant="soft", color_scheme="gray"),
            rx.text(e.user_name, size="1", weight="medium"),
            rx.text("•", size="1", color="var(--gray-7)"),
            rx.text(e.created_at, size="1", color="var(--gray-9)"),
            spacing="2", align="center", wrap="wrap",
        ),
        rx.cond(
            e.details != "",
            rx.text(e.details, size="2", color="var(--gray-11)", margin_top="0.15rem"),
            rx.fragment(),
        ),
        width="100%",
        padding="0.6rem 0",
        border_bottom="1px solid var(--gray-4)",
    )


def _exam_audit_section() -> rx.Component:
    """Action history (add/remove a test, modify a value…) — kept separate from
    the doctor's free-text medical interpretation above."""
    return rx.cond(
        ConsultationDetailState.active_exam_audit_log.length() > 0,
        rx.vstack(
            rx.separator(width="100%"),
            rx.hstack(
                rx.icon("list", size=16, color="var(--gray-9)"),
                rx.heading("Historique des modifications", size="4"),
                spacing="2",
                align="center",
            ),
            rx.vstack(
                rx.foreach(ConsultationDetailState.active_exam_audit_log, _audit_entry_row),
                width="100%",
                spacing="0",
            ),
            width="100%",
            spacing="3",
        ),
        rx.fragment(),
    )


def _tab_exam_params() -> rx.Component:
    can_edit = (
        ~ConsultationDetailState.is_patient_user
        & (ConsultationDetailState.active_exam_status != "done")
        & (ConsultationDetailState.active_exam_status != "in_progress_interpretation")
    )
    return rx.vstack(
        # ── Exam action bar ────────────────────────────────────────────────────
        rx.cond(
            ~ConsultationDetailState.is_patient_user,
            rx.hstack(
                # Add missed param button — only when exam is editable and has a type ref
                rx.cond(
                    can_edit & (ConsultationDetailState.active_exam_type_ref_id != ""),
                    rx.button(
                        rx.icon("plus-circle", size=14),
                        "Ajouter un test",
                        on_click=ConsultationDetailState.open_add_param_dialog,
                        size="1",
                        variant="soft",
                        color_scheme="teal",
                    ),
                    rx.fragment(),
                ),
                rx.spacer(),
                # Delete exam button
                rx.button(
                    rx.icon("trash-2", size=14),
                    "Supprimer",
                    on_click=ConsultationDetailState.open_delete_exam_dialog,
                    size="1",
                    variant="soft",
                    color_scheme="red",
                ),
                width="100%",
                align="center",
                spacing="2",
            ),
        ),
        # Status banner
        _exam_status_banner(ConsultationDetailState.active_exam_status),
        # Params table or loading
        rx.cond(
            ConsultationDetailState.is_loading_params,
            rx.center(rx.spinner(size="3"), padding="3rem"),
            rx.cond(
                ConsultationDetailState.active_exam_params.length() > 0,
                rx.vstack(
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell(rx.text("Paramètre", size="2")),
                                    rx.table.column_header_cell(rx.text("Valeur", size="2")),
                                    rx.table.column_header_cell(rx.text("Unité", size="2")),
                                    rx.table.column_header_cell(rx.text("Référence", size="2")),
                                    rx.table.column_header_cell(rx.text("Statut", size="2")),
                                    rx.table.column_header_cell(""),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(ConsultationDetailState.active_exam_params, _param_row)
                            ),
                            width="100%",
                            variant="surface",
                            size="2",
                        ),
                        overflow_x="auto",
                        width="100%",
                    ),
                    # Save + transmit row (lab view)
                    rx.cond(
                        can_edit,
                        rx.hstack(
                            rx.text(
                                "* paramètre requis",
                                size="1",
                                color="var(--gray-8)",
                                style={"font_style": "italic"},
                            ),
                            rx.spacer(),
                            rx.button(
                                rx.cond(
                                    ConsultationDetailState.is_saving_params,
                                    rx.spinner(size="2"),
                                    rx.icon("save", size=14),
                                ),
                                "Enregistrer",
                                on_click=ConsultationDetailState.save_exam_params,
                                loading=ConsultationDetailState.is_saving_params,
                                size="2",
                                variant="soft",
                            ),
                            rx.cond(
                                ConsultationDetailState.active_exam_status == "in_progress_results",
                                rx.button(
                                    rx.cond(
                                        ConsultationDetailState.is_transmitting,
                                        rx.spinner(size="2"),
                                        rx.icon("send", size=14),
                                    ),
                                    "Transmettre au médecin",
                                    on_click=ConsultationDetailState.transmit_to_doctor,
                                    loading=ConsultationDetailState.is_transmitting,
                                    size="2",
                                    color_scheme="blue",
                                ),
                                rx.fragment(),
                            ),
                            # Doctor: delegate result entry to the lab instead of
                            # filling the values themselves
                            rx.cond(
                                ConsultationDetailState.is_doctor
                                & (ConsultationDetailState.active_exam_status == "todo"),
                                rx.button(
                                    rx.cond(
                                        ConsultationDetailState.is_transmitting,
                                        rx.spinner(size="2"),
                                        rx.icon("flask-conical", size=14),
                                    ),
                                    "Transmettre au labo",
                                    on_click=ConsultationDetailState.transmit_to_lab,
                                    loading=ConsultationDetailState.is_transmitting,
                                    size="2",
                                    variant="soft",
                                    color_scheme="purple",
                                ),
                                rx.fragment(),
                            ),
                            width="100%",
                            align="center",
                            spacing="2",
                        ),
                    ),
                    # Interpretation section (clinic doctor view)
                    rx.cond(
                        ConsultationDetailState.active_exam_status == "in_progress_interpretation",
                        rx.cond(
                            ConsultationDetailState.is_doctor,
                            rx.vstack(
                                rx.separator(width="100%"),
                                rx.hstack(
                                    rx.icon("stethoscope", size=16, color="var(--accent-9)"),
                                    rx.heading("Interprétation médicale", size="4"),
                                    spacing="2",
                                    align="center",
                                ),
                                rx.text_area(
                                    value=ConsultationDetailState.active_exam_interpretation,
                                    on_change=ConsultationDetailState.set_active_exam_interpretation,
                                    placeholder="Rédigez votre interprétation clinique…",
                                    size="2",
                                    width="100%",
                                    rows="4",
                                ),
                                rx.hstack(
                                    rx.spacer(),
                                    rx.button(
                                        rx.cond(
                                            ConsultationDetailState.is_transmitting,
                                            rx.spinner(size="2"),
                                            rx.icon("send", size=14),
                                        ),
                                        "Transmettre au médecin du travail",
                                        on_click=ConsultationDetailState.transmit_to_work_doctor,
                                        loading=ConsultationDetailState.is_transmitting,
                                        size="2",
                                        color_scheme="green",
                                        disabled=(ConsultationDetailState.active_exam_interpretation == ""),
                                    ),
                                    width="100%",
                                ),
                                width="100%",
                                spacing="3",
                            ),
                            # Non-doctor: show read-only waiting message
                            rx.callout(
                                "Résultats transmis — en attente d'interprétation par le médecin.",
                                icon="clock",
                                color_scheme="blue",
                                size="1",
                            ),
                        ),
                        rx.fragment(),
                    ),
                    # Interpretation read-only (done)
                    rx.cond(
                        (ConsultationDetailState.active_exam_status == "done")
                        & (ConsultationDetailState.active_exam_interpretation != ""),
                        rx.vstack(
                            rx.separator(width="100%"),
                            rx.hstack(
                                rx.icon("stethoscope", size=16, color="var(--green-9)"),
                                rx.heading("Interprétation médicale", size="4"),
                                rx.badge("Terminé", color_scheme="green", variant="soft", size="1"),
                                spacing="2",
                                align="center",
                            ),
                            rx.box(
                                rx.text(
                                    ConsultationDetailState.active_exam_interpretation,
                                    size="2",
                                ),
                                padding="0.75rem 1rem",
                                background="var(--green-2)",
                                border="1px solid var(--green-5)",
                                border_radius="8px",
                                width="100%",
                            ),
                            width="100%",
                            spacing="3",
                        ),
                        rx.fragment(),
                    ),
                    # Action history — separate from the interpretation above
                    _exam_audit_section(),
                    width="100%",
                    spacing="3",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("flask-conical", size=32, color="var(--gray-5)"),
                        rx.text(
                            "Aucun paramètre défini pour cet examen.",
                            size="2",
                            color="var(--gray-7)",
                        ),
                        align="center",
                        spacing="2",
                    ),
                    padding="3rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="8px",
                    width="100%",
                ),
            ),
        ),
        width="100%",
        spacing="4",
        padding_top="1.25rem",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Dialogs
# ══════════════════════════════════════════════════════════════════════════════

def _cancel_consultation_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Annuler le rendez-vous"),
            rx.vstack(
                rx.text(
                    "Veuillez indiquer le motif d'annulation. Cette action est irréversible.",
                    size="2", color="var(--gray-11)",
                ),
                rx.vstack(
                    rx.text("Motif d'annulation *", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Ex : Patient absent, demande du patient, problème médical…",
                        value=ConsultationDetailState.cancel_reason,
                        on_change=ConsultationDetailState.set_cancel_reason,
                        rows="3",
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.cond(
                    ConsultationDetailState.cancel_reason_error != "",
                    rx.callout(
                        ConsultationDetailState.cancel_reason_error,
                        icon="triangle-alert", color_scheme="red", size="1",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Retour",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ConsultationDetailState.close_cancel_dialog,
                    ),
                    rx.button(
                        "Confirmer l'annulation",
                        color_scheme="red",
                        on_click=ConsultationDetailState.confirm_cancel_consultation,
                        loading=ConsultationDetailState.is_cancelling,
                    ),
                    spacing="2", width="100%",
                ),
                spacing="4", width="100%", padding_top="0.5rem",
            ),
            on_interact_outside=ConsultationDetailState.close_cancel_dialog,
            on_escape_key_down=ConsultationDetailState.close_cancel_dialog,
            max_width="480px",
        ),
        open=ConsultationDetailState.show_cancel_dialog,
    )


def _close_consultation_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Clôturer la consultation"),
            rx.alert_dialog.description(
                "Confirmer la clôture de cette consultation ? Elle passera au statut « Clôturée »."
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button("Annuler", variant="soft", color_scheme="gray", size="2"),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Confirmer",
                        on_click=ConsultationDetailState.confirm_close_consultation,
                        loading=ConsultationDetailState.is_closing,
                        size="2",
                        color_scheme="green",
                    ),
                ),
                spacing="2",
                justify="end",
            ),
        ),
        open=ConsultationDetailState.show_close_dialog,
        on_open_change=ConsultationDetailState.close_close_dialog,
    )


def _exam_ref_option(opt: ExamTypeRefOption) -> rx.Component:
    return rx.select.item(opt.name, value=opt.id)


def _new_exam_param_item(param: ExamParamOption) -> rx.Component:
    return rx.flex(
        rx.cond(
            param.is_selected,
            rx.box(
                rx.icon("check", size=11, color="white"),
                width="18px", min_width="18px", height="18px",
                border_radius="3px",
                background="var(--accent-9)",
                display="flex", align_items="center", justify_content="center",
            ),
            rx.box(
                width="18px", min_width="18px", height="18px",
                border_radius="3px",
                border="2px solid var(--gray-6)",
                background="white",
            ),
        ),
        rx.flex(
            rx.hstack(
                rx.text(param.name, size="2", weight=rx.cond(param.is_selected, "medium", "regular")),
                rx.cond(
                    param.is_required,
                    rx.badge("Requis", size="1", color_scheme="red", variant="soft"),
                    rx.fragment(),
                ),
                spacing="2", align="center", flex_wrap="wrap",
            ),
            rx.cond(
                param.unit != "",
                rx.text(param.unit, size="1", color="var(--gray-9)"),
                rx.fragment(),
            ),
            direction="column", gap="0",
        ),
        rx.spacer(),
        align="center", gap="3",
        padding="0.5rem 0.75rem",
        border_radius="var(--radius-2)",
        background=rx.cond(param.is_selected, "var(--accent-2)", "transparent"),
        border=rx.cond(param.is_selected, "1px solid var(--accent-6)", "1px solid var(--gray-4)"),
        width="100%", cursor="pointer",
        on_click=ConsultationDetailState.toggle_new_exam_param(param.id),
        _hover={"background": rx.cond(param.is_selected, "var(--accent-3)", "var(--gray-2)")},
    )


def _new_exam_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajouter un examen"),
            rx.vstack(
                rx.vstack(
                    rx.text("Type d'examen", size="2", weight="medium"),
                    rx.cond(
                        ConsultationDetailState.new_exam_is_loading_types,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Chargement du référentiel…", size="2", color="var(--gray-9)"),
                            spacing="2", align="center",
                        ),
                        rx.cond(
                            ConsultationDetailState.new_exam_ref_options.length() > 0,
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Sélectionner un type d'examen…",
                                    width="100%",
                                ),
                                rx.select.content(
                                    rx.foreach(ConsultationDetailState.new_exam_ref_options, _exam_ref_option),
                                ),
                                value=ConsultationDetailState.new_exam_type,
                                on_change=ConsultationDetailState.select_new_exam_type_ref,
                                size="2",
                                width="100%",
                            ),
                            rx.callout(
                                "Aucun type d'examen disponible. Créez-en dans l'onglet Référentiel des examens.",
                                icon="info", color_scheme="orange", size="1",
                            ),
                        ),
                    ),
                    spacing="1", width="100%",
                ),
                rx.cond(
                    ConsultationDetailState.new_exam_type != "",
                    rx.vstack(
                        rx.hstack(
                            rx.text("Tests inclus", size="2", weight="bold"),
                            rx.spacer(),
                            rx.hstack(
                                rx.text(
                                    ConsultationDetailState.new_exam_selected_param_count.to(str),
                                    " / ",
                                    ConsultationDetailState.new_exam_params.length().to(str),
                                    " sélectionné(s)",
                                    size="1", color="var(--gray-9)",
                                ),
                                rx.button("Tout cocher", on_click=ConsultationDetailState.select_all_new_exam_params, variant="ghost", size="1", type="button"),
                                rx.button("Tout décocher", on_click=ConsultationDetailState.clear_all_new_exam_params, variant="ghost", size="1", type="button", color_scheme="gray"),
                                spacing="2", align="center",
                            ),
                            width="100%", align="center",
                        ),
                        rx.cond(
                            ConsultationDetailState.new_exam_params.length() > 0,
                            rx.vstack(
                                rx.foreach(ConsultationDetailState.new_exam_params, _new_exam_param_item),
                                spacing="1", width="100%",
                                max_height="200px", overflow_y="auto",
                                padding="0.25rem",
                                border="1px solid var(--gray-4)",
                                border_radius="var(--radius-2)",
                                background="var(--gray-1)",
                            ),
                            rx.center(
                                rx.text("Aucun test défini pour ce type d'examen.", size="2", color="var(--gray-9)"),
                                padding="1rem", border="1px dashed var(--gray-5)", border_radius="var(--radius-2)", width="100%",
                            ),
                        ),
                        width="100%", spacing="2",
                    ),
                    rx.fragment(),
                ),
                rx.vstack(
                    rx.text("Date de l'examen", size="2", weight="medium"),
                    rx.input(
                        type="date",
                        value=ConsultationDetailState.new_exam_date,
                        on_change=ConsultationDetailState.set_new_exam_date,
                        size="2",
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.cond(
                    ConsultationDetailState.new_exam_error != "",
                    rx.callout(ConsultationDetailState.new_exam_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button("Annuler", variant="outline", on_click=ConsultationDetailState.close_new_exam_dialog),
                    rx.button(
                        "Ajouter l'examen",
                        on_click=ConsultationDetailState.save_new_exam,
                        loading=ConsultationDetailState.new_exam_is_saving,
                        disabled=(ConsultationDetailState.new_exam_type == ""),
                    ),
                    spacing="2", width="100%",
                ),
                spacing="4", width="100%", padding_top="1rem",
            ),
            on_interact_outside=ConsultationDetailState.close_new_exam_dialog,
            on_escape_key_down=ConsultationDetailState.close_new_exam_dialog,
            max_width="540px",
        ),
        open=ConsultationDetailState.show_new_exam_dialog,
    )


def _drug_row(drug: DrugLineDTO, index: int) -> rx.Component:
    return rx.hstack(
        rx.input(placeholder="Médicament", value=drug.name, on_change=lambda v: ConsultationDetailState.presc_set_drug_name(index, v), size="2", flex="2"),
        rx.input(placeholder="Dosage", value=drug.dosage, on_change=lambda v: ConsultationDetailState.presc_set_drug_dosage(index, v), size="2", flex="1"),
        rx.input(placeholder="Fréquence", value=drug.frequency, on_change=lambda v: ConsultationDetailState.presc_set_drug_frequency(index, v), size="2", flex="1"),
        rx.input(placeholder="Durée", value=drug.duration, on_change=lambda v: ConsultationDetailState.presc_set_drug_duration(index, v), size="2", flex="1"),
        rx.icon_button(rx.icon("trash-2", size=14), variant="ghost", color_scheme="red", size="2", on_click=lambda: ConsultationDetailState.presc_remove_drug(index)),
        spacing="2", width="100%", align="center",
    )


def _new_prescription_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nouvelle ordonnance"),
            rx.vstack(
                rx.vstack(
                    rx.text("Date", size="2", weight="medium"),
                    rx.input(type="date", value=ConsultationDetailState.presc_form_date, on_change=ConsultationDetailState.set_presc_form_date, size="2", width="100%"),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.text("Diagnostic", size="2", weight="medium"),
                    rx.input(placeholder="Diagnostic (optionnel)", value=ConsultationDetailState.presc_form_diagnosis, on_change=ConsultationDetailState.set_presc_form_diagnosis, size="2", width="100%"),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text("Médicaments", size="2", weight="medium"),
                        rx.spacer(),
                        rx.button(rx.icon("plus", size=13), "Ajouter", on_click=ConsultationDetailState.presc_add_drug, size="1", variant="ghost"),
                        width="100%", align="center",
                    ),
                    rx.foreach(ConsultationDetailState.presc_form_drugs, _drug_row),
                    spacing="2", width="100%",
                ),
                rx.cond(
                    ConsultationDetailState.presc_form_error != "",
                    rx.callout(ConsultationDetailState.presc_form_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button("Annuler", variant="outline", on_click=ConsultationDetailState.close_new_prescription_dialog),
                    rx.button("Créer l'ordonnance", on_click=ConsultationDetailState.save_new_prescription, loading=ConsultationDetailState.is_saving_prescription),
                    spacing="2", width="100%",
                ),
                spacing="4", width="100%", padding_top="1rem",
            ),
            on_interact_outside=ConsultationDetailState.close_new_prescription_dialog,
            on_escape_key_down=ConsultationDetailState.close_new_prescription_dialog,
            max_width="700px",
        ),
        open=ConsultationDetailState.show_new_prescription_dialog,
    )


def _new_certificate_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Émettre un certificat médical"),
            rx.vstack(
                rx.vstack(
                    rx.text("Date d'émission", size="2", weight="medium"),
                    rx.input(type="date", value=ConsultationDetailState.cert_form_issue_date, on_change=ConsultationDetailState.set_cert_form_issue_date, size="2", width="100%"),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.text("Aptitude", size="2", weight="medium"),
                    rx.radio_group.root(
                        rx.hstack(
                            rx.radio_group.item(value="true"),
                            rx.text("Apte", size="2"),
                            rx.radio_group.item(value="false"),
                            rx.text("Inapte", size="2"),
                            spacing="2", align="center",
                        ),
                        value=rx.cond(ConsultationDetailState.cert_form_is_fit_for_work, "true", "false"),
                        on_change=lambda v: ConsultationDetailState.set_cert_form_is_fit_for_work(v == "true"),
                    ),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.text("Conclusion", size="2", weight="medium"),
                    rx.text_area(placeholder="Conclusion médicale…", value=ConsultationDetailState.cert_form_conclusion, on_change=ConsultationDetailState.set_cert_form_conclusion, size="2", width="100%", rows="3"),
                    spacing="1", width="100%",
                ),
                rx.cond(
                    ConsultationDetailState.cert_form_error != "",
                    rx.callout(ConsultationDetailState.cert_form_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button("Annuler", variant="outline", on_click=ConsultationDetailState.close_new_certificate_dialog),
                    rx.button(
                        "Émettre le certificat",
                        on_click=ConsultationDetailState.save_new_certificate,
                        loading=ConsultationDetailState.is_saving_certificate,
                        disabled=(ConsultationDetailState.cert_form_conclusion == ""),
                    ),
                    spacing="2", width="100%",
                ),
                spacing="4", width="100%", padding_top="1rem",
            ),
            on_interact_outside=ConsultationDetailState.close_new_certificate_dialog,
            on_escape_key_down=ConsultationDetailState.close_new_certificate_dialog,
            max_width="560px",
        ),
        open=ConsultationDetailState.show_new_certificate_dialog,
    )


def _edit_reason_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Motif de modification"),
            rx.vstack(
                rx.callout(
                    "Des résultats ont déjà été enregistrés pour cet examen. "
                    "Veuillez indiquer le motif de la modification pour la traçabilité.",
                    icon="pencil",
                    color_scheme="orange",
                    size="1",
                ),
                rx.vstack(
                    rx.text("Motif *", size="2", weight="medium"),
                    rx.text_area(
                        value=ConsultationDetailState.edit_reason,
                        on_change=ConsultationDetailState.set_edit_reason,
                        placeholder="Ex : erreur de saisie, résultat corrigé par le laboratoire…",
                        size="2",
                        width="100%",
                        rows="3",
                    ),
                    spacing="1", width="100%",
                ),
                rx.cond(
                    ConsultationDetailState.edit_reason_error != "",
                    rx.callout(
                        ConsultationDetailState.edit_reason_error,
                        icon="triangle-alert", color_scheme="red", size="1",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button("Annuler", variant="soft", color_scheme="gray",
                              on_click=ConsultationDetailState.close_edit_reason_dialog),
                    rx.button(
                        "Enregistrer la modification",
                        on_click=ConsultationDetailState.confirm_edit_save,
                        loading=ConsultationDetailState.is_saving_params,
                    ),
                    spacing="2", width="100%",
                ),
                spacing="4", width="100%", padding_top="0.5rem",
            ),
            on_interact_outside=ConsultationDetailState.close_edit_reason_dialog,
            on_escape_key_down=ConsultationDetailState.close_edit_reason_dialog,
            max_width="480px",
        ),
        open=ConsultationDetailState.show_edit_reason_dialog,
    )


def _delete_exam_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Supprimer l'examen"),
            rx.vstack(
                rx.callout(
                    "Cet examen sera marqué comme annulé. Le motif sera consigné.",
                    icon="triangle-alert",
                    color_scheme="orange",
                    size="1",
                ),
                rx.vstack(
                    rx.text("Motif de suppression *", size="2", weight="medium"),
                    rx.text_area(
                        value=ConsultationDetailState.delete_exam_reason,
                        on_change=ConsultationDetailState.set_delete_exam_reason,
                        placeholder="Ex : examen prescrit par erreur, doublon, patient refus…",
                        size="2",
                        width="100%",
                        rows="3",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.cond(
                    ConsultationDetailState.delete_exam_reason_error != "",
                    rx.callout(
                        ConsultationDetailState.delete_exam_reason_error,
                        icon="triangle-alert", color_scheme="red", size="1",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button("Annuler", variant="soft", color_scheme="gray",
                              on_click=ConsultationDetailState.close_delete_exam_dialog),
                    rx.button(
                        "Confirmer la suppression",
                        color_scheme="red",
                        on_click=ConsultationDetailState.confirm_delete_exam,
                        loading=ConsultationDetailState.is_deleting_exam,
                    ),
                    spacing="2", width="100%",
                ),
                spacing="4", width="100%", padding_top="0.5rem",
            ),
            on_interact_outside=ConsultationDetailState.close_delete_exam_dialog,
            on_escape_key_down=ConsultationDetailState.close_delete_exam_dialog,
            max_width="480px",
        ),
        open=ConsultationDetailState.show_delete_exam_dialog,
    )


def _add_param_item(p: ExamParamOption) -> rx.Component:
    return rx.flex(
        rx.cond(
            p.is_selected,
            rx.box(
                rx.icon("check", size=11, color="white"),
                width="18px", min_width="18px", height="18px",
                border_radius="3px",
                background="var(--accent-9)",
                display="flex", align_items="center", justify_content="center",
            ),
            rx.box(
                width="18px", min_width="18px", height="18px",
                border_radius="3px",
                border="2px solid var(--gray-6)",
                background="white",
            ),
        ),
        rx.flex(
            rx.hstack(
                rx.text(p.name, size="2", weight=rx.cond(p.is_selected, "medium", "regular")),
                rx.cond(
                    p.is_required,
                    rx.badge("Requis", size="1", color_scheme="red", variant="soft"),
                    rx.fragment(),
                ),
                spacing="2", align="center",
            ),
            rx.cond(
                p.unit != "",
                rx.text(p.unit, size="1", color="var(--gray-9)"),
                rx.fragment(),
            ),
            direction="column", gap="0",
        ),
        align="center", gap="3",
        padding="0.5rem 0.75rem",
        border_radius="var(--radius-2)",
        background=rx.cond(p.is_selected, "var(--accent-2)", "transparent"),
        border=rx.cond(p.is_selected, "1px solid var(--accent-6)", "1px solid var(--gray-4)"),
        width="100%", cursor="pointer",
        on_click=lambda: ConsultationDetailState.toggle_add_param(p.id),
        _hover={"background": rx.cond(p.is_selected, "var(--accent-3)", "var(--gray-2)")},
    )


def _add_param_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajouter des tests"),
            rx.dialog.description(
                "Sélectionnez les tests à ajouter à cet examen.",
                size="2", color="var(--gray-11)",
            ),
            rx.vstack(
                rx.cond(
                    ConsultationDetailState.add_param_error != "",
                    rx.callout(
                        ConsultationDetailState.add_param_error,
                        icon="info", color_scheme="orange", size="1",
                    ),
                    rx.cond(
                        ConsultationDetailState.add_param_options.length() > 0,
                        rx.vstack(
                            rx.hstack(
                                rx.text(
                                    ConsultationDetailState.add_param_selected_count.to(str),
                                    " / ",
                                    ConsultationDetailState.add_param_options.length().to(str),
                                    " sélectionné(s)",
                                    size="1", color="var(--gray-9)",
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            rx.vstack(
                                rx.foreach(ConsultationDetailState.add_param_options, _add_param_item),
                                spacing="1", width="100%",
                                max_height="240px", overflow_y="auto",
                                padding="0.25rem",
                                border="1px solid var(--gray-4)",
                                border_radius="var(--radius-2)",
                                background="var(--gray-1)",
                            ),
                            width="100%", spacing="2",
                        ),
                        rx.fragment(),
                    ),
                ),
                rx.cond(
                    ConsultationDetailState.add_param_options.length() > 0,
                    rx.vstack(
                        rx.text("Motif de l'ajout *", size="2", weight="medium"),
                        rx.text_area(
                            value=ConsultationDetailState.add_param_reason,
                            on_change=ConsultationDetailState.set_add_param_reason,
                            placeholder="Pourquoi ajoutez-vous ce(s) test(s) ? (oubli, paramètre nécessaire au calcul d'une constante…)",
                            size="2",
                            width="100%",
                            rows="3",
                        ),
                        rx.cond(
                            ConsultationDetailState.add_param_reason_error != "",
                            rx.text(
                                ConsultationDetailState.add_param_reason_error,
                                size="1", color="var(--red-9)",
                            ),
                            rx.fragment(),
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button("Annuler", variant="outline",
                              on_click=ConsultationDetailState.close_add_param_dialog),
                    rx.button(
                        "Ajouter les tests",
                        on_click=ConsultationDetailState.save_add_params,
                        loading=ConsultationDetailState.is_saving_add_params,
                        disabled=(
                            (ConsultationDetailState.add_param_selected_count == 0)
                            | (ConsultationDetailState.add_param_error != "")
                        ),
                    ),
                    spacing="2", width="100%",
                ),
                spacing="4", width="100%", padding_top="1rem",
            ),
            on_interact_outside=ConsultationDetailState.close_add_param_dialog,
            on_escape_key_down=ConsultationDetailState.close_add_param_dialog,
            max_width="500px",
        ),
        open=ConsultationDetailState.show_add_param_dialog,
    )


def _delete_param_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Supprimer ce test"),
            rx.alert_dialog.description(
                rx.hstack(
                    rx.text("Supprimer le test"),
                    rx.text(ConsultationDetailState.delete_param_name, weight="bold"),
                    rx.text("? Le résultat associé sera également supprimé."),
                    spacing="1", wrap="wrap",
                ),
                size="2",
            ),
            rx.vstack(
                rx.text("Motif de la suppression *", size="2", weight="medium"),
                rx.text_area(
                    value=ConsultationDetailState.delete_param_reason,
                    on_change=ConsultationDetailState.set_delete_param_reason,
                    placeholder="Pourquoi ce test est-il retiré de l'examen ?",
                    size="2",
                    width="100%",
                    rows="3",
                ),
                rx.cond(
                    ConsultationDetailState.delete_param_reason_error != "",
                    rx.text(
                        ConsultationDetailState.delete_param_reason_error,
                        size="1", color="var(--red-9)",
                    ),
                    rx.fragment(),
                ),
                spacing="1", width="100%", padding_top="0.75rem",
            ),
            rx.hstack(
                rx.spacer(),
                rx.alert_dialog.cancel(
                    rx.button("Annuler", variant="soft", color_scheme="gray"),
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    "Supprimer",
                    color_scheme="red",
                    on_click=ConsultationDetailState.confirm_delete_param,
                    loading=ConsultationDetailState.is_deleting_param,
                ),
                spacing="3", margin_top="1rem",
            ),
        ),
        open=ConsultationDetailState.show_delete_param_dialog,
        on_open_change=ConsultationDetailState.close_delete_param_dialog,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Page
# ══════════════════════════════════════════════════════════════════════════════

def consultation_detail_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.cond(
                ConsultationDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding_y="6em"),
                rx.cond(
                    ConsultationDetailState.consultation,
                    rx.vstack(
                        # Back button
                        rx.button(
                            rx.icon("arrow-left", size=14),
                            LanguageState.tr["btn_back"],
                            variant="ghost",
                            color_scheme="gray",
                            size="2",
                            on_click=ConsultationDetailState.go_back,
                        ),
                        # Alerts
                        rx.cond(
                            ConsultationDetailState.error_message != "",
                            rx.callout(
                                ConsultationDetailState.error_message,
                                icon="circle-alert", color_scheme="red",
                            ),
                        ),
                        rx.cond(
                            ConsultationDetailState.success_message != "",
                            rx.callout(
                                ConsultationDetailState.success_message,
                                icon="circle-check", color_scheme="green",
                            ),
                        ),
                        # Header card
                        _consultation_header(ConsultationDetailState.consultation),
                        # Tab bar
                        _tab_bar(),
                        # Tab content
                        rx.cond(
                            ConsultationDetailState.active_tab == "informations",
                            _tab_informations(),
                            _tab_exam_params(),
                        ),
                        # Dialogs
                        _cancel_consultation_dialog(),
                        _close_consultation_dialog(),
                        _new_exam_dialog(),
                        _edit_reason_dialog(),
                        _delete_exam_dialog(),
                        _delete_param_dialog(),
                        _add_param_dialog(),
                        _new_prescription_dialog(),
                        _new_certificate_dialog(),
                        spacing="4",
                        width="100%",
                        padding="1.5em",
                        padding_bottom="4em",
                    ),
                    rx.center(
                        rx.text("Consultation introuvable.", size="3", color="var(--gray-8)"),
                        padding_y="6em",
                    ),
                ),
            )
        )
    )
