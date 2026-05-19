"""Settings page component — tabs for Import, User Roles, and Notifications config."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..notifications.notifications_state import NotificationsState
from .admin_state import AdminState, EntityOption, StaffContactDTO, UserRoleRowDTO
from .import_component import import_dialog
from .import_state import ImportState

_PSC_STAFF_ROLES = [
    "SUPER_ADMIN_PSC", "DIRECTEUR_PSC", "ADMIN_PSC",
    "OPERATEUR_TERRAIN", "OPERATEUR_LABO", "MEDECIN_PSC",
]
_COMPANY_ROLES = ["MEDECIN_ENTREPRISE", "RH_ENTREPRISE"]
_ALL_ROLES = _PSC_STAFF_ROLES + _COMPANY_ROLES + ["PATIENT"]
_ROLE_LABELS = {
    "SUPER_ADMIN_PSC": "Super Admin PSC",
    "DIRECTEUR_PSC": "Directeur PSC",
    "ADMIN_PSC": "Admin PSC",
    "OPERATEUR_TERRAIN": "Opér. terrain",
    "OPERATEUR_LABO": "Opér. labo",
    "MEDECIN_PSC": "Médecin PSC",
    "MEDECIN_ENTREPRISE": "Méd. entreprise",
    "RH_ENTREPRISE": "RH entreprise",
    "PATIENT": "Patient",
}
_ROLE_COLORS = {
    "SUPER_ADMIN_PSC": "red",
    "DIRECTEUR_PSC": "crimson",
    "ADMIN_PSC": "orange",
    "OPERATEUR_TERRAIN": "green",
    "OPERATEUR_LABO": "teal",
    "MEDECIN_PSC": "blue",
    "MEDECIN_ENTREPRISE": "indigo",
    "RH_ENTREPRISE": "amber",
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


def _user_row(user: UserRoleRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(user.full_name, size="2", weight="medium")),
        rx.table.cell(rx.text(user.email, size="2", color="var(--gray-9)")),
        rx.table.cell(
            rx.vstack(
                # PSC staff role toggles
                rx.text("Équipe PSC", size="1", color="var(--gray-9)", weight="medium"),
                rx.hstack(
                    rx.foreach(
                        rx.Var.create(_PSC_STAFF_ROLES),
                        lambda role: _role_toggle(user, role),
                    ),
                    spacing="1",
                    flex_wrap="wrap",
                ),
                rx.separator(width="100%"),
                # Company roles (Médecin Entreprise + RH) — require account link
                rx.text("Rôles entreprise", size="1", color="var(--gray-9)", weight="medium"),
                rx.hstack(
                    _role_toggle(user, "MEDECIN_ENTREPRISE"),
                    _role_toggle(user, "RH_ENTREPRISE"),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    user.roles.contains("MEDECIN_ENTREPRISE") | user.roles.contains("RH_ENTREPRISE"),
                    rx.hstack(
                        rx.text("Compte:", size="1", color="var(--gray-9)"),
                        rx.select.root(
                            rx.select.trigger(placeholder="Lier un compte…"),
                            rx.select.content(
                                rx.foreach(AdminState.account_options, _account_option),
                            ),
                            value=user.linked_account_id,
                            on_change=lambda val: AdminState.set_account_link(user.id, val),
                            size="1",
                        ),
                        spacing="2",
                        align="center",
                    ),
                ),
                rx.separator(width="100%"),
                # Patient role
                rx.text("Espace patient", size="1", color="var(--gray-9)", weight="medium"),
                rx.hstack(
                    _role_toggle(user, "PATIENT"),
                    rx.cond(
                        user.roles.contains("PATIENT"),
                        rx.select.root(
                            rx.select.trigger(placeholder="Lier un patient…"),
                            rx.select.content(
                                rx.foreach(AdminState.patient_options, _patient_option),
                            ),
                            value=user.linked_patient_id,
                            on_change=lambda val: AdminState.set_patient_link(user.id, val),
                            size="1",
                        ),
                    ),
                    spacing="2",
                    align="center",
                ),
                spacing="2",
                align="start",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _user_roles_tab() -> rx.Component:
    """Replaced by the dedicated /users page — show a redirect card."""
    return rx.vstack(
        rx.callout(
            "La gestion des utilisateurs a été déplacée sur une page dédiée pour plus de clarté.",
            icon="info",
            color_scheme="blue",
            size="2",
        ),
        rx.button(
            rx.icon("users", size=16),
            "Aller à la gestion des utilisateurs",
            size="3",
            on_click=rx.redirect("/users"),
        ),
        rx.separator(width="100%"),
        rx.text("Utilisateurs actuels", size="3", weight="bold"),
        rx.cond(
            AdminState.error_message != "",
            rx.callout(AdminState.error_message, icon="triangle-alert", color_scheme="red"),
        ),
        rx.cond(
            AdminState.is_loading,
            rx.center(rx.spinner(size="3"), padding="3rem"),
            rx.cond(
                AdminState.users,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Nom"),
                            rx.table.column_header_cell("Email"),
                            rx.table.column_header_cell("Rôles"),
                        )
                    ),
                    rx.table.body(rx.foreach(AdminState.users, _user_row)),
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


# ── Annuaire (staff directory) tab ───────────────────────────────────────────────

_STAFF_ROLE_ICON = {
    "MEDECIN_PSC": "stethoscope",
    "MEDECIN_ENTREPRISE": "briefcase-medical",
    "RH_ENTREPRISE": "users",
}
_STAFF_ROLE_COLOR = {
    "MEDECIN_PSC": "blue",
    "MEDECIN_ENTREPRISE": "indigo",
    "RH_ENTREPRISE": "amber",
}


def _staff_card(s: StaffContactDTO) -> rx.Component:
    icon_name = rx.match(
        s.role,
        ("MEDECIN_PSC", "stethoscope"),
        ("MEDECIN_ENTREPRISE", "briefcase-medical"),
        ("RH_ENTREPRISE", "users"),
        "user",
    )
    chip_color = rx.match(
        s.role,
        ("MEDECIN_PSC", "blue"),
        ("MEDECIN_ENTREPRISE", "indigo"),
        ("RH_ENTREPRISE", "amber"),
        "gray",
    )
    return rx.card(
        rx.hstack(
            rx.box(
                rx.icon(icon_name, size=20, color="var(--accent-9)"),
                padding="0.5rem",
                border_radius="8px",
                background="var(--accent-3)",
                flex_shrink="0",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text(s.full_name, size="3", weight="bold"),
                    rx.badge(s.role_label, color_scheme=chip_color, size="1", variant="soft"),
                    spacing="2",
                    align="center",
                    flex_wrap="wrap",
                ),
                rx.hstack(
                    rx.icon("mail", size=13, color="var(--gray-8)"),
                    rx.cond(
                        s.email != "",
                        rx.link(s.email, href=f"mailto:{s.email}", size="2"),
                        rx.text("— email non renseigné", size="2", color="var(--gray-7)"),
                    ),
                    spacing="1",
                    align="center",
                ),
                rx.cond(
                    s.linked_account_name != "",
                    rx.hstack(
                        rx.icon("building-2", size=13, color="var(--gray-8)"),
                        rx.text(s.linked_account_name, size="2", color="var(--gray-10)"),
                        spacing="1",
                        align="center",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align_items="start",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def _staff_section(role_key: str, title: str, icon: str, color: str) -> rx.Component:
    filtered = AdminState.staff_contacts
    return rx.vstack(
        rx.hstack(
            rx.icon(icon, size=16, color=f"var(--{color}-9)"),
            rx.heading(title, size="4"),
            rx.badge(
                AdminState.staff_contacts.length().to(str),
                color_scheme=color,
                variant="soft",
                size="1",
            ),
            spacing="2",
            align="center",
        ),
        rx.separator(width="100%"),
        rx.foreach(
            AdminState.staff_contacts,
            lambda s: rx.cond(
                s.role == role_key,
                _staff_card(s),
                rx.fragment(),
            ),
        ),
        width="100%",
        spacing="2",
    )


def _staff_directory_tab() -> rx.Component:
    return rx.vstack(
        rx.callout(
            "Cet annuaire liste tous les médecins et RH enregistrés dans le système. "
            "Pour ajouter un contact, créez-le dans l’onglet « Gestion utilisateurs » "
            "puis assignez-lui un rôle dans l’onglet « Rôles ».",
            icon="info",
            color_scheme="blue",
            size="1",
        ),
        rx.cond(
            AdminState.staff_contacts.length() == 0,
            rx.center(
                rx.vstack(
                    rx.icon("users", size=36, color="var(--gray-5)"),
                    rx.text(
                        "Aucun médecin ou contact RH trouvé.",
                        size="2", color="var(--gray-9)",
                    ),
                    rx.text(
                        "Allez dans Gestion utilisateurs pour en créer un.",
                        size="2", color="var(--gray-8)",
                    ),
                    spacing="2", align="center",
                ),
                padding="4rem",
            ),
            rx.vstack(
                # PSC doctors section
                rx.vstack(
                    rx.hstack(
                        rx.icon("stethoscope", size=16, color="var(--blue-9)"),
                        rx.heading("Médecins PSC", size="4"),
                        spacing="2", align="center",
                    ),
                    rx.separator(width="100%"),
                    rx.foreach(
                        AdminState.staff_contacts,
                        lambda s: rx.cond(
                            s.role == "MEDECIN_PSC",
                            _staff_card(s),
                            rx.fragment(),
                        ),
                    ),
                    width="100%", spacing="2",
                ),
                rx.separator(width="100%", margin_y="0.5rem"),
                # Enterprise doctors section
                rx.vstack(
                    rx.hstack(
                        rx.icon("briefcase-medical", size=16, color="var(--indigo-9)"),
                        rx.heading("Médecins Entreprise", size="4"),
                        spacing="2", align="center",
                    ),
                    rx.separator(width="100%"),
                    rx.foreach(
                        AdminState.staff_contacts,
                        lambda s: rx.cond(
                            s.role == "MEDECIN_ENTREPRISE",
                            _staff_card(s),
                            rx.fragment(),
                        ),
                    ),
                    width="100%", spacing="2",
                ),
                rx.separator(width="100%", margin_y="0.5rem"),
                # RH section
                rx.vstack(
                    rx.hstack(
                        rx.icon("users", size=16, color="var(--amber-9)"),
                        rx.heading("RH Entreprise", size="4"),
                        spacing="2", align="center",
                    ),
                    rx.separator(width="100%"),
                    rx.foreach(
                        AdminState.staff_contacts,
                        lambda s: rx.cond(
                            s.role == "RH_ENTREPRISE",
                            _staff_card(s),
                            rx.fragment(),
                        ),
                    ),
                    width="100%", spacing="2",
                ),
                width="100%",
                spacing="3",
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
        width="100%",
        spacing="4",
    )


# ── Notification preferences helpers ──────────────────────────────────────────

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
        # ── SMTP server configuration ─────────────────────────────────────────
        rx.card(
            rx.vstack(
                rx.heading("SMTP Server Configuration", size="4"),
                rx.text(
                    "Configure the outgoing mail server used to deliver notification emails.",
                    size="2",
                    color="var(--gray-10)",
                ),
                rx.separator(width="100%"),
                rx.grid(
                    rx.vstack(
                        rx.text("SMTP Host", size="2", weight="medium"),
                        rx.input(
                            placeholder="smtp.example.com",
                            value=NotificationsState.smtp_host,
                            on_change=NotificationsState.set_smtp_host,
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
                            on_change=NotificationsState.set_smtp_port,
                            type="number",
                            min="1",
                            max="65535",
                            size="2",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Username", size="2", weight="medium"),
                        rx.input(
                            placeholder="user@example.com",
                            value=NotificationsState.smtp_username,
                            on_change=NotificationsState.set_smtp_username,
                            size="2",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Credentials Name", size="2", weight="medium"),
                        rx.input(
                            placeholder="e.g. smtp-care",
                            value=NotificationsState.smtp_credentials_name,
                            on_change=NotificationsState.set_smtp_credentials_name,
                            size="2",
                            width="100%",
                        ),
                        rx.text(
                            "Name of a Constellab Credentials (type Basic) that holds the SMTP password. The password is never stored in the app database.",
                            size="1",
                            color="var(--gray-9)",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("From Email", size="2", weight="medium"),
                        rx.input(
                            placeholder="noreply@example.com",
                            value=NotificationsState.smtp_from_email,
                            on_change=NotificationsState.set_smtp_from_email,
                            size="2",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("From Name", size="2", weight="medium"),
                        rx.input(
                            placeholder="Constellab Care",
                            value=NotificationsState.smtp_from_name,
                            on_change=NotificationsState.set_smtp_from_name,
                            size="2",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Use TLS", size="2", weight="medium"),
                    rx.spacer(),
                    rx.switch(
                        checked=NotificationsState.smtp_use_tls,
                        on_change=NotificationsState.set_smtp_use_tls,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    NotificationsState.smtp_error != "",
                    rx.callout(NotificationsState.smtp_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.cond(
                    NotificationsState.smtp_success != "",
                    rx.callout(NotificationsState.smtp_success, icon="check", color_scheme="green", size="1"),
                ),
                rx.button(
                    rx.icon("save", size=14),
                    "Save SMTP Settings",
                    on_click=NotificationsState.save_smtp_config,
                    loading=NotificationsState.is_saving_smtp,
                    size="2",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        # ── Brevo configuration ───────────────────────────────────────────────
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("message-circle", size=18, color="var(--accent-9)"),
                    rx.heading("Brevo Configuration", size="4"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Configure Brevo to send emails, SMS, and WhatsApp messages. When a Brevo API key is configured, Brevo is used for email delivery instead of SMTP.",
                    size="2",
                    color="var(--gray-10)",
                ),
                rx.separator(width="100%"),
                rx.vstack(
                    rx.text("API Key Credentials Name", size="2", weight="medium"),
                    rx.input(
                        placeholder="e.g. brevo-care",
                        value=NotificationsState.brevo_credentials_name,
                        on_change=NotificationsState.set_brevo_credentials_name,
                        size="2",
                        width="100%",
                    ),
                    rx.text(
                        "Name of a Constellab Credentials (type Basic) whose password field holds the Brevo API key.",
                        size="1",
                        color="var(--gray-9)",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("From Email", size="2", weight="medium"),
                        rx.input(
                            placeholder="noreply@example.com",
                            value=NotificationsState.brevo_from_email,
                            on_change=NotificationsState.set_brevo_from_email,
                            type="email",
                            size="2",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("From Name", size="2", weight="medium"),
                        rx.input(
                            placeholder="Constellab Care",
                            value=NotificationsState.brevo_from_name,
                            on_change=NotificationsState.set_brevo_from_name,
                            size="2",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("SMS / WhatsApp Sender Name", size="2", weight="medium"),
                    rx.input(
                        placeholder="ConstellCare",
                        value=NotificationsState.brevo_sms_sender,
                        on_change=NotificationsState.set_brevo_sms_sender,
                        size="2",
                        max_length=11,
                        width="200px",
                    ),
                    rx.text(
                        "Alphanumeric sender ID shown on the recipient's device (max 11 characters). Must be registered with Brevo.",
                        size="1",
                        color="var(--gray-9)",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.cond(
                    NotificationsState.brevo_error != "",
                    rx.callout(NotificationsState.brevo_error, icon="triangle-alert", color_scheme="red", size="1"),
                ),
                rx.cond(
                    NotificationsState.brevo_success != "",
                    rx.callout(NotificationsState.brevo_success, icon="check", color_scheme="green", size="1"),
                ),
                rx.button(
                    rx.icon("save", size=14),
                    "Save Brevo Settings",
                    on_click=NotificationsState.save_brevo_config,
                    loading=NotificationsState.is_saving_brevo,
                    size="2",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ── Page ───────────────────────────────────────────────────────────────────────

def settings_page() -> rx.Component:
    """Settings page — import, user roles, and notification configuration."""
    return main_component(
        page_layout(
            import_dialog(),
            rx.cond(
                AdminState.is_admin,
                rx.vstack(
                    rx.hstack(
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
                    ),
                    rx.tabs.root(
                        rx.hstack(
                            rx.tabs.list(
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("globe", size=15),
                                        rx.text(LanguageState.tr["settings_tab_general"]),
                                        spacing="2",
                                        align="center",
                                    ),
                                    value="general",
                                    width="100%",
                                    justify="start",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("file-up", size=15),
                                        rx.text(LanguageState.tr["settings_tab_import"]),
                                        spacing="2",
                                        align="center",
                                    ),
                                    value="import",
                                    width="100%",
                                    justify="start",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("shield", size=15),
                                        rx.text(LanguageState.tr["settings_tab_roles"]),
                                        spacing="2",
                                        align="center",
                                    ),
                                    value="roles",
                                    width="100%",
                                    justify="start",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("book-user", size=15),
                                        rx.text("Annuaire"),
                                        spacing="2",
                                        align="center",
                                    ),
                                    value="annuaire",
                                    width="100%",
                                    justify="start",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(
                                        rx.icon("bell", size=15),
                                        rx.text(LanguageState.tr["settings_tab_notifications"]),
                                        spacing="2",
                                        align="center",
                                    ),
                                    value="notifications",
                                    width="100%",
                                    justify="start",
                                ),
                                flex_direction="column",
                                min_width="185px",
                                align_items="stretch",
                                border_right="1px solid var(--gray-5)",
                                padding_right="0.5rem",
                                gap="0",
                            ),
                            rx.box(
                                rx.tabs.content(_general_tab(), value="general", padding_left="1rem"),
                                rx.tabs.content(_import_tab(), value="import", padding_left="1rem"),
                                rx.tabs.content(_user_roles_tab(), value="roles", padding_left="1rem"),
                                rx.tabs.content(_staff_directory_tab(), value="annuaire", padding_left="1rem"),
                                rx.tabs.content(_notifications_tab(), value="notifications", padding_left="1rem"),
                                flex="1",
                                min_width="0",
                            ),
                            width="100%",
                            align="start",
                            spacing="0",
                        ),
                        default_value="general",
                        orientation="vertical",
                        width="100%",
                    ),
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
        )
    )
