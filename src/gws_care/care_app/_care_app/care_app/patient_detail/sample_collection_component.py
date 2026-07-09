"""Sample collection component — tube generation, label printing, status tracking."""
from __future__ import annotations

import reflex as rx

from ..common.language_state import LanguageState
from .sample_collection_state import SAMPLE_TYPE_OPTIONS, SampleCollectionState, TubeRowDTO


# ── Helpers ───────────────────────────────────────────────────────────────────

def _status_badge(tube: TubeRowDTO) -> rx.Component:
    return rx.badge(
        tube.status_label,
        color_scheme=tube.status_color,
        size="1",
        variant="soft",
    )


def _print_label_script(short_id: str, exam_label: str, sample_type: str) -> str:
    """Return a JS snippet that opens a printable label in a new window."""
    return f"""
(function() {{
    var w = window.open('', '_blank', 'width=400,height=300');
    w.document.write(`
<!DOCTYPE html>
<html>
<head>
<style>
  @page {{ size: 60mm 30mm; margin: 0; }}
  body {{ font-family: monospace; padding: 4px; font-size: 10px; }}
  .big {{ font-size: 22px; font-weight: bold; letter-spacing: 4px; text-align: center; margin: 4px 0; }}
  .line {{ text-align: center; font-size: 9px; color: #333; }}
  @media screen {{ body {{ padding: 16px; }} }}
</style>
</head>
<body>
  <div class="big">{short_id}</div>
  <div class="line">{exam_label}</div>
  <div class="line">{sample_type}</div>
  <script>window.onload = function() {{ window.print(); }};</script>
</body>
</html>`);
    w.document.close();
}})();
"""


def _tube_row(t: TubeRowDTO) -> rx.Component:
    """One row in the tubes table."""
    return rx.table.row(
        # Short ID + print button
        rx.table.cell(
            rx.hstack(
                rx.text(t.short_id, size="2", weight="bold", font_family="monospace"),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("printer", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="gray",
                        on_click=rx.call_script(
                            rx.Var.create(f"(function(){{ var t = '{t.short_id}'; var e = '{t.exam_type_label}'; var s = '{t.sample_type}'; ") +
                            """var w=window.open('','_blank','width=420,height=280');
w.document.write('<!DOCTYPE html><html><head><style>@page{size:60mm 30mm;margin:0}body{font-family:monospace;padding:4px;font-size:10px}.big{font-size:22px;font-weight:bold;letter-spacing:4px;text-align:center;margin:4px 0}.line{text-align:center;font-size:9px;color:#333}</style></head><body><div class=\"big\">'+t+'</div><div class=\"line\">'+e+'</div><div class=\"line\">'+s+'</div><scr'+'ipt>window.onload=function(){window.print();}<\\/scr'+'ipt></body></html>');
w.document.close(); })();"""
                        ),
                    ),
                    content="Print label",
                ),
                spacing="1",
                align="center",
            )
        ),
        # Status
        rx.table.cell(_status_badge(t)),
        # Exam type
        rx.table.cell(rx.text(t.exam_type_label, size="2")),
        # Sample type
        rx.table.cell(rx.text(t.sample_type, size="2")),
        # Volume
        rx.table.cell(
            rx.cond(
                t.volume_ml != "",
                rx.text(t.volume_ml + " mL", size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        # Campaign (only shown out-of-campaign context)
        rx.table.cell(
            rx.cond(
                t.campaign_name != "",
                rx.text(t.campaign_name, size="1", color="var(--gray-8)"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        # Collected at
        rx.table.cell(
            rx.cond(
                t.collected_at != "",
                rx.text(t.collected_at, size="1", color="var(--green-9)"),
                rx.cond(
                    t.associated_at != "",
                    rx.text(t.associated_at, size="1", color="var(--gray-7)"),
                    rx.text("—", size="2", color="var(--gray-7)"),
                ),
            )
        ),
        # Actions
        rx.table.cell(
            rx.hstack(
                # Mark collected button — only when ASSOCIATED
                rx.cond(
                    t.status == "ASSOCIATED",
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("check-circle", size=14),
                            variant="soft",
                            size="1",
                            color_scheme="green",
                            on_click=SampleCollectionState.mark_collected(t.id),
                        ),
                        content="Mark as collected",
                    ),
                    rx.fragment(),
                ),
                # Cancel button — only when not COLLECTED or CANCELLED
                rx.cond(
                    (t.status == "ASSOCIATED") | (t.status == "BLANK"),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("x-circle", size=14),
                            variant="soft",
                            size="1",
                            color_scheme="red",
                            on_click=SampleCollectionState.open_cancel_dialog(t.id),
                        ),
                        content="Cancel this tube",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
            )
        ),
        align="center",
    )


def _create_dialog() -> rx.Component:
    """Dialog to generate a new tube for a patient."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("New sample"),
            rx.dialog.description(
                "Generate a tube barcode and enter the sample information.",
                size="2",
                color="var(--gray-9)",
                margin_bottom="1rem",
            ),

            rx.vstack(
                # Exam type
                rx.vstack(
                    rx.text(LanguageState.tr["exam_type_required_label"], size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder=LanguageState.tr["select_exam_placeholder"], width="100%"),
                        rx.select.content(
                            rx.foreach(
                                SampleCollectionState.exam_type_options,
                                lambda o: rx.select.item(
                                    o.name + " (" + o.category_label + ")", value=o.id
                                ),
                            )
                        ),
                        value=SampleCollectionState.create_exam_type_id,
                        on_change=SampleCollectionState.set_create_exam_type_id,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),

                # Sample type
                rx.vstack(
                    rx.text(LanguageState.tr["sample_type_required_label"], size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder=LanguageState.tr["sample_nature_placeholder"], width="100%"),
                        rx.select.content(
                            *[
                                rx.select.item(label, value=value)
                                for value, label in SAMPLE_TYPE_OPTIONS
                            ]
                        ),
                        value=SampleCollectionState.create_sample_type,
                        on_change=SampleCollectionState.set_create_sample_type,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),

                # Volume
                rx.vstack(
                    rx.text(LanguageState.tr["collected_volume_label"], size="2", weight="medium"),
                    rx.input(
                        placeholder="E.g. 5",
                        type="number",
                        value=SampleCollectionState.create_volume_ml,
                        on_change=SampleCollectionState.set_create_volume_ml,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),

                # Notes
                rx.vstack(
                    rx.text(LanguageState.tr["collector_notes_label"], size="2", weight="medium"),
                    rx.text_area(
                        placeholder=LanguageState.tr["puncture_note_placeholder"],
                        value=SampleCollectionState.create_notes,
                        on_change=SampleCollectionState.set_create_notes,
                        rows="3",
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),

                # Error
                rx.cond(
                    SampleCollectionState.create_error != "",
                    rx.callout(
                        SampleCollectionState.create_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),

                spacing="4", width="100%",
            ),

            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=SampleCollectionState.close_create_dialog,
                    )
                ),
                rx.button(
                    rx.cond(
                        SampleCollectionState.is_creating,
                        rx.spinner(size="2"),
                        rx.icon("tag", size=14),
                    ),
                    "Generate label",
                    on_click=SampleCollectionState.submit_create,
                    disabled=SampleCollectionState.is_creating,
                    color_scheme="blue",
                ),
                justify="end",
                spacing="3",
                margin_top="1rem",
            ),
            max_width="500px",
        ),
        open=SampleCollectionState.show_create_dialog,
        on_open_change=SampleCollectionState.close_create_dialog,
    )


def _cancel_dialog() -> rx.Component:
    """Confirmation dialog for tube cancellation."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Cancel this tube", color_scheme="red"),
            rx.vstack(
                rx.text(LanguageState.tr["cancellation_reason_label"], size="2", weight="medium"),
                rx.text_area(
                    placeholder=LanguageState.tr["hemolysis_reason_placeholder"],
                    value=SampleCollectionState.cancel_reason,
                    on_change=SampleCollectionState.set_cancel_reason,
                    rows="3",
                    width="100%",
                ),
                rx.cond(
                    SampleCollectionState.cancel_error != "",
                    rx.callout(
                        SampleCollectionState.cancel_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                spacing="3", width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Back",
                        variant="soft",
                        color_scheme="gray",
                        on_click=SampleCollectionState.close_cancel_dialog,
                    )
                ),
                rx.button(
                    "Confirm cancellation",
                    on_click=SampleCollectionState.confirm_cancel,
                    color_scheme="red",
                ),
                justify="end",
                spacing="3",
                margin_top="1rem",
            ),
            max_width="420px",
        ),
        open=SampleCollectionState.show_cancel_dialog,
        on_open_change=SampleCollectionState.close_cancel_dialog,
    )


def sample_collection_panel(show_campaign_column: bool = True) -> rx.Component:
    """Full sample-collection panel — embed in patient detail or campaign-patient page."""
    return rx.vstack(
        _create_dialog(),
        _cancel_dialog(),

        # Header
        rx.hstack(
            rx.hstack(
                rx.icon("flask-conical", size=18, color="var(--accent-9)"),
                rx.heading(LanguageState.tr["section_samples"], size="4"),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                "New tube",
                size="2",
                variant="soft",
                on_click=SampleCollectionState.open_create_dialog(""),
            ),
            width="100%",
            align="center",
        ),

        # Error banner
        rx.cond(
            SampleCollectionState.tubes_error != "",
            rx.callout(
                SampleCollectionState.tubes_error,
                icon="triangle-alert",
                color_scheme="red",
                size="1",
            ),
        ),

        # Loading / empty / table
        rx.cond(
            SampleCollectionState.is_loading_tubes,
            rx.center(rx.spinner(size="2"), padding="2rem"),
            rx.cond(
                SampleCollectionState.tubes.length() > 0,
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Tube code"),
                                rx.table.column_header_cell("Status"),
                                rx.table.column_header_cell("Exam"),
                                rx.table.column_header_cell("Sample"),
                                rx.table.column_header_cell("Volume"),
                                rx.table.column_header_cell("Campaign"),
                                rx.table.column_header_cell("Date"),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(SampleCollectionState.tubes, _tube_row)
                        ),
                        width="100%",
                        size="2",
                    ),
                    overflow_x="auto",
                    width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("flask-conical", size=32, color="var(--gray-6)"),
                        rx.text(
                            "No sample recorded for this patient.",
                            size="2",
                            color="var(--gray-7)",
                        ),
                        rx.text(
                            "Click on 'New tube' to generate a tube barcode.",
                            size="1",
                            color="var(--gray-6)",
                        ),
                        align="center",
                        spacing="2",
                    ),
                    padding="2rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="8px",
                    width="100%",
                ),
            ),
        ),

        width="100%",
        spacing="3",
        padding="1.25rem",
        border="1px solid var(--blue-5)",
        border_radius="8px",
        background="var(--blue-1)",
    )
