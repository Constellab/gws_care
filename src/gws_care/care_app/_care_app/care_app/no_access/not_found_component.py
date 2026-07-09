"""Custom 404 page — replaces Reflex's default plain text 404."""

import reflex as rx

from ..common.language_state import LanguageState


def not_found_page() -> rx.Component:
    """Fullscreen 404 page with a clear visual and a link back home."""
    return rx.center(
        rx.card(
            rx.vstack(
                # Icon
                rx.center(
                    rx.box(
                        rx.icon(
                            "search-x",
                            size=40,
                            color="var(--blue-9)",
                        ),
                        background="var(--blue-3)",
                        border_radius="50%",
                        padding="1.25rem",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    width="100%",
                    padding_bottom="0.5rem",
                ),
                # Status badge
                rx.badge("404", color_scheme="blue", variant="surface", size="2"),
                # Heading
                rx.heading(
                    LanguageState.tr["not_found_title"],
                    size="6",
                    weight="bold",
                    text_align="center",
                    color="var(--gray-12)",
                ),
                # Message
                rx.text(
                    LanguageState.tr["not_found_desc"],
                    size="3",
                    color="var(--gray-11)",
                    text_align="center",
                    line_height="1.6",
                ),
                rx.separator(width="100%", color_scheme="gray"),
                # Back home button
                rx.link(
                    rx.button(
                        rx.icon("house", size=14),
                        LanguageState.tr["back_to_home_btn"],
                        color_scheme="blue",
                        variant="solid",
                        size="3",
                        width="100%",
                    ),
                    href="/",
                    width="100%",
                ),
                spacing="4",
                align="center",
                width="100%",
            ),
            max_width="400px",
            width="100%",
            padding="2.5rem",
            box_shadow="0 4px 24px -4px var(--gray-a5), 0 2px 8px -2px var(--gray-a3)",
        ),
        width="100%",
        height="100vh",
        background="var(--gray-2)",
    )
