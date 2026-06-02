"""Campaign detail page — full workflow UI.

Dialogs have been extracted to campaign_detail_dialogs_component.py to keep
this file focused on layout, info card, workflow bar, patient and exam tables.
"""

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
from .campaign_detail_dialogs_component import campaign_detail_dialogs

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
            rx.text(CampaignDetailState.campaign.company_name, size="2", color="var(--gray-9)"),
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
        rx.table.cell(
            rx.link(
                f"{p.last_name} {p.first_name}",
                href="/patient/" + p.patient_id,
                style={"font_weight": "500", "color": "var(--accent-9)",
                       "_hover": {"text_decoration": "underline"}},
                size="2",
            )
        ),
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
        # ── Patients pagination ──────────────────────────────────────────
        rx.cond(
            CampaignDetailState.patients_total_count > CampaignDetailState.patients_page_size,
            rx.hstack(
                rx.text(
                    CampaignDetailState.patients_total_count.to(str)
                    + " patient(s) — page ",
                    CampaignDetailState.patients_page.to(str),
                    " / ",
                    CampaignDetailState.patients_total_pages.to(str),
                    size="2",
                    color="var(--gray-9)",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("chevron-left", size=14),
                    on_click=CampaignDetailState.patients_prev_page,
                    variant="soft",
                    size="2",
                    disabled=~CampaignDetailState.patients_has_prev,
                ),
                rx.button(
                    rx.icon("chevron-right", size=14),
                    on_click=CampaignDetailState.patients_next_page,
                    variant="soft",
                    size="2",
                    disabled=~CampaignDetailState.patients_has_next,
                ),
                width="100%",
                align="center",
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



# ── Dialogs — defined in campaign_detail_dialogs_component.py ─────────────


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
            # Dialogs (see campaign_detail_dialogs_component.py)
            campaign_detail_dialogs(),






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
