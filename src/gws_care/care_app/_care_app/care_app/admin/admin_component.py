"""Settings page component — tabs for Import, User Roles, and Notifications config."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..notifications.notifications_state import NotificationsState
from .admin_state import AdminState, EntityOption, UserRoleRowDTO
from .database_state import FLUSH_CONFIRM_PHRASE, DatabaseState
from .general_settings_state import GeneralSettingsState
from .import_component import import_dialog
from .import_state import ImportState

_ROLE_LABELS = {
    "ADMIN": "Administrator",
    "DOCTOR": "Doctor",
    "OPERATOR": "Operator",
    "ACCOUNT_ADMIN": "Account Admin",
    "PATIENT": "Patient",
}
_ROLE_COLORS = {
    "ADMIN": "red",
    "DOCTOR": "blue",
    "OPERATOR": "green",
    "ACCOUNT_ADMIN": "orange",
    "PATIENT": "purple",
}


# ── User Roles tab ─────────────────────────────────────────────────────────────

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


def _account_option(opt: EntityOption) -> rx.Component:
    return rx.select.item(opt.label, value=opt.id)


def _patient_option(opt: EntityOption) -> rx.Component:
    return rx.select.item(opt.label, value=opt.id)


def _doctor_option(opt: EntityOption) -> rx.Component:
    return rx.select.item(opt.label, value=opt.id)


def _account_chip(account_id: str, account_label: str, user_id: str, role: str) -> rx.Component:
    """Small removable chip for one assigned account."""
    return rx.badge(
        rx.hstack(
            rx.text(account_label, size="1"),
            rx.icon(
                "x",
                size=10,
                cursor="pointer",
                on_click=lambda: AdminState.remove_account_link(user_id, role, account_id),
            ),
            spacing="1",
            align="center",
        ),
        color_scheme="gray",
        variant="soft",
        size="1",
    )


def _account_label_for_id(account_id: rx.Var) -> rx.Component:
    """Resolve an account ID to its label from the account_options list."""
    # Use rx.cond chain — simpler: just show the ID if not found
    # We iterate options and return the matching label; fallback to account_id
    return rx.fragment(
        rx.foreach(
            AdminState.account_options,
            lambda opt: rx.cond(
                opt.id == account_id,
                rx.text(opt.label, size="1"),
                rx.fragment(),
            ),
        )
    )


def _doctor_section(user: UserRoleRowDTO) -> rx.Component:
    """Linked doctor selector shown when the DOCTOR role is assigned."""
    return rx.cond(
        user.roles.contains("DOCTOR"),
        rx.box(
            rx.select.root(
                rx.select.trigger(
                    placeholder=LanguageState.tr["link_doctor_placeholder"],
                    size="1",
                ),
                rx.select.content(
                    rx.select.item(LanguageState.tr["no_doctor_option"], value="__none__"),
                    rx.foreach(AdminState.doctor_options, _doctor_option),
                ),
                value=user.linked_doctor_id,
                on_change=lambda val: AdminState.set_doctor_link(user.id, val),
                size="1",
            ),
            padding_left="1.5rem",
        ),
    )


def _account_admin_section(user: UserRoleRowDTO) -> rx.Component:
    """Multi-account section shown when the ACCOUNT_ADMIN role is assigned."""
    return rx.cond(
        user.roles.contains("ACCOUNT_ADMIN"),
        rx.vstack(
            rx.hstack(
                rx.foreach(
                    user.account_admin_accounts,
                    lambda opt: rx.badge(
                        rx.hstack(
                            rx.text(opt.label, size="1"),
                            rx.icon(
                                "x", size=10, cursor="pointer",
                                on_click=lambda: AdminState.remove_account_link(user.id, "ACCOUNT_ADMIN", opt.id),
                            ),
                            spacing="1", align="center",
                        ),
                        color_scheme="orange", variant="soft", size="1",
                    ),
                ),
                wrap="wrap",
                spacing="1",
            ),
            rx.select.root(
                rx.select.trigger(
                    placeholder=LanguageState.tr["link_account_placeholder"],
                    size="1",
                ),
                rx.select.content(
                    rx.foreach(AdminState.account_options, _account_option),
                ),
                on_change=lambda val: AdminState.add_account_link(user.id, "ACCOUNT_ADMIN", val),
                size="1",
            ),
            spacing="1",
            align="start",
            padding_left="1.5rem",
        ),
    )


def _user_row(user: UserRoleRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(user.full_name, size="2", weight="medium")),
        rx.table.cell(rx.text(user.email, size="2", color="var(--gray-9)")),
        rx.table.cell(
            rx.vstack(
                # ── ADMIN ──────────────────────────────────────────────────
                _role_toggle(user, "ADMIN"),
                # ── DOCTOR + linked doctor profile ──────────────────────────
                rx.vstack(
                    _role_toggle(user, "DOCTOR"),
                    _doctor_section(user),
                    spacing="1",
                    align="start",
                ),
                # ── OPERATOR ───────────────────────────────────────────────
                _role_toggle(user, "OPERATOR"),
                # ── ACCOUNT_ADMIN + account list ───────────────────────────
                rx.vstack(
                    _role_toggle(user, "ACCOUNT_ADMIN"),
                    _account_admin_section(user),
                    spacing="1",
                    align="start",
                ),
                # ── PATIENT + linked patient selector ──────────────────────
                rx.vstack(
                    _role_toggle(user, "PATIENT"),
                    rx.cond(
                        user.roles.contains("PATIENT"),
                        rx.box(
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder=LanguageState.tr["link_patient_placeholder"],
                                    size="1",
                                ),
                                rx.select.content(
                                    rx.foreach(AdminState.patient_options, _patient_option),
                                ),
                                value=user.linked_patient_id,
                                on_change=lambda val: AdminState.set_patient_link(user.id, val),
                                size="1",
                            ),
                            padding_left="1.5rem",
                        ),
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="2",
                align="start",
                padding="0.25rem 0",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _user_roles_tab() -> rx.Component:
    return rx.vstack(
        rx.text(
            LanguageState.tr["roles_hint"],
            size="2",
            color="var(--gray-9)",
        ),
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
        rx.input(
            rx.input.slot(rx.icon("search", size=14)),
            placeholder=LanguageState.tr["filter_users_placeholder"],
            value=AdminState.user_name_filter,
            on_change=AdminState.set_user_name_filter,
            size="2",
            width="100%",
            max_width="320px",
        ),
        rx.cond(
            AdminState.is_loading,
            rx.center(rx.spinner(size="3"), padding="3rem"),
            rx.cond(
                AdminState.filtered_users,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(LanguageState.tr["col_name"]),
                            rx.table.column_header_cell(LanguageState.tr["col_email"]),
                            rx.table.column_header_cell(LanguageState.tr["col_roles"]),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(AdminState.filtered_users, _user_row),
                    ),
                    width="100%",
                    variant="surface",
                ),
                rx.center(
                    rx.text(LanguageState.tr["no_users_found"], size="2", color="var(--gray-8)"),
                    padding="3rem",
                ),
            ),
        ),
        width="100%",
        spacing="3",
    )


# ── Import tab ─────────────────────────────────────────────────────────────────

def _import_tab() -> rx.Component:
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.heading(LanguageState.tr["import_title"], size="4"),
                rx.text(
                    LanguageState.tr["import_desc"],
                    size="2",
                    color="var(--gray-10)",
                ),
                rx.separator(width="100%"),
                rx.hstack(
                    rx.button(
                        rx.icon("users", size=14),
                        LanguageState.tr["import_patients_btn"],
                        on_click=lambda: ImportState.open_import_dialog("patients"),
                        variant="outline",
                        color_scheme="blue",
                        size="2",
                    ),
                    rx.button(
                        rx.icon("building-2", size=14),
                        LanguageState.tr["import_accounts_btn"],
                        on_click=lambda: ImportState.open_import_dialog("accounts"),
                        variant="outline",
                        color_scheme="blue",
                        size="2",
                    ),
                    rx.button(
                        rx.icon("stethoscope", size=14),
                        LanguageState.tr["import_doctors_btn"],
                        on_click=lambda: ImportState.open_import_dialog("doctors"),
                        variant="outline",
                        color_scheme="blue",
                        size="2",
                    ),
                    spacing="3",
                    wrap="wrap",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        width="100%",
        spacing="4",
    )


# ── General tab ───────────────────────────────────────────────────────────────

def _general_tab() -> rx.Component:
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("languages", size=18, color="var(--accent-9)"),
                    rx.heading(LanguageState.tr["language_label"], size="4"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    LanguageState.tr["language_desc"],
                    size="2",
                    color="var(--gray-10)",
                ),
                rx.separator(width="100%"),
                rx.segmented_control.root(
                    rx.segmented_control.item(
                        rx.hstack(
                            rx.icon("flag", size=13),
                            rx.text(LanguageState.tr["language_en"]),
                            spacing="1",
                            align="center",
                        ),
                        value="en",
                    ),
                    rx.segmented_control.item(
                        rx.hstack(
                            rx.icon("flag", size=13),
                            rx.text(LanguageState.tr["language_fr"]),
                            spacing="1",
                            align="center",
                        ),
                        value="fr",
                    ),
                    value=LanguageState.language,
                    on_change=LanguageState.set_language,
                    size="2",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("list", size=18, color="var(--accent-9)"),
                    rx.heading("List page size", size="4"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Maximum number of items displayed per page in patient, account, visit and program lists.",
                    size="2",
                    color="var(--gray-10)",
                ),
                rx.separator(width="100%"),
                rx.hstack(
                    rx.select.root(
                        rx.select.trigger(placeholder=LanguageState.tr["page_size_placeholder"]),
                        rx.select.content(
                            rx.select.item("10 items", value="10"),
                            rx.select.item("25 items", value="25"),
                            rx.select.item("50 items", value="50"),
                            rx.select.item("100 items", value="100"),
                            rx.select.item("200 items", value="200"),
                        ),
                        value=GeneralSettingsState.page_size,
                        on_change=GeneralSettingsState.set_page_size,
                    ),
                    rx.button(
                        "Save",
                        on_click=GeneralSettingsState.save_page_size_setting,
                        loading=GeneralSettingsState.is_saving_page_size,
                        size="2",
                    ),
                    rx.cond(
                        GeneralSettingsState.save_page_size_success != "",
                        rx.badge(GeneralSettingsState.save_page_size_success, color_scheme="green", size="1"),
                    ),
                    rx.cond(
                        GeneralSettingsState.save_page_size_error != "",
                        rx.badge(GeneralSettingsState.save_page_size_error, color_scheme="red", size="1"),
                    ),
                    spacing="3",
                    align="center",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("palette", size=18, color="var(--accent-9)"),
                    rx.heading(LanguageState.tr["theme_label"], size="4"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    LanguageState.tr["theme_desc"],
                    size="2",
                    color="var(--gray-10)",
                ),
                rx.separator(width="100%"),
                rx.hstack(
                    # Green (Constellab primary teal)
                    rx.box(
                        rx.vstack(
                            rx.box(
                                width="40px",
                                height="40px",
                                border_radius="50%",
                                background="linear-gradient(135deg, #1d907d 0%, #25b49c 100%)",
                                box_shadow=rx.cond(
                                    GeneralSettingsState.color_theme == "green",
                                    "0 0 0 3px var(--gray-12)",
                                    "none",
                                ),
                            ),
                            rx.text(LanguageState.tr["theme_green"], size="1", weight=rx.cond(
                                GeneralSettingsState.color_theme == "green", "bold", "regular"
                            )),
                            align="center",
                            spacing="1",
                        ),
                        cursor="pointer",
                        on_click=lambda: GeneralSettingsState.set_color_theme("green"),
                        opacity=rx.cond(GeneralSettingsState.color_theme == "green", "1", "0.6"),
                    ),
                    # Pink (Constellab warn palette)
                    rx.box(
                        rx.vstack(
                            rx.box(
                                width="40px",
                                height="40px",
                                border_radius="50%",
                                background="linear-gradient(135deg, #c35895 0%, #ff93d0 100%)",
                                box_shadow=rx.cond(
                                    GeneralSettingsState.color_theme == "pink",
                                    "0 0 0 3px var(--gray-12)",
                                    "none",
                                ),
                            ),
                            rx.text(LanguageState.tr["theme_pink"], size="1", weight=rx.cond(
                                GeneralSettingsState.color_theme == "pink", "bold", "regular"
                            )),
                            align="center",
                            spacing="1",
                        ),
                        cursor="pointer",
                        on_click=lambda: GeneralSettingsState.set_color_theme("pink"),
                        opacity=rx.cond(GeneralSettingsState.color_theme == "pink", "1", "0.6"),
                    ),
                    # Purple (Constellab accent palette)
                    rx.box(
                        rx.vstack(
                            rx.box(
                                width="40px",
                                height="40px",
                                border_radius="50%",
                                background="linear-gradient(135deg, #675a9d 0%, #c5bbee 100%)",
                                box_shadow=rx.cond(
                                    GeneralSettingsState.color_theme == "purple",
                                    "0 0 0 3px var(--gray-12)",
                                    "none",
                                ),
                            ),
                            rx.text(LanguageState.tr["theme_purple"], size="1", weight=rx.cond(
                                GeneralSettingsState.color_theme == "purple", "bold", "regular"
                            )),
                            align="center",
                            spacing="1",
                        ),
                        cursor="pointer",
                        on_click=lambda: GeneralSettingsState.set_color_theme("purple"),
                        opacity=rx.cond(GeneralSettingsState.color_theme == "purple", "1", "0.6"),
                    ),
                    spacing="5",
                    align="center",
                ),
                rx.cond(
                    GeneralSettingsState.save_theme_success != "",
                    rx.badge(GeneralSettingsState.save_theme_success, color_scheme="green", size="1"),
                ),
                rx.cond(
                    GeneralSettingsState.save_theme_error != "",
                    rx.badge(GeneralSettingsState.save_theme_error, color_scheme="red", size="1"),
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        width="100%",
        spacing="4",
    )

def _day_chip(day: int) -> rx.Component:
    return rx.badge(
        rx.hstack(
            rx.text(f"{day} day(s)", size="2"),
            rx.icon(
                "x",
                size=12,
                cursor="pointer",
                on_click=lambda: NotificationsState.remove_reminder_day(day),
                color="var(--gray-9)",
            ),
            spacing="1",
            align="center",
        ),
        color_scheme="blue",
        variant="soft",
        style={"padding": "4px 8px"},
    )


# ── Notifications config tab ───────────────────────────────────────────────────

def _notifications_tab() -> rx.Component:
    return rx.vstack(
        # ── Email reminder preferences ────────────────────────────────────────
        rx.card(
            rx.vstack(
                rx.heading("Email Reminder Settings", size="4"),
                rx.text(
                    "Automatically send appointment reminder emails to patients on the configured days before their appointment.",
                    size="2",
                    color="var(--gray-10)",
                ),
                rx.separator(width="100%"),
                rx.hstack(
                    rx.text("Enable email reminders", size="2", weight="medium"),
                    rx.spacer(),
                    rx.switch(
                        checked=NotificationsState.pref_enabled,
                        on_change=NotificationsState.set_pref_enabled,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.vstack(
                    rx.text("Remind patients N days before appointment:", size="2", weight="medium"),
                    rx.hstack(
                        rx.foreach(NotificationsState.pref_days, _day_chip),
                        wrap="wrap",
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="e.g. 15",
                            value=NotificationsState.pref_new_day,
                            on_change=NotificationsState.set_pref_new_day,
                            type="number",
                            min="1",
                            size="2",
                            width="120px",
                        ),
                        rx.button(
                            rx.icon("plus", size=14),
                            "Add",
                            on_click=NotificationsState.add_reminder_day,
                            size="2",
                            variant="soft",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.cond(
                    NotificationsState.pref_error != "",
                    rx.callout(NotificationsState.pref_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.cond(
                    NotificationsState.pref_success != "",
                    rx.callout(NotificationsState.pref_success, icon="check", color_scheme="green", size="1"),
                ),
                rx.hstack(
                    rx.button(
                        rx.icon("save", size=14),
                        "Save Preferences",
                        on_click=NotificationsState.save_preferences,
                        loading=NotificationsState.is_saving_pref,
                        size="2",
                    ),
                    spacing="2",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        # ── SMTP server configuration ────────────────────────────────────────
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("mail", size=18, color="var(--accent-9)"),
                    rx.heading("SMTP Configuration", size="4"),
                    rx.spacer(),
                    rx.cond(
                        NotificationsState.smtp_is_loading,
                        rx.spinner(size="2"),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.text(
                    "Configure the outgoing SMTP server used for email notifications. "
                    "The password is stored securely via a Constellab Credentials record (type BASIC) — "
                    "never entered here directly.",
                    size="2",
                    color="var(--gray-10)",
                ),
                rx.separator(width="100%"),
                # Row 1: host + port
                rx.hstack(
                    rx.vstack(
                        rx.text("Host", size="2", weight="medium"),
                        rx.input(
                            placeholder="smtp.example.com",
                            value=NotificationsState.smtp_host,
                            on_change=NotificationsState.smtp_set_host,
                            size="2",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Port", size="2", weight="medium"),
                        rx.input(
                            placeholder="587",
                            value=NotificationsState.smtp_port,
                            on_change=NotificationsState.smtp_set_port,
                            type="number",
                            min="1",
                            max="65535",
                            size="2",
                            width="120px",
                        ),
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                    align="end",
                ),
                # Row 2: from_email + from_name
                rx.hstack(
                    rx.vstack(
                        rx.text("From email", size="2", weight="medium"),
                        rx.input(
                            placeholder="noreply@example.com",
                            value=NotificationsState.smtp_from_email,
                            on_change=NotificationsState.smtp_set_from_email,
                            size="2",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("From name", size="2", weight="medium"),
                        rx.input(
                            placeholder="Constellab Care",
                            value=NotificationsState.smtp_from_name,
                            on_change=NotificationsState.smtp_set_from_name,
                            size="2",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                    align="end",
                ),
                # Row 3: credentials name + TLS toggle
                rx.hstack(
                    rx.vstack(
                        rx.text("Credentials name", size="2", weight="medium"),
                        rx.input(
                            placeholder="my-smtp-credentials",
                            value=NotificationsState.smtp_credentials_name,
                            on_change=NotificationsState.smtp_set_credentials_name,
                            size="2",
                            width="100%",
                        ),
                        rx.text(
                            "Name of a Constellab BASIC Credentials record (type BASIC) — provides the login and password",
                            size="1",
                            color="var(--gray-9)",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Use TLS", size="2", weight="medium"),
                        rx.switch(
                            checked=NotificationsState.smtp_use_tls,
                            on_change=NotificationsState.smtp_set_use_tls,
                        ),
                        spacing="1",
                        align="center",
                    ),
                    spacing="3",
                    width="100%",
                    align="end",
                ),
                # Feedback
                rx.cond(
                    NotificationsState.smtp_error != "",
                    rx.callout(NotificationsState.smtp_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.cond(
                    NotificationsState.smtp_success != "",
                    rx.callout(NotificationsState.smtp_success, icon="check", color_scheme="green", size="1"),
                ),
                rx.cond(
                    NotificationsState.smtp_test_result.contains("successful"),
                    rx.callout(NotificationsState.smtp_test_result, icon="circle-check", color_scheme="green", size="1"),
                    rx.cond(
                        NotificationsState.smtp_test_result != "",
                        rx.callout(NotificationsState.smtp_test_result, icon="triangle-alert", color_scheme="red", size="1"),
                    ),
                ),
                # Buttons
                rx.hstack(
                    rx.button(
                        rx.icon("plug", size=14),
                        "Test Connection",
                        on_click=NotificationsState.test_smtp_connection,
                        loading=NotificationsState.smtp_is_testing,
                        size="2",
                        variant="soft",
                        color_scheme="blue",
                    ),
                    rx.button(
                        rx.icon("save", size=14),
                        "Save",
                        on_click=NotificationsState.save_smtp_config,
                        loading=NotificationsState.smtp_is_saving,
                        size="2",
                    ),
                    spacing="2",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        # ── Send reminders manually ───────────────────────────────────────────
        rx.card(
            rx.vstack(
                rx.heading("Send Reminders Now", size="4"),
                rx.text(
                    "Trigger reminder processing immediately for all upcoming appointments matching your configured reminder days.",
                    size="2",
                    color="var(--gray-10)",
                ),
                rx.hstack(
                    rx.button(
                        rx.icon("send", size=14),
                        "Process Reminders",
                        on_click=NotificationsState.process_reminders,
                        loading=NotificationsState.is_processing_reminders,
                        size="2",
                        color_scheme="blue",
                    ),
                    rx.cond(
                        NotificationsState.reminder_result != "",
                        rx.text(NotificationsState.reminder_result, size="2", color="var(--gray-10)"),
                    ),
                    spacing="3",
                    align="center",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ── Database tab (dev mode only) ───────────────────────────────────────────────

def _flush_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.icon("triangle-alert", size=20, color="var(--red-9)"),
                rx.dialog.title("Flush database", color="var(--red-11)"),
                spacing="2",
                align="center",
                margin_bottom="0.5rem",
            ),
            rx.vstack(
                rx.callout(
                    "This will permanently erase ALL data in the database. "
                    "This action cannot be undone.",
                    icon="skull",
                    color_scheme="red",
                    size="2",
                ),
                rx.vstack(
                    rx.text(
                        "To confirm, copy and paste the following phrase exactly:",
                        size="2",
                        weight="medium",
                    ),
                    rx.code(
                        FLUSH_CONFIRM_PHRASE,
                        size="1",
                        color_scheme="red",
                        style={"user_select": "all", "word_break": "break-all"},
                    ),
                    rx.text_area(
                        value=DatabaseState.db_flush_confirm_text,
                        on_change=DatabaseState.set_flush_confirm_text,
                        placeholder="Paste the phrase here…",
                        size="2",
                        width="100%",
                        rows="3",
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.cond(
                    DatabaseState.db_flush_error != "",
                    rx.callout(
                        DatabaseState.db_flush_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                rx.hstack(
                    rx.button(
                        rx.cond(
                            DatabaseState.db_flush_is_flushing,
                            rx.hstack(rx.spinner(size="2"), rx.text("Flushing…"), spacing="2", align="center"),
                            rx.hstack(rx.icon("trash-2", size=14), rx.text("Flush database"), spacing="2", align="center"),
                        ),
                        on_click=DatabaseState.flush_database,
                        disabled=~DatabaseState.flush_confirm_valid | DatabaseState.db_flush_is_flushing,
                        color_scheme="red",
                        size="2",
                    ),
                    rx.button(
                        "Cancel",
                        on_click=DatabaseState.close_flush_dialog,
                        variant="outline",
                        color_scheme="gray",
                        size="2",
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            on_interact_outside=DatabaseState.close_flush_dialog,
            on_escape_key_down=DatabaseState.close_flush_dialog,
            max_width="520px",
        ),
        open=DatabaseState.db_flush_open,
    )


def _database_tab() -> rx.Component:
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("trash-2", size=18, color="var(--red-9)"),
                    rx.heading("Flush database", size="4", color="var(--red-11)"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Delete all data from every table in the gws_care database. "
                    "The schema is preserved — tables are kept empty. "
                    "Only available in dev mode.",
                    size="2",
                    color="var(--gray-10)",
                ),
                rx.separator(width="100%"),
                rx.cond(
                    DatabaseState.db_flush_success != "",
                    rx.callout(
                        DatabaseState.db_flush_success,
                        icon="circle-check",
                        color_scheme="green",
                        size="1",
                    ),
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    "Flush all data…",
                    on_click=DatabaseState.open_flush_dialog,
                    color_scheme="red",
                    variant="soft",
                    size="2",
                ),
                _flush_dialog(),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        width="100%",
        spacing="4",
    )


# ── Page ───────────────────────────────────────────────────────────────────────

def _settings_header_admin() -> rx.Component:
    return rx.hstack(
        rx.icon("settings", size=22, color="var(--accent-9)"),
        rx.heading(LanguageState.tr["settings_title"], size="6"),
        rx.spacer(),
        rx.badge(
            LanguageState.tr["settings_admin_only"],
            color_scheme="red",
            variant="soft",
            size="2",
        ),
        width="100%",
        align="center",
        spacing="2",
    )


def _settings_header_user() -> rx.Component:
    return rx.hstack(
        rx.icon("settings", size=22, color="var(--accent-9)"),
        rx.heading(LanguageState.tr["settings_title"], size="6"),
        width="100%",
        align="center",
        spacing="2",
    )


def settings_page() -> rx.Component:
    """Settings page — full 4-tab view for admin, General-only for other roles."""
    return main_component(
        page_layout(
            import_dialog(),
            rx.cond(
                AdminState.is_admin,
                # ── Admin view: 4 tabs ────────────────────────────────────────
                rx.vstack(
                    _settings_header_admin(),
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger(
                                rx.hstack(
                                    rx.icon("globe", size=15),
                                    rx.text(LanguageState.tr["settings_tab_general"]),
                                    spacing="1",
                                    align="center",
                                ),
                                value="general",
                            ),
                            rx.tabs.trigger(
                                rx.hstack(
                                    rx.icon("file-up", size=15),
                                    rx.text(LanguageState.tr["settings_tab_import"]),
                                    spacing="1",
                                    align="center",
                                ),
                                value="import",
                            ),
                            rx.tabs.trigger(
                                rx.hstack(
                                    rx.icon("shield", size=15),
                                    rx.text(LanguageState.tr["settings_tab_roles"]),
                                    spacing="1",
                                    align="center",
                                ),
                                value="roles",
                            ),
                            rx.tabs.trigger(
                                rx.hstack(
                                    rx.icon("bell", size=15),
                                    rx.text(LanguageState.tr["settings_tab_notifications"]),
                                    spacing="1",
                                    align="center",
                                ),
                                value="notifications",
                            ),
                            rx.cond(
                                DatabaseState.is_dev_mode,
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("database", size=15),
                                        rx.text("Database"),
                                        spacing="1",
                                        align="center",
                                    ),
                                    value="database",
                                ),
                                rx.fragment(),
                            ),
                        ),
                        rx.tabs.content(_general_tab(), value="general", padding_top="1rem"),
                        rx.tabs.content(_import_tab(), value="import", padding_top="1rem"),
                        rx.tabs.content(_user_roles_tab(), value="roles", padding_top="1rem"),
                        rx.tabs.content(_notifications_tab(), value="notifications", padding_top="1rem"),
                        rx.cond(
                            DatabaseState.is_dev_mode,
                            rx.tabs.content(_database_tab(), value="database", padding_top="1rem"),
                            rx.fragment(),
                        ),
                        default_value="general",
                        width="100%",
                    ),
                    width="100%",
                    spacing="4",
                ),
                # ── Non-admin view: General tab only ──────────────────────────
                rx.cond(
                    AdminState.has_any_role,
                    rx.vstack(
                        _settings_header_user(),
                        _general_tab(),
                        width="100%",
                        spacing="4",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("lock", size=40, color="var(--gray-7)"),
                            rx.text(
                                LanguageState.tr["access_denied"],
                                size="3",
                                color="var(--gray-9)",
                            ),
                            spacing="3",
                            align="center",
                        ),
                        padding="4rem",
                    ),
                ),
            ),
        )
    )
