"""Company detail page — shows company info, its campaigns, billing accounts and its patients."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..company_list.company_form_component import company_form_dialog
from ..company_list.company_form_state import CompanyFormState
from ..patient_list.patient_form_component import patient_form_dialog
from ..patient_list.patient_form_state import PatientFormState
from ..patient_list.patient_delete_component import patient_delete_dialog
from ..patient_list.patient_delete_state import PatientDeleteState
from ..account_list.account_form_component import account_form_dialog
from ..account_list.account_form_state import AccountFormState
from .company_detail_state import (
    CompanyAccountRowDTO,
    CompanyDetailDTO,
    CompanyDetailState,
    CompanyCampaignRowDTO,
    CompanyPatientRowDTO,
)


def _info_item(label: str, value: rx.Var) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", color="var(--gray-9)", weight="medium"),
        rx.cond(
            value != "",
            rx.text(value, size="2"),
            rx.text("—", size="2", color="var(--gray-7)"),
        ),
        spacing="0",
        align_items="start",
    )


def _company_info_card(company: CompanyDetailDTO) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("building-2", size=18, color="var(--accent-9)"),
                rx.heading(company.name, size="5"),
                rx.cond(
                    company.is_active,
                    rx.badge(LanguageState.tr["active_badge"], color_scheme="green", variant="soft", size="1"),
                    rx.badge(LanguageState.tr["inactive_badge"], color_scheme="gray", variant="soft", size="1"),
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("pencil", size=14),
                    LanguageState.tr["edit_btn"],
                    variant="outline",
                    size="2",
                    on_click=CompanyFormState.open_edit_dialog(company.id),
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.separator(width="100%"),
            rx.grid(
                _info_item(LanguageState.tr["info_registration"], company.registration_number),
                _info_item(LanguageState.tr["col_city"], company.city),
                _info_item(LanguageState.tr["field_address"], company.address),
                _info_item(LanguageState.tr["field_postal_code"], company.postal_code),
                _info_item(LanguageState.tr["field_phone"], company.phone),
                _info_item(LanguageState.tr["field_email"], company.email),
                _info_item(LanguageState.tr["info_contact"], company.contact_name),
                columns="3",
                spacing="4",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def _gender_badge(gender: str) -> rx.Component:
    return rx.match(
        gender,
        ("M", rx.badge("M", color_scheme="blue", variant="soft", size="1")),
        ("F", rx.badge("F", color_scheme="pink", variant="soft", size="1")),
        rx.badge(gender, color_scheme="gray", variant="soft", size="1"),
    )


def _patient_row(p: CompanyPatientRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p.patient_number, size="2", weight="medium")),
        rx.table.cell(rx.text(f"{p.first_name} {p.last_name}", size="2")),
        rx.table.cell(_gender_badge(p.gender)),
        rx.table.cell(rx.text(p.date_of_birth, size="2")),
        rx.table.cell(
            rx.cond(p.city, rx.text(p.city, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.cond(p.phone, rx.text(p.phone, size="2"), rx.text("—", size="2", color="var(--gray-8)"))
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("chevron-right", size=14),
                        variant="ghost",
                        size="1",
                        on_click=lambda: CompanyDetailState.go_to_patient(p.id),
                    ),
                    content=LanguageState.tr["tooltip_view_patient"],
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("unlink", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="orange",
                        on_click=lambda: CompanyDetailState.remove_patient(p.id),
                    ),
                    content=LanguageState.tr["tooltip_remove_from_company"],
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("trash-2", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="red",
                        on_click=lambda: PatientDeleteState.open_delete_dialog(
                            p.id,
                            p.first_name + " " + p.last_name,
                            "/company/" + CompanyDetailState.company.id,
                        ),
                    ),
                    content=LanguageState.tr["tooltip_delete_patient"],
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}, "cursor": "pointer"},
        on_click=lambda: CompanyDetailState.go_to_patient(p.id),
    )


def _assign_patient_dialog() -> rx.Component:
    """Dialog to assign an existing unlinked patient to this company."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["assign_patient_dialog_title"]),
            rx.dialog.description(
                LanguageState.tr["assign_company_patient_dialog_desc"],
                size="2",
                margin_bottom="1rem",
            ),
            rx.cond(
                CompanyDetailState.unassigned_patients.length() > 0,
                rx.vstack(
                    rx.select.root(
                        rx.select.trigger(placeholder=LanguageState.tr["search_a_patient_placeholder"], width="100%"),
                        rx.select.content(
                            rx.foreach(
                                CompanyDetailState.unassigned_patients,
                                lambda p: rx.select.item(p.label, value=p.id),
                            )
                        ),
                        value=CompanyDetailState.assign_patient_id,
                        on_change=CompanyDetailState.set_assign_patient_id,
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button(
                            LanguageState.tr["cancel_btn"],
                            variant="soft",
                            color_scheme="gray",
                            on_click=CompanyDetailState.close_assign_dialog,
                            disabled=CompanyDetailState.is_assigning,
                        ),
                        rx.button(
                            rx.cond(
                                CompanyDetailState.is_assigning,
                                rx.spinner(size="2"),
                                rx.text(LanguageState.tr["assign_btn"]),
                            ),
                            on_click=CompanyDetailState.confirm_assign,
                            disabled=(CompanyDetailState.assign_patient_id == "")
                            | CompanyDetailState.is_assigning,
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    width="100%",
                    spacing="4",
                ),
                rx.vstack(
                    rx.text(
                        LanguageState.tr["all_patients_assigned_company"],
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.button(
                        LanguageState.tr["close_btn"],
                        variant="soft",
                        color_scheme="gray",
                        on_click=CompanyDetailState.close_assign_dialog,
                    ),
                    spacing="3",
                    align_items="end",
                    width="100%",
                ),
            ),
            on_interact_outside=CompanyDetailState.close_assign_dialog,
            on_escape_key_down=CompanyDetailState.close_assign_dialog,
            max_width="480px",
        ),
        open=CompanyDetailState.assign_dialog_open,
    )


def _campaign_row(c: CompanyCampaignRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.link(c.name, href=rx.cond(c.id != "", "/campaign/" + c.id, "#"),
                    size="2", weight="medium")
        ),
        rx.table.cell(
            rx.badge(c.status_label, color_scheme=c.status_color, size="1", variant="soft")
        ),
        rx.table.cell(rx.text(c.patient_count.to_string() + " patients", size="2")),
        rx.table.cell(rx.text(c.start_date, size="2")),
        rx.table.cell(rx.text(c.end_date, size="2")),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _campaigns_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Campagnes", size="4"),
            rx.spacer(),
            rx.tooltip(
                rx.icon("info", size=14, color="var(--gray-8)"),
                content="Les campagnes de médecine du travail associées à cette entreprise. La facturation est gérée depuis le Compte de facturation lié.",
            ),
            width="100%", align="center",
        ),
        rx.separator(width="100%"),
        rx.cond(
            CompanyDetailState.campaigns.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Nom"),
                        rx.table.column_header_cell("Statut"),
                        rx.table.column_header_cell("Participants"),
                        rx.table.column_header_cell("Début"),
                        rx.table.column_header_cell("Fin"),
                    )
                ),
                rx.table.body(rx.foreach(CompanyDetailState.campaigns, _campaign_row)),
                width="100%", variant="surface", size="1",
            ),
            rx.callout(
                "Aucune campagne pour cette entreprise. Créez une campagne depuis un Compte de facturation en lui associant cette entreprise.",
                icon="info", color_scheme="blue", size="1",
            ),
        ),
        width="100%",
        spacing="3",
    )


def _patients_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading(LanguageState.tr["patients_in_account_title"], size="4"),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("user-plus", size=14),
                    LanguageState.tr["assign_existing_btn"],
                    variant="outline",
                    size="2",
                    on_click=CompanyDetailState.open_assign_dialog,
                ),
                rx.button(
                    rx.icon("plus", size=14),
                    LanguageState.tr["new_patient_small_btn"],
                    size="2",
                    on_click=lambda: PatientFormState.open_create_for_company(CompanyDetailState.company.id),
                ),
                spacing="2",
            ),
            width="100%",
            align="center",
        ),
        rx.separator(width="100%"),
        rx.cond(
            CompanyDetailState.patients.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("N°"),
                        rx.table.column_header_cell(LanguageState.tr["col_patient"]),
                        rx.table.column_header_cell(LanguageState.tr["col_gender"]),
                        rx.table.column_header_cell(LanguageState.tr["col_dob"]),
                        rx.table.column_header_cell(LanguageState.tr["col_city"]),
                        rx.table.column_header_cell(LanguageState.tr["col_phone"]),
                        rx.table.column_header_cell(LanguageState.tr["col_actions"]),
                    )
                ),
                rx.table.body(
                    rx.foreach(CompanyDetailState.patients, _patient_row)
                ),
                width="100%",
                variant="surface",
            ),
            rx.center(
                rx.text(
                    LanguageState.tr["no_patients_in_company"],
                    size="2",
                    color="var(--gray-9)",
                ),
                padding="2rem",
            ),
        ),
        width="100%",
        spacing="3",
    )


def _account_row(a: CompanyAccountRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(a.name, size="2", weight="medium")),
        rx.table.cell(rx.text(a.registration_number, size="2", color="var(--gray-9)")),
        rx.table.cell(rx.text(a.email, size="2", color="var(--gray-9)")),
        rx.table.cell(
            rx.cond(
                a.is_active,
                rx.badge("Actif", color_scheme="green", size="1", variant="soft"),
                rx.badge("Inactif", color_scheme="gray", size="1", variant="soft"),
            )
        ),
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("arrow-right", size=14),
                    variant="ghost", size="1", color_scheme="blue",
                    on_click=lambda: CompanyDetailState.go_to_account(a.id),
                ),
                content="Voir le compte de facturation",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _billing_accounts_section() -> rx.Component:
    """Section showing billing accounts linked to this company."""
    return rx.vstack(
        rx.hstack(
            rx.icon("credit-card", size=16, color="var(--accent-9)"),
            rx.heading("Comptes de facturation", size="4"),
            rx.badge(
                CompanyDetailState.billing_accounts.length().to_string(),
                color_scheme="blue", variant="soft", size="1",
            ),
            rx.spacer(),
            rx.tooltip(
                rx.button(
                    rx.icon("plus", size=14),
                    "Créer un compte",
                    size="2",
                    on_click=CompanyDetailState.open_create_billing_account,
                ),
                content="Créer un compte de facturation lié \u00e0 cette entreprise",
            ),
            width="100%",
            align="center",
            spacing="2",
        ),
        rx.callout(
            rx.hstack(
                rx.icon("info", size=13),
                rx.text(
                    "Chaîne de facturation : Entreprise → Compte de facturation → Préfacturation → Facture. "
                    "Un compte peut être lié à des campagnes et des préfacturations.",
                    size="1",
                ),
                spacing="2",
                align="center",
            ),
            color_scheme="blue",
            size="1",
            width="100%",
        ),
        rx.separator(width="100%"),
        rx.cond(
            CompanyDetailState.billing_accounts.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Nom du compte"),
                        rx.table.column_header_cell("N° SIRET / Immatriculation"),
                        rx.table.column_header_cell("Email de contact"),
                        rx.table.column_header_cell("Statut"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(CompanyDetailState.billing_accounts, _account_row),
                ),
                width="100%",
                variant="surface",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("credit-card", size=28, color="var(--gray-5)"),
                    rx.text(
                        "Aucun compte de facturation. Cliquez sur \u00ab\u00a0Créer un compte\u00a0\u00bb pour en créer un.",
                        size="2", color="var(--gray-8)", text_align="center",
                    ),
                    spacing="2", align="center",
                ),
                padding="2rem",
            ),
        ),
        width="100%",
        spacing="3",
    )


def company_detail_page() -> rx.Component:
    """Company detail page."""
    return main_component(
        page_layout(
            rx.button(
                rx.icon("arrow-left", size=16),
                LanguageState.tr["back_to_companies"],
                on_click=CompanyDetailState.go_back,
                variant="ghost",
                size="2",
            ),
            rx.cond(
                CompanyDetailState.error_message != "",
                rx.callout(
                    CompanyDetailState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                CompanyDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    CompanyDetailState.company,
                    rx.vstack(
                        _company_info_card(CompanyDetailState.company),
                        _billing_accounts_section(),
                        _campaigns_section(),
                        _patients_section(),
                        width="100%",
                        spacing="5",
                    ),
                    rx.center(
                        rx.text(LanguageState.tr["company_not_found"], color="var(--gray-9)"),
                        padding="3rem",
                    ),
                ),
            ),
            _assign_patient_dialog(),
            patient_form_dialog(),
            patient_delete_dialog(),
            company_form_dialog(),
            account_form_dialog(),
        )
    )
