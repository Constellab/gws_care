"""Campaign patient exam results entry page component.

Route: /campaign-patient/[cp_campaign_id]/[cp_patient_id]

Layout:
  ┌──────────────────────────────────────────────────────────┐
  │ ← Retour campagne     [Patient] [Campagne] [Statut badge]│
  ├────────────────────┬─────────────────────────────────────┤
  │ SECTIONS (left)    │ Form: paramètres actifs (right)     │
  │ ✓ NFS              │ Param  | Unité | Ref | Valeur       │
  │ ○ ECG              │ ...                                 │
  │ ○ Glycémie         │         [Enregistrer NFS]           │
  ├────────────────────┴─────────────────────────────────────┤
  │            [Transmettre les résultats au médecin PSC]    │
  └──────────────────────────────────────────────────────────┘
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .campaign_patient_exams_state import (
    CampaignPatientExamsState,
    ExamParamEntry,
    ExamSectionVM,
    SectionFileVM,
)


# ── Section sidebar ───────────────────────────────────────────────────────────

def _section_button(s: ExamSectionVM) -> rx.Component:
    """One button in the left section list."""
    is_active = CampaignPatientExamsState.active_section_id == s.exam_type_ref_id
    return rx.button(
        rx.hstack(
            rx.cond(
                s.is_saved,
                rx.icon("circle-check", size=14, color="var(--green-9)"),
                rx.icon("circle", size=14, color="var(--gray-7)"),
            ),
            rx.vstack(
                rx.text(s.name, size="2", weight="medium"),
                rx.text(
                    s.category_label + " · " + s.param_count.to(str) + " param.",
                    size="1", color="var(--gray-9)",
                ),
                spacing="0",
                align_items="start",
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=rx.cond(s.is_saved, "green", rx.cond(is_active, "indigo", "gray")),
        width="100%",
        justify="start",
        on_click=CampaignPatientExamsState.set_active_section(s.exam_type_ref_id),
        style={"text_align": "left"},
    )


# ── Attachment zone ───────────────────────────────────────────────────────────

def _file_row(f: SectionFileVM) -> rx.Component:
    is_image = f.mime_type.startswith("image/")
    icon_name = rx.cond(is_image, "image", "file-text")
    return rx.hstack(
        rx.icon(icon_name, size=15, color="var(--accent-9)", flex_shrink="0"),
        rx.cond(
            f.download_url != "",
            rx.link(
                f.name,
                href=f.download_url,
                is_external=True,
                size="2",
                style={"max_width": "200px", "overflow": "hidden",
                       "text_overflow": "ellipsis", "white_space": "nowrap"},
            ),
            rx.text(f.name, size="2",
                    style={"max_width": "200px", "overflow": "hidden",
                           "text_overflow": "ellipsis", "white_space": "nowrap"}),
        ),
        rx.text(f.size_label, size="1", color="var(--gray-9)", flex_shrink="0"),
        rx.spacer(),
        rx.icon_button(
            rx.icon("trash-2", size=13),
            variant="ghost", size="1", color_scheme="red",
            on_click=CampaignPatientExamsState.delete_section_file(f.file_id),
        ),
        width="100%",
        align="center",
        spacing="2",
        padding="0.35rem 0.5rem",
        border_radius="6px",
        _hover={"background": "var(--gray-2)"},
    )


def _attachment_zone() -> rx.Component:
    """Upload zone shown when the active section is saved and allows attachments."""
    return rx.cond(
        CampaignPatientExamsState.active_section_is_saved,
        rx.vstack(
            rx.separator(width="100%"),
            rx.hstack(
                rx.icon("paperclip", size=14, color="var(--gray-9)"),
                rx.text("Documents joints", size="2", weight="medium", color="var(--gray-11)"),
                spacing="2", align="center",
            ),
            rx.cond(
                CampaignPatientExamsState.section_attached_files.length() > 0,
                rx.vstack(
                    rx.foreach(CampaignPatientExamsState.section_attached_files, _file_row),
                    width="100%", spacing="0",
                ),
                rx.text("Aucun document joint.", size="1", color="var(--gray-8)"),
            ),
            rx.upload(
                rx.vstack(
                    rx.cond(
                        CampaignPatientExamsState.is_uploading_file,
                        rx.hstack(
                            rx.spinner(size="2"),
                            rx.text("Envoi en cours…", size="2", color="var(--gray-9)"),
                            spacing="2", align="center",
                        ),
                        rx.vstack(
                            rx.icon("upload", size=16, color="var(--gray-6)"),
                            rx.text(
                                "Glisser-déposer ou cliquer pour joindre",
                                size="1", color="var(--gray-8)",
                            ),
                            rx.text(
                                "PDF · Images · Word · Excel",
                                size="1", color="var(--gray-7)",
                            ),
                            align="center", spacing="0",
                        ),
                    ),
                    align="center", justify="center",
                    width="100%", height="60px",
                ),
                id="campaign_exam_file_upload",
                multiple=True,
                accept={
                    "image/*": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"],
                    "application/pdf": [".pdf"],
                    "application/msword": [".doc"],
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
                    "application/vnd.ms-excel": [".xls"],
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                    "text/plain": [".txt"],
                },
                on_drop=CampaignPatientExamsState.handle_section_file_upload(
                    rx.upload_files(upload_id="campaign_exam_file_upload")
                ),
                border="2px dashed var(--gray-5)",
                border_radius="8px",
                padding="0.5rem",
                width="100%",
                cursor="pointer",
                _hover={"border_color": "var(--accent-7)", "background": "var(--gray-1)"},
            ),
            width="100%",
            spacing="2",
            padding_top="0.5rem",
        ),
        rx.fragment(),
    )


# ── Parameter table ───────────────────────────────────────────────────────────

def _param_row(p: ExamParamEntry) -> rx.Component:
    """One parameter row with an input field."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.text(p.name, size="2", weight="medium"),
                rx.cond(
                    p.is_required,
                    rx.badge("*", color_scheme="red", size="1", variant="surface"),
                    rx.fragment(),
                ),
                spacing="1", align="center",
            )
        ),
        rx.table.cell(
            rx.cond(
                p.unit != "",
                rx.text(p.unit, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                p.ref_range != "",
                rx.text(p.ref_range, size="2", color="var(--gray-11)"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                p.critical_range != "",
                rx.badge(p.critical_range, color_scheme="red", size="1", variant="soft"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                p.value_type == "NUMERIC",
                rx.input(
                    placeholder="0.0",
                    type="number",
                    value=p.value,
                    on_change=CampaignPatientExamsState.set_param_value(p.param_id),
                    width="130px",
                    size="2",
                    color_scheme=rx.cond(
                        (p.value_status == "critical_low") | (p.value_status == "critical_high"),
                        "red",
                        rx.cond(
                            (p.value_status == "low") | (p.value_status == "high"),
                            "orange",
                            rx.cond(p.value_status == "normal", "green", "gray"),
                        ),
                    ),
                ),
                rx.cond(
                    p.value_type == "BOOLEAN",
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="— choisir",
                            size="2",
                            width="160px",
                            color_scheme=rx.cond(
                                p.value == "Positif", "red",
                                rx.cond(p.value == "Négatif", "green", "gray"),
                            ),
                        ),
                        rx.select.content(
                            rx.select.item("Négatif", value="Négatif"),
                            rx.select.item("Positif", value="Positif"),
                        ),
                        value=p.value,
                        on_change=CampaignPatientExamsState.set_param_value(p.param_id),
                        size="2",
                    ),
                    rx.input(
                        placeholder="Résultat…",
                        value=p.value,
                        on_change=CampaignPatientExamsState.set_param_value(p.param_id),
                        width="180px",
                        size="2",
                    ),
                ),
            )
        ),
        align="center",
    )


def _param_form() -> rx.Component:
    """Right-side panel: param table + save button for the active section."""
    return rx.vstack(
        # Section title
        rx.hstack(
            rx.icon("file-text", size=16, color="var(--accent-9)"),
            rx.heading(CampaignPatientExamsState.active_section_name, size="4"),
            spacing="2", align="center",
        ),
        # Params table or empty state
        rx.cond(
            CampaignPatientExamsState.active_params.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Paramètre"),
                        rx.table.column_header_cell("Unité"),
                        rx.table.column_header_cell("Réf."),
                        rx.table.column_header_cell("Seuil critique"),
                        rx.table.column_header_cell("Résultat"),
                    )
                ),
                rx.table.body(
                    rx.foreach(CampaignPatientExamsState.active_params, _param_row)
                ),
                width="100%",
                variant="surface",
                size="2",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("circle-check", size=32, color="var(--gray-5)"),
                    rx.text(
                        "Cet examen n'a pas de paramètres définis.",
                        size="2", color="var(--gray-9)",
                    ),
                    rx.text(
                        "Enregistrez-le comme effectué avec le bouton ci-dessous.",
                        size="2", color="var(--gray-9)",
                    ),
                    spacing="2", align="center",
                ),
                padding="3rem",
                border="1px dashed var(--gray-5)",
                border_radius="12px",
                width="100%",
            ),
        ),
        # Error
        rx.cond(
            CampaignPatientExamsState.error != "",
            rx.callout(
                CampaignPatientExamsState.error,
                icon="info", color_scheme="red", size="2",
                on_click=CampaignPatientExamsState.dismiss_messages,
                style={"cursor": "pointer"},
            ),
        ),
        # Save + per-section transmit buttons
        rx.hstack(
            rx.spacer(),
            rx.button(
                rx.icon("save", size=14),
                "Enregistrer ces résultats",
                variant="soft",
                size="2",
                loading=CampaignPatientExamsState.is_saving,
                on_click=CampaignPatientExamsState.save_active_section,
            ),
            rx.cond(
                CampaignPatientExamsState.active_section_is_saved,
                rx.button(
                    rx.icon("send", size=14),
                    "Transmettre cet examen",
                    color_scheme="teal",
                    variant="soft",
                    size="2",
                    loading=CampaignPatientExamsState.is_saving,
                    on_click=CampaignPatientExamsState.transmit_section(
                        CampaignPatientExamsState.active_section_id
                    ),
                ),
                rx.fragment(),
            ),
            width="100%",
            padding_top="0.25rem",
            spacing="2",
        ),
        # Attachment zone (shown once section is saved)
        _attachment_zone(),
        spacing="3",
        width="100%",
        flex="1",
    )


# ── Transmit panel ────────────────────────────────────────────────────────────

def _transmit_panel() -> rx.Component:
    already_sent = CampaignPatientExamsState.medical_status != "PENDING"
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("send", size=16, color="var(--teal-9)"),
                    rx.text("Transmission au médecin PSC", size="3", weight="bold"),
                    spacing="2", align="center",
                ),
                rx.cond(
                    CampaignPatientExamsState.has_saved_sections,
                    rx.text(
                        "Résultats enregistrés. Cliquez ci-contre pour transmettre au médecin PSC.",
                        size="2", color="var(--gray-9)",
                    ),
                    rx.text(
                        "Enregistrez d'abord au moins une section de résultats avant de transmettre.",
                        size="2", color="var(--orange-9)",
                    ),
                ),
                spacing="1",
            ),
            rx.spacer(),
            rx.cond(
                already_sent,
                rx.badge(
                    rx.icon("check", size=13),
                    "Déjà transmis",
                    color_scheme="green",
                    variant="soft",
                    size="2",
                ),
                rx.button(
                    rx.icon("send", size=14),
                    "Transmettre au médecin PSC",
                    color_scheme="teal",
                    size="3",
                    loading=CampaignPatientExamsState.is_saving,
                    disabled=~CampaignPatientExamsState.has_saved_sections,
                    on_click=CampaignPatientExamsState.transmit_to_doctor,
                ),
            ),
            align="center",
            spacing="4",
            width="100%",
        ),
        width="100%",
        background="var(--teal-2)",
    )


def _psc_interpretation_panel() -> rx.Component:
    """Panel for PSC doctor to add interpretation and send to enterprise doctor."""
    already_validated = CampaignPatientExamsState.medical_status == "PSC_VALIDATED"
    lab_done = CampaignPatientExamsState.medical_status == "LAB_ENTERED"
    can_show = lab_done | already_validated
    return rx.cond(
        CampaignPatientExamsState.viewer_is_psc & can_show,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("stethoscope", size=16, color="var(--blue-9)"),
                    rx.text("Interprétation Médecin PSC", size="3", weight="bold"),
                    rx.spacer(),
                    rx.cond(
                        already_validated,
                        rx.badge(rx.icon("check", size=13), "Validé PSC",
                                 color_scheme="blue", variant="soft", size="2"),
                        rx.fragment(),
                    ),
                    spacing="2", align="center", width="100%",
                ),
                rx.text_area(
                    value=CampaignPatientExamsState.psc_notes,
                    on_change=CampaignPatientExamsState.set_psc_notes,
                    placeholder="Saisir votre interprétation médicale ici...",
                    rows="5",
                    width="100%",
                    read_only=already_validated,
                ),
                rx.cond(
                    ~already_validated,
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            rx.icon("send", size=14),
                            "Valider et transmettre au médecin entreprise",
                            color_scheme="blue",
                            size="2",
                            loading=CampaignPatientExamsState.is_saving,
                            on_click=CampaignPatientExamsState.validate_and_send_to_enterprise,
                        ),
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="3", width="100%",
            ),
            width="100%",
            background="var(--blue-2)",
        ),
        rx.fragment(),
    )


def _enterprise_interpretation_panel() -> rx.Component:
    """Panel for enterprise doctor to add interpretation."""
    already_validated = CampaignPatientExamsState.medical_status == "ENTERPRISE_VALIDATED"
    psc_done = (
        (CampaignPatientExamsState.medical_status == "PSC_VALIDATED")
        | (CampaignPatientExamsState.medical_status == "ENTERPRISE_INTERPRETED")
        | already_validated
    )
    return rx.cond(
        CampaignPatientExamsState.viewer_is_enterprise,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("building-2", size=16, color="var(--indigo-9)"),
                    rx.text("Interprétation Médecin Entreprise", size="3", weight="bold"),
                    rx.spacer(),
                    rx.cond(
                        already_validated,
                        rx.badge(rx.icon("check", size=13), "Validé entreprise",
                                 color_scheme="indigo", variant="soft", size="2"),
                        rx.fragment(),
                    ),
                    spacing="2", align="center", width="100%",
                ),
                rx.cond(
                    ~psc_done,
                    rx.callout(
                        "En attente de la validation du médecin PSC.",
                        icon="clock", color_scheme="gray", size="2",
                    ),
                    rx.vstack(
                        rx.text_area(
                            value=CampaignPatientExamsState.enterprise_notes,
                            on_change=CampaignPatientExamsState.set_enterprise_notes,
                            placeholder="Interprétation / commentaires pour l'entreprise...",
                            rows="5",
                            width="100%",
                            read_only=already_validated,
                        ),
                        rx.cond(
                            ~already_validated,
                            rx.hstack(
                                rx.spacer(),
                                rx.button(
                                    rx.icon("check", size=14),
                                    "Valider l'interprétation",
                                    color_scheme="indigo",
                                    size="2",
                                    loading=CampaignPatientExamsState.is_saving,
                                    on_click=CampaignPatientExamsState.validate_enterprise,
                                ),
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2", width="100%",
                    ),
                ),
                spacing="3", width="100%",
            ),
            width="100%",
            background="var(--indigo-2)",
        ),
        rx.fragment(),
    )


# ── Main page ─────────────────────────────────────────────────────────────────

def campaign_patient_exams_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                # ── Header ────────────────────────────────────────────────
                rx.hstack(
                    rx.button(
                        rx.icon("chevron-left", size=14),
                        "Retour à la campagne",
                        variant="ghost",
                        size="2",
                        on_click=CampaignPatientExamsState.go_back,
                    ),
                    rx.spacer(),
                    rx.cond(
                        CampaignPatientExamsState.success != "",
                        rx.callout(
                            CampaignPatientExamsState.success,
                            icon="check", color_scheme="green", size="1",
                            on_click=CampaignPatientExamsState.dismiss_messages,
                            style={"cursor": "pointer"},
                        ),
                        rx.fragment(),
                    ),
                    width="100%", align="center",
                ),

                # ── Patient card ──────────────────────────────────────────
                rx.card(
                    rx.hstack(
                        rx.box(
                            rx.icon("user", size=22, color="var(--accent-9)"),
                            padding="0.5rem",
                            border_radius="8px",
                            background="var(--accent-3)",
                        ),
                        rx.vstack(
                            rx.heading(
                                CampaignPatientExamsState.patient_name, size="5"
                            ),
                            rx.hstack(
                                rx.badge(
                                    CampaignPatientExamsState.patient_number,
                                    color_scheme="gray", variant="soft", size="1",
                                ),
                                rx.badge(
                                    rx.icon("heart-pulse", size=11),
                                    CampaignPatientExamsState.campaign_name,
                                    color_scheme="blue", variant="soft", size="1",
                                ),
                                spacing="2",
                            ),
                            spacing="1",
                        ),
                        spacing="3", align="center", width="100%",
                    ),
                    width="100%",
                ),

                # ── Loading / content ─────────────────────────────────────
                rx.cond(
                    CampaignPatientExamsState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="4rem"),
                    rx.cond(
                        CampaignPatientExamsState.sections.length() > 0,
                        rx.vstack(
                            # Two-column layout
                            rx.hstack(
                                # Left: section list
                                rx.vstack(
                                    rx.text(
                                        "Examens de la campagne",
                                        size="2", weight="medium",
                                        color="var(--gray-9)",
                                    ),
                                    rx.separator(width="100%"),
                                    rx.foreach(
                                        CampaignPatientExamsState.sections,
                                        _section_button,
                                    ),
                                    spacing="2",
                                    width="220px",
                                    flex_shrink="0",
                                    padding="1rem",
                                    background="var(--gray-2)",
                                    border_radius="12px",
                                    align_items="start",
                                ),
                                # Right: param form
                                _param_form(),
                                spacing="4",
                                align_items="start",
                                width="100%",
                            ),
                            # Transmit panel
                            _transmit_panel(),
                            # PSC interpretation
                            _psc_interpretation_panel(),
                            # Enterprise interpretation
                            _enterprise_interpretation_panel(),
                            spacing="4",
                            width="100%",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("file", size=36, color="var(--gray-5)"),
                                rx.text(
                                    "Aucun type d'examen configuré pour cette campagne.",
                                    size="2", color="var(--gray-9)",
                                ),
                                rx.text(
                                    "Allez dans le référentiel examens pour en ajouter.",
                                    size="2", color="var(--gray-9)",
                                ),
                                spacing="2", align="center",
                            ),
                            padding="4rem",
                        ),
                    ),
                ),
                spacing="4",
                width="100%",
            )
        )
    )
