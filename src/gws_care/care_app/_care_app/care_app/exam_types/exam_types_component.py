"""Exam types management page component (US-040, US-041).

Layout:
  - Vue liste  : table de tous les types d'examens → cliquer une ligne → vue détail
  - Vue détail : informations du type + gestion complète des paramètres inline
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .exam_types_state import ExamParamVM, ExamTypeRowVM, ExamTypesState

_VALUE_TYPES = [
    ("NUMERIC", "Numérique"),
    ("TEXT", "Texte"),
    ("BOOLEAN", "Positif / Négatif"),
]

# ── Vue liste ─────────────────────────────────────────────────────────────────

def _type_row(t: ExamTypeRowVM) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(t.name, size="2", weight="bold"),
                rx.hstack(
                    rx.text(t.category_label, size="1", color="var(--gray-9)"),
                    rx.cond(
                        t.department != "",
                        rx.badge(t.department, color_scheme="purple", size="1", variant="soft"),
                    ),
                    spacing="2",
                    align="center",
                ),
                spacing="0",
            )
        ),
        rx.table.cell(
            rx.cond(
                t.is_active,
                rx.badge("Actif", color_scheme="green", size="1", variant="soft"),
                rx.badge("Inactif", color_scheme="gray", size="1", variant="soft"),
            )
        ),
        rx.table.cell(
            rx.badge(t.parameter_count.to(str) + " paramètre(s)", color_scheme="blue", size="1", variant="soft"),
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("settings", size=14),
                        variant="soft",
                        size="1",
                        title="Ouvrir et gérer les paramètres",
                        on_click=ExamTypesState.go_to_detail(t.id),
                    ),
                    content="Gérer les paramètres",
                ),
                rx.cond(
                    t.is_active,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("ban", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="orange",
                            on_click=ExamTypesState.open_confirm_deactivate_type(t.id, t.name),
                        ),
                        content="Désactiver",
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("check", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="green",
                            on_click=ExamTypesState.open_confirm_reactivate_type(t.id, t.name),
                        ),
                        content="Réactiver",
                    ),
                ),
                rx.cond(
                    ~t.is_active,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("trash-2", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="red",
                            on_click=ExamTypesState.open_confirm_delete_type(t.id, t.name),
                        ),
                        content="Supprimer définitivement",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
        # pas de on_click sur la ligne — évite que le bouton désactiver déclenche aussi la navigation
    )


def _list_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.heading("Référentiel des examens", size="6"),
                rx.text(
                    "Définissez vos types d'examens et leurs paramètres. Cliquez sur une ligne pour gérer les paramètres.",
                    size="2",
                    color="var(--gray-9)",
                ),
                spacing="0",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                "Nouveau type d'examen",
                on_click=ExamTypesState.open_create_type_dialog,
            ),
            width="100%",
            align="end",
        ),
        rx.cond(
            ExamTypesState.error != "",
            rx.callout(ExamTypesState.error, icon="info", color_scheme="red", size="2",
                       on_click=ExamTypesState.dismiss_messages, style={"cursor": "pointer"}),
        ),
        rx.cond(
            ExamTypesState.success != "",
            rx.callout(ExamTypesState.success, icon="check", color_scheme="green", size="2",
                       on_click=ExamTypesState.dismiss_messages, style={"cursor": "pointer"}),
        ),
        rx.cond(
            ExamTypesState.is_loading,
            rx.center(rx.spinner(size="3"), padding="4rem"),
            rx.cond(
                ExamTypesState.exam_types.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Nom / Catégorie"),
                            rx.table.column_header_cell("Statut"),
                            rx.table.column_header_cell("Paramètres"),
                            rx.table.column_header_cell(""),
                        )
                    ),
                    rx.table.body(rx.foreach(ExamTypesState.exam_types, _type_row)),
                    width="100%",
                    variant="surface",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("file", size=32, color="var(--gray-6)"),
                        rx.text("Aucun type d'examen configuré.", size="3", color="var(--gray-9)"),
                        rx.text(
                            "Cliquez sur \"+ Nouveau type d'examen\" pour commencer.",
                            size="2", color="var(--gray-9)",
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


# ── Vue détail ────────────────────────────────────────────────────────────────

def _param_row(p: ExamParamVM) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.text(p.name, size="2", weight="medium"),
                rx.cond(
                    p.is_required,
                    rx.badge("Obligatoire", color_scheme="red", size="1"),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(rx.badge(p.value_type, size="1", variant="soft", color_scheme="blue")),
        rx.table.cell(
            rx.cond(p.unit != "", rx.text(p.unit, size="2"), rx.text("—", size="2", color="var(--gray-7)"))
        ),
        rx.table.cell(
            rx.cond(
                (p.ref_low != "") | (p.ref_high != ""),
                rx.text(rx.cond(p.ref_low != "", p.ref_low, "—"), " → ",
                        rx.cond(p.ref_high != "", p.ref_high, "—"), size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.cond(
                (p.critical_low != "") | (p.critical_high != ""),
                rx.hstack(
                    rx.badge(rx.cond(p.critical_low != "", p.critical_low, "—"),
                             color_scheme="red", size="1", variant="soft"),
                    rx.badge(rx.cond(p.critical_high != "", p.critical_high, "—"),
                             color_scheme="red", size="1", variant="soft"),
                    spacing="1",
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pen-line", size=14), variant="ghost", size="1", color_scheme="blue",
                        on_click=ExamTypesState.open_edit_param_dialog(p.id),
                    ),
                    content="Modifier ce paramètre",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("trash-2", size=14), variant="ghost", size="1", color_scheme="red",
                        on_click=ExamTypesState.open_confirm_delete_param(p.id),
                    ),
                    content="Supprimer ce paramètre",
                ),
                spacing="1",
            )
        ),
    )


def _detail_view() -> rx.Component:
    return rx.vstack(
        # Navigation retour
        rx.hstack(
            rx.button(
                rx.icon("chevron-left", size=14),
                "Retour au référentiel",
                variant="ghost",
                size="2",
                on_click=ExamTypesState.back_to_list,
            ),
            rx.spacer(),
            rx.cond(
                ExamTypesState.success != "",
                rx.callout(ExamTypesState.success, icon="check", color_scheme="green", size="1",
                           on_click=ExamTypesState.dismiss_messages, style={"cursor": "pointer"}),
                rx.fragment(),
            ),
            width="100%",
            align="center",
        ),
        # Carte identité du type
        rx.card(
            rx.hstack(
                rx.box(
                    rx.icon("file", size=24, color="var(--accent-9)"),
                    padding="0.5rem",
                    border_radius="8px",
                    background="var(--accent-3)",
                ),
                rx.vstack(
                    rx.heading(ExamTypesState.selected_type_name, size="5"),
                    rx.hstack(
                        rx.badge(ExamTypesState.selected_type_category, color_scheme="blue", variant="soft", size="1"),
                        rx.cond(
                            ExamTypesState.selected_type_active,
                            rx.badge("Actif", color_scheme="green", size="1", variant="soft"),
                            rx.badge("Inactif", color_scheme="gray", size="1", variant="soft"),
                        ),
                        rx.cond(
                            ExamTypesState.selected_type_allows_attachment,
                            rx.badge("Pièce jointe autorisée", color_scheme="gray", size="1", variant="outline"),
                            rx.fragment(),
                        ),
                        rx.cond(
                            ExamTypesState.selected_type_requires_attachment,
                            rx.badge("Pièce jointe obligatoire", color_scheme="orange", size="1", variant="soft"),
                            rx.fragment(),
                        ),
                        spacing="2",
                        flex_wrap="wrap",
                    ),
                    spacing="1",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            width="100%",
            padding="1rem",
        ),
        # Section paramètres
        rx.vstack(
            rx.hstack(
                rx.heading("Paramètres de cet examen", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=14),
                    "Ajouter un paramètre",
                    variant="soft",
                    size="2",
                    on_click=ExamTypesState.open_create_param_dialog,
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                ExamTypesState.error != "",
                rx.callout(ExamTypesState.error, icon="info", color_scheme="red", size="1",
                           on_click=ExamTypesState.dismiss_messages, style={"cursor": "pointer"}),
            ),
            rx.cond(
                ExamTypesState.parameters.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Nom du paramètre"),
                            rx.table.column_header_cell("Type"),
                            rx.table.column_header_cell("Unité"),
                            rx.table.column_header_cell("Valeurs ref."),
                            rx.table.column_header_cell("Seuils critiques"),
                            rx.table.column_header_cell(""),
                        )
                    ),
                    rx.table.body(rx.foreach(ExamTypesState.parameters, _param_row)),
                    width="100%",
                    variant="surface",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("plus", size=28, color="var(--gray-6)"),
                        rx.text("Aucun paramètre configuré pour cet examen.", size="2", color="var(--gray-9)"),
                        rx.text("Cliquez sur \"+ Ajouter un paramètre\" pour commencer.",
                                size="2", color="var(--gray-9)"),
                        spacing="2",
                        align="center",
                    ),
                    padding="3rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="12px",
                    width="100%",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ── Dialogues ─────────────────────────────────────────────────────────────────

def _category_suggestion(cat: str) -> rx.Component:
    return rx.badge(
        cat,
        color_scheme="gray",
        variant="outline",
        size="1",
        cursor="pointer",
        on_click=ExamTypesState.set_type_category(cat),
        _hover={"background": "var(--accent-3)", "border_color": "var(--accent-9)"},
    )


def _type_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nouveau type d'examen"),
            rx.vstack(
                rx.vstack(
                    rx.text("Nom *", size="2", weight="medium"),
                    rx.input(
                        placeholder="ex: NFS, ECG, Sérologie VHB…",
                        value=ExamTypesState.type_form.name,
                        on_change=ExamTypesState.set_type_name,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.text("Catégorie *", size="2", weight="medium"),
                    rx.text("Saisie libre — cliquez sur une suggestion pour la réutiliser.",
                            size="1", color="var(--gray-9)"),
                    rx.input(
                        placeholder="ex: Biologie, Immunologie, Sérologie, ECG…",
                        value=ExamTypesState.type_form.category,
                        on_change=ExamTypesState.set_type_category,
                        width="100%",
                    ),
                    rx.cond(
                        ExamTypesState.existing_categories.length() > 0,
                        rx.flex(
                            rx.foreach(ExamTypesState.existing_categories, _category_suggestion),
                            flex_wrap="wrap",
                            gap="0.4rem",
                            padding_top="0.25rem",
                        ),
                        rx.fragment(),
                    ),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.text("Département", size="2", weight="medium"),
                    rx.text("Service ou département responsable de cet examen.", size="1", color="var(--gray-9)"),
                    rx.input(
                        placeholder="ex: Cytologie, Radiologie, Cardiologie, ORL, Biologie…",
                        value=ExamTypesState.type_form.department,
                        on_change=ExamTypesState.set_type_department,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.text("Description", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Description optionnelle…",
                        value=ExamTypesState.type_form.description,
                        on_change=ExamTypesState.set_type_description,
                        width="100%",
                        rows="2",
                    ),
                    spacing="1", width="100%",
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text("Pièce jointe autorisée", size="2"),
                        rx.switch(checked=ExamTypesState.type_form.allows_attachment,
                                  on_change=ExamTypesState.set_type_allows_attachment),
                        spacing="1", align="center",
                    ),
                    rx.vstack(
                        rx.text("Pièce jointe obligatoire", size="2"),
                        rx.switch(checked=ExamTypesState.type_form.requires_attachment,
                                  on_change=ExamTypesState.set_type_requires_attachment),
                        spacing="1", align="center",
                    ),
                    spacing="6",
                    padding_top="0.25rem",
                ),
                rx.vstack(
                    rx.text("Type de prélèvement associé", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Sélectionner le type de prélèvement...", width="100%"),
                        rx.select.content(
                            rx.select.item("— Aucun —", value="NONE"),
                            rx.select.item("Sang total (EDTA)", value="Sang total (EDTA)"),
                            rx.select.item("Urine (flacon stérile)", value="Urine (flacon stérile)"),
                            rx.select.item("Urine 24h (bidon)", value="Urine 24h (bidon)"),
                            rx.select.item("Salive", value="Salive"),
                            rx.select.item("Écouvillon naso-pharyngé", value="Écouvillon naso-pharyngé"),
                            rx.select.item("Selles (coproculture)", value="Selles (coproculture)"),
                            rx.select.item("LCR", value="LCR"),
                            rx.select.item("Autre", value="Autre"),
                        ),
                        value=ExamTypesState.type_form.required_sample_type,
                        on_change=ExamTypesState.set_type_required_sample_type,
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.cond(
                    ExamTypesState.type_form_error != "",
                    rx.callout(ExamTypesState.type_form_error, icon="info", color_scheme="red", size="1"),
                ),
                spacing="3", width="100%", margin_top="0.5rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=ExamTypesState.close_type_dialog)),
                rx.button("Créer", on_click=ExamTypesState.save_type,
                          loading=ExamTypesState.is_saving_type),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="520px",
        ),
        open=ExamTypesState.type_dialog_open,
        on_open_change=lambda _: ExamTypesState.close_type_dialog(),
    )


def _param_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(ExamTypesState.is_editing_param, "Modifier le paramètre", "Nouveau paramètre")
            ),
            rx.dialog.description(
                "Définissez un paramètre mesuré lors de cet examen.",
                size="2", color="var(--gray-9)",
            ),
            rx.vstack(
                rx.grid(
                    rx.vstack(
                        rx.text("Nom du paramètre *", size="2", weight="medium"),
                        rx.input(
                            placeholder="ex: Globules blancs, CRP…",
                            value=ExamTypesState.param_form.name,
                            on_change=ExamTypesState.set_param_name,
                            width="100%",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Type de valeur *", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(placeholder="— Choisir", width="100%"),
                            rx.select.content(
                                *[rx.select.item(label, value=val) for val, label in _VALUE_TYPES]
                            ),
                            value=ExamTypesState.param_form.value_type,
                            on_change=ExamTypesState.set_param_value_type,
                        ),
                        spacing="1",
                    ),
                    columns="2", spacing="4", width="100%",
                ),
                rx.vstack(
                    rx.text("Unité", size="2", weight="medium"),
                    rx.input(
                        placeholder="ex: g/dL, mmol/L, U/L, %…",
                        value=ExamTypesState.param_form.unit,
                        on_change=ExamTypesState.set_param_unit,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.text("Valeurs de référence", size="2", weight="medium", color="var(--gray-11)"),
                rx.grid(
                    rx.vstack(
                        rx.text("Ref. basse", size="1", color="var(--gray-9)"),
                        rx.input(placeholder="ex: 4.0", type="number",
                                 value=ExamTypesState.param_form.ref_low,
                                 on_change=ExamTypesState.set_param_ref_low, width="100%"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Ref. haute", size="1", color="var(--gray-9)"),
                        rx.input(placeholder="ex: 10.0", type="number",
                                 value=ExamTypesState.param_form.ref_high,
                                 on_change=ExamTypesState.set_param_ref_high, width="100%"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Seuil critique bas", size="1", color="var(--gray-9)"),
                        rx.input(placeholder="ex: 2.0", type="number",
                                 value=ExamTypesState.param_form.critical_low,
                                 on_change=ExamTypesState.set_param_critical_low, width="100%"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Seuil critique haut", size="1", color="var(--gray-9)"),
                        rx.input(placeholder="ex: 15.0", type="number",
                                 value=ExamTypesState.param_form.critical_high,
                                 on_change=ExamTypesState.set_param_critical_high, width="100%"),
                        spacing="1",
                    ),
                    columns="2", spacing="3", width="100%",
                ),
                rx.hstack(
                    rx.text("Paramètre obligatoire", size="2"),
                    rx.switch(checked=ExamTypesState.param_form.is_required,
                              on_change=ExamTypesState.set_param_required),
                    spacing="2", align="center",
                ),
                rx.cond(
                    ExamTypesState.param_form_error != "",
                    rx.callout(ExamTypesState.param_form_error, icon="info",
                               color_scheme="red", size="1"),
                ),
                spacing="3", width="100%", margin_top="0.5rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=ExamTypesState.close_param_dialog)),
                rx.button(
                    rx.cond(ExamTypesState.is_editing_param, "Enregistrer les modifications", "Ajouter le paramètre"),
                    on_click=ExamTypesState.save_param,
                    loading=ExamTypesState.is_saving_param,
                ),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="520px",
        ),
        open=ExamTypesState.param_dialog_open,
        on_open_change=lambda _: ExamTypesState.close_param_dialog(),
    )


# ── Page principale ───────────────────────────────────────────────────────────

def exam_types_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.cond(
                ExamTypesState.view == "list",
                _list_view(),
                _detail_view(),
            ),
            _type_dialog(),
            _param_dialog(),
            # ── Confirm suppression paramètre ───────────────────────────────
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(
                        rx.hstack(rx.icon("trash-2", size=18, color="var(--red-9)"),
                                  rx.text("Supprimer ce paramètre ?"), spacing="2"),
                    ),
                    rx.dialog.description(
                        "Cette action est irréversible. Le paramètre sera définitivement supprimé.",
                        size="2", color="var(--gray-9)",
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Annuler", variant="soft", color_scheme="gray",
                                      on_click=ExamTypesState.dismiss_confirm_delete_param),
                        ),
                        rx.button("Supprimer", color_scheme="red",
                                  on_click=ExamTypesState.confirmed_delete_param),
                        justify="end", spacing="2", margin_top="1rem", width="100%",
                    ),
                    max_width="400px",
                ),
                open=ExamTypesState.confirm_delete_param_open,
                on_open_change=lambda _: ExamTypesState.dismiss_confirm_delete_param(),
            ),
            # ── Confirm désactivation type d'examen ──────────────────────────
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(
                        rx.hstack(rx.icon("ban", size=18, color="var(--orange-9)"),
                                  rx.text("Désactiver ce type d'examen ?"), spacing="2"),
                    ),
                    rx.dialog.description(
                        rx.vstack(
                            rx.text(
                                "Le type « ", rx.text.strong(ExamTypesState.confirm_deactivate_type_name),
                                " » sera désactivé et ne sera plus proposable dans de nouvelles campagnes.",
                                size="2",
                            ),
                            rx.text("Les campagnes existantes ne sont pas affectées.",
                                    size="2", color="var(--gray-9)"),
                            spacing="2",
                        ),
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Annuler", variant="soft", color_scheme="gray",
                                      on_click=ExamTypesState.dismiss_confirm_deactivate_type),
                        ),
                        rx.button("Désactiver", color_scheme="orange",
                                  on_click=ExamTypesState.confirmed_deactivate_type),
                        justify="end", spacing="2", margin_top="1rem", width="100%",
                    ),
                    max_width="440px",
                ),
                open=ExamTypesState.confirm_deactivate_type_open,
                on_open_change=lambda _: ExamTypesState.dismiss_confirm_deactivate_type(),
            ),
            # ── Confirm réactivation type d'examen ──────────────────────────
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(
                        rx.hstack(rx.icon("check", size=18, color="var(--green-9)"),
                                  rx.text("Réactiver ce type d'examen ?"), spacing="2"),
                    ),
                    rx.dialog.description(
                        rx.vstack(
                            rx.text(
                                "Le type « ", rx.text.strong(ExamTypesState.confirm_reactivate_type_name),
                                " » sera réactivé et proposé dans les nouvelles campagnes.",
                                size="2",
                            ),
                            spacing="2",
                        ),
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Annuler", variant="soft", color_scheme="gray",
                                      on_click=ExamTypesState.dismiss_confirm_reactivate_type),
                        ),
                        rx.button("Réactiver", color_scheme="green",
                                  on_click=ExamTypesState.confirmed_reactivate_type),
                        justify="end", spacing="2", margin_top="1rem", width="100%",
                    ),
                    max_width="440px",
                ),
                open=ExamTypesState.confirm_reactivate_type_open,
                on_open_change=lambda _: ExamTypesState.dismiss_confirm_reactivate_type(),
            ),
            # ── Confirm suppression totale type d'examen ────────────────────
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(
                        rx.hstack(rx.icon("trash-2", size=18, color="var(--red-9)"),
                                  rx.text("Supprimer définitivement ce type d'examen ?"), spacing="2"),
                    ),
                    rx.dialog.description(
                        rx.vstack(
                            rx.text(
                                "Le type « ", rx.text.strong(ExamTypesState.confirm_delete_type_name),
                                " » et tous ses paramètres seront supprimés définitivement.",
                                size="2",
                            ),
                            rx.text(
                                "Cette action est irréversible. Assurez-vous que ce type n'est"
                                " utilisé dans aucune campagne active.",
                                size="2", color="var(--red-9)",
                            ),
                            spacing="2",
                        ),
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Annuler", variant="soft", color_scheme="gray",
                                      on_click=ExamTypesState.dismiss_confirm_delete_type),
                        ),
                        rx.button("Supprimer définitivement", color_scheme="red",
                                  on_click=ExamTypesState.confirmed_delete_type),
                        justify="end", spacing="2", margin_top="1rem", width="100%",
                    ),
                    max_width="460px",
                ),
                open=ExamTypesState.confirm_delete_type_open,
                on_open_change=lambda _: ExamTypesState.dismiss_confirm_delete_type(),
            ),
        )
    )
