"""UI component for the correction requests page."""

import reflex as rx

from ..common.page_layout import page_layout
from .corrections_state import CorrectionRowDTO, CorrectionsState


def _status_badge(row: CorrectionRowDTO) -> rx.Component:
    return rx.badge(row.status_label, color_scheme=row.status_color, variant="soft", size="1")


def _review_btn(row: CorrectionRowDTO) -> rx.Component:
    return rx.cond(
        row.status == "PENDING",
        rx.tooltip(
            rx.icon_button(
                rx.icon("check-circle", size=14),
                variant="soft", size="1", color_scheme="blue",
                on_click=CorrectionsState.open_review_dialog(row.id),
            ),
            content="Review this request",
        ),
        rx.fragment(),
    )


def _correction_row(row: CorrectionRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(rx.cond(row.created_at != "", row.created_at[:10], "—"), size="2")),
        rx.table.cell(
            rx.cond(
                row.patient_name != "",
                rx.vstack(
                    rx.link(
                        row.patient_name,
                        href=rx.cond(row.patient_id != "", f"/patient/{row.patient_id}", "#"),
                        size="2",
                        color="var(--accent-9)",
                    ),
                    rx.cond(
                        row.campaign_name != "",
                        rx.text(row.campaign_name, size="1", color="var(--gray-9)"),
                        rx.fragment(),
                    ),
                    spacing="0",
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(
            rx.badge(row.field_name, color_scheme="gray", variant="outline", size="1")
        ),
        rx.table.cell(
            rx.vstack(
                rx.hstack(
                    rx.text("Before:", size="1", color="var(--gray-9)"),
                    rx.text(row.old_value, size="2", color="var(--red-11)"),
                    spacing="1",
                ),
                rx.hstack(
                    rx.text("After:", size="1", color="var(--gray-9)"),
                    rx.text(row.new_value, size="2", color="var(--green-11)"),
                    spacing="1",
                ),
                spacing="1",
            )
        ),
        rx.table.cell(
            rx.text(
                row.reason,
                size="2",
                max_width="200px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            )
        ),
        rx.table.cell(_status_badge(row)),
        rx.table.cell(rx.text(row.requested_by_name, size="2")),
        rx.table.cell(_review_btn(row)),
        _hover={"background": "var(--gray-2)"},
    )


def _corrections_table() -> rx.Component:
    return rx.cond(
        CorrectionsState.rows.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Date"),
                    rx.table.column_header_cell("Patient / Campaign"),
                    rx.table.column_header_cell("Field"),
                    rx.table.column_header_cell("Values"),
                    rx.table.column_header_cell("Reason"),
                    rx.table.column_header_cell("Status"),
                    rx.table.column_header_cell("Requested by"),
                    rx.table.column_header_cell(""),
                )
            ),
            rx.table.body(
                rx.foreach(CorrectionsState.rows, _correction_row)
            ),
            width="100%",
            variant="surface",
            size="2",
        ),
        rx.center(
            rx.vstack(
                rx.icon("pencil-ruler", size=40, color="var(--gray-7)"),
                rx.text("No correction request", size="3", color="var(--gray-9)"),
                rx.text(
                    "Validated data correction requests will appear here.",
                    size="2", color="var(--gray-7)", text_align="center",
                ),
                align="center", spacing="2",
            ),
            padding="4rem",
        ),
    )


def _review_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Review correction request"),
            rx.vstack(
                rx.text("Decision *", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(width="100%"),
                    rx.select.content(
                        rx.select.item("Accept correction", value="ACCEPTED"),
                        rx.select.item("Refuse correction", value="REFUSED"),
                        rx.select.item("Apply and close", value="APPLIED"),
                    ),
                    value=CorrectionsState.review_decision,
                    on_change=CorrectionsState.set_review_decision,
                    width="100%",
                ),
                rx.text("Comment (optional)", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Reason for your decision...",
                    value=CorrectionsState.review_reason_text,
                    on_change=CorrectionsState.set_review_reason,
                    width="100%",
                    rows="3",
                ),
                spacing="3", width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancel", variant="soft", color_scheme="gray"),
                ),
                rx.button(
                    "Submit decision",
                    on_click=CorrectionsState.submit_review,
                    color_scheme="blue",
                ),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="480px",
        ),
        open=CorrectionsState.review_dialog_open,
        on_open_change=lambda _: CorrectionsState.close_review_dialog(),
    )


def _filter_btn(label: str, value: str) -> rx.Component:
    is_active = CorrectionsState.status_filter == value
    return rx.button(
        label,
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=rx.cond(is_active, "blue", "gray"),
        size="2",
        on_click=CorrectionsState.set_status_filter(value),
    )


def corrections_page() -> rx.Component:
    return page_layout(
        _review_dialog(),
        rx.hstack(
            rx.hstack(
                rx.icon("pencil-ruler", size=22, color="var(--accent-9)"),
                rx.heading("Correction requests", size="6"),
                spacing="2", align="center",
            ),
            rx.spacer(),
            rx.badge(
                CorrectionsState.total_count.to(str),
                " result(s)",
                color_scheme="gray", variant="soft", size="2",
            ),
            width="100%", align="center",
        ),
        rx.hstack(
            rx.debounce_input(
                rx.input(
                    placeholder="Search patient, field, reason...",
                    value=CorrectionsState.search_query,
                    on_change=CorrectionsState.set_search,
                    width="280px",
                    size="2",
                ),
                debounce_timeout=350,
            ),
            rx.separator(orientation="vertical", height="28px"),
            _filter_btn("Pending", "PENDING"),
            _filter_btn("Accepted", "ACCEPTED"),
            _filter_btn("Refused", "REFUSED"),
            _filter_btn("Applied", "APPLIED"),
            _filter_btn("All", "ALL"),
            spacing="2", align="center", flex_wrap="wrap",
        ),
        rx.cond(
            CorrectionsState.error_message != "",
            rx.callout(
                CorrectionsState.error_message,
                icon="triangle-alert",
                color_scheme="red", variant="soft",
            ),
            rx.fragment(),
        ),
        rx.cond(
            CorrectionsState.is_loading,
            rx.center(rx.spinner(size="3"), padding="2rem"),
            _corrections_table(),
        ),
        # Pagination controls
        rx.cond(
            CorrectionsState.total_count > 0,
            rx.hstack(
                rx.text(
                    CorrectionsState.total_count.to(str)
                    + " correction(s) — page "
                    + CorrectionsState.page.to(str)
                    + " / "
                    + CorrectionsState.total_pages.to(str),
                    size="2",
                    color="var(--gray-9)",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("chevron-left", size=14),
                    on_click=CorrectionsState.prev_page,
                    variant="soft",
                    size="2",
                    disabled=~CorrectionsState.has_prev_page,
                ),
                rx.button(
                    rx.icon("chevron-right", size=14),
                    on_click=CorrectionsState.next_page,
                    variant="soft",
                    size="2",
                    disabled=~CorrectionsState.has_next_page,
                ),
                width="100%",
                align="center",
            ),
            rx.fragment(),
        ),
    )
