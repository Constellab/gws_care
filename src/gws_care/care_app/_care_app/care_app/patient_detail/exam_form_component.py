"""Exam create form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from ..common.language_state import LanguageState
from .exam_form_state import ExamFormState, ExamParamOption, ExamTypeRefOption


def _field(label, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        label if not isinstance(label, str) else rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _exam_type_option(opt: ExamTypeRefOption) -> rx.Component:
    return rx.select.item(opt.name, value=opt.id)


def _exam_type_selector() -> rx.Component:
    return rx.vstack(
        rx.text(LanguageState.tr["field_exam_type_required"], size="2", weight="medium"),
        rx.cond(
            ExamFormState.is_loading_exam_types,
            rx.hstack(
                rx.spinner(size="1"),
                rx.text("Chargement du référentiel…", size="2", color="var(--gray-9)"),
                spacing="2",
                align="center",
            ),
            rx.cond(
                ExamFormState.exam_type_ref_options.length() > 0,
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Sélectionner un type d'examen…",
                        width="100%",
                    ),
                    rx.select.content(
                        rx.foreach(ExamFormState.exam_type_ref_options, _exam_type_option),
                    ),
                    value=ExamFormState.form_exam_type_ref_id,
                    on_change=ExamFormState.select_exam_type_ref,
                    size="2",
                    width="100%",
                ),
                rx.callout(
                    "Aucun type d'examen disponible. Veuillez d'abord en créer dans l'onglet Référentiel des examens.",
                    icon="info",
                    color_scheme="orange",
                    size="1",
                ),
            ),
        ),
        width="100%",
        spacing="1",
    )


def _param_item(param: ExamParamOption) -> rx.Component:
    return rx.flex(
        # Custom checkbox visual
        rx.cond(
            param.is_selected,
            rx.box(
                rx.icon("check", size=11, color="white"),
                width="18px",
                min_width="18px",
                height="18px",
                border_radius="3px",
                background="var(--accent-9)",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.box(
                width="18px",
                min_width="18px",
                height="18px",
                border_radius="3px",
                border="2px solid var(--gray-6)",
                background="white",
            ),
        ),
        # Test info
        rx.flex(
            rx.hstack(
                rx.text(param.name, size="2", weight=rx.cond(param.is_selected, "medium", "regular")),
                rx.cond(
                    param.is_required,
                    rx.badge("Requis", size="1", color_scheme="red", variant="soft"),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
                flex_wrap="wrap",
            ),
            rx.cond(
                param.unit != "",
                rx.text(param.unit, size="1", color="var(--gray-9)"),
                rx.fragment(),
            ),
            direction="column",
            gap="0",
        ),
        rx.spacer(),
        # Selected tick indicator
        rx.cond(
            param.is_selected,
            rx.icon("check-circle", size=14, color="var(--green-9)"),
            rx.fragment(),
        ),
        align="center",
        gap="3",
        padding="0.5rem 0.75rem",
        border_radius="var(--radius-2)",
        background=rx.cond(param.is_selected, "var(--accent-2)", "transparent"),
        border=rx.cond(
            param.is_selected,
            "1px solid var(--accent-6)",
            "1px solid var(--gray-4)",
        ),
        width="100%",
        cursor="pointer",
        on_click=ExamFormState.toggle_param(param.id),
        _hover={
            "background": rx.cond(param.is_selected, "var(--accent-3)", "var(--gray-2)"),
        },
    )


def _params_section() -> rx.Component:
    return rx.cond(
        ExamFormState.form_exam_type_ref_id != "",
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("flask-conical", size=14, color="var(--accent-9)"),
                    rx.text("Tests inclus", size="2", weight="bold", color="var(--gray-11)"),
                    spacing="1",
                    align="center",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.text(
                        ExamFormState.selected_param_count.to(str),
                        " / ",
                        ExamFormState.available_params.length().to(str),
                        " sélectionné(s)",
                        size="1",
                        color="var(--gray-9)",
                    ),
                    rx.button(
                        "Tout cocher",
                        on_click=ExamFormState.select_all_params,
                        variant="ghost",
                        size="1",
                        type="button",
                    ),
                    rx.button(
                        "Tout décocher",
                        on_click=ExamFormState.clear_all_params,
                        variant="ghost",
                        size="1",
                        type="button",
                        color_scheme="gray",
                    ),
                    spacing="2",
                    align="center",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                ExamFormState.available_params.length() > 0,
                rx.vstack(
                    rx.foreach(ExamFormState.available_params, _param_item),
                    spacing="1",
                    width="100%",
                    max_height="260px",
                    overflow_y="auto",
                    padding="0.25rem",
                    border="1px solid var(--gray-4)",
                    border_radius="var(--radius-2)",
                    background="var(--gray-1)",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("info", size=20, color="var(--gray-6)"),
                        rx.text(
                            "Aucun test défini pour ce type d'examen.",
                            size="2",
                            color="var(--gray-9)",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    padding="1.5rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="var(--radius-2)",
                    width="100%",
                ),
            ),
            width="100%",
            spacing="2",
        ),
        rx.fragment(),
    )


def _form_fields() -> rx.Component:
    return rx.vstack(
        _field(
            LanguageState.tr["field_exam_date"],
            rx.input(
                value=ExamFormState.form_exam_date,
                on_change=ExamFormState.set_form_exam_date,
                type="date",
                size="2",
                width="100%",
            ),
        ),
        _exam_type_selector(),
        _params_section(),
        width="100%",
        spacing="4",
    )


def exam_form_dialog() -> rx.Component:
    """Render the create exam dialog (must be placed in the component tree)."""
    return form_dialog_component(
        state=ExamFormState,
        title=LanguageState.tr["new_exam_form_title"],
        form_content=_form_fields(),
    )
