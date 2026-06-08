"""Exam create form dialog component."""

import reflex as rx
from gws_reflex_base import form_dialog_component

from ..common.language_state import LanguageState
from .exam_form_state import ExamFormState

_EXAM_TYPE_OPTIONS = [
    ("biology", "Biology"),
    ("radiology", "Radiology"),
    ("ophthalmology", "Ophthalmology"),
    ("orl", "ORL"),
    ("ecg", "ECG"),
    ("spirometry", "Spirometry"),
    ("clinical", "Clinical Exam"),
    ("hormones", "Hormones"),
    ("hematology", "Hematology"),
    ("bacteriology", "Bacteriology"),
    ("parasitology", "Parasitology"),
    ("drug_test", "Drug Test"),
    ("immunology", "Immunology"),
    ("hepatic_markers", "Hepatic Markers"),
    ("other", "Other"),
]


def _field(label, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        label if not isinstance(label, str) else rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
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
        _field(
            LanguageState.tr["field_exam_type_required"],
            rx.select.root(
                rx.select.trigger(width="100%"),
                rx.select.content(
                    *[rx.select.item(label, value=value) for value, label in _EXAM_TYPE_OPTIONS],
                ),
                value=ExamFormState.form_exam_type,
                on_change=ExamFormState.set_form_exam_type,
                size="2",
                width="100%",
            ),
        ),
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
