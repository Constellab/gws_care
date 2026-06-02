"""Staff directory — all care personnel displayed by role group, card layout.

This page reuses UserManagementState entirely (same CRUD).
It presents a visual, role-grouped card view instead of a flat table.
"""

import reflex as rx

from ..common.page_layout import page_layout
from ..user_management.user_management_state import UserManagementState, UserRowDTO


# ── Role group configuration ──────────────────────────────────────────────────
# (icon, label, color_scheme, accent_bg)
_GROUPS = [
    ("stethoscope", "Médecins PSC",         "blue",   "var(--blue-2)"),
    ("heart",       "Médecins Entreprise",   "pink",   "var(--pink-2)"),
    ("shield",      "Administration",        "violet", "var(--violet-2)"),
    ("wrench",      "Opérateurs",            "orange", "var(--orange-2)"),
    ("briefcase",   "RH Entreprise",         "green",  "var(--green-2)"),
]


# ── Person card ───────────────────────────────────────────────────────────────

def _initials(u: UserRowDTO) -> rx.Component:
    """Circular avatar with initials."""
    return rx.box(
        rx.text(
            u.first_name[0:1] + u.last_name[0:1],
            size="3",
            weight="bold",
            color="white",
        ),
        background="var(--accent-9)",
        border_radius="50%",
        width="2.5rem",
        height="2.5rem",
        display="flex",
        align_items="center",
        justify_content="center",
        flex_shrink="0",
    )


def _role_badge_row(u: UserRowDTO) -> rx.Component:
    return rx.hstack(
        rx.foreach(
            u.role_labels,
            lambda lbl: rx.badge(lbl, size="1", variant="soft", color_scheme="blue"),
        ),
        spacing="1",
        flex_wrap="wrap",
    )


def _person_card(u: UserRowDTO) -> rx.Component:
    return rx.box(
        rx.vstack(
            # Top: avatar + name + actions
            rx.hstack(
                _initials(u),
                rx.vstack(
                    rx.text(
                        u.last_name + " " + u.first_name,
                        size="2",
                        weight="medium",
                        line_height="1.2em",
                    ),
                    rx.text(u.email, size="1", color="var(--gray-9)"),
                    spacing="0",
                    flex="1",
                    overflow="hidden",
                ),
                rx.hstack(
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("eye", size=13),
                            variant="ghost",
                            size="1",
                            color_scheme="blue",
                            on_click=UserManagementState.preview_user(u.id),
                        ),
                        content="Prévisualiser la navigation",
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("pencil", size=13),
                            variant="ghost",
                            size="1",
                            color_scheme="gray",
                            on_click=UserManagementState.open_edit_dialog(u.id),
                        ),
                        content="Modifier la spécialité / le rôle",
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("power", size=13),
                            variant="ghost",
                            size="1",
                            color_scheme=rx.cond(u.is_active, "red", "green"),
                            on_click=UserManagementState.toggle_active(u.id),
                        ),
                        content=rx.cond(u.is_active, "Suspendre", "Réactiver"),
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("trash-2", size=13),
                            variant="ghost",
                            size="1",
                            color_scheme="red",
                            on_click=UserManagementState.open_confirm_revoke(u.id, u.email),
                        ),
                        content="Supprimer l'utilisateur",
                    ),
                    spacing="0",
                ),
                width="100%",
                align="center",
                spacing="2",
            ),
            # Role badges
            _role_badge_row(u),
            # Status
            rx.cond(
                u.is_active,
                rx.fragment(),
                rx.badge("Suspendu", color_scheme="red", size="1", variant="soft"),
            ),
            rx.cond(
                u.linked_account_name != "",
                rx.hstack(
                    rx.icon("building-2", size=12, color="var(--gray-9)"),
                    rx.text(u.linked_account_name, size="1", color="var(--gray-9)"),
                    spacing="1",
                    align="center",
                ),
                rx.fragment(),
            ),
            # Specialty badge for doctors
            rx.cond(
                u.specialty != "",
                rx.hstack(
                    rx.icon("stethoscope", size=12, color="var(--blue-9)"),
                    rx.text(u.specialty, size="1", color="var(--blue-9)", weight="medium"),
                    spacing="1",
                    align="center",
                ),
                rx.fragment(),
            ),
            spacing="2",
            align_items="start",
        ),
        padding="0.85rem 1rem",
        border="1px solid var(--gray-4)",
        border_radius="10px",
        background="white",
        _hover={"border_color": "var(--accent-7)", "box_shadow": "0 2px 8px rgba(0,0,0,0.06)"},
        transition="border-color 0.15s, box-shadow 0.15s",
    )


# ── Role group section ────────────────────────────────────────────────────────

def _group_section(
    icon_tag: str,
    label: str,
    color: str,
    accent_bg: str,
    users: rx.Var,
) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(icon_tag, size=16, color=f"var(--{color}-9)"),
                padding="0.4rem",
                background=accent_bg,
                border_radius="8px",
            ),
            rx.text(label, size="3", weight="bold"),
            rx.badge(
                users.length().to_string(),
                color_scheme=color,
                variant="soft",
                size="1",
            ),
            rx.spacer(),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("user-plus", size=14),
                    variant="soft",
                    color_scheme=color,
                    size="2",
                    on_click=UserManagementState.open_create_dialog,
                ),
                content=f"Ajouter un membre — {label}",
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        rx.cond(
            users.length() > 0,
            rx.grid(
                rx.foreach(users, _person_card),
                columns="3",
                spacing="3",
                width="100%",
                style={"@media (max-width: 900px)": {"grid_template_columns": "1fr 1fr"},
                       "@media (max-width: 600px)": {"grid_template_columns": "1fr"}},
            ),
            rx.box(
                rx.text(
                    f"Aucun {label.lower()} enregistré.",
                    size="2",
                    color="var(--gray-8)",
                    font_style="italic",
                ),
                padding="0.75rem 0",
            ),
        ),
        background=accent_bg,
        border="1px solid var(--gray-4)",
        border_radius="12px",
        padding="1rem 1.25rem",
        width="100%",
    )


# ── User add / confirm-revoke dialogs — reused inline ────────────────────────

def _confirm_revoke_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("user-x", size=18, color="var(--red-9)"),
                    rx.text("Supprimer l'utilisateur ?"),
                    spacing="2",
                ),
            ),
            rx.vstack(
                rx.text(
                    "Vous allez révoquer tous les rôles de ",
                    rx.text.strong(UserManagementState.confirm_revoke_user_email),
                    ". Cette action est irréversible.",
                    size="2",
                ),
                rx.vstack(
                    rx.text("Motif *", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Indiquez le motif (départ, faute, erreur de saisie…)",
                        value=UserManagementState.confirm_revoke_motif,
                        on_change=UserManagementState.set_confirm_revoke_motif,
                        rows="3",
                        width="100%",
                    ),
                    rx.text(
                        "Le motif est obligatoire et sera enregistré dans les logs.",
                        size="1",
                        color="var(--gray-9)",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Annuler",
                            variant="soft",
                            color_scheme="gray",
                            on_click=UserManagementState.dismiss_confirm_revoke,
                        ),
                    ),
                    rx.button(
                        "Supprimer",
                        color_scheme="red",
                        disabled=UserManagementState.confirm_revoke_motif.strip() == "",
                        on_click=UserManagementState.confirmed_revoke,
                    ),
                    justify="end",
                    spacing="2",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                margin_top="0.5rem",
            ),
            max_width="480px",
        ),
        open=UserManagementState.confirm_revoke_open,
        on_open_change=UserManagementState.dismiss_confirm_revoke,
    )


# ── Page ─────────────────────────────────────────────────────────────────────

def staff_directory_page() -> rx.Component:
    from ..user_management.user_management_component import _user_dialog

    return page_layout(
        # Header
        rx.hstack(
            rx.vstack(
                rx.heading("Annuaire du personnel", size="5"),
                rx.text(
                    "Gérez tous les membres de l'équipe par rôle. "
                    "Choisissez un médecin lors de la création d'un dossier patient.",
                    size="2",
                    color="var(--gray-9)",
                ),
                spacing="1",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("user-plus", size=16),
                "Ajouter un membre",
                on_click=UserManagementState.open_create_dialog,
                size="2",
            ),
            width="100%",
            align="center",
        ),

        rx.cond(
            UserManagementState.is_loading,
            rx.center(rx.spinner(size="3"), padding="4rem"),
            rx.vstack(
                _group_section(
                    "stethoscope", "Médecins PSC", "blue", "var(--blue-2)",
                    UserManagementState.medecin_psc_users,
                ),
                _group_section(
                    "heart", "Médecins Entreprise", "pink", "var(--pink-2)",
                    UserManagementState.medecin_enterprise_users,
                ),
                _group_section(
                    "shield", "Administration", "violet", "var(--violet-2)",
                    UserManagementState.admin_users,
                ),
                _group_section(
                    "wrench", "Opérateurs terrain & labo", "orange", "var(--orange-2)",
                    UserManagementState.operator_users,
                ),
                _group_section(
                    "briefcase", "RH Entreprise", "green", "var(--green-2)",
                    UserManagementState.rh_users,
                ),
                spacing="4",
                width="100%",
            ),
        ),
        # Dialogs (shared with user management page)
        _user_dialog(),
        _confirm_revoke_dialog(),
    )
