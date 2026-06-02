"""Messaging page component — doctor ↔ patient direct messaging."""

import reflex as rx

from ..common.page_layout import page_layout
from .messaging_state import MessageDTO, MessagingState, ThreadRowDTO


# ── Thread list ───────────────────────────────────────────────────────────────

def _thread_row(t: ThreadRowDTO) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon("user-circle", size=32, color="var(--gray-9)"),
                flex_shrink="0",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text(t.patient_name, size="2", weight="medium"),
                    rx.spacer(),
                    rx.text(t.last_message_at, size="1", color="var(--gray-9)"),
                    width="100%",
                    align="center",
                ),
                rx.hstack(
                    rx.text(
                        t.last_message,
                        size="1",
                        color="var(--gray-9)",
                        flex="1",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                    ),
                    rx.cond(
                        t.unread_count > 0,
                        rx.badge(
                            t.unread_count.to_string(),
                            color_scheme="red",
                            variant="solid",
                            size="1",
                            radius="full",
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    align="center",
                ),
                spacing="1",
                flex="1",
                overflow="hidden",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        padding="0.75rem 1rem",
        border_bottom="1px solid var(--gray-4)",
        cursor="pointer",
        _hover={"background": "var(--gray-2)"},
        on_click=MessagingState.open_thread(t.patient_id),
        background=rx.cond(
            MessagingState.active_patient_id == t.patient_id,
            "var(--accent-2)",
            "transparent",
        ),
    )


def _thread_list_panel() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Messages", size="4"),
            rx.spacer(),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("refresh-cw", size=14),
                    variant="ghost",
                    size="1",
                    color_scheme="gray",
                    on_click=MessagingState.refresh,
                ),
                content="Actualiser les messages",
            ),
            width="100%",
            padding="1rem",
            align="center",
            border_bottom="1px solid var(--gray-4)",
        ),
        rx.cond(
            MessagingState.threads.length() > 0,
            rx.vstack(
                rx.foreach(MessagingState.threads, _thread_row),
                spacing="0",
                width="100%",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("message-circle", size=36, color="var(--gray-6)"),
                    rx.text("Aucune conversation", size="2", color="var(--gray-9)"),
                    align="center",
                    spacing="2",
                ),
                flex="1",
                padding="2rem",
            ),
        ),
        width="300px",
        min_width="300px",
        height="100%",
        border_right="1px solid var(--gray-4)",
        overflow_y="auto",
        spacing="0",
        flex_shrink="0",
    )


# ── Conversation ──────────────────────────────────────────────────────────────

def _message_bubble(msg: MessageDTO) -> rx.Component:
    is_mine = MessagingState.my_role == msg.sender_role

    bubble_bg = rx.cond(is_mine, "var(--accent-9)", "var(--gray-3)")
    bubble_color = rx.cond(is_mine, "white", "var(--gray-12)")
    align_side = rx.cond(is_mine, "flex-end", "flex-start")

    return rx.box(
        rx.vstack(
            rx.cond(
                ~is_mine,
                rx.text(msg.sender_name, size="1", color="var(--gray-9)", weight="medium"),
                rx.fragment(),
            ),
            rx.box(
                rx.text(msg.content, size="2", color=bubble_color),
                background=bubble_bg,
                border_radius=rx.cond(is_mine, "12px 12px 2px 12px", "12px 12px 12px 2px"),
                padding="0.5rem 0.75rem",
                max_width="480px",
            ),
            rx.text(msg.sent_at, size="1", color="var(--gray-7)"),
            spacing="1",
            align_items=align_side,
        ),
        width="100%",
        display="flex",
        justify_content=align_side,
    )


def _conversation_panel() -> rx.Component:
    return rx.cond(
        MessagingState.active_patient_id != "",
        # Conversation open
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon_button(
                    rx.icon("arrow-left", size=16),
                    variant="ghost",
                    size="2",
                    on_click=MessagingState.back_to_threads,
                    display=rx.cond(MessagingState.my_role == "patient", "none", "flex"),
                ),
                rx.vstack(
                    rx.text(MessagingState.active_patient_name, size="3", weight="medium"),
                    rx.text("Conversation directe", size="1", color="var(--gray-9)"),
                    spacing="0",
                ),
                rx.spacer(),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("refresh-cw", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="gray",
                        on_click=MessagingState.refresh,
                    ),
                    content="Actualiser la conversation",
                ),
                spacing="2",
                align="center",
                padding="0.75rem 1rem",
                border_bottom="1px solid var(--gray-4)",
                width="100%",
            ),
            # Messages
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(MessagingState.messages, _message_bubble),
                    spacing="3",
                    padding="1rem",
                    width="100%",
                    align_items="stretch",
                ),
                height="100%",
                flex="1",
            ),
            # Compose bar
            rx.hstack(
                rx.text_area(
                    placeholder="Écrire un message…",
                    value=MessagingState.compose_text,
                    on_change=MessagingState.set_compose_text,
                    auto_height=True,
                    min_rows=1,
                    max_rows=4,
                    flex="1",
                    resize="none",
                ),
                rx.icon_button(
                    rx.icon("send", size=16),
                    color_scheme="blue",
                    size="3",
                    on_click=MessagingState.send_message,
                    disabled=MessagingState.compose_text == "",
                ),
                padding="0.75rem 1rem",
                border_top="1px solid var(--gray-4)",
                align="end",
                spacing="2",
                width="100%",
            ),
            height="100%",
            flex="1",
            spacing="0",
            overflow="hidden",
        ),
        # No conversation selected yet
        rx.center(
            rx.vstack(
                rx.icon("message-circle-dashed", size=48, color="var(--gray-6)"),
                rx.text("Sélectionnez une conversation", size="3", color="var(--gray-9)"),
                align="center",
                spacing="2",
            ),
            flex="1",
        ),
    )


def messaging_page() -> rx.Component:
    return page_layout(
        rx.cond(
            MessagingState.is_loading,
            rx.center(rx.spinner(size="3"), padding="4rem"),
            rx.vstack(
                rx.cond(
                    MessagingState.error != "",
                    rx.callout(
                        MessagingState.error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="2",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.box(
                    rx.hstack(
                        # Left: thread list (doctor) or nothing (patient goes straight to conversation)
                        rx.cond(
                            MessagingState.my_role == "doctor",
                            _thread_list_panel(),
                            rx.fragment(),
                        ),
                        # Right: conversation
                        _conversation_panel(),
                        height="calc(100vh - 8rem)",
                        width="100%",
                        spacing="0",
                        overflow="hidden",
                    ),
                    border="1px solid var(--gray-4)",
                    border_radius="12px",
                    overflow="hidden",
                    width="100%",
                    height="calc(100vh - 8rem)",
                ),
                width="100%",
                spacing="3",
            ),
        ),
    )
