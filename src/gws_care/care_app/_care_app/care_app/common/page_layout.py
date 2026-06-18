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


def _admin_popover_footer() -> rx.Component:
    """Fixed bottom button that pops a menu upward with admin links."""
    return rx.cond(
        NavRoleState.can_see_any_admin,
        rx.popover.root(
            rx.popover.trigger(
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.icon("settings-2", size=16, color="var(--gray-10)"),
                            padding="0.4rem",
                            background="var(--gray-3)",
                            border_radius="8px",
                        ),
                        rx.vstack(
                            rx.text("Administration", size="2", weight="medium", color="var(--gray-12)"),
                            rx.text("Outils & configuration", size="1", color="var(--gray-9)"),
                            spacing="0",
                            align_items="start",
                        ),
                        rx.spacer(),
                        rx.icon("chevrons-up-down", size=14, color="var(--gray-9)"),
                        spacing="2",
                        align="center",
                        width="100%",
                    ),
                    padding="0.6rem 0.75rem",
                    border="1px solid var(--gray-4)",
                    border_radius="10px",
                    cursor="pointer",
                    background="var(--gray-1)",
                    _hover={"background": "var(--gray-3)"},
                    width="100%",
                ),
            ),
            rx.popover.content(
                rx.vstack(
                    rx.text("Administration", size="2", weight="medium", color="var(--gray-9)",
                            padding="0 0.25rem 0.25rem 0.25rem"),
                    rx.separator(width="100%"),
                    rx.cond(
                        NavRoleState.can_see_admin_section,
                        rx.link(
                            rx.hstack(
                                rx.icon("users-round", size=14),
                                rx.text("Annuaire du personnel", size="2"),
                                spacing="2", align="center",
                            ),
                            href="/staff",
                            text_decoration="none",
                            color="var(--gray-12)",
                            padding="0.4rem 0.5rem",
                            border_radius="var(--radius-2)",
                            width="100%",
                            _hover={"background": "var(--gray-3)"},
                            display="block",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        NavRoleState.can_see_companies,
                        rx.link(
                            rx.hstack(
                                rx.icon("building-2", size=14),
                                rx.text("Entreprises", size="2"),
                                spacing="2", align="center",
                            ),
                            href="/companies",
                            text_decoration="none",
                            color="var(--gray-12)",
                            padding="0.4rem 0.5rem",
                            border_radius="var(--radius-2)",
                            width="100%",
                            _hover={"background": "var(--gray-3)"},
                            display="block",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        NavRoleState.can_see_exam_types,
                        rx.link(
                            rx.hstack(
                                rx.icon("file", size=14),
                                rx.text("Référentiel examens", size="2"),
                                spacing="2", align="center",
                            ),
                            href="/exam-types",
                            text_decoration="none",
                            color="var(--gray-12)",
                            padding="0.4rem 0.5rem",
                            border_radius="var(--radius-2)",
                            width="100%",
                            _hover={"background": "var(--gray-3)"},
                            display="block",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        NavRoleState.can_see_settings,
                        rx.link(
                            rx.hstack(
                                rx.icon("settings", size=14),
                                rx.text("Paramètres", size="2"),
                                spacing="2", align="center",
                            ),
                            href="/settings",
                            text_decoration="none",
                            color="var(--gray-12)",
                            padding="0.4rem 0.5rem",
                            border_radius="var(--radius-2)",
                            width="100%",
                            _hover={"background": "var(--gray-3)"},
                            display="block",
                        ),
                        rx.fragment(),
                    ),
                    # ── Facturation ──────────────────────────────────────────
                    rx.cond(
                        NavRoleState.can_see_admin_section,
                        rx.vstack(
                            rx.separator(width="100%"),
                            rx.text("Facturation", size="1", color="var(--gray-8)",
                                    padding="0.2rem 0.5rem", font_weight="500"),
                            rx.link(
                                rx.hstack(
                                    rx.icon("credit-card", size=14),
                                    rx.text("Comptes de facturation", size="2"),
                                    spacing="2", align="center",
                                ),
                                href="/accounts",
                                text_decoration="none",
                                color="var(--gray-12)",
                                padding="0.4rem 0.5rem",
                                border_radius="var(--radius-2)",
                                width="100%",
                                _hover={"background": "var(--gray-3)"},
                                display="block",
                            ),
                            rx.link(
                                rx.hstack(
                                    rx.icon("receipt", size=14),
                                    rx.text("Pré-facturation", size="2"),
                                    spacing="2", align="center",
                                ),
                                href="/prebilling",
                                text_decoration="none",
                                color="var(--gray-12)",
                                padding="0.4rem 0.5rem",
                                border_radius="var(--radius-2)",
                                width="100%",
                                _hover={"background": "var(--gray-3)"},
                                display="block",
                            ),
                            rx.cond(
                                NavRoleState.can_see_invoices,
                                rx.link(
                                    rx.hstack(
                                        rx.icon("file-text", size=14),
                                        rx.text("Factures patients", size="2"),
                                        spacing="2", align="center",
                                    ),
                                    href="/invoices",
                                    text_decoration="none",
                                    color="var(--gray-12)",
                                    padding="0.4rem 0.5rem",
                                    border_radius="var(--radius-2)",
                                    width="100%",
                                    _hover={"background": "var(--gray-3)"},
                                    display="block",
                                ),
                                rx.fragment(),
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    # ── Simuler un rôle (admins uniquement) ──────────────────
                    rx.cond(
                        NavRoleState.is_upper_admin,
                        rx.vstack(
                            rx.separator(width="100%"),
                            rx.text("Simuler un rôle", size="1", color="var(--gray-8)",
                                    padding="0.2rem 0.5rem", font_weight="500"),
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Choisir un rôle...",
                                    size="1",
                                    width="100%",
                                ),
                                rx.select.content(
                                    rx.select.item("— Désactiver —", value="__reset__"),
                                    rx.select.item("Super Administrateur", value="SUPER_ADMIN_PSC"),
                                    rx.select.item("Administrateur PSC", value="ADMIN_PSC"),
                                    rx.select.item("Directeur", value="DIRECTEUR_PSC"),
                                    rx.select.item("Médecin PSC", value="MEDECIN_PSC"),
                                    rx.select.item("Médecin Entreprise", value="MEDECIN_ENTREPRISE"),
                                    rx.select.item("RH Entreprise", value="RH_ENTREPRISE"),
                                    rx.select.item("Opérateur Terrain", value="OPERATEUR_TERRAIN"),
                                    rx.select.item("Opérateur Labo", value="OPERATEUR_LABO"),
                                    rx.select.item("Patient", value="PATIENT"),
                                ),
                                value=rx.cond(
                                    NavRoleState.preview_active,
                                    NavRoleState.preview_roles[0],
                                    "__reset__",
                                ),
                                on_change=NavRoleState.simulate_any_role,
                                size="1",
                                width="100%",
                            ),
                            spacing="1",
                            width="100%",
                            padding="0 0.25rem",
                        ),
                        rx.fragment(),
                    ),
                    spacing="1",
                    width="220px",
                    padding="0.25rem",
                ),
                side="top",
                align="start",
                avoid_collisions=True,
            ),
        ),
        rx.fragment(),
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
        ),        # ── Role identity badge + multi-role switcher ──────────────────
        rx.box(
            rx.hstack(
                rx.badge(
                    NavRoleState.role_badge_label,
                    color_scheme=NavRoleState.role_color_scheme,
                    variant="soft",
                    size="1",
                ),
                rx.cond(
                    NavRoleState.has_multiple_roles,
                    rx.tooltip(
                        rx.select.root(
                            rx.select.trigger(
                                rx.icon("refresh-cw", size=12),
                                variant="ghost",
                                size="1",
                            ),
                            rx.select.content(
                                rx.select.item("— Vue complète —", value="__reset__"),
                                rx.foreach(
                                    NavRoleState.role_switch_options,
                                    lambda opt: rx.select.item(opt[1], value=opt[0]),
                                ),
                            ),
                            value=rx.cond(
                                NavRoleState.preview_active,
                                NavRoleState.preview_roles[0],
                                "",
                            ),
                            on_change=NavRoleState.switch_active_role,
                            size="1",
                        ),
                        content="Changer de vue de rôle",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
            ),
            padding="0 1em 0.75em 1em",
        ),
        # ── Preview mode banner (for admin previewing another user) ─────
        rx.cond(
            NavRoleState.preview_active,
            rx.box(
                rx.hstack(
                    rx.icon("eye", size=13, color="var(--amber-11)"),
                    rx.vstack(
                        rx.text("Vue active :", size="1", color="var(--amber-9)"),
                        rx.text(NavRoleState.preview_user_name, size="1", color="var(--amber-11)", weight="bold"),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=11),
                        variant="ghost",
                        size="1",
                        color_scheme="orange",
                        on_click=NavRoleState.stop_preview,
                    ),
                    align="center",
                    spacing="2",
                    width="100%",
                ),
                background="var(--amber-2)",
                border="1px solid var(--amber-6)",
                border_radius="6px",
                padding="0.4rem 0.75rem",
                margin="0 0.75rem 0.5rem 0.75rem",
                width="calc(100% - 1.5rem)",
            ),
            rx.fragment(),
        ),
        rx.scroll_area(
          rx.cond(
            NavRoleState.pending_role_access,
            # ── No role: show waiting message instead of nav ──────────
            rx.vstack(
                rx.box(
                    rx.vstack(
                        rx.icon("clock", size=28, color="var(--amber-9)"),
                        rx.text("Accès en cours de configuration",
                                size="2", weight="medium", color="var(--amber-11)",
                                text_align="center"),
                        rx.text("Un administrateur doit vous attribuer un rôle pour accéder à l'application.",
                                size="1", color="var(--gray-9)", text_align="center"),
                        spacing="2",
                        align="center",
                    ),
                    background="var(--amber-2)",
                    border="1px solid var(--amber-6)",
                    border_radius="8px",
                    padding="1rem",
                    margin="0 0.75rem",
                ),
                width="100%",
                padding_top="0.5rem",
            ),
            # ── Normal nav ─────────────────────────────────────────────
            rx.vstack(
            # ── 1. Tableau de bord ────────────────────────────────────────────
            _cond_nav(NavRoleState.can_see_dashboard,
                      "list", LanguageState.tr["nav_dashboard"], "/dashboard"),

            rx.separator(width="100%", margin_y="0.25rem"),

            # ── 2. Activité clinique ──────────────────────────────────────────
            rx.cond(
                NavRoleState.can_see_campaigns | NavRoleState.can_see_patients
                | NavRoleState.can_see_dossiers_medicaux | NavRoleState.can_see_appointments
                | NavRoleState.can_see_doctor_schedule,
                rx.text("Activité clinique", size="1", color="var(--gray-8)", weight="medium",
                        padding="0.25rem 0.5rem 0"),
                rx.fragment(),
            ),
            # Campagnes — cœur du produit
            _cond_nav(NavRoleState.can_see_campaigns,
                      "flag", "Campagnes", "/campaigns",
                      additional_active_route_prefixes=["/campaign"]),
            # Patients / employés
            _cond_nav(NavRoleState.can_see_patients,
                      "users", LanguageState.tr["nav_patients"], "/"),
            # Dossiers médicaux (fusion Médecin PSC + Médecin Entreprise)
            _cond_nav(NavRoleState.can_see_dossiers_medicaux,
                      "stethoscope", "Dossiers médicaux", "/doctor-psc"),
            # Planning RDV (liste des rendez-vous planifiés)
            _cond_nav(NavRoleState.can_see_appointments,
                      "calendar", "Planning RDV", "/appointments"),
            # Disponibilités médecins (créneaux récurrents)
            _cond_nav(NavRoleState.can_see_doctor_schedule,
                      "calendar-clock", "Disponibilités médecins", "/schedule"),

            rx.separator(width="100%", margin_y="0.25rem"),

            # ── 3. Suivi transversal (lecture / traçabilité) ──────────────────
            rx.cond(
                NavRoleState.can_see_consultations | NavRoleState.can_see_prescriptions
                | NavRoleState.can_see_certificates
                | NavRoleState.can_see_lab_queue,
                rx.text("Suivi & traçabilité", size="1", color="var(--gray-8)", weight="medium",
                        padding="0.25rem 0.5rem 0"),
                rx.fragment(),
            ),
            _cond_nav(NavRoleState.can_see_consultations,
                      "clipboard-list", "Consultations", "/consultations"),
            _cond_nav(NavRoleState.can_see_prescriptions,
                      "pill", "Ordonnances", "/prescriptions"),
            _cond_nav(NavRoleState.can_see_certificates,
                      "file-check", "Certificats médicaux", "/certificates"),

            _cond_nav(NavRoleState.can_see_lab_queue,
                      "flask-conical", "File d'attente labo", "/lab-queue"),

            rx.separator(width="100%", margin_y="0.25rem"),

            # ── 4. Communication ──────────────────────────────────────────────
            rx.cond(
                NavRoleState.can_see_notifications | NavRoleState.can_see_messages,
                rx.text("Communication", size="1", color="var(--gray-8)", weight="medium",
                        padding="0.25rem 0.5rem 0"),
                rx.fragment(),
            ),
            _cond_nav(NavRoleState.can_see_messages,
                      "message-circle", "Messages", "/messages"),
            _cond_nav(NavRoleState.can_see_notifications,
                      "bell", "Communications & envois", "/notifications"),

            rx.separator(width="100%", margin_y="0.25rem"),

            # ── 5. Espace patient ─────────────────────────────────────────────
            rx.cond(
                NavRoleState.can_see_patient_portal,
                rx.text("Mon espace", size="1", color="var(--gray-8)", weight="medium",
                        padding="0.25rem 0.5rem 0"),
                rx.fragment(),
            ),
            _cond_nav(NavRoleState.can_see_patient_portal,
                      "flask-conical", "Mes examens", "/my-exams"),
            _cond_nav(NavRoleState.can_see_patient_portal,
                      "calendar-plus", "Mes rendez-vous", "/my-appointments"),
            _cond_nav(NavRoleState.can_see_patient_portal,
                      "file-check-2", "Mes certificats", "/my-certificates"),

            width="100%",
            spacing="1",
            align_items="start",
            padding="0 1rem",
          ),  # end normal-nav vstack
          ),  # end rx.cond(pending_role_access)
          scrollbars="vertical",
          style={"flex": "1", "min_height": "0"},
        ),
        # ── Administration pinned footer ──────────────────────────────────
        rx.box(
            _admin_popover_footer(),
            padding="0.6rem 0.75rem",
            border_top="1px solid var(--gray-4)",
            width="100%",
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
