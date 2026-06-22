"""Shared empty-state component — dashed border card with icon + message."""

import reflex as rx


def empty_state(icon: str, message: rx.Var | str, padding: str = "4rem") -> rx.Component:
    """Centered dashed-border box with an icon and a message.

    Use this wherever a list page has no results to display.
    """
    return rx.center(
        rx.vstack(
            rx.icon(icon, size=40, color="var(--gray-6)"),
            rx.text(message, size="2", color="var(--gray-9)"),
            align="center",
            spacing="2",
        ),
        padding=padding,
        border="1px dashed var(--gray-5)",
        border_radius="8px",
        width="100%",
    )
