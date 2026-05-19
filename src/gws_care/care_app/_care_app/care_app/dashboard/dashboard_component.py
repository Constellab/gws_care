"""Dashboard V2 component — PSC global operations dashboard."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .dashboard_state import (
    AccountOption,
    CampaignStatusStat,
    DashboardState,
    RecentCampaignRow,
)

# ── Colour constants (aligned with gws_project StatusColors) ─────────────────
_C_PRIMARY = "var(--accent-9)"
_C_DONE = "var(--teal-9)"
_C_WARN = "var(--orange-9)"
_C_DANGER = "var(--red-9)"
_C_NEUTRAL = "var(--gray-9)"
_C_INFO = "var(--blue-9)"
_C_PURPLE = "var(--violet-9)"
_C_SURFACE = "var(--gray-1)"
_C_BORDER = "var(--gray-4)"


# ── Primitives ────────────────────────────────────────────────────────────────

def _kpi_card(
    label: str,
    value: rx.Var,
    icon: str,
    color_var: str,
    *,
    subtitle: str | None = None,
) -> rx.Component:
    """A single KPI tile with icon, value and label."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon(icon, size=18, color=color_var),
                    width="36px",
                    height="36px",
                    border_radius="8px",
                    background=color_var.replace("9)", "3)"),
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.spacer(),
            ),
            rx.text(value, size="8", weight="bold", line_height="1"),
            rx.vstack(
                rx.text(label, size="2", color="var(--gray-11)", weight="medium"),
                rx.cond(
                    subtitle is not None,
                    rx.text(subtitle or "", size="1", color="var(--gray-9)"),
                    rx.fragment(),
                ),
                spacing="0",
            ),
            spacing="2",
            align_items="start",
        ),
        padding="1.25rem",
        border="1px solid " + _C_BORDER,
        border_radius="12px",
        background=_C_SURFACE,
        width="100%",
        _hover={"border_color": color_var, "box_shadow": f"0 0 0 1px {color_var}"},
        transition="border-color 0.15s, box-shadow 0.15s",
    )


def _section_header(title: str, icon: str) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(icon, size=16, color=_C_PRIMARY),
            padding="0.4rem",
            border_radius="8px",
            background="var(--accent-3)",
        ),
        rx.heading(title, size="4", weight="bold"),
        spacing="2",
        align="center",
        padding_bottom="0.75rem",
    )


def _panel(*children: rx.Component, title: str, icon: str) -> rx.Component:
    return rx.vstack(
        _section_header(title, icon),
        rx.separator(width="100%"),
        *children,
        padding="1.25rem",
        border="1px solid " + _C_BORDER,
        border_radius="12px",
        background=_C_SURFACE,
        width="100%",
        spacing="3",
    )


# ── Campaign status bar ───────────────────────────────────────────────────────

def _status_bar_row(stat: CampaignStatusStat) -> rx.Component:
    """One row in the campaign-by-status horizontal bar chart."""
    bar_width = rx.cond(
        DashboardState.total_campaigns > 0,
        (stat.count * 280 / DashboardState.total_campaigns).to(int).to(str) + "px",
        "4px",
    )
    color_var = "var(--" + stat.color + "-9)"
    bg_var = "var(--" + stat.color + "-3)"
    return rx.hstack(
        rx.badge(
            stat.label,
            color_scheme=stat.color,
            variant="soft",
            size="1",
            min_width="210px",
            white_space="nowrap",
        ),
        rx.box(
            rx.box(
                height="10px",
                border_radius="5px",
                background=color_var,
                width=bar_width,
                min_width="4px",
                transition="width 0.4s ease",
            ),
            height="10px",
            background=bg_var,
            border_radius="5px",
            width="280px",
            overflow="hidden",
        ),
        rx.text(stat.count, size="2", weight="bold", color="var(--gray-11)", min_width="24px"),
        spacing="3",
        align="center",
        width="100%",
    )


# ── Recent campaigns table ────────────────────────────────────────────────────

def _campaign_row(row: RecentCampaignRow) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(row.name, size="2", weight="medium"),
                rx.text(row.account_name, size="1", color=_C_NEUTRAL),
                spacing="0",
            )
        ),
        rx.table.cell(
            rx.badge(
                row.status_label,
                color_scheme=row.status_color,
                variant="soft",
                size="1",
            )
        ),
        rx.table.cell(rx.text(row.patient_count, size="2")),
        rx.table.cell(rx.text(row.start_date, size="2", color=_C_NEUTRAL)),
        rx.table.cell(rx.text(row.end_date, size="2", color=_C_NEUTRAL)),
        rx.table.cell(
            rx.icon_button(
                rx.icon("arrow-right", size=14),
                variant="ghost",
                size="1",
                on_click=rx.redirect("/campaign/" + row.id),
                title="Voir la campagne",
            )
        ),
        vertical_align="middle",
        cursor="pointer",
        on_click=rx.redirect("/campaign/" + row.id),
        _hover={"background": "var(--gray-2)"},
    )


def _campaigns_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Campagne / Entreprise"),
                rx.table.column_header_cell("Statut"),
                rx.table.column_header_cell("Patients"),
                rx.table.column_header_cell("Début"),
                rx.table.column_header_cell("Fin"),
                rx.table.column_header_cell(""),
            )
        ),
        rx.table.body(
            rx.foreach(DashboardState.recent_campaigns, _campaign_row)
        ),
        width="100%",
        variant="surface",
        size="1",
    )


# ── Filter bar ────────────────────────────────────────────────────────────────

def _filter_account_option(opt: AccountOption) -> rx.Component:
    return rx.select.item(opt.name, value=opt.id)


def _filter_bar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.icon("search", size=16, color=_C_NEUTRAL),
            rx.text("Filtrer par entreprise", size="2", color=_C_NEUTRAL),
            spacing="1",
            align="center",
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Toutes les entreprises", width="260px"),
            rx.select.content(
                rx.select.item("Toutes les entreprises", value="ALL"),
                rx.foreach(DashboardState.accounts, _filter_account_option),
            ),
            on_change=DashboardState.set_filter_account,
            value=rx.cond(DashboardState.filter_account_id != "", DashboardState.filter_account_id, "ALL"),
        ),
        rx.cond(
            DashboardState.is_loading,
            rx.hstack(
                rx.spinner(size="2"),
                rx.text("Chargement…", size="2", color=_C_NEUTRAL),
                spacing="2",
                align="center",
            ),
            rx.fragment(),
        ),
        rx.button(
            rx.icon("refresh-cw", size=14),
            "Actualiser",
            on_click=DashboardState.refresh,
            variant="soft",
            size="2",
            loading=DashboardState.is_loading,
        ),
        rx.cond(
            DashboardState.last_updated != "",
            rx.text(
                "Mis à jour à " + DashboardState.last_updated,
                size="1",
                color=_C_NEUTRAL,
            ),
            rx.fragment(),
        ),
        spacing="4",
        align="center",
        flex_wrap="wrap",
    )


# ── Error banner ──────────────────────────────────────────────────────────────

def _error_banner() -> rx.Component:
    return rx.cond(
        DashboardState.error_message != "",
        rx.callout(
            DashboardState.error_message,
            icon="info",
            color_scheme="red",
            width="100%",
        ),
        rx.fragment(),
    )


# ── KPI grid row ─────────────────────────────────────────────────────────────

def _kpi_grid_1() -> rx.Component:
    """Row 1 KPI: campaigns, patients, convocations, présents/absents + taux."""
    return rx.grid(
        _kpi_card("Campagnes", DashboardState.total_campaigns, "list", _C_PRIMARY),
        _kpi_card("Patients", DashboardState.total_patients, "users", _C_INFO),
        _kpi_card("Convoqués", DashboardState.total_convocations_sent, "mail", _C_WARN),
        _kpi_card("Présents", DashboardState.total_present, "check", _C_DONE),
        columns="4",
        spacing="4",
        width="100%",
    )


def _kpi_grid_2() -> rx.Component:
    """Row 2 KPI: absents, taux participation, examens réalisés, certificats."""
    return rx.grid(
        _kpi_card("Absents", DashboardState.total_absent, "ban", _C_DANGER),
        _kpi_card(
            "Taux de participation",
            DashboardState.participation_rate.to(str) + " %",
            "flag",
            _C_DONE,
        ),
        _kpi_card("Examens réalisés", DashboardState.exams_done, "eye", _C_INFO),
        _kpi_card("Certificats générés", DashboardState.total_certificates, "award", _C_PURPLE),
        columns="4",
        spacing="4",
        width="100%",
    )


def _kpi_grid_3() -> rx.Component:
    """Row 3 KPI: pipeline médical + notifications."""
    return rx.grid(
        _kpi_card(
            "Examens à saisir",
            DashboardState.exams_to_enter,
            "pen-line",
            _C_WARN,
        ),
        _kpi_card(
            "En attente médecin PSC",
            DashboardState.dossiers_awaiting_psc,
            "shield",
            _C_PURPLE,
        ),
        _kpi_card(
            "Notifs envoyées",
            DashboardState.notifications_sent,
            "send",
            _C_DONE,
        ),
        _kpi_card(
            "Notifs échouées",
            DashboardState.notifications_failed,
            "x",
            _C_DANGER,
        ),
        columns="4",
        spacing="4",
        width="100%",
    )


# ── Pipeline strip ────────────────────────────────────────────────────────────

def _pipeline_strip() -> rx.Component:
    """Compact 3-step publication pipeline."""
    def _step(label: str, value: rx.Var, icon: str, color: str) -> rx.Component:
        return rx.vstack(
            rx.box(
                rx.icon(icon, size=20, color=f"var(--{color}-9)"),
                rx.text(value, size="6", weight="bold"),
                display="flex",
                flex_direction="column",
                align_items="center",
                gap="0.25rem",
                padding="0.75rem 1.25rem",
                border="1px solid " + _C_BORDER,
                border_radius="10px",
                background=f"var(--{color}-2)",
                min_width="120px",
            ),
            rx.text(label, size="1", color=_C_NEUTRAL, text_align="center", max_width="120px"),
            spacing="1",
            align="center",
        )

    return rx.hstack(
        _step("Labo validé", DashboardState.exams_labo_validated, "file", "teal"),
        rx.icon("arrow-right", size=16, color=_C_NEUTRAL),
        _step("Médecin entreprise", DashboardState.dossiers_available_medecin_entreprise, "building-2", "violet"),
        rx.icon("arrow-right", size=16, color=_C_NEUTRAL),
        _step("Publié patient", DashboardState.dossiers_published_patient, "users", "green"),
        spacing="3",
        align="center",
        flex_wrap="wrap",
        padding="0.5rem 0",
    )


# ── Role-adaptive header banner ───────────────────────────────────────────────

def _role_banner() -> rx.Component:
    """Show a contextual banner with role-specific quick actions."""
    return rx.match(
        DashboardState.user_role_context,
        ("doctor_psc", rx.card(
            rx.hstack(
                rx.box(rx.icon("shield", size=20, color=_C_PURPLE),
                       padding="0.5rem", border_radius="8px", background="var(--violet-3)"),
                rx.vstack(
                    rx.text(f"Bonjour {DashboardState.user_display_name} — Médecin PSC", size="3", weight="bold"),
                    rx.text("Dossiers en attente de votre interprétation", size="2", color="var(--gray-9)"),
                    spacing="0",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text(DashboardState.my_pending_interpretations, size="6", weight="bold", color=_C_PURPLE),
                            rx.text("À interpréter", size="1", color="var(--gray-9)"),
                            align="center", spacing="0",
                        ),
                        padding="0.75rem 1rem",
                        border="2px solid var(--violet-6)",
                        border_radius="10px",
                        background="var(--violet-2)",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text(DashboardState.my_pending_validation, size="6", weight="bold", color=_C_WARN),
                            rx.text("À valider", size="1", color="var(--gray-9)"),
                            align="center", spacing="0",
                        ),
                        padding="0.75rem 1rem",
                        border="2px solid var(--orange-6)",
                        border_radius="10px",
                        background="var(--orange-2)",
                    ),
                    rx.button(
                        rx.icon("arrow-right", size=14), "Voir ma file",
                        color_scheme="violet", size="2",
                        on_click=rx.redirect("/doctor-psc"),
                    ),
                    spacing="3", align="center",
                ),
                spacing="3", align="center", width="100%",
            ),
            background="var(--violet-1)",
            border="1px solid var(--violet-4)",
        )),
        ("doctor_enterprise", rx.card(
            rx.hstack(
                rx.box(rx.icon("heart", size=20, color="var(--green-9)"),
                       padding="0.5rem", border_radius="8px", background="var(--green-3)"),
                rx.vstack(
                    rx.text(f"Bonjour {DashboardState.user_display_name} — Médecin Entreprise", size="3", weight="bold"),
                    rx.text("Dossiers disponibles pour votre interprétation", size="2", color="var(--gray-9)"),
                    spacing="0",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text(DashboardState.my_enterprise_pending, size="6", weight="bold", color="var(--green-9)"),
                            rx.text("Dossiers à traiter", size="1", color="var(--gray-9)"),
                            align="center", spacing="0",
                        ),
                        padding="0.75rem 1rem",
                        border="2px solid var(--green-6)",
                        border_radius="10px",
                        background="var(--green-2)",
                    ),
                    rx.button(
                        rx.icon("arrow-right", size=14), "Voir les dossiers",
                        color_scheme="green", size="2",
                        on_click=rx.redirect("/doctor-enterprise"),
                    ),
                    spacing="3", align="center",
                ),
                spacing="3", align="center", width="100%",
            ),
            background="var(--green-1)",
            border="1px solid var(--green-4)",
        )),
        ("rh", rx.card(
            rx.hstack(
                rx.box(rx.icon("user-plus", size=20, color="var(--blue-9)"),
                       padding="0.5rem", border_radius="8px", background="var(--blue-3)"),
                rx.vstack(
                    rx.text(f"Bonjour {DashboardState.user_display_name} — Responsable RH", size="3", weight="bold"),
                    rx.text("Suivi administratif de vos campagnes de santé", size="2", color="var(--gray-9)"),
                    spacing="0",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text(DashboardState.total_campaigns, size="6", weight="bold", color="var(--blue-9)"),
                            rx.text("Campagnes actives", size="1", color="var(--gray-9)"),
                            align="center", spacing="0",
                        ),
                        padding="0.75rem 1rem",
                        border="2px solid var(--blue-6)",
                        border_radius="10px",
                        background="var(--blue-2)",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text(DashboardState.total_convocations_sent, size="6", weight="bold", color=_C_DONE),
                            rx.text("Salariés convoqués", size="1", color="var(--gray-9)"),
                            align="center", spacing="0",
                        ),
                        padding="0.75rem 1rem",
                        border="2px solid var(--teal-6)",
                        border_radius="10px",
                        background="var(--teal-2)",
                    ),
                    rx.button(
                        rx.icon("arrow-right", size=14), "Espace RH",
                        color_scheme="blue", size="2",
                        on_click=rx.redirect("/hr"),
                    ),
                    spacing="3", align="center",
                ),
                spacing="3", align="center", width="100%",
            ),
            background="var(--blue-1)",
            border="1px solid var(--blue-4)",
        )),
        ("operator", rx.card(
            rx.hstack(
                rx.box(rx.icon("flask-conical", size=20, color="var(--teal-9)"),
                       padding="0.5rem", border_radius="8px", background="var(--teal-3)"),
                rx.vstack(
                    rx.text(f"Bonjour {DashboardState.user_display_name} — Opérateur", size="3", weight="bold"),
                    rx.text("Campagnes en cours à gérer", size="2", color="var(--gray-9)"),
                    spacing="0",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("arrow-right", size=14), "Voir les campagnes",
                    color_scheme="teal", size="2",
                    on_click=rx.redirect("/campaigns"),
                ),
                spacing="3", align="center", width="100%",
            ),
            background="var(--teal-1)",
            border="1px solid var(--teal-4)",
        )),
        rx.fragment(),  # admin / unknown: no specific banner
    )


# ── Page assembly ─────────────────────────────────────────────────────────────

def dashboard_page() -> rx.Component:
    return main_component(
        page_layout(
            # Header
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Dashboard opérationnel", size="6", weight="bold"),
                        rx.text(
                            "Vue globale PSC — campagnes médicales en entreprise",
                            size="2",
                            color=_C_NEUTRAL,
                        ),
                        spacing="1",
                    ),
                    rx.spacer(),
                    _filter_bar(),
                    align="center",
                    width="100%",
                    flex_wrap="wrap",
                    spacing="4",
                ),
                _error_banner(),
                spacing="3",
                width="100%",
            ),

            # Role-specific banner
            _role_banner(),

            # KPI rows
            _kpi_grid_1(),
            _kpi_grid_2(),
            _kpi_grid_3(),

            # Two-column middle section
            rx.grid(
                _panel(
                    rx.foreach(DashboardState.campaigns_by_status, _status_bar_row),
                    rx.cond(
                        DashboardState.campaigns_by_status.length() == 0,
                        rx.center(
                            rx.text("Aucune campagne", size="2", color=_C_NEUTRAL),
                            padding="1rem",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    title="Campagnes par statut",
                    icon="list",
                ),
                _panel(
                    _pipeline_strip(),
                    title="Pipeline de publication",
                    icon="arrow-right",
                ),
                columns="2",
                spacing="4",
                width="100%",
            ),

            # Recent campaigns table
            _panel(
                _campaigns_table(),
                rx.cond(
                    DashboardState.recent_campaigns.length() == 0,
                    rx.center(
                        rx.text("Aucune campagne récente", size="2", color=_C_NEUTRAL),
                        padding="1rem",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                title="Campagnes récentes",
                icon="list",
            ),
        )
    )
