"""Consultation creation dialog component."""

import reflex as rx

from ..common.language_state import LanguageState
from .consultation_form_state import AccountOption, ConsultationFormState, ExamTypeCheckOption, ParamCheckOption


def _field(label: str, control: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        control,
        spacing="1",
        width="100%",
    )


def _param_check_row(type_id: str):
    """Factory — returns a foreach-compatible renderer for one param row."""
    def _render(p: ParamCheckOption) -> rx.Component:
        return rx.hstack(
            rx.checkbox(
                checked=p.is_selected,
                on_change=lambda _: ConsultationFormState.toggle_param(type_id, p.id),
                size="1",
            ),
            rx.text(p.name, size="2", flex="1"),
            rx.cond(
                p.unit != "",
                rx.text(p.unit, size="1", color="var(--gray-8)"),
                rx.fragment(),
            ),
            spacing="2",
            align="center",
            padding_y="0.15rem",
            cursor="pointer",
            on_click=lambda: ConsultationFormState.toggle_param(type_id, p.id),
            _hover={"background": "var(--gray-3)", "border_radius": "4px"},
        )
    return _render


def _exam_type_pill(opt: ExamTypeCheckOption) -> rx.Component:
    """Clickable pill for one exam type; expands to show parameter checkboxes when selected."""
    selected_count = rx.Var.create(0)  # placeholder — computed below via rx.cond chain
    return rx.box(
        rx.vstack(
            # ── Header row (always visible) ───────────────────────────────
            rx.hstack(
                rx.cond(
                    opt.is_selected,
                    rx.icon("check-square", size=14, color="var(--accent-9)"),
                    rx.icon("square", size=14, color="var(--gray-6)"),
                ),
                rx.vstack(
                    rx.text(opt.name, size="2", weight=rx.cond(opt.is_selected, "medium", "regular")),
                    rx.text(opt.category_label, size="1", color="var(--gray-8)"),
                    spacing="0",
                    flex="1",
                ),
                rx.cond(
                    opt.is_selected & opt.params,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon(
                                rx.cond(opt.params_expanded, "chevron-up", "chevron-down"),
                                size=13,
                            ),
                            variant="ghost",
                            size="1",
                            color_scheme="gray",
                            on_click=lambda: ConsultationFormState.toggle_params_expanded(opt.id),
                        ),
                        content="Choisir les tests",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
                width="100%",
                on_click=lambda: ConsultationFormState.toggle_exam_type(opt.id),
                cursor="pointer",
            ),
            # ── Parameter list (visible only when selected + expanded) ────
            rx.cond(
                opt.is_selected & opt.params_expanded & opt.params,
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.text(LanguageState.tr["tests_to_perform_label"], size="1", weight="medium", color="var(--gray-10)"),
                            rx.spacer(),
                            rx.button(
                                "Tout cocher",
                                size="1",
                                variant="ghost",
                                color_scheme="blue",
                                on_click=lambda: ConsultationFormState.select_all_params(opt.id),
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.foreach(opt.params, _param_check_row(opt.id)),
                        spacing="1",
                        width="100%",
                    ),
                    padding="0.5rem",
                    border_top="1px solid var(--accent-5)",
                    margin_top="0.25rem",
                    width="100%",
                ),
                rx.fragment(),
            ),
            spacing="1",
            width="100%",
        ),
        padding="0.5rem 0.75rem",
        border_radius="8px",
        border=rx.cond(
            opt.is_selected,
            "2px solid var(--accent-8)",
            "1px solid var(--gray-5)",
        ),
        background=rx.cond(
            opt.is_selected,
            "var(--accent-2)",
            "var(--gray-1)",
        ),
        transition="all 0.12s",
        width="100%",
    )


def _account_option(opt: AccountOption) -> rx.Component:
    return rx.select.item(opt.name, value=opt.id)


def _biometrics_grid() -> rx.Component:
    return rx.grid(
        _field(
            "Poids (kg)",
            rx.input(
                placeholder="70",
                value=ConsultationFormState.form_weight,
                on_change=ConsultationFormState.set_form_weight,
                on_blur=ConsultationFormState.set_form_height(ConsultationFormState.form_height),
                size="2", type="number", width="100%",
            ),
        ),
        _field(
            "Taille (cm)",
            rx.input(
                placeholder="175",
                value=ConsultationFormState.form_height,
                on_change=ConsultationFormState.set_form_height,
                size="2", type="number", width="100%",
            ),
        ),
        _field(
            "IMC",
            rx.input(
                placeholder="auto",
                value=ConsultationFormState.form_bmi,
                on_change=ConsultationFormState.set_form_bmi,
                size="2", type="number", width="100%",
            ),
        ),
        _field(
            "Tension artérielle",
            rx.input(
                placeholder="120/80",
                value=ConsultationFormState.form_bp,
                on_change=ConsultationFormState.set_form_bp,
                size="2", width="100%",
            ),
        ),
        _field(
            "FC (bpm)",
            rx.input(
                placeholder="75",
                value=ConsultationFormState.form_hr,
                on_change=ConsultationFormState.set_form_hr,
                size="2", type="number", width="100%",
            ),
        ),
        _field(
            "Température (°C)",
            rx.input(
                placeholder="37.0",
                value=ConsultationFormState.form_temp,
                on_change=ConsultationFormState.set_form_temp,
                size="2", type="number", width="100%",
            ),
        ),
        columns="3",
        spacing="3",
        width="100%",
    )


def consultation_form_dialog() -> rx.Component:
    """Dialog for creating a new consultation with N ordered exams."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("stethoscope", size=18, color="var(--blue-9)"),
                    rx.text(LanguageState.tr["new_consultation_btn"]),
                    spacing="2",
                    align="center",
                )
            ),
            rx.scroll_area(
                rx.vstack(
                    # ── Date + Compte ────────────────────────────────────────
                    rx.grid(
                        _field(
                            "Date de consultation *",
                            rx.input(
                                type="date",
                                value=ConsultationFormState.form_date,
                                on_change=ConsultationFormState.set_form_date,
                                size="2",
                                width="100%",
                            ),
                        ),
                        _field(
                            "Compte de facturation",
                            rx.select.root(
                                rx.select.trigger(placeholder="Aucun", size="2", width="100%"),
                                rx.select.content(
                                    rx.select.item("Aucun", value="NONE"),
                                    rx.foreach(ConsultationFormState.account_options, _account_option),
                                ),
                                value=ConsultationFormState.form_account_id,
                                on_change=ConsultationFormState.set_form_account,
                                size="2",
                            ),
                        ),
                        columns="2",
                        spacing="3",
                        width="100%",
                    ),
                    rx.separator(size="4"),
                    # ── Contexte clinique ────────────────────────────────────
                    rx.hstack(
                        rx.icon("clipboard-list", size=15, color="var(--gray-9)"),
                        rx.text(LanguageState.tr["clinical_context_label"], size="3", weight="medium"),
                        spacing="2",
                        align="center",
                    ),
                    _field(
                        "Motif de la consultation",
                        rx.text_area(
                            placeholder="Motif de la visite…",
                            value=ConsultationFormState.form_reason,
                            on_change=ConsultationFormState.set_form_reason,
                            size="2",
                            rows="2",
                            width="100%",
                        ),
                    ),
                    _field(
                        "Antécédents médicaux",
                        rx.text_area(
                            placeholder="Antécédents, traitements en cours…",
                            value=ConsultationFormState.form_history,
                            on_change=ConsultationFormState.set_form_history,
                            size="2",
                            rows="2",
                            width="100%",
                        ),
                    ),
                    rx.text(LanguageState.tr["biometrics_section"], size="2", weight="medium"),
                    _biometrics_grid(),
                    _field(
                        "Conclusion / Impression clinique (optionnel)",
                        rx.text_area(
                            placeholder=LanguageState.tr["general_impression_placeholder"],
                            value=ConsultationFormState.form_conclusion,
                            on_change=ConsultationFormState.set_form_conclusion,
                            size="2",
                            rows="2",
                            width="100%",
                        ),
                    ),
                    rx.separator(size="4"),
                    # ── Examens à prescrire ──────────────────────────────────
                    rx.hstack(
                        rx.icon("flask-conical", size=15, color="var(--blue-9)"),
                        rx.text(LanguageState.tr["exams_to_prescribe_label"], size="3", weight="medium"),
                        rx.text("*", size="3", color="var(--red-9)"),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "Sélectionnez les examens à réaliser lors de cette consultation.",
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.vstack(
                        rx.foreach(ConsultationFormState.exam_type_options, _exam_type_pill),
                        spacing="2",
                        width="100%",
                    ),
                    # ── Error ────────────────────────────────────────────────
                    rx.cond(
                        ConsultationFormState.error != "",
                        rx.callout(
                            ConsultationFormState.error,
                            icon="triangle-alert",
                            color_scheme="red",
                            size="1",
                        ),
                    ),
                    spacing="4",
                    width="100%",
                    padding_right="0.5rem",
                ),
                type="auto",
                scrollbars="vertical",
                style={"max_height": "70vh"},
            ),
            # ── Actions ──────────────────────────────────────────────────────
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Annuler",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ConsultationFormState.close_dialog,
                    )
                ),
                rx.spacer(),
                rx.button(
                    rx.cond(
                        ConsultationFormState.is_saving,
                        rx.spinner(size="2"),
                        rx.icon("plus", size=14),
                    ),
                    "Créer la consultation",
                    on_click=ConsultationFormState.submit,
                    disabled=ConsultationFormState.is_saving,
                    color_scheme="blue",
                ),
                width="100%",
                margin_top="1rem",
            ),
            max_width="680px",
            width="95vw",
        ),
        open=ConsultationFormState.dialog_open,
        on_open_change=lambda _: ConsultationFormState.close_dialog(),
    )
