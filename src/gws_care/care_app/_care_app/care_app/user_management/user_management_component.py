"""User management page component (US-001, US-002, US-003)."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .user_management_state import AccountOptionDTO, UserManagementState, UserRowDTO

_PSC_ROLES = [
    ("SUPER_ADMIN_PSC", "Super Admin PSC"),
    ("ADMIN_PSC", "Admin PSC"),
    ("OPERATEUR_TERRAIN", "Field operator"),
    ("OPERATEUR_LABO", "Lab operator"),
    ("MEDECIN_PSC", "PSC Doctor"),
]
_ENTERPRISE_ROLES = [
    ("MEDECIN_ENTREPRISE", "Company doctor"),
    ("RH_ENTREPRISE", "Company HR"),
]
_PATIENT_ROLES = [
    ("PATIENT", "Patient"),
]
_ALL_ROLES = _PSC_ROLES + _ENTERPRISE_ROLES + _PATIENT_ROLES


def _role_badge(label: str) -> rx.Component:
    return rx.badge(label, size="1", variant="soft", color_scheme="blue")


def _status_badge(is_active: bool) -> rx.Component:
    return rx.cond(
        is_active,
        rx.badge("Active", color_scheme="green", size="1", variant="soft"),
        rx.badge("Suspended", color_scheme="red", size="1", variant="soft"),
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
                u.specialty != "",
                rx.badge(u.specialty, size="1", variant="soft", color_scheme="blue"),
                rx.text("—", size="2", color="var(--gray-7)"),
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
                        rx.icon("eye", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="blue",
                        on_click=UserManagementState.preview_user(u.id),
                    ),
                    content="Preview this user's navigation",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pencil", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="gray",
                        on_click=UserManagementState.open_edit_dialog(u.id),
                    ),
                    content="Edit specialty / role",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("power", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme=rx.cond(u.is_active, "red", "green"),
                        on_click=lambda: UserManagementState.toggle_active(u.id),
                    ),
                    content=rx.cond(u.is_active, "Suspend", "Reactivate"),
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("trash-2", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="red",
                        on_click=UserManagementState.open_confirm_revoke(u.id, u.email),
                    ),
                    content="Revoke all roles",
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
            rx.dialog.title(
                rx.cond(UserManagementState.is_editing, "Edit user", "Add user")
            ),
            rx.dialog.description(
                rx.cond(
                    UserManagementState.is_editing,
                    "Edit the specialty, role, or linked account.",
                    "Enter the person's email address and role. The user will be created automatically.",
                ),
                size="2",
                color="var(--gray-9)",
            ),
            rx.vstack(
                rx.grid(
                    rx.vstack(
                        rx.text("First name *", size="2", weight="medium"),
                        rx.input(
                            placeholder="First name",
                            value=UserManagementState.form.first_name,
                            on_change=UserManagementState.set_first_name,
                            width="100%",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Last name *", size="2", weight="medium"),
                        rx.input(
                            placeholder="Last name",
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
                    rx.text("Role *", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Select a role", width="100%"),
                        rx.select.content(
                            rx.select.group(
                                rx.select.label("PSC"),
                                *[rx.select.item(label, value=val) for val, label in _PSC_ROLES],
                            ),
                            rx.select.separator(),
                            rx.select.group(
                                rx.select.label("Company"),
                                *[rx.select.item(label, value=val) for val, label in _ENTERPRISE_ROLES],
                            ),
                            rx.select.separator(),
                            rx.select.group(
                                rx.select.label("Patient portal"),
                                *[rx.select.item(label, value=val) for val, label in _PATIENT_ROLES],
                            ),
                        ),
                        value=UserManagementState.form.role,
                        on_change=UserManagementState.set_role,
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Billing account", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Optional — for company roles", width="100%"),
                        rx.select.content(
                            rx.select.item("— None —", value="_none_"),
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
                # Specialty — shown only for doctor roles
                rx.cond(
                    (UserManagementState.form.role == "MEDECIN_PSC")
                    | (UserManagementState.form.role == "MEDECIN_ENTREPRISE"),
                    rx.vstack(
                        rx.text("Specialty", size="2", weight="medium"),
                        # Quick-pick from existing specialties
                        rx.cond(
                            UserManagementState.specialty_suggestions.length() > 0,
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Choose an existing specialty…",
                                    width="100%",
                                ),
                                rx.select.content(
                                    rx.foreach(
                                        UserManagementState.specialty_suggestions,
                                        lambda s: rx.select.item(s, value=s),
                                    ),
                                ),
                                value=UserManagementState.form.specialty,
                                on_change=UserManagementState.set_specialty,
                            ),
                        ),
                        rx.input(
                            placeholder="Or type freely: Occupational medicine, Cardiology…",
                            value=UserManagementState.form.specialty,
                            on_change=UserManagementState.set_specialty,
                            width="100%",
                        ),
                        rx.text(
                            "Allows the patient to filter by specialty when booking an appointment.",
                            size="1",
                            color="var(--gray-9)",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                ),
                rx.hstack(
                    rx.text("Active status", size="2"),
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
                    rx.button("Cancel", variant="soft", color_scheme="gray"),
                ),
                rx.button(
                    "Save",
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
        users.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Name"),
                    rx.table.column_header_cell("Email"),
                    rx.table.column_header_cell("Roles"),
                    rx.table.column_header_cell("Linked account"),
                    rx.table.column_header_cell("Status"),
                    rx.table.column_header_cell(""),
                )
            ),
            rx.table.body(rx.foreach(users, _user_row)),
            width="100%",
            variant="surface",
        ),
        rx.center(
            rx.text("No user found.", size="2", color="var(--gray-9)"),
            padding="2rem",
        ),
    )




def user_management_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.heading("User management", size="6"),
                        rx.text("PSC and company users in Constellab Care", size="2", color="var(--gray-9)"),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("user-plus", size=16),
                        "Add",
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
                # ── Context banner: explain difference with /staff ────────────────
                rx.callout(
                    rx.hstack(
                        rx.text(
                            "This page manages accounts, roles, and user previews. "
                            "To view the visual directory grouped by position, see ",
                            size="2",
                        ),
                        rx.link("Staff directory →", href="/staff", size="2"),
                        spacing="1",
                        align="center",
                        flex_wrap="wrap",
                    ),
                    icon="users",
                    color_scheme="blue",
                    size="1",
                ),
                # Tabs: PSC / Enterprise
                rx.cond(
                    UserManagementState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="3rem"),
                    rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger(
                            rx.hstack(rx.icon("shield", size=14), rx.text("PSC Team"), spacing="1"),
                            value="psc",
                        ),
                        rx.tabs.trigger(
                            rx.hstack(rx.icon("building-2", size=14), rx.text("Companies"), spacing="1"),
                            value="enterprise",
                        ),
                    ),
                    # PSC tab
                    rx.tabs.content(
                        rx.cond(
                            UserManagementState.psc_tab_users.length() > 0,
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Name"),
                                        rx.table.column_header_cell("Email"),
                                        rx.table.column_header_cell("Roles"),
                                        rx.table.column_header_cell("Specialty"),
                                        rx.table.column_header_cell("Linked account"),
                                        rx.table.column_header_cell("Status"),
                                        rx.table.column_header_cell(""),
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(UserManagementState.psc_tab_users, _user_row),
                                ),
                                width="100%",
                                variant="surface",
                            ),
                            rx.center(
                                rx.text("No PSC user found.", size="2", color="var(--gray-9)"),
                                padding="2rem",
                            ),
                        ),
                        value="psc",
                    ),
                    # Enterprise tab
                    rx.tabs.content(
                        rx.cond(
                            UserManagementState.enterprise_tab_users.length() > 0,
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Name"),
                                        rx.table.column_header_cell("Email"),
                                        rx.table.column_header_cell("Roles"),
                                        rx.table.column_header_cell("Specialty"),
                                        rx.table.column_header_cell("Linked account"),
                                        rx.table.column_header_cell("Status"),
                                        rx.table.column_header_cell(""),
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(UserManagementState.enterprise_tab_users, _user_row),
                                ),
                                width="100%",
                                variant="surface",
                            ),
                            rx.center(
                                rx.text("No company user found.", size="2", color="var(--gray-9)"),
                                padding="2rem",
                            ),
                        ),
                        value="enterprise",
                    ),
                    default_value="psc",
                    width="100%",
                ),  # end rx.tabs.root
                ),  # end rx.cond(is_loading)
                spacing="4",
                width="100%",
            ),
            _user_dialog(),
            # ── Confirm suppression utilisateur ─────────────────────────────────
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(
                        rx.hstack(rx.icon("user-x", size=18, color="var(--red-9)"),
                                  rx.text("Delete user?"), spacing="2"),
                    ),
                    rx.vstack(
                        rx.text(
                            "You are about to revoke all roles for ",
                            rx.text.strong(UserManagementState.confirm_revoke_user_email),
                            ". This action is irreversible.",
                            size="2",
                        ),
                        rx.vstack(
                            rx.text("Reason *", size="2", weight="medium"),
                            rx.text_area(
                                placeholder="State the reason (departure, misconduct, data entry error…)",
                                value=UserManagementState.confirm_revoke_motif,
                                on_change=UserManagementState.set_confirm_revoke_motif,
                                rows="3",
                                width="100%",
                            ),
                            rx.text(
                                "The reason is mandatory and will be recorded in the logs.",
                                size="1",
                                color="var(--gray-9)",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.dialog.close(
                                rx.button("Cancel", variant="soft", color_scheme="gray",
                                          on_click=UserManagementState.dismiss_confirm_revoke),
                            ),
                            rx.button(
                                "Delete",
                                color_scheme="red",
                                disabled=UserManagementState.confirm_revoke_motif.strip() == "",
                                on_click=UserManagementState.confirmed_revoke,
                            ),
                            justify="end", spacing="2", width="100%",
                        ),
                        spacing="4",
                        width="100%",
                        margin_top="0.5rem",
                    ),
                    max_width="480px",
                ),
                open=UserManagementState.confirm_revoke_open,
                on_open_change=lambda _: UserManagementState.dismiss_confirm_revoke(),
            ),
        )
    )
