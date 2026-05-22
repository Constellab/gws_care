"""Bulk import dialog component for patients and accounts."""

import reflex as rx

from ..common.language_state import LanguageState
from .import_state import ImportRowResultDTO, ImportState

# ── Sub-components ─────────────────────────────────────────────────────────────

def _header_cell(text: str) -> rx.Component:
    return rx.table.column_header_cell(rx.text(text, size="2"))


def _cell_text(text: str) -> rx.Component:
    return rx.table.cell(rx.text(text, size="2"))


def _preview_row(row: ImportRowResultDTO) -> rx.Component:
    """Render one preview row with background colour based on status."""
    return rx.table.row(
        rx.foreach(row.cells, _cell_text),
        style={
            "background_color": rx.cond(
                row.status == "error",
                "var(--red-2)",
                rx.cond(row.status == "success", "var(--green-2)", "transparent"),
            )
        },
    )


def _format_requirements() -> rx.Component:
    """Show column requirements specific to the current import type."""
    return rx.cond(
        ImportState.import_type == "patients",
        rx.callout(
            rx.vstack(
                rx.text("Required columns:", size="2", weight="medium"),
                rx.code(
                    "last_name, first_name, date_of_birth (YYYY-MM-DD), gender (M / F / Other)",
                    size="1",
                ),
                rx.text("Optional columns:", size="2", weight="medium"),
                rx.code(
                    "birth_name, address, postal_code, city, phone, email, "
                    "primary_physician_name, primary_physician_phone, account_name, "
                    "social_security_number, weight (kg), height (cm)",
                    size="1",
                ),
                spacing="2",
                align_items="start",
            ),
            color_scheme="blue",
            icon="info",
            size="1",
        ),
        rx.callout(
            rx.vstack(
                rx.text("Required columns:", size="2", weight="medium"),
                rx.code("name", size="1"),
                rx.text("Optional columns:", size="2", weight="medium"),
                rx.code(
                    "registration_number, address, postal_code, city, phone, email, contact_name",
                    size="1",
                ),
                spacing="2",
                align_items="start",
            ),
            color_scheme="blue",
            icon="info",
            size="1",
        ),
    )


def _upload_zone() -> rx.Component:
    return rx.upload(
        rx.vstack(
            rx.cond(
                ImportState.is_parsing,
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text("Parsing CSV…", size="2", color="var(--gray-9)"),
                    spacing="2",
                    align="center",
                ),
                rx.vstack(
                    rx.icon("file-up", size=24, color="var(--gray-7)"),
                    rx.text(
                        "Drop CSV file here or click to browse",
                        size="2",
                        color="var(--gray-7)",
                    ),
                    align="center",
                    spacing="1",
                ),
            ),
            align="center",
            justify="center",
            width="100%",
            height="90px",
        ),
        id="bulk_import_csv",
        multiple=False,
        accept={"text/csv": [".csv"], "text/plain": [".csv", ".txt"]},
        on_drop=ImportState.handle_csv_upload(
            rx.upload_files(upload_id="bulk_import_csv")
        ),
        border="2px dashed var(--gray-5)",
        border_radius="8px",
        padding="0.75rem",
        width="100%",
        cursor="pointer",
        _hover={"border_color": "var(--accent-8)", "background": "var(--gray-1)"},
    )


def _preview_table() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                "Preview — ",
                rx.badge(ImportState.valid_row_count, color_scheme="green", size="1"),
                rx.text(" ready, ", size="2", color="var(--gray-9)", display="inline"),
                rx.badge(
                    ImportState.preview_rows.length() - ImportState.valid_row_count,
                    color_scheme="red",
                    size="1",
                ),
                rx.text(" with errors", size="2", color="var(--gray-9)", display="inline"),
                size="2",
                weight="medium",
            ),
            width="100%",
        ),
        rx.scroll_area(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.foreach(ImportState.preview_headers, _header_cell),
                    )
                ),
                rx.table.body(
                    rx.foreach(ImportState.preview_rows, _preview_row),
                ),
                width="100%",
                variant="surface",
                size="1",
            ),
            max_height="300px",
            width="100%",
        ),
        width="100%",
        spacing="2",
    )


def _import_summary() -> rx.Component:
    return rx.cond(
        ImportState.error_count > 0,
        rx.callout(
            rx.hstack(
                rx.text("Imported", size="2"),
                rx.badge(ImportState.success_count, color_scheme="green"),
                rx.text("rows —", size="2"),
                rx.badge(ImportState.error_count, color_scheme="red"),
                rx.text("failed.", size="2"),
                rx.text(
                    "Rows with errors are highlighted in red.",
                    size="2",
                    color="var(--gray-9)",
                ),
                spacing="2",
                align="center",
                wrap="wrap",
            ),
            color_scheme="orange",
            icon="triangle-alert",
        ),
        rx.callout(
            rx.hstack(
                rx.text("Successfully imported", size="2"),
                rx.badge(ImportState.success_count, color_scheme="green"),
                rx.text("rows.", size="2"),
                spacing="2",
                align="center",
            ),
            color_scheme="green",
            icon="circle-check",
        ),
    )


# ── Main dialog ───────────────────────────────────────────────────────────────

def import_dialog() -> rx.Component:
    """Controlled dialog for bulk CSV import (patients or accounts)."""
    return rx.dialog.root(
        rx.dialog.content(
            # Title
            rx.dialog.title(
                rx.cond(
                    ImportState.import_type == "patients",
                    "Import Patients from CSV",
                    "Import Accounts from CSV",
                )
            ),
            rx.dialog.description(
                rx.cond(
                    ImportState.import_type == "patients",
                    "Upload a CSV file to create multiple patient records at once.",
                    "Upload a CSV file to create multiple billing accounts at once.",
                ),
                size="2",
                margin_bottom="0.5rem",
                color="var(--gray-10)",
            ),

            # Body
            rx.vstack(
                # Format requirements + template download
                rx.hstack(
                    rx.box(_format_requirements(), flex="1"),
                    rx.button(
                        rx.icon("download", size=14),
                        "Template",
                        on_click=ImportState.download_template,
                        variant="outline",
                        color_scheme="gray",
                        size="2",
                        flex_shrink="0",
                    ),
                    width="100%",
                    align="start",
                    spacing="3",
                ),

                # Upload zone
                _upload_zone(),

                # Parse error
                rx.cond(
                    ImportState.parse_error != "",
                    rx.callout(
                        ImportState.parse_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),

                # Preview table (shown once CSV is parsed)
                rx.cond(ImportState.has_preview, _preview_table()),

                # Import result summary
                rx.cond(ImportState.import_done, _import_summary()),

                width="100%",
                spacing="4",
            ),

            # Footer buttons
            rx.hstack(
                rx.button(
                    "Close",
                    on_click=ImportState.close_import_dialog,
                    variant="soft",
                    color_scheme="gray",
                    size="2",
                ),
                rx.spacer(),
                # Re-upload button after a completed import
                rx.cond(
                    ImportState.import_done,
                    rx.button(
                        rx.icon("rotate-ccw", size=14),
                        "Import another file",
                        on_click=ImportState.open_import_dialog(ImportState.import_type),
                        variant="outline",
                        color_scheme="blue",
                        size="2",
                    ),
                    # Import button (only while not done)
                    rx.button(
                        rx.cond(
                            ImportState.is_importing,
                            rx.hstack(
                                rx.spinner(size="2"),
                                rx.text(LanguageState.tr["importing_text"]),
                                spacing="2",
                                align="center",
                            ),
                            rx.hstack(
                                rx.icon("upload", size=14),
                                rx.text(LanguageState.tr["import_btn"]),
                                rx.badge(
                                    ImportState.valid_row_count,
                                    color_scheme="blue",
                                    variant="soft",
                                    size="1",
                                ),
                                rx.text(LanguageState.tr["rows_suffix"]),
                                spacing="2",
                                align="center",
                            ),
                        ),
                        on_click=ImportState.start_import,
                        disabled=~ImportState.can_import,
                        color_scheme="blue",
                        size="2",
                    ),
                ),
                width="100%",
                padding_top="1rem",
                align="center",
            ),

            on_interact_outside=ImportState.close_import_dialog,
            on_escape_key_down=ImportState.close_import_dialog,
            max_width="860px",
            width="95vw",
        ),
        open=ImportState.import_dialog_open,
    )
