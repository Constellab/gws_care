"""Shared page layout with collapsible sidebar navigation."""

import reflex as rx
from gws_reflex_main import menu_item_component

from ..admin.general_settings_state import GeneralSettingsState
from .bell_state import BellEntryDTO, BellState
from .language_state import LanguageState
from .role_state import RoleState
from .user_menu_component import user_menu_button

_SIDEBAR_FULL = "300px"
_SIDEBAR_FOLDED = "60px"


class SidebarFoldState(rx.State):
    is_folded: bool = False

    def toggle(self) -> None:
        self.is_folded = not self.is_folded

    def fold(self) -> None:
        self.is_folded = True

    def unfold(self) -> None:
        self.is_folded = False

    @rx.var
    def current_path(self) -> str:
        return self.router.page.path


# ── Bell notification popover ─────────────────────────────────────────────────


def _bell_entry(entry: BellEntryDTO) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.cond(
                    ~entry.is_read,
                    rx.box(
                        width="6px", height="6px", border_radius="50%", background="var(--accent-9)"
                    ),
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
                        rx.text(
                            LanguageState.tr["notifications_empty"], size="2", color="var(--gray-9)"
                        ),
                        padding="1rem",
                    ),
                ),
                rx.link(
                    rx.text(
                        LanguageState.tr["notifications_view_all"],
                        size="2",
                        color="var(--accent-9)",
                    ),
                    href=rx.cond(RoleState.is_patient_user, "/my-notifications", "/notifications"),
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


# ── Nav helpers ───────────────────────────────────────────────────────────────


def _nav_group_label(label: str) -> rx.Component:
    """Category header: full text when open, thin separator when folded."""
    return rx.cond(
        SidebarFoldState.is_folded,
        rx.separator(margin_y="0.4rem", width="70%", margin_x="auto"),
        rx.text(
            label,
            size="1",
            color="var(--gray-9)",
            weight="bold",
            text_transform="uppercase",
            letter_spacing="0.05em",
            padding_left="0.5rem",
            padding_top="0.5rem",
        ),
    )


def _folded_item(icon_name: str, label, href: str) -> rx.Component:
    """Icon-only nav item used when the sidebar is folded."""
    is_active = SidebarFoldState.current_path == href
    return rx.tooltip(
        rx.link(
            rx.center(
                rx.icon(
                    icon_name,
                    size=20,
                    color=rx.cond(is_active, "var(--accent-9)", "var(--gray-11)"),
                ),
                width="100%",
                padding_y="0.45rem",
                border_radius="var(--radius-2)",
                background=rx.cond(is_active, "var(--accent-3)", "transparent"),
                _hover={"background": rx.cond(is_active, "var(--accent-4)", "var(--gray-3)")},
            ),
            href=href,
            width="100%",
            text_decoration="none",
        ),
        content=label,
        side="right",
    )


def _nav_item(
    icon_name: str,
    label,
    href: str,
    additional_active_route_prefixes: list[str] | None = None,
) -> rx.Component:
    """Full or folded nav item depending on sidebar state."""
    full = menu_item_component(
        icon_name,
        label,
        href,
        **(
            {"additional_active_route_prefixes": additional_active_route_prefixes}
            if additional_active_route_prefixes
            else {}
        ),
    )
    return rx.cond(SidebarFoldState.is_folded, _folded_item(icon_name, label, href), full)


# ── Sidebar content ───────────────────────────────────────────────────────────


def _sidebar_content() -> rx.Component:
    return rx.box(
        # ── Header + toggle badge ─────────────────────────────────────────────
        rx.cond(
            SidebarFoldState.is_folded,
            # Folded: logo icon then arrow badge stacked — no overlap at 60 px
            rx.vstack(
                rx.center(
                    rx.icon("heart-pulse", size=24, color="var(--accent-9)"),
                    width="100%",
                    padding_top="0.9em",
                ),
                rx.center(
                    rx.icon_button(
                        rx.icon("chevron-right", size=14),
                        on_click=SidebarFoldState.toggle,
                        variant="soft",
                        size="1",
                        color_scheme="gray",
                        cursor="pointer",
                    ),
                    width="100%",
                    padding_bottom="0.6em",
                ),
                spacing="2",
                width="100%",
            ),
            # Unfolded: logo + title on the left, arrow badge on the right
            rx.hstack(
                rx.icon("heart-pulse", size=28, color="var(--accent-9)"),
                rx.vstack(
                    rx.heading("Constellab Care", size="4", line_height="1em"),
                    rx.text("By Constellab", size="1", color="var(--gray-9)", line_height="1em"),
                    spacing="1",
                    flex="1",
                ),
                rx.icon_button(
                    rx.icon("chevron-left", size=14),
                    on_click=SidebarFoldState.toggle,
                    variant="soft",
                    size="1",
                    color_scheme="gray",
                    cursor="pointer",
                ),
                spacing="2",
                align="center",
                padding="0.85em 0.75em 0.85em 1em",
                width="100%",
            ),
        ),
        # ── Nav (scrollable) ──────────────────────────────────────────────────
        rx.vstack(
            # Patient portal
            rx.cond(
                RoleState.is_patient_user,
                rx.vstack(
                    _nav_group_label(LanguageState.tr["nav_group_patient_essentials"]),
                    _nav_item(
                        "layout-dashboard",
                        LanguageState.tr["nav_patient_dashboard"],
                        "/patient-dashboard",
                    ),
                    _nav_item(
                        "calendar-plus", LanguageState.tr["nav_my_appointments"], "/my-appointments"
                    ),
                    _nav_item(
                        "stethoscope", LanguageState.tr["nav_my_consultations"], "/my-consultations"
                    ),
                    _nav_item(
                        "bell", LanguageState.tr["nav_my_notifications"], "/my-notifications"
                    ),
                    _nav_group_label(LanguageState.tr["nav_group_patient_documents"]),
                    _nav_item(
                        "file-text", LanguageState.tr["nav_my_prescriptions"], "/my-prescriptions"
                    ),
                    _nav_item(
                        "folder-open", LanguageState.tr["nav_my_all_documents"], "/my-all-documents"
                    ),
                    width="100%",
                    spacing="1",
                    align_items="start",
                ),
            ),
            # Essentials — Operator, Doctor
            rx.cond(
                RoleState.is_operator | RoleState.is_doctor,
                rx.vstack(
                    _nav_group_label(LanguageState.tr["nav_group_essentials"]),
                    _nav_item("layout-dashboard", LanguageState.tr["nav_dashboard"], "/dashboard"),
                    _nav_item("users", LanguageState.tr["nav_patients"], "/"),
                    _nav_item(
                        "calendar-clock", LanguageState.tr["nav_appointments"], "/appointments"
                    ),
                    _nav_item(
                        "stethoscope",
                        LanguageState.tr["nav_consultations"],
                        "/consultations",
                        additional_active_route_prefixes=["/consultation/"],
                    ),
                    _nav_item("bell", LanguageState.tr["nav_notifications"], "/notifications"),
                    _nav_item(
                        "message-circle",
                        LanguageState.tr["nav_messaging"],
                        "/messaging",
                    ),
                    width="100%",
                    spacing="1",
                    align_items="start",
                ),
            ),
            # Campaigns — Operator, Doctor
            rx.cond(
                RoleState.is_operator | RoleState.is_doctor,
                rx.vstack(
                    _nav_group_label(LanguageState.tr["nav_group_campaigns"]),
                    _nav_item(
                        "clipboard-list",
                        LanguageState.tr["nav_campaigns"],
                        "/campaigns",
                        additional_active_route_prefixes=["/campaign/"],
                    ),
                    _nav_item(
                        "calendar",
                        LanguageState.tr["nav_campaign_visits"],
                        "/campaign-visits",
                        additional_active_route_prefixes=["/visit/"],
                    ),
                    width="100%",
                    spacing="1",
                    align_items="start",
                ),
            ),
            # Documents — Operator, Doctor, Admin
            rx.cond(
                RoleState.is_operator | RoleState.is_doctor | RoleState.is_admin,
                rx.vstack(
                    _nav_group_label(LanguageState.tr["nav_group_documents"]),
                    _nav_item("folder-open", LanguageState.tr["nav_admin_documents"], "/documents"),
                    width="100%",
                    spacing="1",
                    align_items="start",
                ),
            ),
            # Administration — Operator, Doctor, Admin, Account Admin
            rx.cond(
                RoleState.is_operator
                | RoleState.is_doctor
                | RoleState.is_admin
                | RoleState.is_account_admin,
                rx.vstack(
                    _nav_group_label(LanguageState.tr["nav_group_administration"]),
                    rx.cond(
                        RoleState.is_operator | RoleState.is_admin | RoleState.is_account_admin,
                        _nav_item(
                            "building-2",
                            LanguageState.tr["nav_accounts"],
                            "/accounts",
                            additional_active_route_prefixes=["/account"],
                        ),
                    ),
                    rx.cond(
                        RoleState.is_operator | RoleState.is_admin | RoleState.is_account_admin,
                        _nav_item(
                            "user-round-check", LanguageState.tr["nav_doctors"], "/doctors"
                        ),
                    ),
                    rx.cond(
                        RoleState.is_operator | RoleState.is_admin | RoleState.is_account_admin,
                        _nav_item(
                            "calendar-clock",
                            LanguageState.tr["nav_doctor_schedule"],
                            "/doctor-schedule",
                        ),
                    ),
                    rx.cond(
                        RoleState.is_doctor | RoleState.is_operator | RoleState.is_admin,
                        _nav_item("stethoscope", "Mes examens assignés", "/my-assigned-exams"),
                    ),
                    rx.cond(
                        RoleState.is_admin,
                        _nav_item("shield-check", LanguageState.tr["nav_audit_log"], "/audit-log"),
                    ),
                    width="100%",
                    spacing="1",
                    align_items="start",
                ),
            ),
            width="100%",
            spacing="4",
            align_items="start",
            padding_x=rx.cond(SidebarFoldState.is_folded, "0.35rem", "1rem"),
            overflow_y="auto",
            flex="1",
            min_height="0",
        ),
        # ── Footer ────────────────────────────────────────────────────────────
        rx.cond(
            SidebarFoldState.is_folded,
            rx.center(
                rx.icon("circle-user-round", size=22, color="var(--gray-9)"),
                width="100%",
                padding_y="0.75rem",
            ),
            rx.box(
                user_menu_button(),
                width="100%",
                padding="0 1rem 0.75rem 1rem",
            ),
        ),
        # Box props
        position="relative",
        width="100%",
        height="100%",
        display="flex",
        flex_direction="column",
        align_items="start",
        overflow="hidden",
    )


# ── Page layout ───────────────────────────────────────────────────────────────


def page_layout(*children: rx.Component, **kwargs) -> rx.Component:
    """Wrap content in the standard collapsible sidebar layout."""
    sidebar_width = rx.cond(SidebarFoldState.is_folded, _SIDEBAR_FOLDED, _SIDEBAR_FULL)

    vstack_props = {
        "width": "100%",
        "spacing": "4",
        "padding": "1.5rem",
        "min_width": "0",
        "overflow_x": "hidden",
        "flex_shrink": "0",
    }
    vstack_props.update(kwargs)

    return rx.box(
        rx.el.style(GeneralSettingsState.theme_css),
        # Hidden buttons used by the JS resize listener to drive Reflex state
        rx.box(
            rx.icon_button(
                rx.icon("chevron-right", size=1),
                id="__care-fold-btn",
                on_click=SidebarFoldState.fold,
                display="none",
            ),
            rx.icon_button(
                rx.icon("chevron-left", size=1),
                id="__care-unfold-btn",
                on_click=SidebarFoldState.unfold,
                display="none",
            ),
        ),
        # Auto-fold on small screens, auto-unfold when resized back
        rx.script("""
(function() {
    var BP = 768;
    var lastSmall = null;
    function applyFold() {
        var isSmall = window.innerWidth < BP;
        if (isSmall === lastSmall) return;
        lastSmall = isSmall;
        var btn = document.getElementById(isSmall ? '__care-fold-btn' : '__care-unfold-btn');
        if (btn) btn.click();
    }
    setTimeout(applyFold, 150);
    window.addEventListener('resize', applyFold);
})();
"""),
        # Fixed sidebar
        rx.box(
            _sidebar_content(),
            position="fixed",
            left="0",
            top="0",
            height="100vh",
            width=sidebar_width,
            background="white",
            border_right="1px solid var(--gray-4)",
            z_index="10",
            overflow="hidden",
            style={"transition": "width 0.22s ease"},
        ),
        # Content area — offset by sidebar width
        rx.box(
            rx.vstack(*children, **vstack_props),
            margin_left=sidebar_width,
            height="100vh",
            overflow_y="auto",
            style={"transition": "margin-left 0.22s ease"},
        ),
        width="100%",
        position="relative",
    )
