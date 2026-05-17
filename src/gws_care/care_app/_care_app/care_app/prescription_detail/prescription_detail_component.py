"""Prescription detail page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .prescription_detail_state import DrugLineDTO, PrescriptionDetailDTO, PrescriptionDetailState


def _drug_row(drug: DrugLineDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(drug.name, size="2", weight="medium")),
        rx.table.cell(rx.text(drug.dosage, size="2")),
        rx.table.cell(rx.text(drug.frequency, size="2")),
        rx.table.cell(rx.text(drug.duration, size="2")),
    )


def _info_row(label: str, value: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="2", weight="medium", color="var(--gray-9)", min_width="180px", flex_shrink="0"),
        rx.cond(
            value != "",
            rx.text(value, size="2"),
            rx.text("—", size="2", color="var(--gray-7)"),
        ),
        spacing="4",
        align="start",
        padding_y="0.3rem",
        width="100%",
    )


def prescription_detail_page() -> rx.Component:
    return main_component(
        page_layout(
            # ── Header ──────────────────────────────────────────────────────
            rx.hstack(
                rx.icon_button(
                    rx.icon("arrow-left", size=16),
                    on_click=PrescriptionDetailState.go_back_to_patient,
                    variant="ghost",
                    size="2",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.heading(
                            rx.cond(
                                PrescriptionDetailState.prescription,
                                LanguageState.tr["prescription_detail_title"],
                                "Ordonnance",
                            ),
                            size="5",
                        ),
                        rx.cond(
                            PrescriptionDetailState.prescription & PrescriptionDetailState.prescription.is_archived,
                            rx.badge(
                                LanguageState.tr["archived_badge"],
                                color_scheme="gray",
                                variant="soft",
                                size="2",
                            ),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.cond(
                        PrescriptionDetailState.prescription,
                        rx.text(
                            PrescriptionDetailState.prescription.patient_name,
                            size="2",
                            color="var(--gray-9)",
                        ),
                    ),
                    spacing="0",
                ),
                rx.spacer(),
                # Action buttons
                rx.hstack(
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("plane", size=16),
                            on_click=PrescriptionDetailState.send_pdf_email,
                            loading=PrescriptionDetailState.is_sending_email,
                            variant="outline",
                            size="2",
                        ),
                        content=LanguageState.tr["send_pdf_email_btn"],
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("eye", size=16),
                            on_click=PrescriptionDetailState.view_pdf,
                            variant="outline",
                            size="2",
                        ),
                        content=LanguageState.tr["view_pdf_btn"],
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("download", size=16),
                            on_click=PrescriptionDetailState.download_pdf,
                            variant="outline",
                            size="2",
                        ),
                        content=LanguageState.tr["download_pdf_btn"],
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon(
                                rx.cond(
                                    PrescriptionDetailState.prescription & PrescriptionDetailState.prescription.is_archived,
                                    "archive-restore",
                                    "archive",
                                ),
                                size=16,
                            ),
                            on_click=PrescriptionDetailState.toggle_archive,
                            loading=PrescriptionDetailState.is_archiving,
                            variant="outline",
                            color_scheme=rx.cond(
                                PrescriptionDetailState.prescription & PrescriptionDetailState.prescription.is_archived,
                                "accent",
                                "gray",
                            ),
                            size="2",
                        ),
                        content=rx.cond(
                            PrescriptionDetailState.prescription & PrescriptionDetailState.prescription.is_archived,
                            LanguageState.tr["unarchive_btn"],
                            LanguageState.tr["archive_btn"],
                        ),
                    ),
                    spacing="2",
                ),
                width="100%",
                align="center",
                padding_bottom="1rem",
            ),

            # ── Error ────────────────────────────────────────────────────────
            rx.cond(
                PrescriptionDetailState.error_message != "",
                rx.callout(
                    PrescriptionDetailState.error_message,
                    color_scheme="red",
                    size="2",
                    icon="triangle-alert",
                    margin_bottom="1rem",
                ),
            ),

            # ── Loading ──────────────────────────────────────────────────────
            rx.cond(
                PrescriptionDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    PrescriptionDetailState.prescription,
                    # ── Content ──────────────────────────────────────────────
                    rx.vstack(
                        # Patient / prescription metadata card
                        rx.card(
                            rx.vstack(
                                rx.text(
                                    LanguageState.tr["prescription_info_section"],
                                    size="2",
                                    weight="bold",
                                    color="var(--gray-11)",
                                    margin_bottom="0.5rem",
                                ),
                                _info_row(
                                    LanguageState.tr["prescription_date_label"],
                                    PrescriptionDetailState.prescription.prescription_date,
                                ),
                                _info_row(
                                    LanguageState.tr["field_patient"],
                                    PrescriptionDetailState.prescription.patient_name,
                                ),
                                _info_row(
                                    LanguageState.tr["col_patient_number"],
                                    PrescriptionDetailState.prescription.patient_number,
                                ),
                                _info_row(
                                    LanguageState.tr["col_date_of_birth"],
                                    PrescriptionDetailState.prescription.patient_date_of_birth,
                                ),
                                _info_row(
                                    LanguageState.tr["col_prescribed_by"],
                                    PrescriptionDetailState.prescription.prescribed_by_name,
                                ),
                                rx.cond(
                                    PrescriptionDetailState.prescription.diagnosis != "",
                                    _info_row(
                                        LanguageState.tr["prescription_diagnosis_label"],
                                        PrescriptionDetailState.prescription.diagnosis,
                                    ),
                                ),
                                width="100%",
                                spacing="0",
                            ),
                            width="100%",
                        ),

                        # Drugs table
                        rx.card(
                            rx.vstack(
                                rx.text(
                                    LanguageState.tr["prescription_drugs_section"],
                                    size="2",
                                    weight="bold",
                                    color="var(--gray-11)",
                                    margin_bottom="0.5rem",
                                ),
                                rx.cond(
                                    PrescriptionDetailState.prescription.drugs,
                                    rx.table.root(
                                        rx.table.header(
                                            rx.table.row(
                                                rx.table.column_header_cell(LanguageState.tr["prescription_drug_name"]),
                                                rx.table.column_header_cell(LanguageState.tr["prescription_drug_dosage"]),
                                                rx.table.column_header_cell(LanguageState.tr["prescription_drug_frequency"]),
                                                rx.table.column_header_cell(LanguageState.tr["prescription_drug_duration"]),
                                            )
                                        ),
                                        rx.table.body(
                                            rx.foreach(PrescriptionDetailState.prescription.drugs, _drug_row),
                                        ),
                                        variant="surface",
                                        width="100%",
                                    ),
                                    rx.text("—", size="2", color="var(--gray-7)"),
                                ),
                                width="100%",
                                spacing="2",
                            ),
                            width="100%",
                        ),

                        # Instructions card
                        rx.cond(
                            PrescriptionDetailState.prescription.instructions != "",
                            rx.card(
                                rx.vstack(
                                    rx.text(
                                        LanguageState.tr["prescription_instructions_label"],
                                        size="2",
                                        weight="bold",
                                        color="var(--gray-11)",
                                        margin_bottom="0.5rem",
                                    ),
                                    rx.text(
                                        PrescriptionDetailState.prescription.instructions,
                                        size="2",
                                        white_space="pre-wrap",
                                    ),
                                    width="100%",
                                    spacing="1",
                                ),
                                width="100%",
                            ),
                        ),

                        width="100%",
                        spacing="4",
                    ),
                    # No prescription found
                    rx.center(
                        rx.vstack(
                            rx.icon("file-x", size=40, color="var(--gray-6)"),
                            rx.text("Ordonnance introuvable.", color="var(--gray-8)", size="2"),
                            align="center",
                            spacing="2",
                        ),
                        padding="3rem",
                    ),
                ),
            ),
        )
    )
