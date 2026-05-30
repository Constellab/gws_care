"""No Access page — shown when the authenticated user has no CareRole assigned."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState


def no_access_page() -> rx.Component:
    """Fullscreen message telling the user they have no access rights."""
    return main_component(
        rx.center(
            rx.card(
                rx.vstack(
                    # Icon
                    rx.center(
                        rx.box(
                            rx.icon(
                                "shield-alert",
                                size=40,
                                color="var(--orange-9)",
                            ),
                            background="var(--orange-3)",
                            border_radius="50%",
                            padding="1.25rem",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                        ),
                        width="100%",
                        padding_bottom="0.5rem",
                    ),
                    # Heading
                    rx.heading(
                        LanguageState.tr["no_access_title"],
                        size="6",
                        weight="bold",
                        text_align="center",
                        color="var(--gray-12)",
                    ),
                    # Message
                    rx.text(
                        LanguageState.tr["no_access_message"],
                        size="3",
                        color="var(--gray-11)",
                        text_align="center",
                        line_height="1.6",
                    ),
                    rx.separator(width="100%", color_scheme="gray"),
                    # Contact callout
                    rx.callout(
                        LanguageState.tr["no_access_contact"],
                        icon="mail",
                        color_scheme="orange",
                        size="2",
                    ),
                    spacing="5",
                    align="center",
                    width="100%",
                ),
                max_width="440px",
                width="100%",
                padding="2.5rem",
                box_shadow="0 4px 24px -4px var(--gray-a5), 0 2px 8px -2px var(--gray-a3)",
            ),
            width="100%",
            height="100vh",
            background="var(--gray-2)",
        ),
    )
