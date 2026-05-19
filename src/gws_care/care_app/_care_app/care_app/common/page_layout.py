"""Shared page layout with sidebar navigation."""

import reflex as rx
from gws_reflex_main import (
    menu_item_component,
    page_sidebar_component,
)

from .bell_state import BellEntryDTO, BellState
from .language_state import LanguageState
from .role_state import RoleState
from .user_menu_component import user_menu_button


def _bell_entry(entry: BellEntryDTO) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.cond(
                    ~entry.is_read,
                    rx.box(width="6px", height="6px", border_radius="50%", background="var(--accent-9)"),
                ),
                rx.text(entry.message, size="2", flex="1"),
                spacing="2",
                align="start",
                width="100%",
            ),
            rx.text(entry.created_at, size="1", color="var(--gray-9)"),
            spacing="1",
            width="100%",
        ),
        padding="0.5rem 0.75rem",
        border_bottom="1px solid var(--gray-4)",
        background=rx.cond(entry.is_read, "transparent", "var(--accent-2)"),
        width="100%",
    )


def _bell_button() -> rx.Component:
    return rx.popover.root(
        rx.popover.trigger(
            rx.box(
                rx.hstack(
                    rx.icon("bell", size=18),
                    rx.cond(
                        BellState.unread_count > 0,
                        rx.badge(
                            BellState.unread_count,
                            color_scheme="red",
                            variant="solid",
                            size="1",
                            style={"min_width": "18px", "text_align": "center"},
                        ),
                    ),
                    spacing="1",
                    align="center",
                ),
                padding="0.4rem 0.75rem",
                border_radius="var(--radius-2)",
                cursor="pointer",
                width="100%",
                _hover={"background": "var(--gray-3)"},
                on_click=BellState.load_bell,
            ),
        ),
        rx.popover.content(
            rx.vstack(
                rx.hstack(
                    rx.text(LanguageState.tr["notifications_title"], size="3", weight="medium"),
                    rx.spacer(),
                    rx.cond(
                        BellState.unread_count > 0,
                        rx.button(
                            LanguageState.tr["notifications_mark_all_read"],
                            variant="ghost",
                            size="1",
                            on_click=BellState.mark_all_read,
                        ),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.separator(width="100%"),
                rx.cond(
                    BellState.bell_entries.length() > 0,
                    rx.vstack(
                        rx.foreach(BellState.bell_entries, _bell_entry),
                        spacing="0",
                        width="100%",
                        max_height="320px",
                        overflow_y="auto",
                    ),
                    rx.center(
                        rx.text(LanguageState.tr["notifications_empty"], size="2", color="var(--gray-9)"),
                        padding="1rem",
                    ),
                ),
                rx.link(
                    rx.text(LanguageState.tr["notifications_view_all"], size="2", color="var(--accent-9)"),
                    href="/notifications",
                    text_align="center",
                    width="100%",
                    padding_top="0.5rem",
                ),
                spacing="2",
                width="280px",
            ),
            side="right",
            align="start",
        ),
    )


def _sidebar_content() -> rx.Component:
    return rx.vstack(
        # Header — keep the existing heart-pulse logo
        rx.hstack(
            rx.icon("heart-pulse", size=28, color="var(--accent-9)"),
            rx.vstack(
                rx.heading("Constellab Care", size="4", line_height="1em"),
                rx.text("By Constellab", size="1", color="var(--gray-9)", line_height="1em"),
                spacing="1",
            ),
            spacing="2",
            align="center",
            padding="1em",
        ),
        # Nav items — shown / hidden based on the user's CareRole
        rx.vstack(
            # Dashboard — visible to everyone with a role
            menu_item_component("layout-dashboard", LanguageState.tr["nav_dashboard"], "/dashboard"),

            # Patients — Operator, Doctor, Admin (not RH, not Patient)
            rx.cond(
                RoleState.is_operator | RoleState.is_doctor,
                menu_item_component("users", LanguageState.tr["nav_patients"], "/"),
            ),

            # Visits — Operator, Doctor, Admin
            rx.cond(
                RoleState.is_operator | RoleState.is_doctor,
                menu_item_component("calendar", LanguageState.tr["nav_visits"], "/visits"),
            ),

            # Campaigns — Operator, Doctor, Admin
            rx.cond(
                RoleState.is_operator | RoleState.is_doctor | RoleState.is_admin,
                menu_item_component(
                    "clipboard-list",
                    LanguageState.tr["nav_campaigns"],
                    "/campaigns",
                    additional_active_route_prefixes=["/campaign", "/campaign-visit/"],
                ),
            ),

            # Accounts — Operator, Doctor, Account Admin, Admin
            rx.cond(
                RoleState.is_operator | RoleState.is_doctor | RoleState.is_account_admin,
                menu_item_component(
                    "building-2",
                    LanguageState.tr["nav_accounts"],
                    "/accounts",
                    additional_active_route_prefixes=["/account"],
                ),
            ),

            # Patient portal — Patient role only
            rx.cond(
                RoleState.is_patient_user,
                rx.vstack(
                    menu_item_component("file-heart", LanguageState.tr["nav_my_results"], "/my-results"),
                    menu_item_component("calendar-check", LanguageState.tr["nav_my_appointments"], "/my-appointments"),
                    menu_item_component("file-text", LanguageState.tr["nav_my_documents"], "/my-documents"),
                    width="100%",
                    spacing="1",
                ),
            ),

            rx.separator(width="100%", margin_y="0.25rem"),
            menu_item_component("bell", LanguageState.tr["nav_notifications"], "/notifications"),
            width="100%",
            spacing="1",
            align_items="start",
            padding="0 1rem",
        ),
        # Push user menu to the bottom
        rx.spacer(),
        rx.box(
            user_menu_button(),
            width="100%",
            padding="0 1rem 0.75rem 1rem",
        ),
        width="100%",
        height="100%",
        align_items="start",
    )


def page_layout(*children: rx.Component, **kwargs) -> rx.Component:
    """Wrap content in the standard sidebar layout.

    :param children: Page content components
    :return: Laid-out page
    :rtype: rx.Component
    """
    vstack_props = {"width": "100%", "spacing": "4", "padding": "1.5rem", "min_width": "0", "overflow_x": "hidden"}
    vstack_props.update(kwargs)
    return page_sidebar_component(
        sidebar_content=_sidebar_content(),
        content=rx.vstack(*children, **vstack_props),
    )
