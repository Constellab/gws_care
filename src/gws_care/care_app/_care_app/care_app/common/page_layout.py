"""Shared page layout with sidebar navigation."""

import reflex as rx
from gws_reflex_main import (
    menu_item_component,
    page_sidebar_component,
)

from .bell_state import BellEntryDTO, BellState
from .language_state import LanguageState
from .nav_role_state import NavRoleState


def _cond_nav(condition: rx.Var, icon: str, label: str, route: str, **kwargs) -> rx.Component:
    """Render a nav item only when *condition* is True."""
    return rx.cond(
        condition,
        menu_item_component(icon, label, route, **kwargs),
        rx.fragment(),
    )


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
        # Header — click logo to go to role-appropriate home
        rx.link(
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
            href=NavRoleState.home_route,
            text_decoration="none",
            _hover={"opacity": "0.85"},
        ),
        rx.scroll_area(
          rx.vstack(
            # ── 1. Tableau de bord — tout le monde ───────────────────────
            menu_item_component("list", LanguageState.tr["nav_dashboard"], "/dashboard"),

            rx.separator(width="100%", margin_y="0.25rem"),

            # ── 2. Opérations quotidiennes (ordre du flux métier) ─────────
            # Campagnes d'abord — c'est le cœur du produit
            _cond_nav(NavRoleState.can_see_campaigns,
                      "flag", "Campagnes", "/campaigns",
                      additional_active_route_prefixes=["/campaign"]),
            # Entreprises (employeurs)
            _cond_nav(NavRoleState.can_see_companies,
                      "building-2", "Entreprises", "/companies",
                      additional_active_route_prefixes=["/company"]),
            # Puis les patients/employés
            _cond_nav(NavRoleState.can_see_patients,
                      "users", LanguageState.tr["nav_patients"], "/"),
            # Convocations / rendez-vous
            _cond_nav(NavRoleState.can_see_appointments,
                      "calendar", LanguageState.tr["nav_appointments"], "/appointments"),

            rx.separator(width="100%", margin_y="0.25rem"),

            # ── 3. Espaces métier par rôle ────────────────────────────────
            _cond_nav(NavRoleState.can_see_rh,
                      "user-plus", "Espace RH", "/hr"),
            _cond_nav(NavRoleState.can_see_medecin_psc,
                      "shield", "Médecin PSC", "/doctor-psc"),
            _cond_nav(NavRoleState.can_see_medecin_entreprise,
                      "heart", "Médecin Entreprise", "/doctor-enterprise"),

            rx.separator(width="100%", margin_y="0.25rem"),

            # ── 4. Notifications & Finances ───────────────────────────────
            _cond_nav(NavRoleState.can_see_notifications,
                      "bell", LanguageState.tr["nav_notifications"], "/notifications"),
            _cond_nav(NavRoleState.can_see_admin_section,
                      "file-text", "Préfacturation", "/prebilling"),

            rx.separator(width="100%", margin_y="0.25rem"),

            # ── 5. Configuration (rarement modifié — en bas) ──────────────
            _cond_nav(NavRoleState.can_see_exam_types,
                      "file", "Référentiel examens", "/exam-types"),
            _cond_nav(NavRoleState.can_see_admin_section,
                      "users", "Utilisateurs", "/users"),
            _cond_nav(NavRoleState.can_see_admin_section,
                      "list", "Journal d'audit", "/audit"),
            _cond_nav(NavRoleState.can_see_settings,
                      "settings", "Paramètres", "/settings"),

            width="100%",
            spacing="1",
            align_items="start",
            padding="0 1rem",
          ),
          scrollbars="vertical",
          style={"flex": "1", "min_height": "0"},
        ),
        width="100%",
        height="100%",
        align_items="start",
        flex_direction="column",
        flex="1",
        min_height="0",
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
