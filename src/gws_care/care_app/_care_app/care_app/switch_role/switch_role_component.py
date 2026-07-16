"""Switch Role page — choose which role to view the app as."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .switch_role_state import SwitchRoleState


def _role_label(role_value: rx.Var) -> rx.Component:
    """Translate a role value string to a localised label via rx.match."""
    return rx.match(
        role_value,
        ("ADMIN", LanguageState.tr["role_admin"]),
        ("MEDECIN", LanguageState.tr["role_doctor"]),
        ("OPERATEUR", LanguageState.tr["role_operator"]),
        ("RH_ENTREPRISE", LanguageState.tr["role_account_admin"]),
        ("PATIENT", LanguageState.tr["role_patient"]),
        role_value,
    )


def _role_desc(role_value: rx.Var) -> rx.Component:
    """Short description for each role."""
    return rx.match(
        role_value,
        ("ADMIN", LanguageState.tr["role_admin_desc"]),
        ("MEDECIN", LanguageState.tr["role_doctor_desc"]),
        ("OPERATEUR", LanguageState.tr["role_operator_desc"]),
        ("RH_ENTREPRISE", LanguageState.tr["role_account_admin_desc"]),
        ("PATIENT", LanguageState.tr["role_patient_desc"]),
        "",
    )


def _role_icon(role_value: rx.Var) -> rx.Component:
    """Render the icon for a given role value using rx.match."""
    return rx.match(
        role_value,
        ("ADMIN", rx.icon("shield-check", size=28)),
        ("MEDECIN", rx.icon("user-round-check", size=28)),
        ("OPERATEUR", rx.icon("wrench", size=28)),
        ("RH_ENTREPRISE", rx.icon("building-2", size=28)),
        ("PATIENT", rx.icon("user", size=28)),
        rx.icon("user", size=28),
    )


def _role_card_content(role_value: rx.Var) -> rx.Component:
    return rx.hstack(
        _role_icon(role_value),
        rx.vstack(
            rx.text(_role_label(role_value), size="3", weight="medium"),
            rx.text(_role_desc(role_value), size="1", color="var(--gray-9)", line_height="1.3em"),
            spacing="1",
            align_items="start",
        ),
        spacing="3",
        align="center",
    )


_CARD_COMMON = dict(
    border_radius="var(--radius-3)",
    width="360px",
    min_height="72px",
    display="flex",
    align_items="center",
    justify_content="flex-start",
    cursor="pointer",
    transition="background 0.15s",
    padding="0.75rem 1.25rem",
)


def _role_card(role_value: rx.Var) -> rx.Component:
    """Render one role card — active uses accent colour, inactive uses gray border."""
    is_active = SwitchRoleState.active_role_key == role_value
    return rx.cond(
        is_active,
        rx.box(
            _role_card_content(role_value),
            border="2px solid var(--accent-9)",
            background="var(--accent-3)",
            color="var(--accent-11)",
            _hover={"background": "var(--accent-4)"},
            on_click=lambda: SwitchRoleState.switch_role(role_value),
            **_CARD_COMMON,
        ),
        rx.box(
            _role_card_content(role_value),
            border="1px solid var(--gray-5)",
            background="var(--gray-1)",
            color="var(--gray-11)",
            _hover={"background": "var(--gray-3)"},
            on_click=lambda: SwitchRoleState.switch_role(role_value),
            **_CARD_COMMON,
        ),
    )


def switch_role_page() -> rx.Component:
    """Full switch-role selection page."""
    return main_component(
        page_layout(
            rx.vstack(
                rx.vstack(
                    rx.heading(LanguageState.tr["switch_role_page_title"], size="6"),
                    rx.text(
                        LanguageState.tr["switch_role_page_subtitle"],
                        size="3",
                        color="var(--gray-9)",
                    ),
                    spacing="1",
                    align="center",
                ),
                rx.vstack(
                    rx.foreach(SwitchRoleState.switchable_roles, _role_card),
                    spacing="3",
                    align="center",
                    width="100%",
                ),
                spacing="6",
                align="center",
                width="100%",
                padding_top="2rem",
            ),
        ),
    )

