"""Campaign patient exam results entry page component.

Route: /campaign-patient/[cp_campaign_id]/[cp_patient_id]

Layout:
  ┌──────────────────────────────────────────────────────────┐
  │ ← Retour campagne     [Patient] [Campagne] [Statut badge]│
  ├──────────────────────────────────────────────────────────┤
  │  [1: Résultats] ─── [2: PSC] ─── [3: Validé] ─ [4: Fin]│  progress indicator
  ├────────────────────┬─────────────────────────────────────┤
  │ SECTIONS (left)    │ Form: paramètres actifs (right)     │
  │ ✓ NFS  [Labo]      │ Param  | Unité | Ref | Valeur       │
  │ ○ ECG  [Sur place] │ ...                                 │
  │ ○ Glycémie [Labo]  │         [Enregistrer NFS]           │
  ├────────────────────┴─────────────────────────────────────┤
  │         [Transmettre les résultats au médecin PSC]       │
  │         [Transmettre au médecin traitant] (optional)     │
  │         [Interprétation PSC]                             │
  │         [Interprétation Entreprise + Terminer]           │
  └──────────────────────────────────────────────────────────┘
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.nav_role_state import NavRoleState
from ..common.page_layout import page_layout
from .campaign_patient_exams_state import (
    AddParamOption,
    CampaignPatientExamsState,
    ExamParamEntry,
    ExamSectionVM,
    SectionFileVM,
)

# ── Progress indicator ────────────────────────────────────────────────────────


def _progress_step(label: str, is_done) -> rx.Component:
    """One circle + label in the step progress bar."""
    return rx.vstack(
        rx.cond(
            is_done,
            rx.box(
                rx.icon("check", size=12, color="white"),
                width="26px",
                height="26px",
                border_radius="50%",
                background="var(--green-9)",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),
            rx.box(
                width="26px",
                height="26px",
                border_radius="50%",
                background="var(--gray-3)",
                border="2px solid var(--gray-6)",
                flex_shrink="0",
            ),
        ),
        rx.text(
            label,
            size="1",
            color=rx.cond(is_done, "var(--green-11)", "var(--gray-9)"),
            text_align="center",
            weight=rx.cond(is_done, "medium", "regular"),
            style={"white_space": "nowrap"},
        ),
        align="center",
        spacing="1",
    )


def _progress_connector(is_done) -> rx.Component:
    """Horizontal line between two progress steps."""
    return rx.box(
        height="2px",
        flex="1",
        min_width="20px",
        background=rx.cond(is_done, "var(--green-9)", "var(--gray-4)"),
        margin_top="11px",
        align_self="start",
    )


def _progress_indicator() -> rx.Component:
    """Horizontal workflow progress bar (same terms as visit detail lifeline)."""
    s = CampaignPatientExamsState.medical_status

    # Visit Done = results being entered (at least one section saved)
    step_visit_done = CampaignPatientExamsState.has_saved_sections
    # Lab Done = all results transmitted to PSC doctor
    step_lab_done = (
        (s == "LAB_ENTERED")
        | (s == "PSC_INTERPRETED")
        | (s == "PSC_VALIDATED")
        | (s == "TRANSMITTED_TREATING_DOCTOR")
        | (s == "ENTERPRISE_VALIDATED")
        | (s == "PUBLISHED")
    )
    step_clinic = (
        (s == "PSC_VALIDATED")
        | (s == "TRANSMITTED_TREATING_DOCTOR")
        | (s == "ENTERPRISE_VALIDATED")
        | (s == "PUBLISHED")
    )
    step_company = (s == "ENTERPRISE_VALIDATED") | (s == "PUBLISHED")
    step_done = s == "PUBLISHED"

    return rx.card(
        rx.hstack(
            _progress_step("Pending", step_visit_done),
            _progress_connector(step_visit_done),
            _progress_step("Visit Done", step_lab_done),
            _progress_connector(step_lab_done),
            _progress_step("Lab Done", step_clinic),
            _progress_connector(step_clinic),
            _progress_step("Clinic Validated", step_company),
            _progress_connector(step_company),
            _progress_step("Company Validated", step_done),
            width="100%",
            align="start",
            spacing="0",
        ),
        width="100%",
        padding="0.75rem 1.5rem",
    )


# ── Horizontal exam tab bar ───────────────────────────────────────────────────


def _exam_tab(s: ExamSectionVM) -> rx.Component:
    """One horizontal tab button for an exam type."""
    is_active = CampaignPatientExamsState.active_section_id == s.exam_type_ref_id
    return rx.button(
        rx.hstack(
            rx.cond(
                s.is_transmitted,
                rx.icon("send", size=13, color="var(--teal-9)"),
                rx.cond(
                    s.is_saved,
                    rx.icon("circle-check", size=13, color="var(--green-9)"),
                    rx.icon("circle", size=13, color="var(--gray-6)"),
                ),
            ),
            rx.text(s.name, size="2", weight=rx.cond(is_active, "bold", "regular")),
            rx.cond(
                ~s.requires_lab_validation,
                rx.badge("Sur place", size="1", color_scheme="violet", variant="soft"),
                rx.fragment(),
            ),
            spacing="1",
            align="center",
        ),
        variant="ghost",
        radius="none",
        color_scheme=rx.cond(
            s.is_transmitted,
            "teal",
            rx.cond(s.is_saved, "green", rx.cond(is_active, "indigo", "gray")),
        ),
        on_click=CampaignPatientExamsState.set_active_section(s.exam_type_ref_id),
        padding="0.5rem 0.9rem",
        border_bottom=rx.cond(
            is_active,
            "2px solid var(--accent-9)",
            "2px solid transparent",
        ),
        border_radius="0",
        flex_shrink="0",
    )


def _exam_tabs() -> rx.Component:
    """Scrollable horizontal tab bar listing all exam types."""
    return rx.box(
        rx.hstack(
            rx.foreach(CampaignPatientExamsState.sections, _exam_tab),
            spacing="0",
            width="max-content",
        ),
        width="100%",
        overflow_x="auto",
        border_bottom="1px solid var(--gray-4)",
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
                style={
                    "max_width": "200px",
                    "overflow": "hidden",
                    "text_overflow": "ellipsis",
                    "white_space": "nowrap",
                },
            ),
            rx.text(
                f.name,
                size="2",
                style={
                    "max_width": "200px",
                    "overflow": "hidden",
                    "text_overflow": "ellipsis",
                    "white_space": "nowrap",
                },
            ),
        ),
        rx.text(f.size_label, size="1", color="var(--gray-9)", flex_shrink="0"),
        rx.spacer(),
        rx.icon_button(
            rx.icon("trash-2", size=13),
            variant="ghost",
            size="1",
            color_scheme="red",
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
                spacing="2",
                align="center",
            ),
            rx.cond(
                CampaignPatientExamsState.section_attached_files.length() > 0,
                rx.vstack(
                    rx.foreach(CampaignPatientExamsState.section_attached_files, _file_row),
                    width="100%",
                    spacing="0",
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
                            spacing="2",
                            align="center",
                        ),
                        rx.vstack(
                            rx.icon("upload", size=16, color="var(--gray-6)"),
                            rx.text(
                                "Glisser-déposer ou cliquer pour joindre",
                                size="1",
                                color="var(--gray-8)",
                            ),
                            rx.text(
                                "PDF · Images · Word · Excel",
                                size="1",
                                color="var(--gray-7)",
                            ),
                            align="center",
                            spacing="0",
                        ),
                    ),
                    align="center",
                    justify="center",
                    width="100%",
                    height="60px",
                ),
                id="campaign_exam_file_upload",
                multiple=True,
                accept={
                    "image/*": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"],
                    "application/pdf": [".pdf"],
                    "application/msword": [".doc"],
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
                        ".docx"
                    ],
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
    """One parameter row with a selection checkbox and an input field."""
    status_label = rx.match(
        p.value_status,
        ("normal", p.label_normal),
        ("low", p.label_low),
        ("high", p.label_high),
        ("critical_low", p.label_critical_low),
        ("critical_high", p.label_critical_high),
        "",
    )
    status_color = rx.match(
        p.value_status,
        ("critical_low", "red"),
        ("critical_high", "red"),
        ("low", "orange"),
        ("high", "orange"),
        ("normal", "green"),
        "gray",
    )
    status_variant = rx.match(
        p.value_status,
        ("critical_low", "solid"),
        ("critical_high", "solid"),
        "soft",
    )
    return rx.table.row(
        # Checkbox: deselected rows are greyed out and their value won't be saved
        rx.table.cell(
            rx.checkbox(
                checked=p.is_selected,
                on_change=lambda _: CampaignPatientExamsState.toggle_param_selection(p.param_id),
                size="2",
                disabled=p.is_required,
            ),
            width="36px",
        ),
        rx.table.cell(
            rx.hstack(
                rx.text(
                    p.name,
                    size="2",
                    weight="medium",
                    color=rx.cond(p.is_selected, "inherit", "var(--gray-7)"),
                ),
                rx.cond(
                    p.is_required,
                    rx.text("*", size="2", color="var(--gray-9)", weight="bold"),
                    rx.fragment(),
                ),
                spacing="1",
                align="center",
            )
        ),
        rx.table.cell(
            rx.cond(
                p.unit != "",
                rx.text(p.unit, size="2", color=rx.cond(p.is_selected, "inherit", "var(--gray-6)")),
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
                rx.text(p.critical_range, size="2", color="var(--gray-11)"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                p.is_computed,
                # Computed param: read-only with calculator icon
                rx.hstack(
                    rx.input(
                        value=p.value,
                        read_only=True,
                        width="120px",
                        size="2",
                        style={
                            "background": "var(--gray-2)",
                            "cursor": "not-allowed",
                            "color": "var(--gray-11)",
                        },
                    ),
                    rx.tooltip(
                        rx.icon("calculator", size=13, color="var(--accent-9)"),
                        content="Calculé automatiquement",
                    ),
                    spacing="1",
                    align="center",
                ),
                rx.cond(
                    p.is_selected,
                    rx.cond(
                        p.value_type == "NUMERIC",
                        rx.input(
                            placeholder="0.0",
                            type="number",
                            value=p.value,
                            on_change=CampaignPatientExamsState.set_param_value(p.param_id),
                            width="130px",
                            size="2",
                            read_only=CampaignPatientExamsState.active_section_is_readonly,
                            style=rx.cond(
                                CampaignPatientExamsState.active_section_is_readonly,
                                {"background": "var(--gray-2)", "cursor": "not-allowed"},
                                {"background": "transparent"},
                            ),
                        ),
                        rx.cond(
                            p.value_type == "BOOLEAN",
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="— choisir",
                                    size="2",
                                    width="160px",
                                ),
                                rx.select.content(
                                    rx.select.item("Négatif", value="Négatif"),
                                    rx.select.item("Positif", value="Positif"),
                                ),
                                value=p.value,
                                on_change=CampaignPatientExamsState.set_param_value(p.param_id),
                                size="2",
                                disabled=CampaignPatientExamsState.active_section_is_readonly,
                            ),
                            rx.input(
                                placeholder="Résultat…",
                                value=p.value,
                                on_change=CampaignPatientExamsState.set_param_value(p.param_id),
                                width="180px",
                                size="2",
                                read_only=CampaignPatientExamsState.active_section_is_readonly,
                                style=rx.cond(
                                    CampaignPatientExamsState.active_section_is_readonly,
                                    {"background": "var(--gray-2)", "cursor": "not-allowed"},
                                    {"background": "transparent"},
                                ),
                            ),
                        ),
                    ),
                    rx.text("— non saisi", size="1", color="var(--gray-6)", font_style="italic"),
                ),
            ),
        ),
        # Interprétation column: badge based on value status and parameter labels
        rx.table.cell(
            rx.cond(
                status_label != "",
                rx.badge(
                    status_label,
                    color_scheme=status_color,
                    variant=status_variant,
                    size="1",
                ),
                rx.fragment(),
            ),
            vertical_align="middle",
        ),
        align="center",
        opacity=rx.cond(p.is_selected, "1", "0.45"),
    )


def _param_form() -> rx.Component:
    """Right-side panel: param table + save button for the active section."""
    return rx.vstack(
        rx.hstack(
            rx.icon("file-text", size=16, color="var(--accent-9)"),
            rx.heading(CampaignPatientExamsState.active_section_name, size="4"),
            rx.spacer(),
            rx.cond(
                ~CampaignPatientExamsState.active_section_is_readonly,
                rx.button(
                    rx.icon("plus-circle", size=14),
                    "Ajouter un test",
                    on_click=CampaignPatientExamsState.open_add_param_dialog,
                    size="1",
                    variant="soft",
                    color_scheme="teal",
                ),
                rx.fragment(),
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        rx.cond(
            CampaignPatientExamsState.active_params.length() > 0,
            rx.vstack(
                rx.hstack(
                    rx.text("Sélection des paramètres :", size="2", color="var(--gray-9)"),
                    rx.button(
                        rx.icon("check-square", size=13),
                        "Tout sélectionner",
                        variant="ghost",
                        size="1",
                        color_scheme="blue",
                        on_click=CampaignPatientExamsState.select_all_params,
                    ),
                    rx.button(
                        rx.icon("square", size=13),
                        "Tout désélectionner",
                        variant="ghost",
                        size="1",
                        color_scheme="gray",
                        on_click=CampaignPatientExamsState.deselect_all_params,
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("", width="36px"),
                            rx.table.column_header_cell("Paramètre"),
                            rx.table.column_header_cell("Unité"),
                            rx.table.column_header_cell("Réf."),
                            rx.table.column_header_cell("Seuil critique"),
                            rx.table.column_header_cell("Résultat"),
                            rx.table.column_header_cell("Interprétation"),
                        )
                    ),
                    rx.table.body(rx.foreach(CampaignPatientExamsState.active_params, _param_row)),
                    width="100%",
                    variant="surface",
                    size="2",
                ),
                width="100%",
                spacing="2",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("circle-check", size=32, color="var(--gray-5)"),
                    rx.text(
                        "Cet examen n'a pas de paramètres définis.",
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.text(
                        "Enregistrez-le comme effectué avec le bouton ci-dessous.",
                        size="2",
                        color="var(--gray-9)",
                    ),
                    spacing="2",
                    align="center",
                ),
                padding="3rem",
                border="1px dashed var(--gray-5)",
                border_radius="12px",
                width="100%",
            ),
        ),
        rx.hstack(
            rx.spacer(),
            rx.cond(
                CampaignPatientExamsState.active_section_is_transmitted,
                # ── Transmitted: either read-only badge+Modifier, or editing mode ──
                rx.cond(
                    CampaignPatientExamsState.is_editing_section,
                    # Edit mode unlocked: show action dropdown + Valider (will require motif)
                    rx.vstack(
                        rx.hstack(
                            rx.badge(
                                rx.icon("pencil", size=12),
                                "Modification en cours",
                                color_scheme="orange",
                                variant="soft",
                                size="1",
                            ),
                            rx.text(
                                "Sélectionnez une action et cliquez Valider pour re-transmettre.",
                                size="1",
                                color="var(--gray-9)",
                                font_style="italic",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Choisir une action…",
                                    size="2",
                                    width="260px",
                                ),
                                rx.select.content(
                                    rx.select.item("Enregistrer sans transmettre", value="save"),
                                    rx.select.item("Transmettre au labo", value="labo"),
                                    rx.select.item("Transmettre au médecin PSC", value="psc"),
                                    rx.select.item(
                                        "Transmettre au médecin de travail", value="travail"
                                    ),
                                ),
                                value=CampaignPatientExamsState.section_action,
                                on_change=CampaignPatientExamsState.set_section_action,
                                size="2",
                            ),
                            rx.button(
                                rx.icon("check", size=14),
                                "Valider",
                                color_scheme="indigo",
                                size="2",
                                loading=CampaignPatientExamsState.is_saving,
                                disabled=~CampaignPatientExamsState.can_execute_section_action,
                                on_click=CampaignPatientExamsState.execute_section_action,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        spacing="1",
                        align="end",
                        width="100%",
                    ),
                    # Read-only: show transmission badge + Modifier button
                    rx.hstack(
                        rx.match(
                            CampaignPatientExamsState.active_section_transmission_target,
                            (
                                "LABO",
                                rx.badge(
                                    rx.icon("send", size=13),
                                    "Transmis au labo",
                                    color_scheme="orange",
                                    variant="soft",
                                    size="2",
                                ),
                            ),
                            (
                                "PSC",
                                rx.badge(
                                    rx.icon("send", size=13),
                                    "Transmis au médecin PSC",
                                    color_scheme="teal",
                                    variant="soft",
                                    size="2",
                                ),
                            ),
                            (
                                "TRAVAIL",
                                rx.badge(
                                    rx.icon("send", size=13),
                                    "Transmis au médecin de travail",
                                    color_scheme="blue",
                                    variant="soft",
                                    size="2",
                                ),
                            ),
                            rx.badge(
                                rx.icon("send", size=13),
                                "Transmis",
                                color_scheme="teal",
                                variant="soft",
                                size="2",
                            ),
                        ),
                        rx.button(
                            rx.icon("pencil", size=13),
                            "Modifier",
                            variant="ghost",
                            size="2",
                            color_scheme="gray",
                            on_click=CampaignPatientExamsState.enter_edit_mode,
                        ),
                        spacing="2",
                        align="center",
                    ),
                ),
                # ── Not transmitted: 4-action dropdown + Valider ──
                rx.vstack(
                    rx.hstack(
                        rx.select.root(
                            rx.select.trigger(
                                placeholder="Choisir une action…",
                                size="2",
                                width="260px",
                            ),
                            rx.select.content(
                                rx.select.item("Enregistrer sans transmettre", value="save"),
                                rx.select.item("Transmettre au labo", value="labo"),
                                rx.select.item("Transmettre au médecin PSC", value="psc"),
                                rx.select.item(
                                    "Transmettre au médecin de travail", value="travail"
                                ),
                            ),
                            value=CampaignPatientExamsState.section_action,
                            on_change=CampaignPatientExamsState.set_section_action,
                            size="2",
                        ),
                        rx.button(
                            rx.icon("check", size=14),
                            "Valider",
                            color_scheme="indigo",
                            size="2",
                            loading=CampaignPatientExamsState.is_saving,
                            disabled=~CampaignPatientExamsState.can_execute_section_action,
                            on_click=CampaignPatientExamsState.execute_section_action,
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.cond(
                        CampaignPatientExamsState.active_section_is_saved,
                        rx.hstack(
                            rx.badge(
                                rx.icon("circle-check", size=12),
                                "Enregistré",
                                color_scheme="green",
                                variant="soft",
                                size="1",
                            ),
                            rx.text(
                                "Résultats déjà enregistrés — choisissez une action pour transmettre.",
                                size="1",
                                color="var(--gray-9)",
                                font_style="italic",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.text(
                            "« Enregistrer sans transmettre » sauvegarde sans envoyer — "
                            "transmettez plus tard quand vous êtes prêt.",
                            size="1",
                            color="var(--gray-8)",
                            font_style="italic",
                        ),
                    ),
                    spacing="1",
                    align="end",
                    width="100%",
                ),
            ),
            width="100%",
            padding_top="0.25rem",
            spacing="2",
        ),
        _attachment_zone(),
        spacing="3",
        width="100%",
        flex="1",
    )


# ── Transmit panel (PSC) ──────────────────────────────────────────────────────


def _transmit_panel() -> rx.Component:
    """Global panel to transfer ALL validated exams to the PSC doctor."""
    all_tx = CampaignPatientExamsState.all_sections_transmitted
    s = CampaignPatientExamsState.medical_status
    lab_entered = s == "LAB_ENTERED"
    lab_validated = s == "LAB_VALIDATED"
    already_advanced = (
        (s == "LAB_VALIDATED")
        | (s == "PSC_INTERPRETED")
        | (s == "PSC_VALIDATED")
        | (s == "TRANSMITTED_TREATING_DOCTOR")
        | (s == "ENTERPRISE_VALIDATED")
        | (s == "PUBLISHED")
    )
    return rx.vstack(
        # ── Transfer to PSC card ──
        rx.card(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.icon("send", size=16, color="var(--teal-9)"),
                        rx.text(
                            "Transférer tous les résultats au médecin PSC", size="3", weight="bold"
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.cond(
                        CampaignPatientExamsState.all_sections_saved,
                        rx.text(
                            "Tous les examens sont enregistrés. Cliquez ci-contre pour transférer au médecin PSC.",
                            size="2",
                            color="var(--gray-9)",
                        ),
                        rx.text(
                            "Enregistrez tous les examens avant de transférer l'ensemble.",
                            size="2",
                            color="var(--orange-9)",
                        ),
                    ),
                    spacing="1",
                ),
                rx.spacer(),
                rx.cond(
                    all_tx,
                    rx.badge(
                        rx.icon("check", size=13),
                        "Transféré",
                        color_scheme="teal",
                        variant="soft",
                        size="2",
                    ),
                    rx.button(
                        rx.icon("send", size=14),
                        "Transférer au médecin PSC",
                        color_scheme="teal",
                        size="3",
                        loading=CampaignPatientExamsState.is_saving,
                        disabled=~CampaignPatientExamsState.all_sections_saved,
                        on_click=CampaignPatientExamsState.transmit_to_doctor,
                    ),
                ),
                align="center",
                spacing="4",
                width="100%",
            ),
            width="100%",
            background="var(--teal-2)",
        ),
        # ── Lab validation card (shown once transmitted, not yet validated) ──
        rx.cond(
            all_tx & ~already_advanced | lab_entered,
            rx.card(
                rx.hstack(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("flask-conical", size=16, color="var(--amber-9)"),
                            rx.text(
                                "Validation des résultats de laboratoire", size="3", weight="bold"
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.cond(
                            lab_validated,
                            rx.text("Résultats validés.", size="2", color="var(--green-10)"),
                            rx.text(
                                "Confirmez que les résultats de laboratoire sont corrects avant interprétation.",
                                size="2",
                                color="var(--gray-9)",
                            ),
                        ),
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.cond(
                        lab_validated,
                        rx.badge(
                            rx.icon("check", size=13),
                            "Validé labo",
                            color_scheme="amber",
                            variant="soft",
                            size="2",
                        ),
                        rx.hstack(
                            rx.button(
                                rx.icon("check-circle", size=14),
                                "Valider résultats labo",
                                color_scheme="amber",
                                size="2",
                                loading=CampaignPatientExamsState.is_saving,
                                on_click=CampaignPatientExamsState.validate_lab,
                            ),
                            rx.cond(
                                CampaignPatientExamsState.next_patient_id != "",
                                rx.button(
                                    rx.icon("check-circle", size=14),
                                    "Valider et suivant",
                                    color_scheme="amber",
                                    variant="soft",
                                    size="2",
                                    loading=CampaignPatientExamsState.is_saving,
                                    on_click=CampaignPatientExamsState.validate_lab_and_next,
                                ),
                                rx.fragment(),
                            ),
                            spacing="2",
                            align="center",
                        ),
                    ),
                    align="center",
                    spacing="4",
                    width="100%",
                ),
                width="100%",
                background="var(--amber-2)",
            ),
            rx.fragment(),
        ),
        width="100%",
        spacing="3",
    )


# ── Treating doctor panel (optional) ─────────────────────────────────────────


def _treating_doctor_panel() -> rx.Component:
    """Optional step: transmit results to the patient's treating doctor."""
    s = CampaignPatientExamsState.medical_status
    can_show = (
        (s == "PSC_VALIDATED")
        | (s == "TRANSMITTED_TREATING_DOCTOR")
        | (s == "ENTERPRISE_VALIDATED")
        | (s == "PUBLISHED")
    )
    already_sent = CampaignPatientExamsState.treating_doctor_transmitted
    return rx.cond(
        can_show,
        rx.card(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.icon("user-round", size=16, color="var(--teal-9)"),
                        rx.text("Médecin traitant", size="3", weight="bold"),
                        rx.badge("Optionnel", size="1", color_scheme="gray", variant="soft"),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "Transmettre les résultats au médecin traitant du patient.",
                        size="2",
                        color="var(--gray-9)",
                    ),
                    spacing="1",
                ),
                rx.spacer(),
                rx.cond(
                    already_sent,
                    rx.badge(
                        rx.icon("check", size=13),
                        "Transmis",
                        color_scheme="teal",
                        variant="soft",
                        size="2",
                    ),
                    rx.button(
                        rx.icon("send", size=14),
                        "Transmettre au médecin traitant",
                        color_scheme="teal",
                        variant="soft",
                        size="2",
                        loading=CampaignPatientExamsState.is_saving,
                        on_click=CampaignPatientExamsState.transmit_to_treating_doctor,
                    ),
                ),
                align="center",
                spacing="4",
                width="100%",
            ),
            width="100%",
            background="var(--teal-2)",
        ),
        rx.fragment(),
    )


# ── PSC interpretation panel ──────────────────────────────────────────────────


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
                        rx.badge(
                            rx.icon("check", size=13),
                            "Validé PSC",
                            color_scheme="blue",
                            variant="soft",
                            size="2",
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
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
                            "Transférer au médecin de travail",
                            color_scheme="blue",
                            size="2",
                            loading=CampaignPatientExamsState.is_saving,
                            on_click=CampaignPatientExamsState.validate_and_send_to_enterprise,
                        ),
                        rx.cond(
                            CampaignPatientExamsState.next_patient_id != "",
                            rx.button(
                                rx.icon("send", size=14),
                                "Valider et suivant",
                                color_scheme="blue",
                                variant="soft",
                                size="2",
                                loading=CampaignPatientExamsState.is_saving,
                                on_click=CampaignPatientExamsState.validate_psc_and_next,
                            ),
                            rx.fragment(),
                        ),
                        width="100%",
                        spacing="2",
                        align="center",
                    ),
                    rx.fragment(),
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            background="var(--blue-2)",
        ),
        rx.fragment(),
    )


# ── Enterprise interpretation panel ──────────────────────────────────────────


def _enterprise_interpretation_panel() -> rx.Component:
    """Panel for enterprise doctor to add interpretation and validate."""
    s = CampaignPatientExamsState.medical_status
    already_validated = s == "ENTERPRISE_VALIDATED"
    psc_done = (
        (s == "PSC_VALIDATED")
        | (s == "TRANSMITTED_TREATING_DOCTOR")
        | already_validated
        | (s == "PUBLISHED")
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
                        rx.badge(
                            rx.icon("check", size=13),
                            "Validé entreprise",
                            color_scheme="indigo",
                            variant="soft",
                            size="2",
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.cond(
                    ~psc_done,
                    rx.callout(
                        "En attente de la validation du médecin PSC.",
                        icon="clock",
                        color_scheme="gray",
                        size="2",
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
                        spacing="2",
                        width="100%",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            background="var(--indigo-2)",
        ),
        rx.fragment(),
    )


# ── Finish / close panel ──────────────────────────────────────────────────────


def _finish_panel() -> rx.Component:
    """Shown when enterprise validated — allows closing the dossier."""
    s = CampaignPatientExamsState.medical_status
    can_show = (s == "ENTERPRISE_VALIDATED") | (s == "PUBLISHED")
    already_done = s == "PUBLISHED"
    return rx.cond(
        can_show,
        rx.card(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.icon("archive", size=16, color="var(--green-9)"),
                        rx.text("Clôture du dossier", size="3", weight="bold"),
                        spacing="2",
                        align="center",
                    ),
                    rx.cond(
                        already_done,
                        rx.text(
                            "Dossier clôturé et publié.",
                            size="2",
                            color="var(--green-10)",
                        ),
                        rx.text(
                            "L'interprétation est validée. Clôturez le dossier pour le marquer comme terminé.",
                            size="2",
                            color="var(--gray-9)",
                        ),
                    ),
                    spacing="1",
                ),
                rx.spacer(),
                rx.cond(
                    already_done,
                    rx.badge(
                        rx.icon("check", size=13),
                        "Dossier clôturé",
                        color_scheme="green",
                        variant="soft",
                        size="2",
                    ),
                    rx.button(
                        rx.icon("check-circle", size=14),
                        "Terminer",
                        color_scheme="green",
                        size="3",
                        loading=CampaignPatientExamsState.is_saving,
                        on_click=CampaignPatientExamsState.finish_record,
                    ),
                ),
                align="center",
                spacing="4",
                width="100%",
            ),
            width="100%",
            background="var(--green-2)",
        ),
        rx.fragment(),
    )


# ── Motif (modification reason) dialog ───────────────────────────────────────


def _motif_dialog() -> rx.Component:
    """Dialog asking for a reason when the user modifies saved exam results."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Motif de modification"),
            rx.dialog.description(
                "Indiquez la raison pour laquelle vous modifiez les résultats déjà enregistrés.",
                size="2",
                color="var(--gray-9)",
            ),
            rx.vstack(
                rx.text_area(
                    placeholder="Ex. : erreur de saisie, valeur corrigée après analyse complémentaire…",
                    value=CampaignPatientExamsState.modification_motif,
                    on_change=CampaignPatientExamsState.set_modification_motif,
                    rows="3",
                    width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Annuler",
                            variant="ghost",
                            color_scheme="gray",
                            size="2",
                            on_click=CampaignPatientExamsState.close_motif_dialog,
                        ),
                    ),
                    rx.button(
                        rx.icon("check", size=14),
                        "Confirmer la modification",
                        color_scheme="indigo",
                        size="2",
                        disabled=CampaignPatientExamsState.modification_motif.strip() == "",
                        on_click=CampaignPatientExamsState.confirm_modification,
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                width="100%",
                margin_top="0.75rem",
            ),
            on_interact_outside=CampaignPatientExamsState.close_motif_dialog,
            on_escape_key_down=CampaignPatientExamsState.close_motif_dialog,
            max_width="500px",
        ),
        open=CampaignPatientExamsState.show_motif_dialog,
    )


# ── Main page ─────────────────────────────────────────────────────────────────


def _add_param_item(p: AddParamOption) -> rx.Component:
    return rx.hstack(
        rx.checkbox(
            checked=p.is_selected,
            on_change=lambda _: CampaignPatientExamsState.toggle_add_param_option(p.id),
            size="2",
        ),
        rx.text(p.name, size="2", weight=rx.cond(p.is_selected, "medium", "regular")),
        rx.cond(
            p.unit != "",
            rx.text(p.unit, size="1", color="var(--gray-9)"),
            rx.fragment(),
        ),
        spacing="2",
        align="center",
        padding="0.5rem 0.75rem",
        border_radius="var(--radius-2)",
        background=rx.cond(p.is_selected, "var(--accent-2)", "transparent"),
        border=rx.cond(p.is_selected, "1px solid var(--accent-6)", "1px solid var(--gray-4)"),
        width="100%",
        cursor="pointer",
        on_click=CampaignPatientExamsState.toggle_add_param_option(p.id),
        _hover={"background": rx.cond(p.is_selected, "var(--accent-3)", "var(--gray-2)")},
    )


def _add_param_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajouter des tests"),
            rx.dialog.description(
                "Sélectionnez les tests à ajouter à cet examen.",
                size="2",
                color="var(--gray-11)",
            ),
            rx.vstack(
                rx.cond(
                    CampaignPatientExamsState.add_param_error != "",
                    rx.callout(
                        CampaignPatientExamsState.add_param_error,
                        icon="info",
                        color_scheme="orange",
                        size="1",
                    ),
                    rx.cond(
                        CampaignPatientExamsState.add_param_options.length() > 0,
                        rx.vstack(
                            rx.hstack(
                                rx.text(
                                    CampaignPatientExamsState.add_param_selected_count.to(str),
                                    " / ",
                                    CampaignPatientExamsState.add_param_options.length().to(str),
                                    " sélectionné(s)",
                                    size="1",
                                    color="var(--gray-9)",
                                ),
                                width="100%",
                            ),
                            rx.vstack(
                                rx.foreach(
                                    CampaignPatientExamsState.add_param_options,
                                    _add_param_item,
                                ),
                                spacing="1",
                                width="100%",
                                max_height="280px",
                                overflow_y="auto",
                                padding="0.25rem",
                                border="1px solid var(--gray-4)",
                                border_radius="var(--radius-2)",
                                background="var(--gray-1)",
                            ),
                            width="100%",
                            spacing="2",
                        ),
                        rx.fragment(),
                    ),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Annuler",
                        variant="outline",
                        on_click=CampaignPatientExamsState.close_add_param_dialog,
                    ),
                    rx.button(
                        "Ajouter les tests",
                        on_click=CampaignPatientExamsState.save_add_params,
                        loading=CampaignPatientExamsState.is_saving_add_params,
                        disabled=(CampaignPatientExamsState.add_param_selected_count == 0)
                        | (CampaignPatientExamsState.add_param_error != ""),
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                padding_top="1rem",
            ),
            on_interact_outside=CampaignPatientExamsState.close_add_param_dialog,
            on_escape_key_down=CampaignPatientExamsState.close_add_param_dialog,
            max_width="500px",
        ),
        open=CampaignPatientExamsState.show_add_param_dialog,
    )


def campaign_patient_exams_page() -> rx.Component:
    return main_component(
        _motif_dialog(),
        _add_param_dialog(),
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
                    rx.cond(
                        CampaignPatientExamsState.visit_id != "",
                        rx.tooltip(
                            rx.button(
                                rx.icon("stethoscope", size=14),
                                "Interprétation médecin",
                                variant="soft",
                                color_scheme="blue",
                                size="2",
                                on_click=CampaignPatientExamsState.go_to_visit_detail,
                            ),
                            content="Aller à la page d'interprétation médecin",
                        ),
                        rx.fragment(),
                    ),
                    rx.spacer(),
                    rx.cond(
                        CampaignPatientExamsState.success != "",
                        rx.callout(
                            CampaignPatientExamsState.success,
                            icon="check",
                            color_scheme="green",
                            size="1",
                            on_click=CampaignPatientExamsState.dismiss_messages,
                            style={"cursor": "pointer"},
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    align="center",
                    spacing="2",
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
                            rx.heading(CampaignPatientExamsState.patient_name, size="5"),
                            rx.hstack(
                                rx.badge(
                                    CampaignPatientExamsState.patient_number,
                                    color_scheme="gray",
                                    variant="soft",
                                    size="1",
                                ),
                                rx.badge(
                                    rx.icon("heart-pulse", size=11),
                                    CampaignPatientExamsState.campaign_name,
                                    color_scheme="blue",
                                    variant="soft",
                                    size="1",
                                ),
                                spacing="2",
                            ),
                            spacing="1",
                        ),
                        rx.spacer(),
                        # Patient navigation controls
                        rx.cond(
                            CampaignPatientExamsState.patient_nav_label != "",
                            rx.hstack(
                                rx.cond(
                                    CampaignPatientExamsState.prev_patient_id != "",
                                    rx.tooltip(
                                        rx.link(
                                            rx.icon_button(
                                                rx.icon("chevron-left", size=16),
                                                variant="ghost",
                                                size="2",
                                                color_scheme="gray",
                                            ),
                                            href="/campaign-patient/" + CampaignPatientExamsState.cp_campaign_id + "/" + CampaignPatientExamsState.prev_patient_id,
                                        ),
                                        content="Patient précédent",
                                    ),
                                    rx.icon_button(
                                        rx.icon("chevron-left", size=16),
                                        variant="ghost",
                                        size="2",
                                        color_scheme="gray",
                                        disabled=True,
                                    ),
                                ),
                                rx.text(
                                    CampaignPatientExamsState.patient_nav_label,
                                    size="1",
                                    color="var(--gray-9)",
                                    style={"min_width": "40px", "text_align": "center"},
                                ),
                                rx.cond(
                                    CampaignPatientExamsState.next_patient_id != "",
                                    rx.tooltip(
                                        rx.link(
                                            rx.icon_button(
                                                rx.icon("chevron-right", size=16),
                                                variant="ghost",
                                                size="2",
                                                color_scheme="gray",
                                            ),
                                            href="/campaign-patient/" + CampaignPatientExamsState.cp_campaign_id + "/" + CampaignPatientExamsState.next_patient_id,
                                        ),
                                        content="Patient suivant",
                                    ),
                                    rx.icon_button(
                                        rx.icon("chevron-right", size=16),
                                        variant="ghost",
                                        size="2",
                                        color_scheme="gray",
                                        disabled=True,
                                    ),
                                ),
                                spacing="1",
                                align="center",
                            ),
                            rx.fragment(),
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                    ),
                    width="100%",
                ),
                # ── Progress indicator ────────────────────────────────────
                _progress_indicator(),
                # ── Error display (always visible, even when sections=0) ──
                rx.cond(
                    CampaignPatientExamsState.error != "",
                    rx.callout(
                        CampaignPatientExamsState.error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="2",
                        on_click=CampaignPatientExamsState.dismiss_messages,
                        style={"cursor": "pointer"},
                        width="100%",
                    ),
                ),
                # ── Loading / content ─────────────────────────────────────
                rx.cond(
                    CampaignPatientExamsState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="4rem"),
                    rx.cond(
                        CampaignPatientExamsState.sections.length() > 0,
                        rx.vstack(
                            # ── Motif / terrain notes ─────────────────────
                            rx.card(
                                rx.vstack(
                                    rx.hstack(
                                        rx.icon("notebook-pen", size=15, color="var(--accent-9)"),
                                        rx.text(
                                            "Motif / Observations terrain",
                                            size="2",
                                            weight="bold",
                                        ),
                                        rx.cond(
                                            CampaignPatientExamsState.is_saving_notes,
                                            rx.spinner(size="1"),
                                            rx.fragment(),
                                        ),
                                        spacing="2",
                                        align="center",
                                    ),
                                    rx.text_area(
                                        placeholder="Motif de consultation, antécédents, observations à la visite…",
                                        value=CampaignPatientExamsState.terrain_notes,
                                        on_change=CampaignPatientExamsState.set_terrain_notes,
                                        on_blur=CampaignPatientExamsState.save_terrain_notes,
                                        rows="2",
                                        width="100%",
                                    ),
                                    spacing="2",
                                    width="100%",
                                ),
                                width="100%",
                                padding="0.75rem 1rem",
                            ),
                            # ── Horizontal tab bar ─────────────────────────
                            rx.cond(
                                ~CampaignPatientExamsState.patient_is_on_terrain,
                                rx.callout(
                                    "Déclarez d'abord la présence (ou l'absence) du patient pour débloquer la saisie des résultats.",
                                    icon="lock",
                                    color_scheme="orange",
                                    size="2",
                                    width="100%",
                                ),
                                rx.fragment(),
                            ),
                            rx.box(
                                rx.vstack(
                                    _exam_tabs(),
                                    _param_form(),
                                    spacing="3",
                                    width="100%",
                                ),
                                pointer_events=rx.cond(
                                    CampaignPatientExamsState.patient_is_on_terrain, "auto", "none"
                                ),
                                opacity=rx.cond(
                                    CampaignPatientExamsState.patient_is_on_terrain, "1", "0.4"
                                ),
                                width="100%",
                            ),
                            # ── Transfer to PSC panel ──────────────────────
                            _transmit_panel(),
                            # ── Treating doctor (optional) ─────────────────
                            _treating_doctor_panel(),
                            # ── PSC interpretation ─────────────────────────
                            rx.cond(
                                NavRoleState.can_see_interpretation,
                                _psc_interpretation_panel(),
                                rx.fragment(),
                            ),
                            # ── Enterprise interpretation ──────────────────
                            rx.cond(
                                NavRoleState.can_see_interpretation,
                                _enterprise_interpretation_panel(),
                                rx.fragment(),
                            ),
                            # ── Close record ───────────────────────────────
                            rx.cond(
                                NavRoleState.can_see_interpretation,
                                _finish_panel(),
                                rx.fragment(),
                            ),
                            spacing="4",
                            width="100%",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("file", size=36, color="var(--gray-5)"),
                                rx.text(
                                    "Aucun type d'examen configuré pour cette campagne.",
                                    size="2",
                                    color="var(--gray-9)",
                                ),
                                rx.text(
                                    "Allez dans l'onglet « Examens » de la campagne pour en ajouter.",
                                    size="2",
                                    color="var(--gray-9)",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            padding="4rem",
                        ),
                    ),
                ),
                spacing="4",
                width="100%",
            )
        ),
    )
