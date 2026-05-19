"""Audit log page component (US-210)."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .audit_state import AuditLogRowVM, AuditState

_ACTION_OPTIONS = [
    ("__all__", "Toutes les actions"),
    ("LOGIN", "Connexion"),
    ("VIEW_MEDICAL", "Consultation médicale"),
    ("CREATE_PATIENT", "Création patient"),
    ("UPDATE_PATIENT", "Modification patient"),
    ("IMPORT_EMPLOYEES", "Import employés"),
    ("VALIDATE", "Validation"),
    ("CORRECTION", "Correction"),
    ("EXPORT", "Export"),
    ("DOWNLOAD_PDF", "Téléchargement PDF"),
    ("ACCESS_DENIED", "Accès refusé"),
    ("GENERATE_CERTIFICATE", "Génération certificat"),
    ("MODIFY_RIGHTS", "Modification droits"),
    ("CREATE_CAMPAIGN", "Création campagne"),
    ("CAMPAIGN_STATUS_CHANGE", "Changement statut campagne"),
    ("PUBLISH_RESULTS", "Publication résultats"),
]

_ACTION_COLORS = {
    "ACCESS_DENIED": "red",
    "VALIDATE": "green",
    "CREATE_CAMPAIGN": "blue",
    "PUBLISH_RESULTS": "green",
    "GENERATE_CERTIFICATE": "teal",
    "CORRECTION": "orange",
    "MODIFY_RIGHTS": "red",
    "EXPORT": "violet",
    "DOWNLOAD_PDF": "indigo",
}


def _action_badge(action: str, action_label: str) -> rx.Component:
    color = _ACTION_COLORS.get(action, "gray")
    return rx.badge(action_label, color_scheme=color, size="1", variant="soft")


def _log_row(log: AuditLogRowVM) -> rx.Component:
    color = rx.match(
        log.action,
        ("ACCESS_DENIED", "red"),
        ("MODIFY_RIGHTS", "red"),
        ("VALIDATE", "green"),
        ("PUBLISH_RESULTS", "green"),
        ("CREATE_CAMPAIGN", "blue"),
        ("CREATE_PATIENT", "teal"),
        ("UPDATE_PATIENT", "cyan"),
        ("GENERATE_CERTIFICATE", "teal"),
        ("CORRECTION", "orange"),
        ("EXPORT", "violet"),
        ("DOWNLOAD_PDF", "indigo"),
        ("SEND_NOTIFICATION", "purple"),
        "gray",
    )
    return rx.table.row(
        rx.table.cell(rx.text(log.created_at, size="1", color="var(--gray-9)")),
        rx.table.cell(rx.text(log.user_email, size="2")),
        rx.table.cell(
            rx.badge(log.action_label, color_scheme=color, size="1", variant="soft")
        ),
        rx.table.cell(rx.text(log.resource_type, size="2")),
        rx.table.cell(rx.text(log.resource_id, size="1", color="var(--gray-9)")),
        rx.table.cell(
            rx.cond(
                log.details != "",
                rx.tooltip(
                    rx.icon("info", size=14, color="var(--gray-9)"),
                    content=log.details,
                ),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(rx.text(log.ip_address, size="1", color="var(--gray-9)")),
    )


def audit_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Journal d'audit", size="6"),
                        rx.text("Traçabilité des actions sensibles — 200 dernières entrées", size="2", color="var(--gray-9)"),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.button(rx.icon("refresh-cw", size=14), "Actualiser",
                              variant="soft", size="2", on_click=AuditState.on_load),
                    width="100%", align="end",
                ),
                # Filters
                rx.card(
                    rx.hstack(
                        rx.select.root(
                            rx.select.trigger(placeholder="Action"),
                            rx.select.content(
                                *[rx.select.item(label, value=val) for val, label in _ACTION_OPTIONS]
                            ),
                            value=AuditState.filter_action,
                            on_change=AuditState.set_filter_action,
                        ),
                        rx.input(
                            placeholder="Email utilisateur…",
                            value=AuditState.filter_user,
                            on_change=AuditState.set_filter_user,
                            flex="1",
                        ),
                        rx.button("Filtrer", on_click=AuditState.apply_filters, size="2", variant="solid"),
                        spacing="3", width="100%", align="center",
                    ),
                    width="100%",
                ),
                rx.cond(
                    AuditState.error != "",
                    rx.callout(AuditState.error, icon="triangle-alert", color_scheme="red", size="2"),
                    rx.fragment(),
                ),
                rx.cond(
                    AuditState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="4rem"),
                    rx.cond(
                        AuditState.logs.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Date"),
                                    rx.table.column_header_cell("Utilisateur"),
                                    rx.table.column_header_cell("Action"),
                                    rx.table.column_header_cell("Ressource"),
                                    rx.table.column_header_cell("ID"),
                                    rx.table.column_header_cell("Détails"),
                                    rx.table.column_header_cell("IP"),
                                )
                            ),
                            rx.table.body(rx.foreach(AuditState.logs, _log_row)),
                            width="100%",
                            variant="surface",
                        ),
                        rx.center(
                            rx.text("Aucune entrée dans le journal.", size="2", color="var(--gray-9)"),
                            padding="4rem",
                        ),
                    ),
                ),
                spacing="4", width="100%",
            )
        )
    )
