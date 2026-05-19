"""Campaign detail page — full workflow UI."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.nav_role_state import NavRoleState
from ..common.page_layout import page_layout
from .campaign_detail_state import (
    CampaignDetailState,
    CampaignExamTypeDTO,
    CampaignPatientRowDTO,
    ExamTypeOptionDTO,
    PatientSearchOptionDTO,
)

# ── Helper components ──────────────────────────────────────────────────────

def _status_badge(label: str, color: str) -> rx.Component:
    return rx.badge(label, color_scheme=color, variant="soft", size="2")


def _info_item(label: str, value: rx.Var) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", color="var(--gray-9)", weight="medium"),
        rx.cond(
            value != "",
            rx.text(value, size="2"),
            rx.text("—", size="2", color="var(--gray-7)"),
        ),
        spacing="0",
        align_items="start",
    )


def _presence_selector(p: CampaignPatientRowDTO) -> rx.Component:
    return rx.select.root(
        rx.select.trigger(size="1"),
        rx.select.content(
            rx.select.item("En attente", value="PENDING"),
            rx.select.item("Présent", value="PRESENT"),
            rx.select.item("Absent", value="ABSENT"),
        ),
        value=p.presence_status,
        on_change=lambda v: CampaignDetailState.set_presence(p.patient_id, v),
        size="1",
    )


def _presence_badge(p: CampaignPatientRowDTO) -> rx.Component:
    return rx.badge(p.presence_label, color_scheme=p.presence_color, size="1", variant="soft")


def _medical_badge(p: CampaignPatientRowDTO) -> rx.Component:
    return rx.badge(p.medical_status_label, color_scheme=p.medical_status_color, size="1", variant="soft")


# ── Campaign info card ─────────────────────────────────────────────────────

def _campaign_info_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("flag", size=20, color="var(--accent-9)"),
                rx.heading(CampaignDetailState.campaign.name, size="5"),
                rx.spacer(),
                _status_badge(
                    CampaignDetailState.campaign.status_label,
                    CampaignDetailState.campaign.status_color,
                ),
                rx.tooltip(
                    rx.icon_button(rx.icon("pen-line", size=14), variant="ghost", size="1",
                                   on_click=CampaignDetailState.open_edit_dialog),
                    content="Modifier la campagne",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.text(CampaignDetailState.campaign.account_name, size="2", color="var(--gray-9)"),
            rx.separator(width="100%"),
            rx.grid(
                _info_item("Début", CampaignDetailState.campaign.start_date),
                _info_item("Fin", CampaignDetailState.campaign.end_date),
                _info_item("Lieu", CampaignDetailState.campaign.location),
                _info_item("Médecin PSC", CampaignDetailState.campaign.psc_doctor_name),
                _info_item("Médecin entreprise", CampaignDetailState.campaign.enterprise_doctor_name),
                _info_item("Notes", CampaignDetailState.campaign.notes),
                columns="3",
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text(CampaignDetailState.campaign.patient_count, size="5", weight="bold", color="var(--accent-9)"),
                    rx.text("patients inscrits", size="1", color="var(--gray-9)"),
                    align_items="center",
                ),
                rx.vstack(
                    rx.text(CampaignDetailState.campaign.present_count, size="5", weight="bold", color="var(--green-9)"),
                    rx.text("présents", size="1", color="var(--gray-9)"),
                    align_items="center",
                ),
                rx.vstack(
                    rx.text(CampaignDetailState.campaign.absent_count, size="5", weight="bold", color="var(--red-9)"),
                    rx.text("absents", size="1", color="var(--gray-9)"),
                    align_items="center",
                ),
                spacing="6",
                justify="center",
                padding_top="0.5rem",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


# ── Workflow action bar ────────────────────────────────────────────────────

def _workflow_bar() -> rx.Component:
    status = CampaignDetailState.campaign.status
    loading = CampaignDetailState.is_loading
    return rx.card(
        rx.vstack(
            rx.text("Actions disponibles", size="2", weight="medium", color="var(--gray-9)"),
            rx.hstack(
                rx.cond(
                    status == "DRAFT",
                    rx.button("Soumettre", on_click=CampaignDetailState.submit_campaign,
                              color_scheme="blue", size="2", loading=loading),
                ),
                rx.cond(
                    status == "AWAITING_OP_VALIDATION",
                    rx.button("Valider opérationnellement", on_click=CampaignDetailState.validate_ops,
                              color_scheme="cyan", size="2", loading=loading),
                ),
                rx.cond(
                    status == "AWAITING_MEDICAL_VALIDATION",
                    rx.hstack(
                        rx.button("Valider médicalement", on_click=CampaignDetailState.validate_medical,
                                  color_scheme="purple", size="2", loading=loading),
                        rx.button("Refuser", on_click=CampaignDetailState.open_refuse_dialog,
                                  color_scheme="red", variant="soft", size="2", disabled=loading),
                        spacing="2",
                    ),
                ),
                rx.cond(
                    (status == "OPERATIONALLY_VALIDATED") | (status == "MEDICALLY_VALIDATED"),
                    rx.button("Prête pour convocations", on_click=CampaignDetailState.ready_for_convocations,
                              color_scheme="indigo", size="2", loading=loading),
                ),
                rx.cond(
                    status == "READY_FOR_CONVOCATION",
                    rx.button("Envoyer convocations", on_click=CampaignDetailState.send_convocations,
                              color_scheme="sky", size="2", loading=loading),
                ),
                rx.cond(
                    status == "CONVOCATIONS_SENT",
                    rx.button("Démarrer terrain", on_click=CampaignDetailState.start_terrain,
                              color_scheme="orange", size="2", loading=loading),
                ),
                rx.cond(
                    status == "TERRAIN_EN_COURS",
                    rx.button("Clôturer terrain", on_click=CampaignDetailState.close_terrain,
                              color_scheme="amber", size="2", loading=loading),
                ),
                rx.cond(
                    status == "TERRAIN_CLOTURE",
                    rx.button("Démarrer labo", on_click=CampaignDetailState.start_lab,
                              color_scheme="yellow", size="2", loading=loading),
                ),
                rx.cond(
                    status == "LABO_EN_COURS",
                    rx.button("Valider labo campagne", on_click=CampaignDetailState.validate_lab_campaign,
                              color_scheme="lime", size="2", loading=loading),
                ),
                rx.cond(
                    status == "LABO_VALIDE",
                    rx.button("Valider PSC campagne", on_click=CampaignDetailState.validate_psc_campaign,
                              color_scheme="teal", size="2", loading=loading),
                ),
                rx.cond(
                    status == "VALIDE_MEDECIN_PSC",
                    rx.button("Publier médecin entreprise", on_click=CampaignDetailState.publish_campaign,
                              color_scheme="cyan", size="2", loading=loading),
                ),
                rx.cond(
                    status == "PUBLIE_MEDECIN_ENTREPRISE",
                    rx.button("Publier aux patients", on_click=CampaignDetailState.publish_to_patients,
                              color_scheme="green", size="2", loading=loading),
                ),
                rx.cond(
                    status == "PUBLIE_PATIENT",
                    rx.button("Archiver", on_click=CampaignDetailState.archive_campaign,
                              color_scheme="gray", variant="soft", size="2", loading=loading),
                ),
                spacing="2",
                flex_wrap="wrap",
            ),
            spacing="2",
        ),
        width="100%",
        background="var(--gray-1)",
    )


# ── Patients tab ───────────────────────────────────────────────────────────

def _patient_row(p: CampaignPatientRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p.patient_number, size="2", weight="medium")),
        rx.table.cell(rx.text(f"{p.last_name} {p.first_name}", size="2")),
        rx.table.cell(rx.cond(p.phone != "", rx.text(p.phone, size="2"), rx.text("—", size="2", color="var(--gray-7)"))),
        rx.table.cell(_presence_selector(p)),
        rx.table.cell(_medical_badge(p)),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("clipboard-list", size=14),
                        variant="solid",
                        size="1",
                        color_scheme="indigo",
                        on_click=rx.redirect(
                            "/campaign-patient/"
                            + CampaignDetailState.campaign.id
                            + "/"
                            + p.patient_id
                        ),
                        disabled=CampaignDetailState.is_loading,
                    ),
                    content="Saisir les résultats d'examens",
                ),
                rx.cond(
                    NavRoleState.is_operateur_labo | NavRoleState.is_upper_admin | NavRoleState.no_role_assigned,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("check", size=14),
                            variant="ghost", size="1", color_scheme="lime",
                            on_click=lambda: CampaignDetailState.validate_lab_patient(p.patient_id),
                            disabled=CampaignDetailState.is_loading,
                        ),
                        content="Valider résultats labo",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    NavRoleState.is_medecin_psc | NavRoleState.is_upper_admin | NavRoleState.no_role_assigned,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("shield", size=14),
                            variant="ghost", size="1", color_scheme="blue",
                            on_click=lambda: CampaignDetailState.open_psc_dialog(
                                p.patient_id, f"{p.last_name} {p.first_name}", p.psc_notes
                            ),
                            disabled=CampaignDetailState.is_loading,
                        ),
                        content="Interprétation PSC",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    NavRoleState.is_medecin_entreprise | NavRoleState.is_upper_admin | NavRoleState.no_role_assigned,
                    rx.hstack(
                        rx.tooltip(
                            rx.icon_button(
                                rx.icon("building-2", size=14),
                                variant="ghost", size="1", color_scheme="violet",
                                on_click=lambda: CampaignDetailState.open_enterprise_dialog(
                                    p.patient_id, f"{p.last_name} {p.first_name}",
                                    p.enterprise_notes, p.patient_message
                                ),
                                disabled=CampaignDetailState.is_loading,
                            ),
                            content="Interprétation entreprise",
                        ),
                        rx.tooltip(
                            rx.icon_button(
                                rx.icon("send", size=14),
                                variant="ghost", size="1", color_scheme="green",
                                on_click=lambda: CampaignDetailState.publish_patient_results(p.patient_id),
                                disabled=CampaignDetailState.is_loading,
                            ),
                            content="Publier au patient",
                        ),
                        spacing="1",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    NavRoleState.is_upper_admin | NavRoleState.no_role_assigned,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("trash-2", size=14),
                            variant="ghost", size="1", color_scheme="red",
                            on_click=lambda: CampaignDetailState.open_confirm_remove_patient(
                                p.patient_id, f"{p.last_name} {p.first_name}"
                            ),
                            disabled=CampaignDetailState.is_loading,
                        ),
                        content="Retirer de la campagne",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _patients_section() -> rx.Component:
    # Progress bar: ratio of patients with exam done (not PENDING)
    total = CampaignDetailState.patients.length()
    done_count = CampaignDetailState.campaign.present_count
    return rx.vstack(
        rx.hstack(
            rx.heading("Patients inscrits", size="4"),
            rx.spacer(),
            rx.cond(
                CampaignDetailState.patients.length() > 0,
                rx.button(
                    rx.icon("download", size=14), "Exporter CSV",
                    variant="soft", size="2", color_scheme="gray",
                    on_click=CampaignDetailState.export_patients_csv,
                ),
                rx.fragment(),
            ),
            rx.button(
                rx.icon("user-plus", size=14), "Ajouter un patient",
                variant="soft", size="2",
                on_click=CampaignDetailState.open_add_patient_dialog,
            ),
            width="100%", align="center", spacing="2",
        ),
        # Participation progress bar
        rx.cond(
            CampaignDetailState.campaign != None,
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Présents : ",
                        rx.text.strong(CampaignDetailState.campaign.present_count),
                        " / ",
                        CampaignDetailState.campaign.patient_count,
                        size="2",
                    ),
                    rx.spacer(),
                    rx.cond(
                        CampaignDetailState.campaign.patient_count > 0,
                        rx.text(
                            (CampaignDetailState.campaign.present_count * 100 // CampaignDetailState.campaign.patient_count).to(str) + " %",
                            size="2",
                            weight="bold",
                            color="var(--teal-9)",
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                ),
                rx.box(
                    rx.box(
                        height="8px",
                        border_radius="4px",
                        background="var(--teal-9)",
                        width=rx.cond(
                            CampaignDetailState.campaign.patient_count > 0,
                            (CampaignDetailState.campaign.present_count * 100 // CampaignDetailState.campaign.patient_count).to(str) + "%",
                            "0%",
                        ),
                        transition="width 0.4s ease",
                    ),
                    height="8px",
                    background="var(--teal-3)",
                    border_radius="4px",
                    width="100%",
                    overflow="hidden",
                ),
                spacing="1",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            CampaignDetailState.patients.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("N° dossier"),
                        rx.table.column_header_cell("Nom / Prénom"),
                        rx.table.column_header_cell("Téléphone"),
                        rx.table.column_header_cell("Présence"),
                        rx.table.column_header_cell("Statut médical"),
                        rx.table.column_header_cell("Actions"),
                    )
                ),
                rx.table.body(rx.foreach(CampaignDetailState.patients, _patient_row)),
                width="100%",
                variant="surface",
            ),
            rx.center(
                rx.text("Aucun patient inscrit.", size="2", color="var(--gray-9)"),
                padding="2rem",
            ),
        ),
        spacing="3",
        width="100%",
    )


# ── Exam types tab ─────────────────────────────────────────────────────────

def _exam_type_row(ce: CampaignExamTypeDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(ce.exam_type_name, size="2", weight="medium")),
        rx.table.cell(rx.badge(ce.category_label, color_scheme="blue", size="1", variant="soft")),
        rx.table.cell(
            rx.cond(
                NavRoleState.is_upper_admin | NavRoleState.no_role_assigned,
                rx.icon_button(
                    rx.icon("trash-2", size=14),
                    variant="ghost", size="1", color_scheme="red",
                    on_click=lambda: CampaignDetailState.open_confirm_remove_exam_type(ce.id, ce.exam_type_name),
                ),
                rx.fragment(),
            )
        ),
    )


def _exam_types_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Types d'examens configurés", size="4"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14), "Ajouter un examen",
                variant="soft", size="2",
                on_click=CampaignDetailState.open_add_exam_type_dialog,
            ),
            width="100%", align="center",
        ),
        rx.cond(
            CampaignDetailState.exam_types.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Nom"),
                        rx.table.column_header_cell("Catégorie"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(rx.foreach(CampaignDetailState.exam_types, _exam_type_row)),
                width="100%",
                variant="surface",
            ),
            rx.center(
                rx.text("Aucun type d'examen configuré.", size="2", color="var(--gray-9)"),
                padding="2rem",
            ),
        ),
        spacing="3",
        width="100%",
    )


# ── Dialogs ────────────────────────────────────────────────────────────────

def _refuse_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Refus de validation médicale"),
            rx.vstack(
                rx.text("Motif de refus *", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Expliquez la raison du refus…",
                    value=CampaignDetailState.refuse_reason,
                    on_change=CampaignDetailState.set_refuse_reason,
                    width="100%",
                    rows="4",
                ),
                rx.cond(
                    CampaignDetailState.refuse_error != "",
                    rx.callout(
                        CampaignDetailState.refuse_error,
                        icon="info", color_scheme="red", size="1",
                    ),
                ),
                spacing="2",
                width="100%",
                margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray")),
                rx.button("Confirmer le refus", color_scheme="red",
                          on_click=CampaignDetailState.confirm_refuse_medical),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="480px",
        ),
        open=CampaignDetailState.refuse_dialog_open,
        on_open_change=lambda _: CampaignDetailState.dismiss_error(),
    )


def _add_patient_dialog() -> rx.Component:
    def _patient_row(p) -> rx.Component:
        is_selected = CampaignDetailState.selected_patient_ids.contains(p.id)
        return rx.hstack(
            rx.checkbox(
                checked=is_selected,
                on_change=lambda _: CampaignDetailState.toggle_patient_selection(p.id),
                size="2",
            ),
            rx.text(p.label, size="2"),
            spacing="2",
            align="center",
            width="100%",
            padding="0.35rem 0.5rem",
            border_radius="var(--radius-1)",
            background=rx.cond(is_selected, "var(--accent-3)", "transparent"),
            _hover={"background": rx.cond(is_selected, "var(--accent-4)", "var(--gray-2)")},
            cursor="pointer",
            on_click=CampaignDetailState.toggle_patient_selection(p.id),
        )

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajouter des patients à la campagne"),
            rx.dialog.description(
                "Patients actifs affiliés au compte de l'entreprise de cette campagne.",
                size="2", color="var(--gray-9)",
            ),
            rx.vstack(
                rx.hstack(
                    rx.input(
                        placeholder="Filtrer par nom, prénom ou n° dossier…",
                        value=CampaignDetailState.patient_search,
                        on_change=CampaignDetailState.search_patients,
                        width="100%",
                        flex="1",
                    ),
                    rx.cond(
                        CampaignDetailState.selected_patient_ids.length() > 0,
                        rx.badge(
                            CampaignDetailState.selected_patient_ids.length(),
                            " sélectionné(s)",
                            color_scheme="blue",
                            size="2",
                        ),
                    ),
                    spacing="2",
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    CampaignDetailState.patient_options.length() > 0,
                    rx.box(
                        rx.foreach(
                            CampaignDetailState.patient_options,
                            _patient_row,
                        ),
                        max_height="280px",
                        overflow_y="auto",
                        border="1px solid var(--gray-4)",
                        border_radius="var(--radius-2)",
                        padding="0.25rem",
                        width="100%",
                    ),
                    rx.callout(
                        rx.cond(
                            CampaignDetailState.patient_search != "",
                            "Aucun résultat pour cette recherche.",
                            "Aucun patient disponible — vérifiez que des employés sont affiliés à ce compte entreprise.",
                        ),
                        icon="info",
                        color_scheme="orange",
                        size="1",
                    ),
                ),
                rx.text(
                    "Cliquez sur les patients pour les sélectionner / désélectionner.",
                    size="1",
                    color="var(--gray-9)",
                ),
                spacing="3", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=CampaignDetailState.close_add_patient_dialog)),
                rx.button(
                    rx.icon("user-plus", size=14),
                    rx.cond(
                        CampaignDetailState.selected_patient_ids.length() > 0,
                        "Ajouter (" + CampaignDetailState.selected_patient_ids.length().to_string() + ")",
                        "Ajouter",
                    ),
                    on_click=CampaignDetailState.confirm_add_patient,
                    loading=CampaignDetailState.is_adding_patient,
                    disabled=CampaignDetailState.selected_patient_ids.length() == 0,
                ),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="520px",
        ),
        open=CampaignDetailState.add_patient_dialog_open,
        on_open_change=lambda _: CampaignDetailState.close_add_patient_dialog(),
    )


def _add_exam_type_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajouter un type d'examen"),
            rx.vstack(
                rx.select.root(
                    rx.select.trigger(placeholder="Sélectionner un type d'examen", width="100%"),
                    rx.select.content(
                        rx.foreach(
                            CampaignDetailState.exam_type_options,
                            lambda e: rx.select.item(
                                f"{e.name} ({e.category_label})", value=e.id
                            ),
                        )
                    ),
                    value=CampaignDetailState.selected_exam_type_id,
                    on_change=CampaignDetailState.set_selected_exam_type,
                ),
                spacing="3", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=CampaignDetailState.close_add_exam_type_dialog)),
                rx.button("Ajouter", on_click=CampaignDetailState.confirm_add_exam_type,
                          loading=CampaignDetailState.is_adding_exam_type),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="480px",
        ),
        open=CampaignDetailState.add_exam_type_dialog_open,
        on_open_change=lambda _: CampaignDetailState.close_add_exam_type_dialog(),
    )


def _psc_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text("Interprétation PSC — "),
                    rx.text(CampaignDetailState.psc_dialog_patient_name, weight="bold"),
                    spacing="1",
                )
            ),
            rx.vstack(
                rx.text("Interprétation / Conclusion *", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Saisir l'interprétation médicale PSC…",
                    value=CampaignDetailState.psc_notes_input,
                    on_change=CampaignDetailState.set_psc_notes,
                    width="100%",
                    rows="5",
                ),
                spacing="2", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=CampaignDetailState.close_psc_dialog)),
                rx.button("Enregistrer l'interprétation",
                          on_click=CampaignDetailState.save_psc_interpretation),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="600px",
        ),
        open=CampaignDetailState.psc_dialog_open,
        on_open_change=lambda _: CampaignDetailState.close_psc_dialog(),
    )


def _enterprise_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text("Interprétation entreprise — "),
                    rx.text(CampaignDetailState.enterprise_dialog_patient_name, weight="bold"),
                    spacing="1",
                )
            ),
            rx.vstack(
                rx.text("Commentaire interne", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Notes internes (non visibles par le patient)…",
                    value=CampaignDetailState.enterprise_notes_input,
                    on_change=CampaignDetailState.set_enterprise_notes,
                    width="100%",
                    rows="3",
                ),
                rx.text("Message destiné au patient *", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Message qui sera visible par le patient…",
                    value=CampaignDetailState.patient_message_input,
                    on_change=CampaignDetailState.set_patient_message,
                    width="100%",
                    rows="4",
                ),
                rx.callout(
                    "Ce message sera visible par le patient après publication.",
                    icon="info",
                    color_scheme="blue",
                    size="1",
                ),
                spacing="2", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=CampaignDetailState.close_enterprise_dialog)),
                rx.button("Enregistrer", on_click=CampaignDetailState.save_enterprise_interpretation),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="600px",
        ),
        open=CampaignDetailState.enterprise_dialog_open,
        on_open_change=lambda _: CampaignDetailState.close_enterprise_dialog(),
    )


def _edit_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Modifier la campagne"),
            rx.vstack(
                rx.vstack(
                    rx.text("Nom *", size="2", weight="medium"),
                    rx.input(
                        value=CampaignDetailState.edit_name,
                        on_change=CampaignDetailState.set_edit_name,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Date début", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=CampaignDetailState.edit_start,
                            on_change=CampaignDetailState.set_edit_start,
                            width="100%",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Date fin", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=CampaignDetailState.edit_end,
                            on_change=CampaignDetailState.set_edit_end,
                            width="100%",
                        ),
                        spacing="1",
                    ),
                    columns="2", spacing="4", width="100%",
                ),
                rx.vstack(
                    rx.text("Lieu", size="2", weight="medium"),
                    rx.input(
                        value=CampaignDetailState.edit_location,
                        on_change=CampaignDetailState.set_edit_location,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.hstack(
                    rx.text("Revue médicale requise", size="2"),
                    rx.switch(
                        checked=CampaignDetailState.edit_requires_medical_review,
                        on_change=CampaignDetailState.set_edit_requires_medical_review,
                    ),
                    spacing="2", align="center",
                ),
                rx.vstack(
                    rx.text("Notes internes", size="2", weight="medium"),
                    rx.text_area(
                        value=CampaignDetailState.edit_notes,
                        on_change=CampaignDetailState.set_edit_notes,
                        width="100%",
                        rows="3",
                    ),
                    spacing="1", width="100%",
                ),
                rx.cond(
                    CampaignDetailState.edit_error != "",
                    rx.callout(CampaignDetailState.edit_error, icon="info",
                               color_scheme="red", size="1"),
                ),
                spacing="3", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=CampaignDetailState.close_edit_dialog)),
                rx.button("Enregistrer",
                          on_click=CampaignDetailState.save_edit,
                          loading=CampaignDetailState.is_saving_edit),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="520px",
        ),
        open=CampaignDetailState.edit_dialog_open,
        on_open_change=lambda _: CampaignDetailState.close_edit_dialog(),
    )


# ── Main page ──────────────────────────────────────────────────────────────

def campaign_detail_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                # Nav back
                rx.hstack(
                    rx.button(
                        rx.icon("chevron-left", size=14), "Retour",
                        variant="ghost", size="2",
                        on_click=CampaignDetailState.go_back,
                    ),
                    width="100%",
                ),
                # Loading / error states
                rx.cond(
                    CampaignDetailState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="4rem"),
                    rx.cond(
                        CampaignDetailState.campaign != None,
                        rx.vstack(
                            rx.cond(
                                CampaignDetailState.error != "",
                                rx.card(
                                    rx.vstack(
                                        rx.hstack(
                                            rx.icon("triangle-alert", size=16, color="var(--red-9)"),
                                            rx.text(CampaignDetailState.error, size="2", color="var(--red-11)"),
                                            spacing="2", align="center",
                                        ),
                                        rx.hstack(
                                            rx.cond(
                                                CampaignDetailState.error.contains("médecin")
                                                | CampaignDetailState.error.contains("doctor")
                                                | CampaignDetailState.error.contains("PSC"),
                                                rx.button(
                                                    rx.icon("settings", size=13),
                                                    "Configurer les médecins",
                                                    size="1",
                                                    variant="soft",
                                                    color_scheme="red",
                                                    on_click=CampaignDetailState.open_edit_dialog,
                                                ),
                                                rx.fragment(),
                                            ),
                                            rx.spacer(),
                                            rx.button(
                                                rx.icon("x", size=13),
                                                size="1", variant="ghost", color_scheme="gray",
                                                on_click=CampaignDetailState.dismiss_error,
                                            ),
                                            width="100%",
                                        ),
                                        spacing="2", width="100%",
                                    ),
                                    background="var(--red-2)",
                                    width="100%",
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                CampaignDetailState.success != "",
                                rx.callout(
                                    CampaignDetailState.success,
                                    icon="check", color_scheme="green", size="2",
                                    on_click=CampaignDetailState.dismiss_success,
                                    style={"cursor": "pointer"},
                                ),
                            ),
                            _campaign_info_card(),
                            _workflow_bar(),
                            # Tabs
                            rx.tabs.root(
                                rx.tabs.list(
                                    rx.tabs.trigger("Patients", value="patients"),
                                    rx.tabs.trigger("Examens", value="exams"),
                                ),
                                rx.tabs.content(_patients_section(), value="patients"),
                                rx.tabs.content(_exam_types_section(), value="exams"),
                                default_value="patients",
                                width="100%",
                            ),
                            spacing="4",
                            width="100%",
                        ),
                        rx.center(
                            rx.text("Campagne introuvable.", size="2", color="var(--gray-9)"),
                            padding="4rem",
                        ),
                    ),
                ),
                spacing="4",
                width="100%",
            ),
            # Dialogs
            _refuse_dialog(),
            _add_patient_dialog(),
            _add_exam_type_dialog(),
            _psc_dialog(),
            _enterprise_dialog(),
            _edit_dialog(),
            # ── Confirm retrait patient ────────────────────────────────────────
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(
                        rx.hstack(rx.icon("trash-2", size=18, color="var(--red-9)"),
                                  rx.text("Retirer ce patient de la campagne ?"), spacing="2"),
                    ),
                    rx.dialog.description(
                        rx.vstack(
                            rx.text(
                                "Le patient « ",
                                rx.text.strong(CampaignDetailState.confirm_remove_patient_name),
                                " » sera retiré de cette campagne.",
                                size="2",
                            ),
                            rx.text("Ses résultats d'examens saisis ne seront pas supprimés.",
                                    size="2", color="var(--gray-9)"),
                            spacing="2",
                        ),
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Annuler", variant="soft", color_scheme="gray",
                                      on_click=CampaignDetailState.dismiss_confirm_remove_patient),
                        ),
                        rx.button("Retirer", color_scheme="red",
                                  on_click=CampaignDetailState.confirmed_remove_patient),
                        justify="end", spacing="2", margin_top="1rem", width="100%",
                    ),
                    max_width="440px",
                ),
                open=CampaignDetailState.confirm_remove_patient_open,
                on_open_change=lambda _: CampaignDetailState.dismiss_confirm_remove_patient(),
            ),
            # ── Confirm retrait type d'examen ───────────────────────────────────
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(
                        rx.hstack(rx.icon("trash-2", size=18, color="var(--red-9)"),
                                  rx.text("Retirer ce type d'examen ?"), spacing="2"),
                    ),
                    rx.dialog.description(
                        rx.text(
                            "L'examen « ",
                            rx.text.strong(CampaignDetailState.confirm_remove_exam_type_name),
                            " » sera retiré de cette campagne.",
                            size="2",
                        ),
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Annuler", variant="soft", color_scheme="gray",
                                      on_click=CampaignDetailState.dismiss_confirm_remove_exam_type),
                        ),
                        rx.button("Retirer", color_scheme="red",
                                  on_click=CampaignDetailState.confirmed_remove_exam_type),
                        justify="end", spacing="2", margin_top="1rem", width="100%",
                    ),
                    max_width="440px",
                ),
                open=CampaignDetailState.confirm_remove_exam_type_open,
                on_open_change=lambda _: CampaignDetailState.dismiss_confirm_remove_exam_type(),
            ),
        )
    )
