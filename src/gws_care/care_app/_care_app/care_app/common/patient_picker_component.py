"""Reusable patient-picker component (filter bar + table)."""

import reflex as rx

from .language_state import LanguageState
from .patient_picker_state import PatientPickerRowDTO, PatientPickerState


def _gender_badge(gender: str) -> rx.Component:
    return rx.match(
        gender,
        ("M", rx.badge("M", color_scheme="blue", variant="soft", size="1")),
        ("F", rx.badge("F", color_scheme="pink", variant="soft", size="1")),
        rx.badge(gender, color_scheme="gray", variant="soft", size="1"),
    )


def patient_picker_widget(state: type[PatientPickerState] = PatientPickerState) -> rx.Component:
    """Render the picker filter bar + table.

    Pass the specific state subclass (e.g. ``VisitListState``) to ensure the
    correct ``picker_select_patient`` override is invoked on row click.

    The caller is responsible for reading ``state.picker_selected_id``
    and ``state.picker_selected_label`` to know what was chosen.
    """

    def _row(patient: PatientPickerRowDTO) -> rx.Component:
        is_selected = state.picker_selected_id == patient.id
        return rx.table.row(
            rx.table.cell(
                rx.text(patient.patient_number, size="2", weight="medium")
            ),
            rx.table.cell(
                rx.text(patient.last_name + " " + patient.first_name, size="2")
            ),
            rx.table.cell(rx.text(patient.date_of_birth, size="2")),
            rx.table.cell(_gender_badge(patient.gender)),
            rx.table.cell(
                rx.cond(
                    patient.account_name != "",
                    rx.text(patient.account_name, size="2"),
                    rx.text("—", color="var(--gray-8)", size="2"),
                )
            ),
            style=rx.cond(
                is_selected,
                {"background_color": "var(--accent-3)", "cursor": "pointer"},
                {"cursor": "pointer"},
            ),
            _hover={"background_color": "var(--accent-2)"},
            on_click=lambda: state.picker_select_patient(
                patient.id,
                patient.last_name + " " + patient.first_name + " (" + patient.patient_number + ")",
            ),
        )

    return rx.vstack(
        # Filter bar
        rx.hstack(
            rx.input(
                placeholder=LanguageState.tr["search_patient_number"],
                value=state.picker_filter_number,
                on_change=state.picker_set_filter_number,
                size="2",
                min_width="160px",
                flex="1",
            ),
            rx.input(
                placeholder=LanguageState.tr["search_name_placeholder"],
                value=state.picker_filter_name,
                on_change=state.picker_set_filter_name,
                size="2",
                min_width="180px",
                flex="2",
            ),
            rx.button(
                rx.icon("x", size=14),
                on_click=state.picker_clear_filters,
                variant="ghost",
                size="2",
                color_scheme="gray",
                title="Clear filters",
            ),
            spacing="2",
            width="100%",
            align="center",
        ),
        # Error
        rx.cond(
            state.picker_error != "",
            rx.callout(
                state.picker_error,
                icon="triangle-alert",
                color_scheme="red",
                size="1",
            ),
        ),
        # Table
        rx.cond(
            state.picker_is_loading,
            rx.center(rx.spinner(size="2"), padding="1.5rem"),
            rx.cond(
                state.picker_patients.length() > 0,
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(
                                    rx.text(LanguageState.tr["col_patient_number"], size="1")
                                ),
                                rx.table.column_header_cell(
                                    rx.text(LanguageState.tr["col_name"], size="1")
                                ),
                                rx.table.column_header_cell(
                                    rx.text(LanguageState.tr["col_dob"], size="1")
                                ),
                                rx.table.column_header_cell(
                                    rx.text(LanguageState.tr["col_gender"], size="1")
                                ),
                                rx.table.column_header_cell(
                                    rx.text(LanguageState.tr["col_account"], size="1")
                                ),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(state.picker_patients, _row)
                        ),
                        width="100%",
                        size="1",
                        variant="surface",
                    ),
                    max_height="280px",
                    overflow_y="auto",
                    width="100%",
                    border_radius="var(--radius-2)",
                ),
                rx.center(
                    rx.text(
                        LanguageState.tr["no_patients_found"],
                        size="2",
                        color="var(--gray-9)",
                    ),
                    padding="1.5rem",
                ),
            ),
        ),
        # Selected confirmation banner
        rx.cond(
            state.picker_selected_id != "",
            rx.hstack(
                rx.icon("check-circle", size=16, color="var(--green-9)"),
                rx.text(
                    state.picker_selected_label,
                    size="2",
                    color="var(--green-11)",
                    weight="medium",
                ),
                spacing="2",
                align="center",
                padding="0.4rem 0.6rem",
                border="1px solid var(--green-6)",
                border_radius="var(--radius-2)",
                background="var(--green-2)",
                width="100%",
            ),
        ),
        spacing="2",
        width="100%",
    )


def patient_picker_dialog(state: type[PatientPickerState] = PatientPickerState) -> rx.Component:
    """Render the patient picker as a dialog for *state*.

    Must be placed somewhere in the page component.
    Open it by calling ``state.open_patient_picker``.
    Selecting a row closes the dialog and sets ``picker_selected_id`` /
    ``picker_selected_label`` on *state*.
    """

    def _row(patient: PatientPickerRowDTO) -> rx.Component:
        return rx.table.row(
            rx.table.cell(rx.text(patient.patient_number, size="2", weight="medium")),
            rx.table.cell(rx.text(patient.last_name + " " + patient.first_name, size="2")),
            rx.table.cell(rx.text(patient.date_of_birth, size="2")),
            rx.table.cell(_gender_badge(patient.gender)),
            rx.table.cell(
                rx.cond(
                    patient.account_name != "",
                    rx.text(patient.account_name, size="2"),
                    rx.text("—", color="var(--gray-8)", size="2"),
                )
            ),
            _hover={"background_color": "var(--accent-2)", "cursor": "pointer"},
            on_click=lambda: state.picker_select_patient(
                patient.id,
                patient.last_name + " " + patient.first_name + " (" + patient.patient_number + ")",
            ),
        )

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["select_patient_picker_btn"]),
            rx.vstack(
                # Filters
                rx.hstack(
                    rx.input(
                        rx.input.slot(rx.icon("search", size=14)),
                        placeholder=LanguageState.tr["search_patient_number"],
                        value=state.picker_filter_number,
                        on_change=state.picker_set_filter_number,
                        size="2",
                        flex="1",
                    ),
                    rx.input(
                        placeholder=LanguageState.tr["search_name_placeholder"],
                        value=state.picker_filter_name,
                        on_change=state.picker_set_filter_name,
                        size="2",
                        flex="2",
                    ),
                    rx.icon_button(
                        rx.icon("x", size=14),
                        on_click=state.picker_clear_filters,
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                        title="Clear filters",
                    ),
                    spacing="2",
                    width="100%",
                    align="center",
                ),
                # Error
                rx.cond(
                    state.picker_error != "",
                    rx.callout(state.picker_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                # Table
                rx.cond(
                    state.picker_is_loading,
                    rx.center(rx.spinner(size="2"), padding="1.5rem"),
                    rx.cond(
                        state.picker_patients.length() > 0,
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell(LanguageState.tr["col_patient_number"]),
                                        rx.table.column_header_cell(LanguageState.tr["col_name"]),
                                        rx.table.column_header_cell(LanguageState.tr["col_dob"]),
                                        rx.table.column_header_cell(LanguageState.tr["col_gender"]),
                                        rx.table.column_header_cell(LanguageState.tr["col_account"]),
                                    )
                                ),
                                rx.table.body(rx.foreach(state.picker_patients, _row)),
                                width="100%",
                                size="1",
                                variant="surface",
                            ),
                            max_height="320px",
                            overflow_y="auto",
                            width="100%",
                        ),
                        rx.center(
                            rx.text(LanguageState.tr["no_patients_found"], size="2", color="var(--gray-9)"),
                            padding="1.5rem",
                        ),
                    ),
                ),
                # Footer
                rx.hstack(
                    rx.button(
                        LanguageState.tr["cancel_btn"],
                        variant="soft",
                        color_scheme="gray",
                        on_click=state.close_patient_picker,
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            on_interact_outside=state.close_patient_picker,
            on_escape_key_down=state.close_patient_picker,
            max_width="680px",
        ),
        open=state.picker_is_open,
    )


def patient_picker_button(state: type[PatientPickerState] = PatientPickerState) -> rx.Component:
    """A button that shows the selected patient (or a placeholder) and opens the picker.

    Pass the consuming state class so the correct substate vars are used.
    When a patient is selected, also renders an × button to clear it.
    """
    return rx.hstack(
        rx.button(
            rx.icon("user", size=14),
            rx.cond(
                state.picker_selected_id != "",
                rx.text(state.picker_selected_label, size="2"),
                rx.text(LanguageState.tr["select_patient_picker_btn"], size="2"),
            ),
            on_click=state.open_patient_picker,
            variant=rx.cond(
                state.picker_selected_id != "",
                "soft",
                "outline",
            ),
            color_scheme=rx.cond(
                state.picker_selected_id != "",
                "accent",
                "gray",
            ),
            size="2",
        ),
        rx.cond(
            state.picker_selected_id != "",
            rx.icon_button(
                rx.icon("x", size=13),
                on_click=state.picker_clear_selection,
                variant="ghost",
                color_scheme="gray",
                size="2",
                title=LanguageState.tr["acct_picker_clear_tooltip"],
            ),
        ),
        spacing="1",
        align="center",
    )
