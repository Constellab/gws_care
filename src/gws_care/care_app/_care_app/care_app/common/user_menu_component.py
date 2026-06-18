"""User menu button pinned to the bottom of the sidebar.

Shows the current user's name and active role, and opens an upward popover with
sidebar-style buttons for switching role, opening the help centre and going to
the parameters page.
"""

import reflex as rx

from .language_state import LanguageState
from .role_state import RoleState


def _menu_nav_button(icon: str, label, href: str, is_external: bool = False) -> rx.Component:
    """A sidebar-style navigation button for the user menu popover."""
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=16, flex_shrink="0"),
            rx.text(label, size="2"),
            spacing="2",
            align="center",
            width="100%",
        ),
        href=href,
        is_external=is_external,
        padding="0.4rem 0.75rem",
        border_radius="var(--radius-2)",
        color="var(--gray-11)",
        _hover={"background": "var(--gray-3)", "text_decoration": "none"},
        width="100%",
        display="flex",
    )


def user_menu_button() -> rx.Component:
    """User account button with role-switch / help / settings popover."""
    return rx.popover.root(
        rx.popover.trigger(
            rx.box(
                rx.hstack(
                    rx.avatar(
                        src=RoleState.user_photo,
                        fallback=RoleState.user_initials,
                        size="2",
                        radius="full",
                        flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text(
                            RoleState.user_full_name,
                            size="2",
                            weight="bold",
                            color="var(--gray-12)",
                            overflow="hidden",
                            text_overflow="ellipsis",
                            white_space="nowrap",
                            max_width="140px",
                        ),
                        rx.text(
                            RoleState.active_role_display,
                            size="1",
                            color="var(--gray-9)",
                        ),
                        spacing="0",
                        align_items="start",
                    ),
                    rx.spacer(),
                    rx.icon("chevrons-up-down", size=14, color="var(--gray-9)", flex_shrink="0"),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                padding="0.5rem 0.75rem",
                border_radius="var(--radius-2)",
                cursor="pointer",
                width="100%",
                border="1px solid var(--gray-5)",
                _hover={"background": "var(--gray-3)"},
            ),
        ),
        rx.popover.content(
            rx.vstack(
                rx.cond(
                    RoleState.is_patient_user,
                    _menu_nav_button(
                        "user",
                        LanguageState.tr["nav_my_details"],
                        "/my-details",
                    ),
                ),
                rx.cond(
                    RoleState.switchable_roles.length() > 0,
                    _menu_nav_button(
                        "repeat-2",
                        LanguageState.tr["user_menu_switch_role"],
                        "/switch_role",
                    ),
                ),
                _menu_nav_button(
                    "circle-help",
                    LanguageState.tr["user_menu_help_center"],
                    "https://constellab.community/bricks/gws_care/latest",
                    is_external=True,
                ),
                _menu_nav_button(
                    "settings",
                    LanguageState.tr["nav_settings"],
                    "/settings",
                ),
                spacing="1",
                width="220px",
                padding="0.25rem",
            ),
            side="top",
            align="start",
        ),
    )
