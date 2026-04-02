"""Shared page layout with sidebar navigation."""

import reflex as rx
from gws_reflex_main import (
    menu_item_component,
    page_sidebar_component,
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
        # Nav items
        rx.vstack(
            menu_item_component("layout-dashboard", "Dashboard", "/dashboard"),
            menu_item_component("users", "Patients", "/"),
            menu_item_component("calendar", "Appointments", "/appointments"),
            menu_item_component(
                "building-2",
                "Accounts",
                "/accounts",
                additional_active_route_prefixes=["/account"],
            ),
            rx.separator(width="100%", margin_y="0.25rem"),
            menu_item_component("shield", "Admin", "/admin"),
            width="100%",
            spacing="1",
            align_items="start",
            padding="0 1rem",
        ),
        width="100%",
        align_items="start",
    )


def page_layout(*children: rx.Component) -> rx.Component:
    """Wrap content in the standard sidebar layout.

    :param children: Page content components
    :return: Laid-out page
    :rtype: rx.Component
    """
    return page_sidebar_component(
        sidebar_content=_sidebar_content(),
        content=rx.vstack(*children, width="100%", spacing="4", padding="1.5rem"),
    )
