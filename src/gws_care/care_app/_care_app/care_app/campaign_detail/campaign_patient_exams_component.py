"""Campaign patient exam results entry page component.

Route: /campaign-patient/[cp_campaign_id]/[cp_patient_id]

Layout:
  ┌──────────────────────────────────────────────────────────┐
  │ ← Retour campagne     [Patient] [Campagne] [Statut badge]│
  ├──────────────────────────────────────────────────────────┤
  │  [1: Résultats] ─ [2: Interne] ─ [3: Validé] ─ [4: Fin]│  progress indicator
  ├────────────────────┬─────────────────────────────────────┤
  │ SECTIONS (left)    │ Form: paramètres actifs (right)     │
  │ ✓ NFS  [Labo]      │ Param  | Unité | Ref | Valeur       │
  │ ○ ECG  [Sur place] │ ...                                 │
  │ ○ Glycémie [Labo]  │         [Enregistrer NFS]           │
  ├────────────────────┴─────────────────────────────────────┤
  │    [Transmettre les résultats au médecin interne]        │
  │         [Transmettre au médecin traitant] (optional)     │
  │         [Interprétation interne]                         │
  │         [Interprétation Entreprise + Terminer]           │
  └──────────────────────────────────────────────────────────┘
"""

import reflex as rx
from gws_reflex_main import main_component

from ..admin.general_settings_state import GeneralSettingsState
from ..common.language_state import LanguageState
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
    # Lab Done = all results transmitted to internal doctor
    step_lab_done = (
        (s == "LAB_ENTERED")
        | (s == "LAB_VALIDATED")
        | (s == "INTERNAL_INTERPRETED")
        | (s == "INTERNAL_VALIDATED")
        | (s == "TRANSMITTED_TREATING_DOCTOR")
        | (s == "ENTERPRISE_VALIDATED")
        | (s == "PUBLISHED")
    )
    step_clinic = (
        (s == "INTERNAL_VALIDATED")
        | (s == "TRANSMITTED_TREATING_DOCTOR")
        | (s == "ENTERPRISE_VALIDATED")
        | (s == "PUBLISHED")
    )
    step_company = (s == "ENTERPRISE_VALIDATED") | (s == "PUBLISHED")
    step_done = s == "PUBLISHED"

    return rx.card(
        rx.hstack(
            _progress_step(LanguageState.tr["step_pending"], step_visit_done),
            _progress_connector(step_visit_done),
            _progress_step(LanguageState.tr["step_visit_done"], step_lab_done),
            _progress_connector(step_lab_done),
            _progress_step(GeneralSettingsState.step_transmitted_label, step_clinic),
            _progress_connector(step_clinic),
            _progress_step(GeneralSettingsState.step_org_validated_label, step_company),
            _progress_connector(step_company),
            _progress_step(LanguageState.tr["step_company_validated"], step_done),
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
                rx.badge(LanguageState.tr["on_site_badge"], size="1", color_scheme="violet", variant="soft"),
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
                rx.text(LanguageState.tr["attached_documents_label"], size="2", weight="medium", color="var(--gray-11)"),
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
                rx.text(LanguageState.tr["no_attached_documents"], size="1", color="var(--gray-8)"),
            ),
            rx.upload(
                rx.vstack(
                    rx.cond(
                        CampaignPatientExamsState.is_uploading_file,
                        rx.hstack(
                            rx.spinner(size="2"),
                            rx.text(LanguageState.tr["upload_in_progress"], size="2", color="var(--gray-9)"),
                            spacing="2",
                            align="center",
                        ),
                        rx.vstack(
                            rx.icon("upload", size=16, color="var(--gray-6)"),
                            rx.text(
                                LanguageState.tr["drop_files_hint"],
                                size="1",
                                color="var(--gray-8)",
                            ),
                            rx.text(
                                LanguageState.tr["accepted_file_formats"],
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
        ("normal", rx.cond(p.label_normal != "", p.label_normal, "Normal")),
        ("low", rx.cond(p.label_low != "", p.label_low, "Bas")),
        ("high", rx.cond(p.label_high != "", p.label_high, "Élevé")),
        ("critical_low", rx.cond(p.label_critical_low != "", p.label_critical_low, "Critique bas")),
        ("critical_high", rx.cond(p.label_critical_high != "", p.label_critical_high, "Critique haut")),
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
                        content=LanguageState.tr["hint_calc_automatically"],
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
                                    rx.select.item(LanguageState.tr["option_negative"], value="Négatif"),
                                    rx.select.item(LanguageState.tr["option_positive"], value="Positif"),
                                ),
                                value=p.value,
                                on_change=CampaignPatientExamsState.set_param_value(p.param_id),
                                size="2",
                                disabled=CampaignPatientExamsState.active_section_is_readonly,
                            ),
                            rx.input(
                                placeholder="Result…",
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
                    LanguageState.tr["btn_add_test"],
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
                    rx.text(LanguageState.tr["parameter_selection_label"], size="2", color="var(--gray-9)"),
                    rx.button(
                        rx.icon("check-square", size=13),
                        LanguageState.tr["btn_select_all"],
                        variant="ghost",
                        size="1",
                        color_scheme="blue",
                        on_click=CampaignPatientExamsState.select_all_params,
                    ),
                    rx.button(
                        rx.icon("square", size=13),
                        LanguageState.tr["btn_deselect_all"],
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
                            rx.table.column_header_cell(LanguageState.tr["col_parameter"]),
                            rx.table.column_header_cell(LanguageState.tr["col_unit"]),
                            rx.table.column_header_cell(LanguageState.tr["col_ref"]),
                            rx.table.column_header_cell(LanguageState.tr["col_critical_threshold"]),
                            rx.table.column_header_cell(LanguageState.tr["col_result"]),
                            rx.table.column_header_cell(LanguageState.tr["col_interpretation"]),
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
                        LanguageState.tr["hint_no_params"],
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.text(
                        LanguageState.tr["hint_no_params_action"],
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
                CampaignPatientExamsState.active_section_is_saved,
                # ── Saved: either read-only badge+Modifier, or editing mode ──
                rx.cond(
                    CampaignPatientExamsState.is_editing_section,
                    # Edit mode unlocked: show Valider (will require motif)
                    rx.vstack(
                        rx.hstack(
                            rx.badge(
                                rx.icon("pencil", size=12),
                                LanguageState.tr["badge_modification_in_progress"],
                                color_scheme="orange",
                                variant="soft",
                                size="1",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            rx.button(
                                rx.icon("check", size=14),
                                LanguageState.tr["btn_validate"],
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
                    # Read-only: show saved badge + Modifier button (only while the
                    # internal doctor hasn't validated an interpretation based on
                    # these results yet — see internal_validated).
                    rx.hstack(
                        rx.badge(
                            rx.icon("circle-check", size=13),
                            LanguageState.tr["badge_saved"],
                            color_scheme="green",
                            variant="soft",
                            size="2",
                        ),
                        rx.cond(
                            ~CampaignPatientExamsState.internal_validated,
                            rx.button(
                                rx.icon("pencil", size=13),
                                LanguageState.tr["btn_edit"],
                                variant="ghost",
                                size="2",
                                color_scheme="gray",
                                on_click=CampaignPatientExamsState.enter_edit_mode,
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        align="center",
                    ),
                ),
                # ── Not saved yet: choose an action, then Valider ──
                rx.vstack(
                    rx.hstack(
                        rx.select.root(
                            rx.select.trigger(
                                placeholder=LanguageState.tr["choose_action_placeholder"],
                                size="2",
                                width="260px",
                            ),
                            rx.select.content(
                                rx.select.item(LanguageState.tr["btn_save_without_sending"], value="save"),
                                rx.select.item(LanguageState.tr["btn_send_to_lab"], value="labo"),
                            ),
                            value=CampaignPatientExamsState.section_action,
                            on_change=CampaignPatientExamsState.set_section_action,
                            size="2",
                        ),
                        rx.button(
                            rx.icon("check", size=14),
                            LanguageState.tr["btn_validate"],
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
                        CampaignPatientExamsState.active_section_is_dispatched,
                        rx.hstack(
                            rx.badge(
                                rx.icon("send", size=12),
                                LanguageState.tr["badge_dispatched_to_lab"],
                                color_scheme="amber",
                                variant="soft",
                                size="1",
                            ),
                            rx.text(
                                LanguageState.tr["hint_awaiting_lab_entry"],
                                size="1",
                                color="var(--gray-9)",
                                font_style="italic",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.text(
                            LanguageState.tr["hint_save_without_sending"],
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


# ── Transmit panel (internal doctor) ──────────────────────────────────────────


def _transmit_panel() -> rx.Component:
    """Global panel: operator validates lab results (entry + validation are
    both done by the lab technician/operator, so this is a single action —
    not a separate "send to lab" step first)."""
    s = CampaignPatientExamsState.medical_status
    lab_validated = s == "LAB_VALIDATED"
    already_advanced = (
        (s == "LAB_VALIDATED")
        | (s == "INTERNAL_INTERPRETED")
        | (s == "INTERNAL_VALIDATED")
        | (s == "TRANSMITTED_TREATING_DOCTOR")
        | (s == "ENTERPRISE_VALIDATED")
        | (s == "PUBLISHED")
    )
    return rx.vstack(
        # ── Lab validation card (lab technician / operator) ──
        rx.cond(
            CampaignPatientExamsState.viewer_is_operator,
            rx.card(
                rx.hstack(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("flask-conical", size=16, color="var(--amber-9)"),
                            rx.text(
                                LanguageState.tr["lab_validation_label"], size="3", weight="bold"
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.cond(
                            already_advanced,
                            rx.text(LanguageState.tr["results_validated"], size="2", color="var(--green-10)"),
                            rx.cond(
                                CampaignPatientExamsState.all_sections_saved,
                                rx.text(
                                    LanguageState.tr["hint_confirm_lab"],
                                    size="2",
                                    color="var(--gray-9)",
                                ),
                                rx.text(
                                    LanguageState.tr["hint_save_before_validate_lab"],
                                    size="2",
                                    color="var(--orange-9)",
                                ),
                            ),
                        ),
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.cond(
                        already_advanced,
                        rx.badge(
                            rx.icon("check", size=13),
                            LanguageState.tr["badge_lab_validated"],
                            color_scheme="amber",
                            variant="soft",
                            size="2",
                        ),
                        rx.button(
                            rx.icon("check-circle", size=14),
                            LanguageState.tr["btn_validate_lab"],
                            color_scheme="amber",
                            size="3",
                            loading=CampaignPatientExamsState.is_saving,
                            disabled=~CampaignPatientExamsState.all_sections_saved,
                            on_click=CampaignPatientExamsState.transmit_and_validate_lab,
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
        # ── Hand off to internal doctor (shown once lab is validated) ──
        rx.cond(
            (CampaignPatientExamsState.viewer_is_operator | CampaignPatientExamsState.viewer_is_internal)
            & lab_validated,
            rx.card(
                rx.hstack(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("send", size=16, color="var(--blue-9)"),
                            rx.text(
                                GeneralSettingsState.transfer_all_to_org_doctor_label,
                                size="3",
                                weight="bold",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.text(
                            GeneralSettingsState.click_to_transfer_org_label,
                            size="2",
                            color="var(--gray-9)",
                        ),
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.cond(
                        CampaignPatientExamsState.internal_notified,
                        rx.badge(
                            rx.icon("check", size=13),
                            LanguageState.tr["badge_transferred"],
                            color_scheme="blue",
                            variant="soft",
                            size="2",
                        ),
                        rx.button(
                            rx.icon("send", size=14),
                            GeneralSettingsState.send_to_org_doctor_label,
                            color_scheme="blue",
                            size="3",
                            loading=CampaignPatientExamsState.is_saving,
                            on_click=CampaignPatientExamsState.notify_internal_doctor,
                        ),
                    ),
                    align="center",
                    spacing="4",
                    width="100%",
                ),
                width="100%",
                background="var(--blue-2)",
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
        (s == "INTERNAL_VALIDATED")
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
                        rx.text(LanguageState.tr["treating_doctor_label"], size="3", weight="bold"),
                        rx.badge(LanguageState.tr["optional_badge"], size="1", color_scheme="gray", variant="soft"),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        LanguageState.tr["hint_treating_doctor"],
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
                        LanguageState.tr["badge_sent"],
                        color_scheme="teal",
                        variant="soft",
                        size="2",
                    ),
                    rx.button(
                        rx.icon("send", size=14),
                        LanguageState.tr["btn_send_to_treating_doctor"],
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


# ── Internal doctor interpretation panel ──────────────────────────────────────


def _internal_interpretation_panel() -> rx.Component:
    """Panel for the internal doctor to add interpretation and send to enterprise doctor."""
    # internal_validated is a permanent flag (set once, never cleared) — unlike
    # medical_status, which keeps advancing past INTERNAL_VALIDATED, so an exact
    # status match would silently unlock this panel again at later stages.
    already_validated = CampaignPatientExamsState.internal_validated
    already_interpreted = CampaignPatientExamsState.medical_status == "INTERNAL_INTERPRETED"
    # Lab must be validated AND the case explicitly handed off to the internal
    # doctor (notify_internal_doctor) before they can interpret.
    notified_and_lab_validated = (
        CampaignPatientExamsState.medical_status == "LAB_VALIDATED"
    ) & CampaignPatientExamsState.internal_notified
    # SuperAdmin/Admin/operator can always preview this panel, but the fields
    # themselves stay locked (see `unlocked` below) until the lab hand-off has
    # genuinely happened — visibility and editability are separate gates, so
    # an admin preview never lets someone write an interpretation early.
    can_show = (
        notified_and_lab_validated
        | already_interpreted
        | already_validated
        | CampaignPatientExamsState.viewer_is_operator
    )
    unlocked = notified_and_lab_validated | already_interpreted | already_validated
    return rx.cond(
        CampaignPatientExamsState.viewer_is_internal & can_show,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("stethoscope", size=16, color="var(--blue-9)"),
                    rx.text(GeneralSettingsState.org_doctor_interpretation_label, size="3", weight="bold"),
                    rx.spacer(),
                    rx.cond(
                        already_validated,
                        rx.badge(
                            rx.icon("check", size=13),
                            GeneralSettingsState.org_validated_label,
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
                rx.cond(
                    ~unlocked,
                    rx.callout(
                        LanguageState.tr["hint_awaiting_lab_handoff"],
                        icon="lock",
                        color_scheme="gray",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                rx.text_area(
                    value=CampaignPatientExamsState.internal_notes,
                    on_change=CampaignPatientExamsState.set_internal_notes,
                    placeholder=LanguageState.tr["interpretation_placeholder"],
                    rows="5",
                    width="100%",
                    read_only=already_validated | ~unlocked,
                    style=rx.cond(
                        ~unlocked,
                        {"background": "var(--gray-2)", "cursor": "not-allowed"},
                        {"background": "transparent"},
                    ),
                ),
                rx.cond(
                    ~already_validated & unlocked,
                    rx.cond(
                        CampaignPatientExamsState.has_company_doctor,
                        rx.hstack(
                            rx.spacer(),
                            rx.button(
                                rx.icon("send", size=14),
                                CampaignPatientExamsState.send_to_enterprise_label,
                                color_scheme="blue",
                                size="2",
                                loading=CampaignPatientExamsState.is_saving,
                                on_click=CampaignPatientExamsState.validate_and_send_to_enterprise,
                            ),
                            rx.cond(
                                CampaignPatientExamsState.next_patient_id != "",
                                rx.button(
                                    rx.icon("send", size=14),
                                    LanguageState.tr["btn_validate_and_next"],
                                    color_scheme="blue",
                                    variant="soft",
                                    size="2",
                                    loading=CampaignPatientExamsState.is_saving,
                                    on_click=CampaignPatientExamsState.validate_internal_and_next,
                                ),
                                rx.fragment(),
                            ),
                            width="100%",
                            spacing="2",
                            align="center",
                        ),
                        # No company doctor assigned to this campaign — publish
                        # straight to the patient instead of handing off.
                        rx.vstack(
                            rx.callout(
                                LanguageState.tr["no_company_doctor_hint"],
                                icon="info",
                                color_scheme="gray",
                                size="1",
                            ),
                            rx.text(
                                LanguageState.tr["enterprise_patient_message_label"],
                                size="2",
                                weight="medium",
                                color="var(--gray-9)",
                            ),
                            rx.text_area(
                                value=CampaignPatientExamsState.internal_direct_patient_message,
                                on_change=CampaignPatientExamsState.set_internal_direct_patient_message,
                                placeholder=LanguageState.tr["enterprise_patient_message_placeholder"],
                                rows="4",
                                width="100%",
                            ),
                            rx.hstack(
                                rx.spacer(),
                                rx.button(
                                    rx.icon("check", size=14),
                                    LanguageState.tr["btn_publish_directly_to_patient"],
                                    color_scheme="blue",
                                    size="2",
                                    loading=CampaignPatientExamsState.is_saving,
                                    on_click=CampaignPatientExamsState.publish_directly_to_patient,
                                ),
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                        ),
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
    # enterprise_validated is a permanent flag (set once, never cleared) — unlike
    # medical_status, which keeps advancing past ENTERPRISE_VALIDATED, so an exact
    # status match would silently unlock this panel again at later stages.
    already_validated = CampaignPatientExamsState.enterprise_validated
    # A dossier can end up with enterprise_validated=True but no actual
    # interpretation/message content (e.g. a historical record published via
    # the internal doctor's direct-to-patient shortcut before this campaign
    # had a company doctor). Locking the fields in that case leaves the
    # company doctor unable to ever write anything — so "locked" additionally
    # requires there to be real content behind the validated flag.
    has_content = (CampaignPatientExamsState.enterprise_notes != "") | (
        CampaignPatientExamsState.enterprise_patient_message != ""
    )
    locked = already_validated & has_content
    # No viewer_is_operator bypass here: an admin/operator previewing this page
    # must NOT be able to unlock the enterprise doctor's fields before the
    # internal doctor has actually validated — visibility of the panel is
    # already unconditional (gated only on viewer_is_enterprise below).
    internal_done = CampaignPatientExamsState.internal_validated | already_validated
    return rx.cond(
        CampaignPatientExamsState.viewer_is_enterprise,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("building-2", size=16, color="var(--indigo-9)"),
                    rx.text(LanguageState.tr["company_doctor_interpretation"], size="3", weight="bold"),
                    rx.spacer(),
                    rx.cond(
                        locked,
                        rx.badge(
                            rx.icon("check", size=13),
                            LanguageState.tr["badge_company_validated"],
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
                    ~internal_done,
                    rx.callout(
                        GeneralSettingsState.awaiting_org_label,
                        icon="clock",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.vstack(
                        rx.text(
                            LanguageState.tr["enterprise_interp_label"],
                            size="2",
                            weight="medium",
                            color="var(--gray-9)",
                        ),
                        rx.text_area(
                            value=CampaignPatientExamsState.enterprise_notes,
                            on_change=CampaignPatientExamsState.set_enterprise_notes,
                            placeholder=LanguageState.tr["enterprise_interp_placeholder"],
                            rows="5",
                            width="100%",
                            read_only=locked,
                        ),
                        rx.text(
                            LanguageState.tr["enterprise_patient_message_label"],
                            size="2",
                            weight="medium",
                            color="var(--gray-9)",
                        ),
                        rx.text_area(
                            value=CampaignPatientExamsState.enterprise_patient_message,
                            on_change=CampaignPatientExamsState.set_enterprise_patient_message,
                            placeholder=LanguageState.tr["enterprise_patient_message_placeholder"],
                            rows="4",
                            width="100%",
                            read_only=locked,
                        ),
                        rx.cond(
                            ~locked,
                            rx.hstack(
                                rx.spacer(),
                                rx.button(
                                    rx.icon("check", size=14),
                                    LanguageState.tr["btn_validate_interpretation"],
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
    can_show = ((s == "ENTERPRISE_VALIDATED") | (s == "PUBLISHED")) & (
        CampaignPatientExamsState.viewer_is_enterprise | CampaignPatientExamsState.viewer_is_operator
    )
    already_done = s == "PUBLISHED"
    return rx.cond(
        can_show,
        rx.card(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.icon("archive", size=16, color="var(--green-9)"),
                        rx.text(LanguageState.tr["close_file_btn"], size="3", weight="bold"),
                        spacing="2",
                        align="center",
                    ),
                    rx.cond(
                        already_done,
                        rx.text(
                            LanguageState.tr["hint_file_closed_published"],
                            size="2",
                            color="var(--green-10)",
                        ),
                        rx.text(
                            LanguageState.tr["hint_close_file"],
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
                        LanguageState.tr["badge_file_closed"],
                        color_scheme="green",
                        variant="soft",
                        size="2",
                    ),
                    rx.button(
                        rx.icon("check-circle", size=14),
                        LanguageState.tr["btn_finish"],
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
            rx.dialog.title(LanguageState.tr["motif_dialog_title"]),
            rx.dialog.description(
                LanguageState.tr["motif_dialog_desc"],
                size="2",
                color="var(--gray-9)",
            ),
            rx.vstack(
                rx.text_area(
                    placeholder=LanguageState.tr["correction_entry_placeholder"],
                    value=CampaignPatientExamsState.modification_motif,
                    on_change=CampaignPatientExamsState.set_modification_motif,
                    rows="3",
                    width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            LanguageState.tr["cancel_btn"],
                            variant="ghost",
                            color_scheme="gray",
                            size="2",
                            on_click=CampaignPatientExamsState.close_motif_dialog,
                        ),
                    ),
                    rx.button(
                        rx.icon("check", size=14),
                        LanguageState.tr["btn_confirm_modification"],
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
            rx.dialog.title(LanguageState.tr["add_param_dialog_title"]),
            rx.dialog.description(
                LanguageState.tr["add_param_dialog_desc"],
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
                                    " ",
                                    LanguageState.tr["selected_count_suffix"],
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
                        LanguageState.tr["cancel_btn"],
                        variant="outline",
                        on_click=CampaignPatientExamsState.close_add_param_dialog,
                    ),
                    rx.button(
                        LanguageState.tr["btn_add_tests"],
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
                        LanguageState.tr["btn_back_to_campaign"],
                        variant="ghost",
                        size="2",
                        on_click=CampaignPatientExamsState.go_back,
                    ),
                    rx.cond(
                        CampaignPatientExamsState.visit_id != "",
                        rx.tooltip(
                            rx.button(
                                rx.icon("stethoscope", size=14),
                                LanguageState.tr["btn_doctor_interpretation"],
                                variant="soft",
                                color_scheme="blue",
                                size="2",
                                on_click=CampaignPatientExamsState.go_to_visit_detail,
                            ),
                            content=LanguageState.tr["hint_go_to_doctor_interp"],
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
                                        content=LanguageState.tr["tooltip_prev_patient"],
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
                                        content=LanguageState.tr["tooltip_next_patient"],
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
                                            LanguageState.tr["reason_field_obs_label"],
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
                                        placeholder=LanguageState.tr["reason_for_consultation_placeholder"],
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
                                    LanguageState.tr["hint_patient_presence"],
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
                            # ── Transfer to internal doctor panel ──────────
                            _transmit_panel(),
                            # ── Treating doctor (optional) ─────────────────
                            _treating_doctor_panel(),
                            # ── Internal interpretation (internal-scope gate is inside the panel) ──
                            _internal_interpretation_panel(),
                            # ── Enterprise interpretation (company-scope gate is inside the panel) ──
                            _enterprise_interpretation_panel(),
                            # ── Close record (viewer gate is inside the panel) ─
                            _finish_panel(),
                            spacing="4",
                            width="100%",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("file", size=36, color="var(--gray-5)"),
                                rx.text(
                                    "No exam types configured for this campaign.",
                                    size="2",
                                    color="var(--gray-9)",
                                ),
                                rx.text(
                                    "Go to the \"Exams\" tab of the campaign to add some.",
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
