"""Doctor PSC page component — three-tab layout: campagnes / consultations cliniques / entreprise."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .doctor_psc_state import ClinicConsultationRowDTO, DossierRowDTO, IndependentExamRowDTO, DoctorPscState
from ..doctor_enterprise.doctor_enterprise_state import DoctorEnterpriseState, EntDossierRowDTO

_STATUS_FILTER_OPTIONS = [
    ("ALL",             "Tous les dossiers actifs"),
    ("LAB_ENTERED",     "📋 Résultats saisis — à interpréter"),
    ("LAB_VALIDATED",   "✅ Labo validé — à interpréter"),
    ("PSC_INTERPRETED", "🩺 Interprété PSC — à valider"),
    ("PSC_VALIDATED",   "🔒 Validé PSC"),
]


# ── Filter bar (campagnes tab) ────────────────────────────────────────────────

def _campaign_option(c: list) -> rx.Component:
    return rx.select.item(c[1], value=c[0])


def _filter_bar() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text("Statut", size="1", weight="medium", color="var(--gray-9)"),
                rx.select.root(
                    rx.select.trigger(placeholder="Tous les statuts", min_width="240px"),
                    rx.select.content(
                        *[rx.select.item(label, value=val) for val, label in _STATUS_FILTER_OPTIONS]
                    ),
                    value=DoctorPscState.filter_status,
                    on_change=DoctorPscState.set_filter_status,
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Campagne", size="1", weight="medium", color="var(--gray-9)"),
                rx.select.root(
                    rx.select.trigger(placeholder="Toutes les campagnes", min_width="220px"),
                    rx.select.content(
                        rx.select.item("Toutes les campagnes", value="__all__"),
                        rx.foreach(DoctorPscState.campaigns_for_filter, _campaign_option),
                    ),
                    value=DoctorPscState.filter_campaign_id,
                    on_change=DoctorPscState.set_filter_campaign,
                ),
                spacing="1",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("refresh-cw", size=14), "Actualiser",
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
                    content="Voir les résultats saisis",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pen-line", size=14),
                        variant="ghost", size="1", color_scheme="blue",
                        on_click=lambda: DoctorPscState.open_interp_dialog(
                            d.campaign_id, d.patient_id, d.patient_name, d.psc_notes, d.medical_status
                        ),
                    ),
                    content="Saisir / modifier l'interprétation",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("check", size=14),
                        variant="ghost", size="1", color_scheme="green",
                        on_click=lambda: DoctorPscState.validate_patient(d.campaign_id, d.patient_id),
                        disabled=d.medical_status != "PSC_INTERPRETED",
                    ),
                    content="Valider le dossier PSC",
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
                rx.badge("Brouillon", color_scheme="gray", size="1", variant="soft"),
                rx.cond(
                    exam.has_lab_results,
                    rx.badge("Résultats saisis", color_scheme="blue", size="1", variant="soft"),
                    rx.badge("En attente labo", color_scheme="orange", size="1", variant="soft"),
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
                content="Voir l'examen et les résultats",
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
                rx.badge(c.nb_exams.to_string() + " examen(s)", color_scheme="blue", size="1", variant="surface"),
                rx.text("Aucun examen", size="1", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("stethoscope", size=14),
                    variant="ghost", size="1", color_scheme="violet",
                    on_click=rx.redirect("/patient/" + c.patient_id),
                ),
                content="Voir le dossier patient et les examens",
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
                    rx.text("Interprétation PSC —"),
                    rx.text(DoctorPscState.interp_patient_name, weight="bold"),
                    spacing="1",
                )
            ),
            rx.vstack(
                rx.text("Commentaire / Interprétation médicale", size="2", weight="medium"),
                rx.text(
                    "Enregistrer sauvegarde en brouillon. Interpréter et transmettre finalise et envoie au médecin entreprise.",
                    size="1", color="var(--gray-8)",
                ),
                rx.text_area(
                    placeholder="Saisir l'interprétation médicale…",
                    value=DoctorPscState.interp_notes,
                    on_change=DoctorPscState.set_interp_notes,
                    width="100%",
                    rows="7",
                ),
                spacing="2", width="100%", margin_top="0.75rem",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Annuler", variant="soft", color_scheme="gray",
                              on_click=DoctorPscState.close_interp_dialog)
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("save", size=14),
                    "Enregistrer (brouillon)",
                    variant="soft",
                    color_scheme="gray",
                    on_click=DoctorPscState.save_notes_only,
                    loading=DoctorPscState.is_saving,
                ),
                rx.button(
                    rx.icon("send", size=14),
                    "Interpréter et transmettre",
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
                    content="Ajouter / modifier l'interprétation",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("check", size=14),
                        variant="ghost", size="1", color_scheme="green",
                        on_click=lambda: DoctorEnterpriseState.validate_patient(d.campaign_id, d.patient_id),
                        disabled=d.medical_status != "ENTERPRISE_INTERPRETED",
                    ),
                    content="Valider l'interprétation entreprise",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("send", size=14),
                        variant="ghost", size="1", color_scheme="indigo",
                        on_click=lambda: DoctorEnterpriseState.publish_patient(d.campaign_id, d.patient_id),
                        disabled=d.medical_status != "ENTERPRISE_VALIDATED",
                    ),
                    content="Publier au patient",
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
                    rx.text("Interprétation entreprise — "),
                    rx.text(DoctorEnterpriseState.dialog_patient_name, weight="bold"),
                    spacing="1",
                )
            ),
            rx.vstack(
                rx.callout(
                    "Le message patient sera visible par le patient après publication. Ne pas inclure de données médicales brutes.",
                    icon="info", color_scheme="blue", size="1",
                ),
                rx.text("Commentaire interne", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Notes internes (non visibles par le patient)…",
                    value=DoctorEnterpriseState.enterprise_notes_input,
                    on_change=DoctorEnterpriseState.set_enterprise_notes,
                    width="100%", rows="3",
                ),
                rx.text("Message destiné au patient *", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Message qui sera affiché dans l'espace patient…",
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
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=DoctorEnterpriseState.close_dialog)),
                rx.button("Enregistrer", on_click=DoctorEnterpriseState.save_interpretation,
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
                "Résultats limités à 500 dossiers.",
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
                            rx.table.column_header_cell("Campagne"),
                            rx.table.column_header_cell("Statut"),
                            rx.table.column_header_cell("Interprétation PSC"),
                            rx.table.column_header_cell("Message patient"),
                            rx.table.column_header_cell("Actions"),
                        )
                    ),
                    rx.table.body(rx.foreach(DoctorEnterpriseState.dossiers, _enterprise_dossier_row)),
                    width="100%", variant="surface",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("check", size=32, color="var(--green-9)"),
                        rx.text("Aucun dossier disponible.", size="2", color="var(--gray-9)"),
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
                            rx.table.column_header_cell("Campagne"),
                            rx.table.column_header_cell("Entreprise"),
                            rx.table.column_header_cell("Statut médical"),
                            rx.table.column_header_cell("Notes PSC"),
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
                        rx.text("Aucun dossier pour ce filtre.", size="2", color="var(--gray-9)"),
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
                rx.heading("Consultations cliniques", size="4"),
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
                                rx.table.column_header_cell("Motif"),
                                rx.table.column_header_cell("Examens"),
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
                            rx.text("Aucune consultation clinique enregistrée.", size="2", color="var(--gray-7)"),
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
                rx.heading("Examens prescrits (hors consultation)", size="4"),
                rx.badge(
                    DoctorPscState.independent_exams.length().to_string(),
                    color_scheme="blue", variant="soft", size="1",
                ),
                spacing="2", align="center",
            ),
            rx.callout(
                "Ces examens ont été prescrits directement ou créés depuis un rendez-vous, "
                "hors du circuit des consultations cliniques.",
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
                                rx.table.column_header_cell("Type d'examen"),
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
                            rx.text("Aucun examen prescrit en attente.", size="2", color="var(--gray-7)"),
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
                        rx.heading("Dossiers médicaux", size="6"),
                        rx.text(
                            "Interprétation PSC · Validation entreprise · Publication patient",
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
                        "Résultats limités à 500 dossiers. Utilisez les filtres Campagne ou Statut pour affiner la sélection.",
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
                                rx.text("Dossiers campagnes"),
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
                                rx.text("Consultations cliniques"),
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
                                rx.text("Interprétation entreprise"),
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
