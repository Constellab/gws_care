"""User management page component (US-001, US-002, US-003)."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .user_management_state import AccountOptionDTO, UserManagementState, UserRowDTO

_PSC_ROLES = [
    ("SUPER_ADMIN_PSC", "Super Admin PSC"),
    ("ADMIN_PSC", "Admin PSC"),
    ("OPERATEUR_TERRAIN", "Opérateur terrain"),
    ("OPERATEUR_LABO", "Opérateur labo"),
    ("MEDECIN_PSC", "Médecin PSC"),
]
_ENTERPRISE_ROLES = [
    ("MEDECIN_ENTREPRISE", "Médecin entreprise"),
    ("RH_ENTREPRISE", "RH entreprise"),
]
_ALL_ROLES = _PSC_ROLES + _ENTERPRISE_ROLES


def _role_badge(label: str) -> rx.Component:
    return rx.badge(label, size="1", variant="soft", color_scheme="blue")


def _status_badge(is_active: bool) -> rx.Component:
    return rx.cond(
        is_active,
        rx.badge("Actif", color_scheme="green", size="1", variant="soft"),
        rx.badge("Suspendu", color_scheme="red", size="1", variant="soft"),
    )


def _user_row(u: UserRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(f"{u.last_name} {u.first_name}", size="2", weight="medium")),
        rx.table.cell(rx.text(u.email, size="2")),
        rx.table.cell(
            rx.hstack(
                rx.foreach(u.role_labels, _role_badge),
                spacing="1",
                flex_wrap="wrap",
            )
        ),
        rx.table.cell(
            rx.cond(
                u.linked_account_name != "",
                rx.text(u.linked_account_name, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(_status_badge(u.is_active)),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("power", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme=rx.cond(u.is_active, "red", "green"),
                        on_click=lambda: UserManagementState.toggle_active(u.id),
                    ),
                    content=rx.cond(u.is_active, "Suspendre", "Réactiver"),
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("trash-2", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="red",
                        on_click=UserManagementState.open_confirm_revoke(u.id, u.email),
                    ),
                    content="Révoquer tous les rôles",
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _user_dialog() -> rx.Component:
    role_options = _PSC_ROLES + _ENTERPRISE_ROLES
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajouter un utilisateur"),
            rx.dialog.description(
                "Saisissez l'adresse email de la personne et son rôle. L'utilisateur sera créé automatiquement.",
                size="2",
                color="var(--gray-9)",
            ),
            rx.vstack(
                rx.grid(
                    rx.vstack(
                        rx.text("Prénom *", size="2", weight="medium"),
                        rx.input(
                            placeholder="Prénom",
                            value=UserManagementState.form.first_name,
                            on_change=UserManagementState.set_first_name,
                            width="100%",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Nom *", size="2", weight="medium"),
                        rx.input(
                            placeholder="Nom",
                            value=UserManagementState.form.last_name,
                            on_change=UserManagementState.set_last_name,
                            width="100%",
                        ),
                        spacing="1",
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Email *", size="2", weight="medium"),
                    rx.input(
                        placeholder="prenom.nom@example.com",
                        value=UserManagementState.form.email,
                        on_change=UserManagementState.set_email,
                        width="100%",
                        type="email",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Rôle *", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Sélectionner un rôle", width="100%"),
                        rx.select.content(
                            rx.select.group(
                                rx.select.label("PSC"),
                                *[rx.select.item(label, value=val) for val, label in _PSC_ROLES],
                            ),
                            rx.select.separator(),
                            rx.select.group(
                                rx.select.label("Entreprise"),
                                *[rx.select.item(label, value=val) for val, label in _ENTERPRISE_ROLES],
                            ),
                        ),
                        value=UserManagementState.form.role,
                        on_change=UserManagementState.set_role,
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Compte de facturation", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Optionnel — pour les rôles entreprise", width="100%"),
                        rx.select.content(
                            rx.select.item("— Aucun —", value="_none_"),
                            rx.foreach(
                                UserManagementState.account_options,
                                lambda a: rx.select.item(a.name, value=a.id),
                            ),
                        ),
                        value=UserManagementState.form.linked_account_id,
                        on_change=UserManagementState.set_linked_account,
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Statut actif", size="2"),
                    rx.switch(
                        checked=UserManagementState.form.is_active,
                        on_change=UserManagementState.set_is_active,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    UserManagementState.form_error != "",
                    rx.callout(
                        UserManagementState.form_error,
                        icon="info",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                spacing="3",
                width="100%",
                margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Annuler", variant="soft", color_scheme="gray"),
                ),
                rx.button(
                    "Enregistrer",
                    on_click=UserManagementState.save_user,
                    loading=UserManagementState.is_saving,
                ),
                justify="end",
                spacing="2",
                margin_top="1.5rem",
                width="100%",
            ),
            max_width="500px",
        ),
        open=UserManagementState.dialog_open,
        on_open_change=UserManagementState.close_dialog,
    )


def _users_table(users: list[UserRowDTO]) -> rx.Component:
    return rx.cond(
        rx.Var.create(len).call(users) > 0,  # type: ignore[arg-type]
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Nom"),
                    rx.table.column_header_cell("Email"),
                    rx.table.column_header_cell("Rôles"),
                    rx.table.column_header_cell("Compte lié"),
                    rx.table.column_header_cell("Statut"),
                    rx.table.column_header_cell(""),
                )
            ),
            rx.table.body(rx.foreach(users, _user_row)),
            width="100%",
            variant="surface",
        ),
        rx.center(
            rx.text("Aucun utilisateur trouvé.", size="2", color="var(--gray-9)"),
            padding="2rem",
        ),
    )


def _filtered_users(tab: str) -> rx.Component:
    psc_users = rx.Var.create([
        u for u in UserManagementState.users
        if any(r in ["SUPER_ADMIN_PSC", "ADMIN_PSC", "OPERATEUR_TERRAIN", "OPERATEUR_LABO", "MEDECIN_PSC"]
               for r in u.roles)
    ])
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("Utilisateurs PSC", value="psc"),
            rx.tabs.trigger("Utilisateurs Entreprise", value="enterprise"),
        ),
        rx.tabs.content(
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Nom"),
                            rx.table.column_header_cell("Email"),
                            rx.table.column_header_cell("Rôles"),
                            rx.table.column_header_cell("Compte lié"),
                            rx.table.column_header_cell("Statut"),
                            rx.table.column_header_cell(""),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            UserManagementState.users.filter(  # type: ignore[attr-defined]
                                lambda u: u.roles.contains("SUPER_ADMIN_PSC")
                                | u.roles.contains("ADMIN_PSC")
                                | u.roles.contains("OPERATEUR_TERRAIN")
                                | u.roles.contains("OPERATEUR_LABO")
                                | u.roles.contains("MEDECIN_PSC")
                            ),
                            _user_row,
                        )
                    ),
                    width="100%",
                    variant="surface",
                ),
                width="100%",
            ),
            value="psc",
        ),
        rx.tabs.content(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Nom"),
                        rx.table.column_header_cell("Email"),
                        rx.table.column_header_cell("Rôles"),
                        rx.table.column_header_cell("Compte lié"),
                        rx.table.column_header_cell("Statut"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        UserManagementState.users.filter(  # type: ignore[attr-defined]
                            lambda u: u.roles.contains("MEDECIN_ENTREPRISE")
                            | u.roles.contains("RH_ENTREPRISE")
                        ),
                        _user_row,
                    )
                ),
                width="100%",
                variant="surface",
            ),
            value="enterprise",
        ),
        default_value="psc",
        width="100%",
    )


def user_management_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.heading("Gestion des utilisateurs", size="6"),
                        rx.text("Utilisateurs PSC et entreprise de Constellab Care", size="2", color="var(--gray-9)"),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("user-plus", size=16),
                        "Ajouter",
                        on_click=UserManagementState.open_create_dialog,
                        variant="solid",
                    ),
                    width="100%",
                    align="end",
                ),
                rx.cond(
                    UserManagementState.error != "",
                    rx.callout(UserManagementState.error, icon="info", color_scheme="red", size="2"),
                ),
                # Tabs: PSC / Enterprise
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger(
                            rx.hstack(rx.icon("shield", size=14), rx.text("Équipe PSC"), spacing="1"),
                            value="psc",
                        ),
                        rx.tabs.trigger(
                            rx.hstack(rx.icon("building-2", size=14), rx.text("Entreprises"), spacing="1"),
                            value="enterprise",
                        ),
                    ),
                    # PSC tab
                    rx.tabs.content(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Nom"),
                                    rx.table.column_header_cell("Email"),
                                    rx.table.column_header_cell("Rôles"),
                                    rx.table.column_header_cell("Compte lié"),
                                    rx.table.column_header_cell("Statut"),
                                    rx.table.column_header_cell(""),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(UserManagementState.users, _user_row),
                            ),
                            width="100%",
                            variant="surface",
                        ),
                        value="psc",
                    ),
                    # Enterprise tab
                    rx.tabs.content(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Nom"),
                                    rx.table.column_header_cell("Email"),
                                    rx.table.column_header_cell("Rôles"),
                                    rx.table.column_header_cell("Compte lié"),
                                    rx.table.column_header_cell("Statut"),
                                    rx.table.column_header_cell(""),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(UserManagementState.users, _user_row),
                            ),
                            width="100%",
                            variant="surface",
                        ),
                        value="enterprise",
                    ),
                    default_value="psc",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            _user_dialog(),
            # ── Confirm révocation rôles ─────────────────────────────────────────
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(
                        rx.hstack(rx.icon("trash-2", size=18, color="var(--red-9)"),
                                  rx.text("Révoquer les accès ?"), spacing="2"),
                    ),
                    rx.dialog.description(
                        rx.vstack(
                            rx.text(
                                "Tous les rôles de « ",
                                rx.text.strong(UserManagementState.confirm_revoke_user_email),
                                " » seront révoqués.",
                                size="2",
                            ),
                            rx.text("L'utilisateur ne pourra plus accéder à Constellab Care.",
                                    size="2", color="var(--gray-9)"),
                            spacing="2",
                        ),
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Annuler", variant="soft", color_scheme="gray",
                                      on_click=UserManagementState.dismiss_confirm_revoke),
                        ),
                        rx.button("Révoquer", color_scheme="red",
                                  on_click=UserManagementState.confirmed_revoke),
                        justify="end", spacing="2", margin_top="1rem", width="100%",
                    ),
                    max_width="440px",
                ),
                open=UserManagementState.confirm_revoke_open,
                on_open_change=lambda _: UserManagementState.dismiss_confirm_revoke(),
            ),
        )
    )
