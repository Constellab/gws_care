"""Exam types management page component (US-040, US-041).

Layout:
  - List view  : table of all exam types → click a row → detail view
  - Detail view: type information + full parameter management inline
"""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .exam_types_state import AgeRangeVM, ExamParamVM, ExamTypeRowVM, ExamTypesState

# ── List view ─────────────────────────────────────────────────────────────────

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
                rx.badge(LanguageState.tr["status_active"], color_scheme="green", size="1", variant="soft"),
                rx.badge(LanguageState.tr["status_inactive"], color_scheme="gray", size="1", variant="soft"),
            )
        ),
        rx.table.cell(
            rx.badge(
                t.parameter_count.to(str) + " " + LanguageState.tr["param_count_suffix"],
                color_scheme="blue", size="1", variant="soft",
            ),
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("settings", size=14),
                        variant="soft",
                        size="1",
                        title=LanguageState.tr["exam_manage_params_tooltip"],
                        on_click=ExamTypesState.go_to_detail(t.id),
                    ),
                    content=LanguageState.tr["exam_manage_params_tooltip"],
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
                        content=LanguageState.tr["deactivate_tooltip"],
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("check", size=14),
                            variant="ghost",
                            size="1",
                            color_scheme="green",
                            on_click=ExamTypesState.open_confirm_reactivate_type(t.id, t.name),
                        ),
                        content=LanguageState.tr["reactivate_tooltip"],
                    ),
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("trash-2", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="red",
                        on_click=ExamTypesState.open_confirm_delete_type(t.id, t.name),
                    ),
                    content=LanguageState.tr["delete_permanently_tooltip"],
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _list_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.heading(LanguageState.tr["exam_ref_title"], size="6"),
                rx.text(
                    LanguageState.tr["exam_ref_subtitle"],
                    size="2",
                    color="var(--gray-9)",
                ),
                spacing="0",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                LanguageState.tr["exam_new_type_btn"],
                on_click=ExamTypesState.open_create_type_dialog,
            ),
            width="100%",
            align="end",
            spacing="2",
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
                            rx.table.column_header_cell(LanguageState.tr["col_name_category"]),
                            rx.table.column_header_cell(LanguageState.tr["col_status"]),
                            rx.table.column_header_cell(LanguageState.tr["col_parameters"]),
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
                        rx.text(LanguageState.tr["exam_no_types_msg"], size="3", color="var(--gray-9)"),
                        rx.text(LanguageState.tr["exam_no_types_hint"], size="2", color="var(--gray-9)"),
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


# ── Detail view ───────────────────────────────────────────────────────────────

def _param_row(p: ExamParamVM) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.text(p.name, size="2", weight="medium",
                        color=rx.cond(p.is_active, "inherit", "var(--gray-8)")),
                rx.cond(
                    p.is_computed & p.is_active,
                    rx.tooltip(
                        rx.badge(LanguageState.tr["computed_badge"], color_scheme="yellow", size="1", variant="soft"),
                        content=rx.cond(
                            p.formula != "",
                            LanguageState.tr["formula_prefix"] + p.formula,
                            LanguageState.tr["computed_param_label"],
                        ),
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    (p.target_gender != "ALL") & p.is_active,
                    rx.badge(
                        rx.cond(p.target_gender == "M", LanguageState.tr["gender_male_badge"], LanguageState.tr["gender_female_badge"]),
                        color_scheme="pink", size="1", variant="soft",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    p.is_required & p.is_active,
                    rx.badge(LanguageState.tr["required_badge"], color_scheme="red", size="1"),
                    rx.fragment(),
                ),
                rx.cond(
                    ~p.is_active,
                    rx.badge(LanguageState.tr["archived_badge"], color_scheme="gray", size="1", variant="soft"),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(rx.badge(p.value_type, size="1", variant="soft",
                               color_scheme=rx.cond(p.is_active, "blue", "gray"))),
        rx.table.cell(
            rx.cond(p.unit != "", rx.text(p.unit, size="2", color=rx.cond(p.is_active, "inherit", "var(--gray-8)")),
                    rx.text("—", size="2", color="var(--gray-7)"))
        ),
        rx.table.cell(
            rx.cond(
                p.is_active & ((p.ref_low != "") | (p.ref_high != "")),
                rx.text(rx.cond(p.ref_low != "", p.ref_low, "—"), " → ",
                        rx.cond(p.ref_high != "", p.ref_high, "—"), size="2"),
                rx.cond(
                    p.is_active & (p.age_range_summary != ""),
                    rx.tooltip(
                        rx.text(p.age_range_summary, size="2", color="var(--gray-11)"),
                        content="Valeurs issues des tranches d'âge/sexe",
                    ),
                    rx.text("—", size="2", color="var(--gray-7)"),
                ),
            )
        ),
        rx.table.cell(
            rx.cond(
                p.is_active & ((p.critical_low != "") | (p.critical_high != "")),
                rx.hstack(
                    rx.badge(rx.cond(p.critical_low != "", p.critical_low, "—"),
                             color_scheme="red", size="1", variant="soft"),
                    rx.badge(rx.cond(p.critical_high != "", p.critical_high, "—"),
                             color_scheme="red", size="1", variant="soft"),
                    spacing="1",
                ),
                rx.cond(
                    p.is_active & (p.age_range_crit_summary != ""),
                    rx.tooltip(
                        rx.text(p.age_range_crit_summary, size="2", color="var(--gray-11)"),
                        content="Seuils issus des tranches d'âge/sexe",
                    ),
                    rx.text("—", size="2", color="var(--gray-7)"),
                ),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    p.is_active,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("pen-line", size=14), variant="ghost", size="1", color_scheme="blue",
                            on_click=ExamTypesState.open_edit_param_dialog(p.id),
                        ),
                        content=LanguageState.tr["edit_param_tooltip"],
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    p.is_active,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("archive", size=14), variant="ghost", size="1", color_scheme="orange",
                            on_click=ExamTypesState.open_confirm_deactivate_param(p.id, p.name),
                        ),
                        content=LanguageState.tr["archive_param_tooltip"],
                    ),
                    rx.hstack(
                        rx.tooltip(
                            rx.icon_button(
                                rx.icon("rotate-ccw", size=14), variant="ghost", size="1", color_scheme="green",
                                on_click=ExamTypesState.open_confirm_reactivate_param(p.id, p.name),
                            ),
                            content=LanguageState.tr["reactivate_param_tooltip"],
                        ),
                        rx.tooltip(
                            rx.icon_button(
                                rx.icon("trash-2", size=14), variant="ghost", size="1", color_scheme="red",
                                on_click=ExamTypesState.open_confirm_delete_param(p.id),
                            ),
                            content=LanguageState.tr["delete_permanently_tooltip"],
                        ),
                        spacing="1",
                    ),
                ),
                spacing="1",
            )
        ),
        opacity=rx.cond(p.is_active, "1", "0.65"),
    )


def _detail_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.button(
                rx.icon("chevron-left", size=14),
                LanguageState.tr["back_to_ref_btn"],
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
                            ExamTypesState.selected_type_department != "",
                            rx.badge(ExamTypesState.selected_type_department, color_scheme="purple", variant="soft", size="1"),
                            rx.fragment(),
                        ),
                        rx.cond(
                            ExamTypesState.selected_type_active,
                            rx.badge(LanguageState.tr["status_active"], color_scheme="green", size="1", variant="soft"),
                            rx.badge(LanguageState.tr["status_inactive"], color_scheme="gray", size="1", variant="soft"),
                        ),
                        rx.cond(
                            ExamTypesState.selected_type_allows_attachment,
                            rx.badge(LanguageState.tr["attachment_allowed_label"], color_scheme="gray", size="1", variant="outline"),
                            rx.fragment(),
                        ),
                        rx.cond(
                            ExamTypesState.selected_type_requires_attachment,
                            rx.badge(LanguageState.tr["attachment_required_label"], color_scheme="orange", size="1", variant="soft"),
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
        rx.vstack(
            rx.hstack(
                rx.heading(LanguageState.tr["exam_params_section_title"], size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=14),
                    LanguageState.tr["add_param_btn"],
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
                            rx.table.column_header_cell(LanguageState.tr["col_param_name"]),
                            rx.table.column_header_cell(LanguageState.tr["col_type"]),
                            rx.table.column_header_cell(LanguageState.tr["unit_label"]),
                            rx.table.column_header_cell(LanguageState.tr["col_ref_values"]),
                            rx.table.column_header_cell(LanguageState.tr["col_critical_values"]),
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
                        rx.text(LanguageState.tr["no_params_msg"], size="2", color="var(--gray-9)"),
                        rx.text(LanguageState.tr["no_params_hint"], size="2", color="var(--gray-9)"),
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


# ── Dialogs ───────────────────────────────────────────────────────────────────

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


def _department_suggestion(dept: str) -> rx.Component:
    return rx.badge(
        dept,
        color_scheme="purple",
        variant="outline",
        size="1",
        cursor="pointer",
        on_click=ExamTypesState.set_type_department(dept),
        _hover={"background": "var(--purple-3)", "border_color": "var(--purple-9)"},
    )


def _type_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["new_exam_type_title"]),
            rx.vstack(
                rx.vstack(
                    rx.text(LanguageState.tr["name_required_label"], size="2", weight="medium"),
                    rx.input(
                        placeholder="ex: CBC, ECG, HBs serology…",
                        value=ExamTypesState.type_form.name,
                        on_change=ExamTypesState.set_type_name,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.text(LanguageState.tr["category_required_label"], size="2", weight="medium"),
                    rx.text(LanguageState.tr["free_text_suggestion_hint"], size="1", color="var(--gray-9)"),
                    rx.input(
                        placeholder="ex: Biology, Immunology, Serology, ECG…",
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
                    rx.text(LanguageState.tr["department_label"], size="2", weight="medium"),
                    rx.text(LanguageState.tr["free_text_suggestion_hint"], size="1", color="var(--gray-9)"),
                    rx.input(
                        placeholder="ex: Cytology, Radiology, Cardiology, ENT, Biology…",
                        value=ExamTypesState.type_form.department,
                        on_change=ExamTypesState.set_type_department,
                        width="100%",
                    ),
                    rx.cond(
                        ExamTypesState.existing_departments.length() > 0,
                        rx.flex(
                            rx.foreach(ExamTypesState.existing_departments, _department_suggestion),
                            flex_wrap="wrap",
                            gap="0.4rem",
                            padding_top="0.25rem",
                        ),
                        rx.fragment(),
                    ),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.text(LanguageState.tr["description_label"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=LanguageState.tr["description_optional_placeholder"],
                        value=ExamTypesState.type_form.description,
                        on_change=ExamTypesState.set_type_description,
                        width="100%",
                        rows="2",
                    ),
                    spacing="1", width="100%",
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text(LanguageState.tr["attachment_allowed_label"], size="2"),
                        rx.switch(checked=ExamTypesState.type_form.allows_attachment,
                                  on_change=ExamTypesState.set_type_allows_attachment),
                        spacing="1", align="center",
                    ),
                    rx.vstack(
                        rx.text(LanguageState.tr["attachment_required_label"], size="2"),
                        rx.switch(checked=ExamTypesState.type_form.requires_attachment,
                                  on_change=ExamTypesState.set_type_requires_attachment),
                        spacing="1", align="center",
                    ),
                    spacing="6",
                    padding_top="0.25rem",
                ),
                rx.vstack(
                    rx.text(LanguageState.tr["sample_type_label"], size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder=LanguageState.tr["select_sample_type_ph"], width="100%"),
                        rx.select.content(
                            rx.select.item(LanguageState.tr["sample_none"], value="NONE"),
                            rx.select.item(LanguageState.tr["sample_whole_blood"], value="Sang total (EDTA)"),
                            rx.select.item(LanguageState.tr["sample_urine"], value="Urine (flacon stérile)"),
                            rx.select.item(LanguageState.tr["sample_urine_24h"], value="Urine 24h (bidon)"),
                            rx.select.item(LanguageState.tr["sample_saliva"], value="Salive"),
                            rx.select.item(LanguageState.tr["sample_swab"], value="Écouvillon naso-pharyngé"),
                            rx.select.item(LanguageState.tr["sample_stool"], value="Selles (coproculture)"),
                            rx.select.item("LCR", value="LCR"),
                            rx.select.item(LanguageState.tr["sample_other"], value="Autre"),
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
                rx.dialog.close(rx.button(LanguageState.tr["cancel_btn"], variant="soft", color_scheme="gray",
                                          on_click=ExamTypesState.close_type_dialog)),
                rx.button(LanguageState.tr["create_btn"], on_click=ExamTypesState.save_type,
                          loading=ExamTypesState.is_saving_type),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="520px",
        ),
        open=ExamTypesState.type_dialog_open,
        on_open_change=lambda _: ExamTypesState.close_type_dialog(),
    )


def _formula_hint(code: str) -> rx.Component:
    return rx.badge(
        rx.icon("plus", size=10),
        code,
        color_scheme="blue",
        variant="outline",
        size="1",
        cursor="pointer",
        on_click=lambda: ExamTypesState.append_code_to_formula(code),
        _hover={"background": "var(--blue-3)", "border_color": "var(--blue-9)"},
    )


def _param_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    ExamTypesState.is_editing_param,
                    LanguageState.tr["edit_param_title"],
                    LanguageState.tr["new_param_title"],
                )
            ),
            rx.dialog.description(
                LanguageState.tr["param_dialog_desc"],
                size="2", color="var(--gray-9)",
            ),
            rx.vstack(
                rx.grid(
                    rx.vstack(
                        rx.text(LanguageState.tr["param_name_required_label"], size="2", weight="medium"),
                        rx.input(
                            placeholder="ex: White blood cells, CRP…",
                            value=ExamTypesState.param_form.name,
                            on_change=ExamTypesState.set_param_name,
                            width="100%",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text(LanguageState.tr["value_type_required_label"], size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(placeholder=LanguageState.tr["choose_placeholder"], width="100%"),
                            rx.select.content(
                                rx.select.item(LanguageState.tr["value_type_numeric"], value="NUMERIC"),
                                rx.select.item(LanguageState.tr["value_type_text"], value="TEXT"),
                                rx.select.item(LanguageState.tr["value_type_boolean"], value="BOOLEAN"),
                            ),
                            value=ExamTypesState.param_form.value_type,
                            on_change=ExamTypesState.set_param_value_type,
                            disabled=ExamTypesState.param_form.is_computed,
                        ),
                        spacing="1",
                    ),
                    columns="2", spacing="4", width="100%",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(LanguageState.tr["id_code_label"], size="2", weight="medium"),
                        rx.tooltip(
                            rx.icon("info", size=14, color="var(--gray-9)"),
                            content=LanguageState.tr["id_code_tooltip"],
                        ),
                        spacing="1", align="center",
                    ),
                    rx.input(
                        placeholder="ex: hematocrit, white_blood_cells, vgm…",
                        value=ExamTypesState.param_form.code,
                        on_change=ExamTypesState.set_param_code,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text(LanguageState.tr["computed_param_label"], size="2", weight="medium"),
                        rx.text(
                            LanguageState.tr["computed_param_desc"],
                            size="1", color="var(--gray-9)",
                        ),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.switch(
                        checked=ExamTypesState.param_form.is_computed,
                        on_change=ExamTypesState.set_param_is_computed,
                    ),
                    width="100%", align="center",
                    padding="0.5rem 0.75rem",
                    border="1px solid var(--gray-4)",
                    border_radius="var(--radius-2)",
                    background=rx.cond(
                        ExamTypesState.param_form.is_computed,
                        "var(--yellow-2)",
                        "var(--gray-1)",
                    ),
                ),
                rx.cond(
                    ExamTypesState.param_form.is_computed,
                    rx.vstack(
                        rx.hstack(
                            rx.text(LanguageState.tr["formula_required_label"], size="2", weight="medium"),
                            rx.badge(LanguageState.tr["computed_badge"], color_scheme="yellow", size="1", variant="soft"),
                            spacing="2", align="center",
                        ),
                        rx.text(
                            LanguageState.tr["formula_hint"],
                            size="1", color="var(--gray-9)",
                        ),
                        rx.text_area(
                            placeholder="ex: hematocrit * 10 / red_blood_cells",
                            value=ExamTypesState.param_form.formula,
                            on_change=ExamTypesState.set_param_formula,
                            width="100%",
                            rows="2",
                            font_family="monospace",
                        ),
                        rx.cond(
                            ExamTypesState.available_param_codes.length() > 0,
                            rx.vstack(
                                rx.text(
                                    LanguageState.tr["formula_click_to_insert"],
                                    size="1", color="var(--gray-9)",
                                ),
                                rx.flex(
                                    rx.foreach(ExamTypesState.available_param_codes, _formula_hint),
                                    flex_wrap="wrap",
                                    gap="0.3rem",
                                ),
                                spacing="1", width="100%",
                            ),
                            rx.text(
                                LanguageState.tr["no_codes_defined"],
                                size="1", color="var(--gray-8)",
                            ),
                        ),
                        spacing="2", width="100%",
                        padding="0.75rem",
                        border="1px solid var(--yellow-6)",
                        border_radius="var(--radius-2)",
                        background="var(--yellow-2)",
                    ),
                    rx.fragment(),
                ),
                rx.vstack(
                    rx.text(LanguageState.tr["unit_label"], size="2", weight="medium"),
                    rx.input(
                        placeholder="ex: g/dL, mmol/L, U/L, %…",
                        value=ExamTypesState.param_form.unit,
                        on_change=ExamTypesState.set_param_unit,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                # ── Age/sex thresholds — inline, edit mode only ───────────────
                rx.cond(
                    ExamTypesState.is_editing_param,
                    rx.vstack(
                        rx.hstack(
                            rx.icon("chart-no-axes-gantt", size=14, color="var(--violet-9)"),
                            rx.text(LanguageState.tr["age_range_manager_title"], size="2", weight="medium"),
                            rx.spacer(),
                            rx.button(
                                rx.icon("plus-circle", size=14), LanguageState.tr["add_age_range_btn"],
                                on_click=ExamTypesState.open_create_age_range,
                                size="1", variant="soft", color_scheme="violet",
                            ),
                            align="center", width="100%",
                        ),
                        rx.cond(
                            ExamTypesState.age_range_is_loading,
                            rx.center(rx.spinner(size="2"), padding="0.75rem"),
                            rx.cond(
                                ExamTypesState.age_ranges.length() == 0,
                                rx.callout.root(
                                    rx.callout.icon(rx.icon("info", size=14)),
                                    rx.callout.text(LanguageState.tr["no_age_ranges_msg"]),
                                    color_scheme="gray", variant="surface", size="1",
                                ),
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            rx.table.column_header_cell(LanguageState.tr["col_age_range"]),
                                            rx.table.column_header_cell(LanguageState.tr["gender_label"]),
                                            rx.table.column_header_cell(LanguageState.tr["col_normal_values"]),
                                            rx.table.column_header_cell(LanguageState.tr["col_critical_col"]),
                                            rx.table.column_header_cell(""),
                                        )
                                    ),
                                    rx.table.body(rx.foreach(ExamTypesState.age_ranges, _age_range_row)),
                                    width="100%", size="1",
                                ),
                            ),
                        ),
                        spacing="2", width="100%",
                        padding="0.75rem",
                        border="1px solid var(--violet-4)",
                        border_radius="var(--radius-2)",
                        background="var(--violet-1)",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.text(LanguageState.tr["required_param_label"], size="2"),
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
                overflow_y="auto",
                max_height="65vh",
                padding_right="0.25rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button(LanguageState.tr["cancel_btn"], variant="soft", color_scheme="gray",
                                          on_click=ExamTypesState.close_param_dialog)),
                rx.button(
                    rx.cond(
                        ExamTypesState.is_editing_param,
                        LanguageState.tr["save_changes_btn"],
                        LanguageState.tr["add_param_confirm_btn"],
                    ),
                    on_click=ExamTypesState.save_param,
                    loading=ExamTypesState.is_saving_param,
                ),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="700px",
        ),
        open=ExamTypesState.param_dialog_open,
        on_open_change=lambda _: ExamTypesState.close_param_dialog(),
    )


# ── Main page ─────────────────────────────────────────────────────────────────

def exam_types_tab_content() -> rx.Component:
    """Exam types content without page_layout — embeddable in a parent page (e.g. settings tab)."""
    tr = LanguageState.tr
    return rx.box(
        rx.cond(ExamTypesState.view == "list", _list_view(), _detail_view()),
        _type_dialog(),
        _param_dialog(),
        # ── Confirm archive parameter ────────────────────────────────────
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(
                    rx.hstack(rx.icon("archive", size=18, color="var(--orange-9)"),
                              rx.text(tr["archive_param_dialog_title"]), spacing="2"),
                ),
                rx.dialog.description(
                    rx.vstack(
                        rx.text(
                            "« ",
                            rx.text.strong(ExamTypesState.confirm_deactivate_param_name),
                            " " + tr["archive_param_will_be_archived"],
                            size="2",
                        ),
                        rx.text(tr["archive_param_can_reactivate"], size="2", color="var(--gray-9)"),
                        spacing="2",
                    ),
                ),
                rx.vstack(
                    rx.text(tr["archive_reason_label"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=tr["archive_reason_placeholder"],
                        value=ExamTypesState.confirm_deactivate_param_comment,
                        on_change=ExamTypesState.set_deactivate_param_comment,
                        width="100%",
                        rows="3",
                    ),
                    spacing="2", width="100%", margin_top="0.75rem",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(tr["cancel_btn"], variant="soft", color_scheme="gray",
                                  on_click=ExamTypesState.dismiss_confirm_deactivate_param),
                    ),
                    rx.button(tr["archive_btn"], color_scheme="orange",
                              on_click=ExamTypesState.confirmed_deactivate_param,
                              disabled=ExamTypesState.confirm_deactivate_param_comment.strip() == ""),
                    justify="end", spacing="2", margin_top="1rem", width="100%",
                ),
                max_width="480px",
            ),
            open=ExamTypesState.confirm_deactivate_param_open,
            on_open_change=lambda _: ExamTypesState.dismiss_confirm_deactivate_param(),
        ),
        # ── Confirm reactivate parameter ─────────────────────────────────
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(
                    rx.hstack(rx.icon("rotate-ccw", size=18, color="var(--green-9)"),
                              rx.text(tr["reactivate_param_dialog_title"]), spacing="2"),
                ),
                rx.dialog.description(
                    rx.vstack(
                        rx.text(
                            "« ",
                            rx.text.strong(ExamTypesState.confirm_reactivate_param_name),
                            " " + tr["reactivate_param_will_be"],
                            size="2",
                        ),
                        spacing="2",
                    ),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(tr["cancel_btn"], variant="soft", color_scheme="gray",
                                  on_click=ExamTypesState.dismiss_confirm_reactivate_param),
                    ),
                    rx.button(tr["reactivate_tooltip"], color_scheme="green",
                              on_click=ExamTypesState.confirmed_reactivate_param),
                    justify="end", spacing="2", margin_top="1rem", width="100%",
                ),
                max_width="440px",
            ),
            open=ExamTypesState.confirm_reactivate_param_open,
            on_open_change=lambda _: ExamTypesState.dismiss_confirm_reactivate_param(),
        ),
        # ── Confirm delete parameter ────────────────────────────────────
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(
                    rx.hstack(rx.icon("trash-2", size=18, color="var(--red-9)"),
                              rx.text(tr["delete_param_dialog_title"]), spacing="2"),
                ),
                rx.dialog.description(
                    tr["delete_param_irreversible"],
                    size="2", color="var(--gray-9)",
                ),
                rx.vstack(
                    rx.text(tr["delete_reason_label"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=tr["delete_reason_placeholder"],
                        value=ExamTypesState.confirm_delete_param_comment,
                        on_change=ExamTypesState.set_delete_param_comment,
                        width="100%",
                        rows="3",
                    ),
                    spacing="2", width="100%", margin_top="0.75rem",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(tr["cancel_btn"], variant="soft", color_scheme="gray",
                                  on_click=ExamTypesState.dismiss_confirm_delete_param),
                    ),
                    rx.button(tr["delete_btn"], color_scheme="red",
                              on_click=ExamTypesState.confirmed_delete_param,
                              disabled=ExamTypesState.confirm_delete_param_comment.strip() == ""),
                    justify="end", spacing="2", margin_top="1rem", width="100%",
                ),
                max_width="440px",
            ),
            open=ExamTypesState.confirm_delete_param_open,
            on_open_change=lambda _: ExamTypesState.dismiss_confirm_delete_param(),
        ),
        # ── Confirm archive exam type ──────────────────────────────────
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(
                    rx.hstack(rx.icon("archive", size=18, color="var(--orange-9)"),
                              rx.text(tr["archive_type_dialog_title"]), spacing="2"),
                ),
                rx.dialog.description(
                    rx.vstack(
                        rx.text(
                            "« ", rx.text.strong(ExamTypesState.confirm_deactivate_type_name),
                            " " + tr["archive_type_will_be"],
                            size="2",
                        ),
                        rx.text(tr["archive_type_existing"], size="2", color="var(--gray-9)"),
                        spacing="2",
                    ),
                ),
                rx.vstack(
                    rx.text(tr["archive_reason_label"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=tr["archive_reason_placeholder"],
                        value=ExamTypesState.confirm_deactivate_type_comment,
                        on_change=ExamTypesState.set_deactivate_type_comment,
                        width="100%",
                        rows="3",
                    ),
                    spacing="2", width="100%", margin_top="0.75rem",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(tr["cancel_btn"], variant="soft", color_scheme="gray",
                                  on_click=ExamTypesState.dismiss_confirm_deactivate_type),
                    ),
                    rx.button(tr["archive_btn"], color_scheme="orange",
                              on_click=ExamTypesState.confirmed_deactivate_type,
                              disabled=ExamTypesState.confirm_deactivate_type_comment.strip() == ""),
                    justify="end", spacing="2", margin_top="1rem", width="100%",
                ),
                max_width="480px",
            ),
            open=ExamTypesState.confirm_deactivate_type_open,
            on_open_change=lambda _: ExamTypesState.dismiss_confirm_deactivate_type(),
        ),
        # ── Confirm reactivate exam type ──────────────────────────────────────
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(
                    rx.hstack(rx.icon("check", size=18, color="var(--green-9)"),
                              rx.text(tr["reactivate_type_dialog_title"]), spacing="2"),
                ),
                rx.dialog.description(
                    rx.vstack(
                        rx.text(
                            "« ", rx.text.strong(ExamTypesState.confirm_reactivate_type_name),
                            " " + tr["reactivate_type_will_be"],
                            size="2",
                        ),
                        spacing="2",
                    ),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(tr["cancel_btn"], variant="soft", color_scheme="gray",
                                  on_click=ExamTypesState.dismiss_confirm_reactivate_type),
                    ),
                    rx.button(tr["reactivate_tooltip"], color_scheme="green",
                              on_click=ExamTypesState.confirmed_reactivate_type),
                    justify="end", spacing="2", margin_top="1rem", width="100%",
                ),
                max_width="440px",
            ),
            open=ExamTypesState.confirm_reactivate_type_open,
            on_open_change=lambda _: ExamTypesState.dismiss_confirm_reactivate_type(),
        ),
        # ── Confirm permanent delete exam type ────────────────────────────
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(
                    rx.hstack(rx.icon("trash-2", size=18, color="var(--red-9)"),
                              rx.text(tr["delete_type_dialog_title"]), spacing="2"),
                ),
                rx.dialog.description(
                    rx.vstack(
                        rx.text(
                            "« ", rx.text.strong(ExamTypesState.confirm_delete_type_name),
                            " " + tr["delete_type_will_be"],
                            size="2",
                        ),
                        rx.text(tr["delete_type_warning"], size="2", color="var(--red-9)"),
                        spacing="2",
                    ),
                ),
                rx.vstack(
                    rx.text(tr["delete_reason_label"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=tr["delete_reason_placeholder"],
                        value=ExamTypesState.confirm_delete_type_comment,
                        on_change=ExamTypesState.set_delete_type_comment,
                        width="100%",
                        rows="3",
                    ),
                    spacing="2", width="100%", margin_top="0.75rem",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(tr["cancel_btn"], variant="soft", color_scheme="gray",
                                  on_click=ExamTypesState.dismiss_confirm_delete_type),
                    ),
                    rx.button(tr["delete_permanently_btn"], color_scheme="red",
                              on_click=ExamTypesState.confirmed_delete_type,
                              disabled=ExamTypesState.confirm_delete_type_comment.strip() == ""),
                    justify="end", spacing="2", margin_top="1rem", width="100%",
                ),
                max_width="480px",
            ),
            open=ExamTypesState.confirm_delete_type_open,
            on_open_change=lambda _: ExamTypesState.dismiss_confirm_delete_type(),
        ),
        # ── Age range form/delete dialogs ────────────────────────────────
        _age_range_form_dialog(),
        _confirm_delete_age_range_dialog(),
        width="100%",
    )


# ── Age range manager components ─────────────────────────────────────────────

def _age_range_row(r: AgeRangeVM) -> rx.Component:
    tr = LanguageState.tr
    age_label = rx.cond(
        (r.age_min != "") & (r.age_max != ""),
        r.age_min + " – " + r.age_max + " " + tr["years_label"],
        rx.cond(
            r.age_min != "",
            "≥ " + r.age_min + " " + tr["years_label"],
            rx.cond(r.age_max != "", "≤ " + r.age_max + " " + tr["years_label"], tr["all_ages_label"]),
        ),
    )
    gender_label = rx.match(
        r.gender,
        ("M", rx.badge(tr["gender_male_badge"], color_scheme="blue", size="1", variant="soft")),
        ("F", rx.badge(tr["gender_female_badge"], color_scheme="pink", size="1", variant="soft")),
        rx.badge(tr["gender_all_short"], color_scheme="gray", size="1", variant="soft"),
    )
    ref_label = rx.cond(
        (r.ref_low != "") | (r.ref_high != ""),
        rx.text(
            rx.cond(r.ref_low != "", r.ref_low, "—"),
            " → ",
            rx.cond(r.ref_high != "", r.ref_high, "—"),
            size="2",
        ),
        rx.text("—", size="2", color="var(--gray-7)"),
    )
    crit_label = rx.cond(
        (r.crit_low != "") | (r.crit_high != ""),
        rx.hstack(
            rx.badge(rx.cond(r.crit_low != "", r.crit_low, "—"),
                     color_scheme="red", size="1", variant="soft"),
            rx.badge(rx.cond(r.crit_high != "", r.crit_high, "—"),
                     color_scheme="red", size="1", variant="soft"),
            spacing="1",
        ),
        rx.text("—", size="2", color="var(--gray-7)"),
    )
    return rx.table.row(
        rx.table.cell(rx.text(age_label, size="2")),
        rx.table.cell(gender_label),
        rx.table.cell(ref_label),
        rx.table.cell(crit_label),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("copy", size=14), variant="ghost", size="1", color_scheme="violet",
                        on_click=lambda: ExamTypesState.duplicate_age_range(r.id),
                    ),
                    content=tr["duplicate_gender_tooltip"],
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pen-line", size=14), variant="ghost", size="1", color_scheme="blue",
                        on_click=lambda: ExamTypesState.open_edit_age_range(r.id),
                    ),
                    content=tr["edit_tooltip"],
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("trash-2", size=14), variant="ghost", size="1", color_scheme="red",
                        on_click=lambda: ExamTypesState.open_confirm_delete_age_range(r.id),
                    ),
                    content=tr["delete_tooltip"],
                ),
                spacing="1",
            )
        ),
    )


def _age_range_manager_dialog() -> rx.Component:
    tr = LanguageState.tr
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("chart-no-axes-gantt", size=18, color="var(--violet-9)"),
                    rx.text(tr["age_range_manager_title"]),
                    spacing="2", align="center",
                )
            ),
            rx.dialog.description(
                rx.text(
                    tr["param_colon"],
                    rx.text.strong(ExamTypesState.age_range_param_name),
                    size="2", color="var(--gray-11)",
                )
            ),
            rx.cond(
                ExamTypesState.age_range_is_loading,
                rx.center(rx.spinner(size="3"), padding="2rem"),
                rx.vstack(
                    rx.cond(
                        ExamTypesState.age_ranges.length() == 0,
                        rx.callout.root(
                            rx.callout.icon(rx.icon("info", size=16)),
                            rx.callout.text(tr["no_age_ranges_msg"]),
                            color_scheme="gray", variant="surface", size="1",
                        ),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell(tr["col_age_range"]),
                                    rx.table.column_header_cell(tr["gender_label"]),
                                    rx.table.column_header_cell(tr["col_normal_values"]),
                                    rx.table.column_header_cell(tr["col_critical_col"]),
                                    rx.table.column_header_cell(""),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(ExamTypesState.age_ranges, _age_range_row)
                            ),
                            width="100%", size="1",
                        ),
                    ),
                    rx.button(
                        rx.icon("plus-circle", size=14), tr["add_age_range_btn"],
                        on_click=ExamTypesState.open_create_age_range,
                        size="2", variant="soft", color_scheme="violet",
                    ),
                    spacing="3", width="100%", align="start",
                ),
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(tr["close_btn"], variant="soft", color_scheme="gray",
                               on_click=ExamTypesState.close_age_range_manager),
                ),
                justify="end", margin_top="1rem", width="100%",
            ),
            max_width="700px",
            on_interact_outside=ExamTypesState.close_age_range_manager,
            on_escape_key_down=ExamTypesState.close_age_range_manager,
        ),
        open=ExamTypesState.age_range_manager_open,
    )


def _age_range_form_dialog() -> rx.Component:
    tr = LanguageState.tr
    is_editing = ExamTypesState.editing_age_range_id != ""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(is_editing, tr["edit_age_range_title"], tr["new_age_range_title"])
            ),
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(tr["age_min_label"], size="2", weight="medium"),
                        rx.input(
                            placeholder="ex: 0",
                            value=ExamTypesState.age_range_form.age_min,
                            on_change=ExamTypesState.set_age_range_age_min,
                            type="number", size="2", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text(tr["age_max_label"], size="2", weight="medium"),
                        rx.input(
                            placeholder="ex: 17",
                            value=ExamTypesState.age_range_form.age_max,
                            on_change=ExamTypesState.set_age_range_age_max,
                            type="number", size="2", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text(tr["gender_label"], size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(width="100%"),
                            rx.select.content(
                                rx.select.item(tr["gender_all_short"], value="ALL"),
                                rx.select.item(tr["gender_male_badge"], value="M"),
                                rx.select.item(tr["gender_female_badge"], value="F"),
                            ),
                            value=ExamTypesState.age_range_form.gender,
                            on_change=ExamTypesState.set_age_range_gender,
                            size="2", width="100%",
                        ),
                        spacing="1", width="120px",
                    ),
                    spacing="3", width="100%", align="end",
                ),
                rx.separator(width="100%"),
                rx.text(tr["ref_thresholds_label"], size="2", weight="medium", color="var(--gray-11)"),
                rx.hstack(
                    rx.vstack(
                        rx.text(tr["normal_low_label"], size="2"),
                        rx.input(
                            placeholder="—",
                            value=ExamTypesState.age_range_form.ref_low,
                            on_change=ExamTypesState.set_age_range_ref_low,
                            size="2", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text(tr["normal_high_label"], size="2"),
                        rx.input(
                            placeholder="—",
                            value=ExamTypesState.age_range_form.ref_high,
                            on_change=ExamTypesState.set_age_range_ref_high,
                            size="2", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text(tr["critical_low_label"], size="2"),
                        rx.input(
                            placeholder="—",
                            value=ExamTypesState.age_range_form.crit_low,
                            on_change=ExamTypesState.set_age_range_crit_low,
                            size="2", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text(tr["critical_high_label"], size="2"),
                        rx.input(
                            placeholder="—",
                            value=ExamTypesState.age_range_form.crit_high,
                            on_change=ExamTypesState.set_age_range_crit_high,
                            size="2", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                rx.separator(width="100%"),
                rx.text(tr["interp_labels_optional"], size="2", weight="medium", color="var(--gray-11)"),
                rx.hstack(
                    rx.vstack(
                        rx.text(tr["label_critical_low_badge"], size="2"),
                        rx.input(
                            placeholder=tr["label_critical_low_placeholder"],
                            value=ExamTypesState.age_range_form.label_crit_low,
                            on_change=ExamTypesState.set_age_range_label_crit_low,
                            size="2", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text(tr["label_low"], size="2"),
                        rx.input(
                            placeholder=tr["label_low_placeholder"],
                            value=ExamTypesState.age_range_form.label_low,
                            on_change=ExamTypesState.set_age_range_label_low,
                            size="2", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text(tr["label_normal"], size="2"),
                        rx.input(
                            placeholder=tr["label_normal_placeholder"],
                            value=ExamTypesState.age_range_form.label_normal,
                            on_change=ExamTypesState.set_age_range_label_normal,
                            size="2", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text(tr["label_high_form"], size="2"),
                        rx.input(
                            placeholder=tr["label_high_placeholder"],
                            value=ExamTypesState.age_range_form.label_high,
                            on_change=ExamTypesState.set_age_range_label_high,
                            size="2", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text(tr["label_critical_high_badge"], size="2"),
                        rx.input(
                            placeholder=tr["label_critical_high_placeholder"],
                            value=ExamTypesState.age_range_form.label_crit_high,
                            on_change=ExamTypesState.set_age_range_label_crit_high,
                            size="2", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                rx.cond(
                    ExamTypesState.age_range_form_error != "",
                    rx.callout.root(
                        rx.callout.icon(rx.icon("triangle-alert", size=16)),
                        rx.callout.text(ExamTypesState.age_range_form_error),
                        color_scheme="red", variant="surface", size="1",
                    ),
                    rx.fragment(),
                ),
                spacing="3", width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(tr["cancel_btn"], variant="soft", color_scheme="gray",
                               on_click=ExamTypesState.close_age_range_form),
                ),
                rx.button(
                    rx.cond(ExamTypesState.is_saving_age_range, rx.spinner(size="2"), rx.fragment()),
                    rx.cond(is_editing, tr["save_btn"], tr["add_btn"]),
                    on_click=ExamTypesState.save_age_range,
                    disabled=ExamTypesState.is_saving_age_range,
                    color_scheme="violet",
                ),
                justify="end", spacing="2", margin_top="1rem", width="100%",
            ),
            max_width="600px",
            on_interact_outside=ExamTypesState.close_age_range_form,
            on_escape_key_down=ExamTypesState.close_age_range_form,
        ),
        open=ExamTypesState.age_range_form_open,
    )


def _confirm_delete_age_range_dialog() -> rx.Component:
    tr = LanguageState.tr
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(tr["delete_age_range_title"]),
            rx.alert_dialog.description(tr["delete_age_range_desc"], size="2"),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(tr["cancel_btn"], variant="soft", color_scheme="gray",
                               on_click=ExamTypesState.close_confirm_delete_age_range),
                ),
                rx.alert_dialog.action(
                    rx.button(tr["delete_btn"], color_scheme="red",
                               on_click=ExamTypesState.delete_age_range),
                ),
                justify="end", spacing="2", margin_top="1rem", width="100%",
            ),
            max_width="400px",
        ),
        open=ExamTypesState.confirm_delete_age_range_open,
    )


def exam_types_page() -> rx.Component:
    return main_component(page_layout(exam_types_tab_content()))
