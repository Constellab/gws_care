"""Prescription form dialog component."""

import reflex as rx

from ..common.language_state import LanguageState
from .patient_detail_state import DrugLineDTO, PatientDetailState

_DOSAGE_UNITS = ["mg", "g", "µg", "ml", "IU", "drops", "tablet(s)", "packet(s)", "vial(s)"]
_FREQUENCY_UNITS = ["times/day", "times/week", "times/month", "in the morning", "in the evening", "morning and evening", "as needed"]
_DURATION_UNITS = ["days", "weeks", "months", "until improvement"]


def _unit_select(
    options: list[str],
    value: rx.Var,
    on_change,
) -> rx.Component:
    return rx.select.root(
        rx.select.trigger(width="100%"),
        rx.select.content(
            *[rx.select.item(u, value=u) for u in options],
        ),
        value=value,
        on_change=on_change,
        size="1",
        width="100%",
    )


def _drug_row(drug: DrugLineDTO, index: int) -> rx.Component:
    """One row of the drug lines form — name + dosage/unit + freq/unit + dur/unit + delete."""
    return rx.vstack(
        # Row 1: Médicament
        rx.hstack(
            rx.icon("pill", size=13, color="var(--gray-9)"),
            rx.input(
                placeholder=LanguageState.tr["prescription_drug_name"],
                value=drug.name,
                on_change=lambda v: PatientDetailState.prescription_set_drug_name(index, v),
                size="2",
                flex="1",
            ),
            rx.icon_button(
                rx.icon("trash-2", size=13),
                on_click=lambda: PatientDetailState.prescription_remove_drug(index),
                variant="ghost",
                color_scheme="red",
                size="2",
                flex_shrink="0",
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        # Row 2: Posologie + Fréquence + Durée avec unités
        rx.grid(
            # Posologie
            rx.vstack(
                rx.text(LanguageState.tr["prescription_drug_dosage"], size="1", color="var(--gray-9)"),
                rx.hstack(
                    rx.input(
                        placeholder="ex: 500",
                        value=drug.dosage,
                        on_change=lambda v: PatientDetailState.prescription_set_drug_dosage(index, v),
                        size="2",
                        flex="1",
                    ),
                    _unit_select(
                        _DOSAGE_UNITS,
                        drug.dosage_unit,
                        lambda v: PatientDetailState.prescription_set_drug_dosage_unit(index, v),
                    ),
                    spacing="1",
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            # Fréquence
            rx.vstack(
                rx.text(LanguageState.tr["prescription_drug_frequency"], size="1", color="var(--gray-9)"),
                rx.hstack(
                    rx.input(
                        placeholder="ex: 3",
                        value=drug.frequency,
                        on_change=lambda v: PatientDetailState.prescription_set_drug_frequency(index, v),
                        size="2",
                        flex="1",
                        max_width="60px",
                    ),
                    _unit_select(
                        _FREQUENCY_UNITS,
                        drug.frequency_unit,
                        lambda v: PatientDetailState.prescription_set_drug_frequency_unit(index, v),
                    ),
                    spacing="1",
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            # Durée
            rx.vstack(
                rx.text(LanguageState.tr["prescription_drug_duration"], size="1", color="var(--gray-9)"),
                rx.hstack(
                    rx.input(
                        placeholder="ex: 7",
                        value=drug.duration,
                        on_change=lambda v: PatientDetailState.prescription_set_drug_duration(index, v),
                        size="2",
                        flex="1",
                        max_width="60px",
                    ),
                    _unit_select(
                        _DURATION_UNITS,
                        drug.duration_unit,
                        lambda v: PatientDetailState.prescription_set_drug_duration_unit(index, v),
                    ),
                    spacing="1",
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            columns="3",
            spacing="2",
            width="100%",
        ),
        padding="0.6rem 0.75rem",
        border="1px solid var(--gray-4)",
        border_radius="var(--radius-2)",
        background="var(--gray-1)",
        width="100%",
        spacing="2",
    )


def prescription_form_dialog() -> rx.Component:
    """Dialog for creating a new prescription."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["new_prescription_title"]),
            rx.dialog.description(LanguageState.tr["new_prescription_desc"]),
            rx.vstack(
                # Error callout
                rx.cond(
                    PatientDetailState.prescription_form_error != "",
                    rx.callout(
                        PatientDetailState.prescription_form_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                # Date
                rx.vstack(
                    rx.text(LanguageState.tr["prescription_date_label"], size="2", weight="medium"),
                    rx.input(
                        type="date",
                        value=PatientDetailState.prescription_form_date,
                        on_change=PatientDetailState.set_prescription_form_date,
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Diagnosis
                rx.vstack(
                    rx.text(LanguageState.tr["prescription_diagnosis_label"], size="2", weight="medium"),
                    rx.input(
                        placeholder=LanguageState.tr["prescription_diagnosis_placeholder"],
                        value=PatientDetailState.prescription_form_diagnosis,
                        on_change=PatientDetailState.set_prescription_form_diagnosis,
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Drug lines header
                rx.hstack(
                    rx.text(LanguageState.tr["prescription_drugs_label"], size="2", weight="medium"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=13),
                        LanguageState.tr["prescription_add_drug_btn"],
                        on_click=PatientDetailState.prescription_add_drug,
                        variant="ghost",
                        size="1",
                    ),
                    width="100%",
                    align="center",
                ),
                # Drug rows (each drug card includes dosage + freq + duration with units)
                rx.vstack(
                    rx.foreach(
                        PatientDetailState.prescription_form_drugs,
                        lambda drug, i: _drug_row(drug, i),
                    ),
                    spacing="2",
                    width="100%",
                ),
                # Instructions
                rx.vstack(
                    rx.text(LanguageState.tr["prescription_instructions_label"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=LanguageState.tr["prescription_instructions_placeholder"],
                        value=PatientDetailState.prescription_form_instructions,
                        on_change=PatientDetailState.set_prescription_form_instructions,
                        rows="3",
                        width="100%",
                        size="2",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Footer buttons
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        on_click=PatientDetailState.close_prescription_dialog,
                        variant="soft",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.button(
                        rx.cond(
                            PatientDetailState.is_saving_prescription,
                            rx.spinner(size="2"),
                            rx.icon("file-text", size=14),
                        ),
                        LanguageState.tr["save_prescription_btn"],
                        on_click=PatientDetailState.save_prescription,
                        loading=PatientDetailState.is_saving_prescription,
                        size="2",
                    ),
                    spacing="2",
                    width="100%",
                    padding_top="0.75rem",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="820px",
            on_interact_outside=PatientDetailState.close_prescription_dialog,
            on_escape_key_down=PatientDetailState.close_prescription_dialog,
        ),
        open=PatientDetailState.show_prescription_dialog,
    )
