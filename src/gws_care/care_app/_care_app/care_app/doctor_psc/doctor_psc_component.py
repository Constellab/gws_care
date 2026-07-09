"""Doctor PSC page component — three-tab layout: campagnes / consultations cliniques / entreprise."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .doctor_psc_state import ClinicConsultationRowDTO, DossierRowDTO, IndependentExamRowDTO, DoctorPscState
from ..doctor_enterprise.doctor_enterprise_state import DoctorEnterpriseState, EntDossierRowDTO

_STATUS_FILTER_OPTIONS = [
    ("ALL",             "All active records"),
    ("LAB_ENTERED",     "📋 Results entered — to interpret"),
    ("LAB_VALIDATED",   "✅ Lab validated — to interpret"),
    ("PSC_INTERPRETED", "🩺 PSC interpreted — to validate"),
    ("PSC_VALIDATED",   "🔒 PSC validated"),
]


# ── Filter bar (campagnes tab) ────────────────────────────────────────────────

def _campaign_option(c: list) -> rx.Component:
    return rx.select.item(c[1], value=c[0])


def _filter_bar() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text("Status", size="1", weight="medium", color="var(--gray-9)"),
                rx.select.root(
                    rx.select.trigger(placeholder="All statuses", min_width="240px"),
                    rx.select.content(
                        *[rx.select.item(label, value=val) for val, label in _STATUS_FILTER_OPTIONS]
                    ),
                    value=DoctorPscState.filter_status,
                    on_change=DoctorPscState.set_filter_status,
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Campaign", size="1", weight="medium", color="var(--gray-9)"),
                rx.select.root(
                    rx.select.trigger(placeholder="All campaigns", min_width="220px"),
                    rx.select.content(
                        rx.select.item("All campaigns", value="__all__"),
                        rx.foreach(DoctorPscState.campaigns_for_filter, _campaign_option),
                    ),
                    value=DoctorPscState.filter_campaign_id,
                    on_change=DoctorPscState.set_filter_campaign,
                ),
                spacing="1",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("refresh-cw", size=14), "Refresh",
                variant="soft", size="2", on_click=DoctorPscState.on_load,
                align_self="end",
            ),
            width="100%", align="end", spacing="4", wrap="wrap",
        ),
        width="100%",
        padding="0.75rem 1rem",
        background="var(--gray-2)",
    )


# ── Dossier row (campagnes) ───────────────────────────────────────────────────

def _dossier_row(d: DossierRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(d.patient_name, size="2", weight="medium"),
                rx.text(d.patient_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(rx.text(d.campaign_name, size="2")),
        rx.table.cell(rx.text(d.account_name, size="2")),
        rx.table.cell(
            rx.badge(d.medical_status_label, color_scheme=d.medical_status_color, size="1", variant="soft")
        ),
        rx.table.cell(
            rx.cond(
                d.psc_notes != "",
                rx.tooltip(
                    rx.hstack(
                        rx.icon("file-text", size=14, color="var(--blue-9)"),
                        rx.text("Notes", size="1", color="var(--blue-9)"),
                        spacing="1", align="center",
                    ),
                    content=d.psc_notes,
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("clipboard-list", size=14),
                        variant="ghost", size="1", color_scheme="gray",
                        on_click=rx.redirect("/campaign-patient/" + d.campaign_id + "/" + d.patient_id),
                    ),
                    content="View entered results",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pen-line", size=14),
                        variant="ghost", size="1", color_scheme="blue",
                        on_click=lambda: DoctorPscState.open_interp_dialog(
                            d.campaign_id, d.patient_id, d.patient_name, d.psc_notes, d.medical_status
                        ),
                    ),
                    content="Enter / edit interpretation",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("check", size=14),
                        variant="ghost", size="1", color_scheme="green",
                        on_click=lambda: DoctorPscState.validate_patient(d.campaign_id, d.patient_id),
                        disabled=d.medical_status != "PSC_INTERPRETED",
                    ),
                    content="Validate PSC record",
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


# ── Independent exam row (standalone exams) ──────────────────────────────────

def _independent_exam_row(exam: IndependentExamRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(exam.patient_name, size="2", weight="medium"),
                rx.text(exam.patient_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(rx.text(exam.exam_date, size="2")),
        rx.table.cell(rx.text(exam.exam_type_label, size="2")),
        rx.table.cell(
            rx.cond(
                exam.is_draft,
                rx.badge("Draft", color_scheme="gray", size="1", variant="soft"),
                rx.cond(
                    exam.has_lab_results,
                    rx.badge("Results entered", color_scheme="blue", size="1", variant="soft"),
                    rx.badge("Awaiting lab", color_scheme="orange", size="1", variant="soft"),
                ),
            )
        ),
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("file-text", size=14),
                    variant="ghost", size="1", color_scheme="blue",
                    on_click=rx.redirect("/exam/" + exam.exam_id),
                ),
                content="View exam and results",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


# ── Clinical consultation row ─────────────────────────────────────────────────

def _clinic_consult_row(c: ClinicConsultationRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(c.patient_name, size="2", weight="medium"),
                rx.text(c.patient_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(rx.text(c.consultation_date, size="2")),
        rx.table.cell(
            rx.badge(c.encounter_type_label, color_scheme="violet", size="1", variant="soft")
        ),
        rx.table.cell(
            rx.cond(
                c.reason_for_visit != "",
                rx.tooltip(
                    rx.text(c.reason_for_visit, size="2", max_width="200px",
                            overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
                    content=c.reason_for_visit,
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                c.nb_exams > 0,
                rx.badge(c.nb_exams.to_string() + " exam(s)", color_scheme="blue", size="1", variant="surface"),
                rx.text("No exam", size="1", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("stethoscope", size=14),
                    variant="ghost", size="1", color_scheme="violet",
                    on_click=rx.redirect("/patient/" + c.patient_id),
                ),
                content="View patient record and exams",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


# ── Interpretation dialog ─────────────────────────────────────────────────────

def _interp_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("stethoscope", size=16, color="var(--blue-9)"),
                    rx.text("PSC Interpretation —"),
                    rx.text(DoctorPscState.interp_patient_name, weight="bold"),
                    spacing="1",
                )
            ),
            rx.vstack(
                rx.text("Comment / Medical interpretation", size="2", weight="medium"),
                rx.text(
                    "Save stores as draft. Interpret and send finalizes and forwards to the occupational doctor.",
                    size="1", color="var(--gray-8)",
                ),
                rx.text_area(
                    placeholder="Enter medical interpretation…",
                    value=DoctorPscState.interp_notes,
                    on_change=DoctorPscState.set_interp_notes,
                    width="100%",
                    rows="7",
                ),
                spacing="2", width="100%", margin_top="0.75rem",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancel", variant="soft", color_scheme="gray",
                              on_click=DoctorPscState.close_interp_dialog)
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("save", size=14),
                    "Save (draft)",
                    variant="soft",
                    color_scheme="gray",
                    on_click=DoctorPscState.save_notes_only,
                    loading=DoctorPscState.is_saving,
                ),
                rx.button(
                    rx.icon("send", size=14),
                    "Interpret and send",
                    color_scheme="blue",
                    on_click=DoctorPscState.save_interpretation,
                    loading=DoctorPscState.is_saving,
                ),
                spacing="2", margin_top="1rem", width="100%",
            ),
            max_width="620px",
        ),
        open=DoctorPscState.interp_dialog_open,
        on_open_change=lambda _: DoctorPscState.close_interp_dialog(),
    )


def _enterprise_dossier_row(d: EntDossierRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(d.patient_name, size="2", weight="medium"),
                rx.text(d.patient_number, size="1", color="var(--gray-9)"),
                spacing="0",
            )
        ),
        rx.table.cell(rx.text(d.campaign_name, size="2")),
        rx.table.cell(
            rx.badge(d.medical_status_label, color_scheme=d.medical_status_color, size="1", variant="soft")
        ),
        rx.table.cell(
            rx.cond(
                d.psc_notes != "",
                rx.tooltip(
                    rx.icon("file-text", size=14, color="var(--gray-9)"),
                    content=d.psc_notes,
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                d.patient_message != "",
                rx.tooltip(
                    rx.icon("mail", size=14, color="var(--accent-9)"),
                    content=d.patient_message,
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pen-line", size=14),
                        variant="ghost", size="1", color_scheme="violet",
                        on_click=lambda: DoctorEnterpriseState.open_dialog(
                            d.campaign_id, d.patient_id, d.patient_name,
                            d.enterprise_notes, d.patient_message
                        ),
                    ),
                    content="Add / edit interpretation",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("check", size=14),
                        variant="ghost", size="1", color_scheme="green",
                        on_click=lambda: DoctorEnterpriseState.validate_patient(d.campaign_id, d.patient_id),
                        disabled=d.medical_status != "ENTERPRISE_INTERPRETED",
                    ),
                    content="Validate company interpretation",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("send", size=14),
                        variant="ghost", size="1", color_scheme="indigo",
                        on_click=lambda: DoctorEnterpriseState.publish_patient(d.campaign_id, d.patient_id),
                        disabled=d.medical_status != "ENTERPRISE_VALIDATED",
                    ),
                    content="Publish to patient",
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _enterprise_interpretation_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text("Company interpretation — "),
                    rx.text(DoctorEnterpriseState.dialog_patient_name, weight="bold"),
                    spacing="1",
                )
            ),
            rx.vstack(
                rx.callout(
                    "The patient message will be visible to the patient after publication. Do not include raw medical data.",
                    icon="info", color_scheme="blue", size="1",
                ),
                rx.text("Internal comment", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Internal notes (not visible to patient)…",
                    value=DoctorEnterpriseState.enterprise_notes_input,
                    on_change=DoctorEnterpriseState.set_enterprise_notes,
                    width="100%", rows="3",
                ),
                rx.text("Message for the patient *", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Message displayed in the patient portal…",
                    value=DoctorEnterpriseState.patient_message_input,
                    on_change=DoctorEnterpriseState.set_patient_message,
                    width="100%", rows="4",
                ),
                rx.cond(
                    DoctorEnterpriseState.dialog_error != "",
                    rx.callout(DoctorEnterpriseState.dialog_error, icon="info",
                               color_scheme="red", size="1"),
                ),
                spacing="3", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Cancel", variant="soft", color_scheme="gray",
                                          on_click=DoctorEnterpriseState.close_dialog)),
                rx.button("Save", on_click=DoctorEnterpriseState.save_interpretation,
                          loading=DoctorEnterpriseState.is_saving),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="600px",
        ),
        open=DoctorEnterpriseState.dialog_open,
        on_open_change=lambda _: DoctorEnterpriseState.close_dialog(),
    )


def _enterprise_tab() -> rx.Component:
    """Dossiers PSC-validés en attente d'interprétation et publication entreprise."""
    return rx.vstack(
        rx.cond(
            DoctorEnterpriseState.error != "",
            rx.callout(DoctorEnterpriseState.error, icon="info", color_scheme="red", size="2",
                       on_click=DoctorEnterpriseState.dismiss_messages, style={"cursor": "pointer"}),
        ),
        rx.cond(
            DoctorEnterpriseState.success != "",
            rx.callout(DoctorEnterpriseState.success, icon="check", color_scheme="green", size="2",
                       on_click=DoctorEnterpriseState.dismiss_messages, style={"cursor": "pointer"}),
        ),
        rx.cond(
            DoctorEnterpriseState.dossiers_truncated,
            rx.callout(
                "Results limited to 500 records.",
                icon="triangle-alert", color_scheme="orange", size="1",
            ),
            rx.fragment(),
        ),
        rx.cond(
            DoctorEnterpriseState.is_loading,
            rx.center(rx.spinner(size="3"), padding="4rem"),
            rx.cond(
                DoctorEnterpriseState.dossiers.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Patient"),
                            rx.table.column_header_cell("Campaign"),
                            rx.table.column_header_cell("Status"),
                            rx.table.column_header_cell("PSC Interpretation"),
                            rx.table.column_header_cell("Patient message"),
                            rx.table.column_header_cell("Actions"),
                        )
                    ),
                    rx.table.body(rx.foreach(DoctorEnterpriseState.dossiers, _enterprise_dossier_row)),
                    width="100%", variant="surface",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("check", size=32, color="var(--green-9)"),
                        rx.text("No record available.", size="2", color="var(--gray-9)"),
                        align="center", spacing="2",
                    ),
                    padding="4rem",
                ),
            ),
        ),
        width="100%",
        spacing="3",
    )


# ── Tab content ───────────────────────────────────────────────────────────────

def _campaigns_tab() -> rx.Component:
    """Dossiers issus des campagnes de médecine du travail."""
    return rx.vstack(
        _filter_bar(),
        rx.cond(
            DoctorPscState.is_loading,
            rx.center(rx.spinner(size="3"), padding="4rem"),
            rx.cond(
                DoctorPscState.dossiers.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Patient"),
                            rx.table.column_header_cell("Campaign"),
                            rx.table.column_header_cell("Company"),
                            rx.table.column_header_cell("Medical status"),
                            rx.table.column_header_cell("PSC notes"),
                            rx.table.column_header_cell("Actions"),
                        )
                    ),
                    rx.table.body(rx.foreach(DoctorPscState.dossiers, _dossier_row)),
                    width="100%",
                    variant="surface",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("check", size=32, color="var(--green-9)"),
                        rx.text("No record for this filter.", size="2", color="var(--gray-9)"),
                        align="center", spacing="2",
                    ),
                    padding="4rem",
                ),
            ),
        ),
        width="100%",
        spacing="3",
    )


def _clinique_tab() -> rx.Component:
    """Consultations cliniques individuelles (hors campagne) et examens prescrits."""
    return rx.vstack(
        # ── Section 1: Consultations from consultation form ────────────────
        rx.vstack(
            rx.hstack(
                rx.icon("stethoscope", size=15, color="var(--violet-9)"),
                rx.heading("Clinical consultations", size="4"),
                rx.badge(
                    DoctorPscState.clinic_consultations.length().to_string(),
                    color_scheme="violet", variant="soft", size="1",
                ),
                spacing="2", align="center",
            ),
            rx.cond(
                DoctorPscState.is_loading,
                rx.center(rx.spinner(size="3"), padding="2rem"),
                rx.cond(
                    DoctorPscState.clinic_consultations.length() > 0,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Patient"),
                                rx.table.column_header_cell("Date"),
                                rx.table.column_header_cell("Type"),
                                rx.table.column_header_cell("Reason"),
                                rx.table.column_header_cell("Exams"),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(DoctorPscState.clinic_consultations, _clinic_consult_row),
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("stethoscope", size=28, color="var(--gray-5)"),
                            rx.text("No clinical consultation recorded.", size="2", color="var(--gray-7)"),
                            align="center", spacing="2",
                        ),
                        padding="2rem",
                    ),
                ),
            ),
            width="100%",
            spacing="2",
        ),
        rx.separator(width="100%"),
        # ── Section 2: Standalone prescribed exams ────────────────────────
        rx.vstack(
            rx.hstack(
                rx.icon("flask-conical", size=15, color="var(--blue-9)"),
                rx.heading("Prescribed exams (outside consultation)", size="4"),
                rx.badge(
                    DoctorPscState.independent_exams.length().to_string(),
                    color_scheme="blue", variant="soft", size="1",
                ),
                spacing="2", align="center",
            ),
            rx.callout(
                "These exams were prescribed directly or created from an appointment, "
                "outside the clinical consultation workflow.",
                icon="info",
                color_scheme="blue",
                size="1",
            ),
            rx.cond(
                DoctorPscState.is_loading,
                rx.center(rx.spinner(size="3"), padding="2rem"),
                rx.cond(
                    DoctorPscState.independent_exams.length() > 0,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Patient"),
                                rx.table.column_header_cell("Date"),
                                rx.table.column_header_cell("Exam type"),
                                rx.table.column_header_cell("Statut"),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(DoctorPscState.independent_exams, _independent_exam_row),
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("check", size=28, color="var(--green-8)"),
                            rx.text("No prescribed exam pending.", size="2", color="var(--gray-7)"),
                            align="center", spacing="2",
                        ),
                        padding="2rem",
                    ),
                ),
            ),
            width="100%",
            spacing="2",
        ),
        width="100%",
        spacing="4",
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def doctor_psc_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Medical records", size="6"),
                        rx.text(
                            "PSC interpretation · Company validation · Patient publication",
                            size="2", color="var(--gray-9)",
                        ),
                        spacing="0",
                    ),
                    width="100%", align="end",
                ),
                rx.cond(
                    DoctorPscState.error != "",
                    rx.callout(DoctorPscState.error, icon="info", color_scheme="red", size="2",
                               on_click=DoctorPscState.dismiss_messages, style={"cursor": "pointer"}),
                ),
                rx.cond(
                    DoctorPscState.success != "",
                    rx.callout(DoctorPscState.success, icon="check", color_scheme="green", size="2",
                               on_click=DoctorPscState.dismiss_messages, style={"cursor": "pointer"}),
                ),
                rx.cond(
                    DoctorPscState.dossiers_truncated,
                    rx.callout(
                        "Results limited to 500 records. Use the Campaign or Status filters to narrow the selection.",
                        icon="triangle-alert",
                        color_scheme="orange",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger(
                            rx.hstack(
                                rx.icon("users", size=14),
                                rx.text("Campaign records"),
                                rx.badge(
                                    DoctorPscState.dossiers.length().to_string(),
                                    color_scheme="blue", variant="soft", size="1",
                                ),
                                spacing="2", align="center",
                            ),
                            value="campaigns",
                        ),
                        rx.tabs.trigger(
                            rx.hstack(
                                rx.icon("stethoscope", size=14),
                                rx.text("Clinical consultations"),
                                rx.badge(
                                    (DoctorPscState.clinic_consultations.length() + DoctorPscState.independent_exams.length()).to_string(),
                                    color_scheme="violet", variant="soft", size="1",
                                ),
                                spacing="2", align="center",
                            ),
                            value="clinique",
                        ),
                        rx.tabs.trigger(
                            rx.hstack(
                                rx.icon("building-2", size=14),
                                rx.text("Company interpretation"),
                                rx.badge(
                                    DoctorEnterpriseState.dossiers.length().to_string(),
                                    color_scheme="indigo", variant="soft", size="1",
                                ),
                                spacing="2", align="center",
                            ),
                            value="enterprise",
                        ),
                    ),
                    rx.tabs.content(_campaigns_tab(), value="campaigns", padding_top="1rem"),
                    rx.tabs.content(_clinique_tab(), value="clinique", padding_top="1rem"),
                    rx.tabs.content(_enterprise_tab(), value="enterprise", padding_top="1rem"),
                    default_value="campaigns",
                    width="100%",
                ),
                spacing="4", width="100%",
            ),
            _interp_dialog(),
            _enterprise_interpretation_dialog(),
        )
    )
