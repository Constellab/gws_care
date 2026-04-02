"""Admin panel component — user management and role assignment."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .admin_state import AdminState, UserRoleRowDTO

_ALL_ROLES = ["ADMIN", "DOCTOR", "OPERATOR"]
_ROLE_LABELS = {"ADMIN": "Administrator", "DOCTOR": "Doctor", "OPERATOR": "Operator"}
_ROLE_COLORS = {"ADMIN": "red", "DOCTOR": "blue", "OPERATOR": "green"}


def _role_toggle(user: UserRoleRowDTO, role: str) -> rx.Component:
    """A toggle badge/button for a single role on a user row."""
    has_role = user.roles.contains(role)
    return rx.cond(
        has_role,
        rx.badge(
            _ROLE_LABELS.get(role, role),
            color_scheme=_ROLE_COLORS.get(role, "gray"),
            variant="solid",
            size="1",
            cursor="pointer",
            on_click=lambda: AdminState.toggle_role(user.id, role),
            title=f"Click to revoke {role}",
        ),
        rx.badge(
            _ROLE_LABELS.get(role, role),
            color_scheme="gray",
            variant="outline",
            size="1",
            cursor="pointer",
            on_click=lambda: AdminState.toggle_role(user.id, role),
            title=f"Click to assign {role}",
        ),
    )


def _user_row(user: UserRoleRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(user.full_name, size="2", weight="medium")),
        rx.table.cell(rx.text(user.email, size="2", color="var(--gray-9)")),
        rx.table.cell(
            rx.hstack(
                rx.foreach(
                    rx.Var.create(_ALL_ROLES),
                    lambda role: _role_toggle(user, role),
                ),
                spacing="2",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def admin_page() -> rx.Component:
    """Admin panel — user role management."""
    return main_component(
        page_layout(
            # Access guard
            rx.cond(
                AdminState.is_admin,
                rx.vstack(
                    rx.hstack(
                        rx.heading("Admin Panel", size="6"),
                        rx.spacer(),
                        rx.badge("Admin Only", color_scheme="red", variant="soft", size="2"),
                        width="100%",
                        align="center",
                    ),
                    rx.text(
                        "Click a role badge to toggle it. Solid = assigned, outline = not assigned.",
                        size="2",
                        color="var(--gray-9)",
                    ),
                    # Feedback messages
                    rx.cond(
                        AdminState.error_message != "",
                        rx.callout(
                            AdminState.error_message,
                            icon="triangle-alert",
                            color_scheme="red",
                        ),
                    ),
                    rx.cond(
                        AdminState.success_message != "",
                        rx.callout(
                            AdminState.success_message,
                            icon="circle-check",
                            color_scheme="green",
                        ),
                    ),
                    # Users table
                    rx.cond(
                        AdminState.is_loading,
                        rx.center(rx.spinner(size="3"), padding="3rem"),
                        rx.cond(
                            AdminState.users,
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Name"),
                                        rx.table.column_header_cell("Email"),
                                        rx.table.column_header_cell("Roles"),
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(AdminState.users, _user_row),
                                ),
                                width="100%",
                                variant="surface",
                            ),
                            rx.center(
                                rx.text("No users found.", size="2", color="var(--gray-8)"),
                                padding="3rem",
                            ),
                        ),
                    ),
                    width="100%",
                    spacing="4",
                ),
                # Not an admin
                rx.center(
                    rx.vstack(
                        rx.icon("lock", size=40, color="var(--gray-7)"),
                        rx.text(
                            "Access denied. Administrator role required.",
                            size="3",
                            color="var(--gray-9)",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    padding="4rem",
                ),
            ),
        )
    )
