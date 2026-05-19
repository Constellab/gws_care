"""Account detail page — shows account info, its patients and its campaigns."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..patient_list.patient_form_component import patient_form_dialog
from ..patient_list.patient_form_state import PatientFormState
from .account_detail_state import (
    AccountDetailDTO,
    AccountDetailState,
    AccountPatientRowDTO,
    CampaignRowDTO,
    DoctorOptionDTO,
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


def _account_info_card(account: AccountDetailDTO) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("building-2", size=18, color="var(--accent-9)"),
                rx.heading(account.name, size="5"),
                rx.cond(
                    account.is_active,
                    rx.badge(LanguageState.tr["active_badge"], color_scheme="green", variant="soft", size="1"),
                    rx.badge(LanguageState.tr["inactive_badge"], color_scheme="gray", variant="soft", size="1"),
                ),
                spacing="2",
                align="center",
            ),
            rx.separator(width="100%"),
            rx.grid(
                _info_item(LanguageState.tr["info_registration"], account.registration_number),
                _info_item(LanguageState.tr["info_city"], account.city),
                _info_item(LanguageState.tr["info_address"], account.address),
                _info_item(LanguageState.tr["info_postal_code"], account.postal_code),
                _info_item(LanguageState.tr["info_phone"], account.phone),
                _info_item(LanguageState.tr["info_email"], account.email),
                _info_item(LanguageState.tr["info_contact"], account.contact_name),
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


def _patient_row(p: AccountPatientRowDTO) -> rx.Component:
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
                        on_click=lambda: AccountDetailState.go_to_patient(p.id),
                    ),
                    content=LanguageState.tr["tooltip_view_patient"],
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("unlink", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="red",
                        on_click=lambda: AccountDetailState.remove_patient(p.id),
                    ),
                    content=LanguageState.tr["tooltip_remove_from_account"],
                ),
                spacing="1",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}, "cursor": "pointer"},
        on_click=lambda: AccountDetailState.go_to_patient(p.id),
    )


def _assign_patient_dialog() -> rx.Component:
    """Dialog to assign an existing unlinked patient to this account."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["assign_patient_dialog_title"]),
            rx.dialog.description(
                LanguageState.tr["assign_patient_dialog_desc"],
                size="2",
                margin_bottom="1rem",
            ),
            rx.cond(
                AccountDetailState.unassigned_patients.length() > 0,
                rx.vstack(
                    rx.select.root(
                        rx.select.trigger(placeholder=LanguageState.tr["search_a_patient_placeholder"], width="100%"),
                        rx.select.content(
                            rx.foreach(
                                AccountDetailState.unassigned_patients,
                                lambda p: rx.select.item(p.label, value=p.id),
                            )
                        ),
                        value=AccountDetailState.assign_patient_id,
                        on_change=AccountDetailState.set_assign_patient_id,
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button(
                            LanguageState.tr["cancel_btn"],
                            variant="soft",
                            color_scheme="gray",
                            on_click=AccountDetailState.close_assign_dialog,
                            disabled=AccountDetailState.is_assigning,
                        ),
                        rx.button(
                            rx.cond(
                                AccountDetailState.is_assigning,
                                rx.spinner(size="2"),
                                rx.text(LanguageState.tr["assign_btn"]),
                            ),
                            on_click=AccountDetailState.confirm_assign,
                            disabled=(AccountDetailState.assign_patient_id == "")
                            | AccountDetailState.is_assigning,
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
                        LanguageState.tr["all_patients_assigned"],
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.button(
                        LanguageState.tr["close_btn"],
                        variant="soft",
                        color_scheme="gray",
                        on_click=AccountDetailState.close_assign_dialog,
                    ),
                    spacing="3",
                    align_items="end",
                    width="100%",
                ),
            ),
            on_interact_outside=AccountDetailState.close_assign_dialog,
            on_escape_key_down=AccountDetailState.close_assign_dialog,
            max_width="480px",
        ),
        open=AccountDetailState.assign_dialog_open,
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
                    on_click=AccountDetailState.open_assign_dialog,
                ),
                rx.button(
                    rx.icon("plus", size=14),
                    LanguageState.tr["new_patient_small_btn"],
                    size="2",
                    on_click=lambda: PatientFormState.open_create_for_account(AccountDetailState.account.id),
                ),
                spacing="2",
            ),
            width="100%",
            align="center",
        ),
        rx.separator(width="100%"),
        rx.cond(
            AccountDetailState.patients.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(LanguageState.tr["col_patient_number"]),
                        rx.table.column_header_cell(LanguageState.tr["col_patient"]),
                        rx.table.column_header_cell(LanguageState.tr["col_gender"]),
                        rx.table.column_header_cell(LanguageState.tr["col_dob"]),
                        rx.table.column_header_cell(LanguageState.tr["col_city"]),
                        rx.table.column_header_cell(LanguageState.tr["col_phone"]),
                        rx.table.column_header_cell(LanguageState.tr["col_actions"]),
                    )
                ),
                rx.table.body(
                    rx.foreach(AccountDetailState.patients, _patient_row)
                ),
                width="100%",
                variant="surface",
            ),
            rx.center(
                rx.text(
                    LanguageState.tr["no_patients_assigned"],
                    size="2",
                    color="var(--gray-9)",
                ),
                padding="2rem",
            ),
        ),
        width="100%",
        spacing="3",
    )


def _campaign_row(c: CampaignRowDTO) -> rx.Component:
    color = c.status_color
    return rx.table.row(
        rx.table.cell(rx.text(c.name, size="2", weight="medium")),
        rx.table.cell(
            rx.badge(c.status_label, color_scheme=color, variant="soft", size="1")
        ),
        rx.table.cell(rx.text(c.patient_count, size="2")),
        rx.table.cell(rx.text(c.start_date, size="2", color="var(--gray-9)")),
        rx.table.cell(rx.text(c.end_date, size="2", color="var(--gray-9)")),
        rx.table.cell(rx.text(c.location, size="2", color="var(--gray-9)")),
        rx.table.cell(
            rx.icon_button(
                rx.icon("chevron-right", size=14),
                variant="ghost",
                size="1",
                on_click=AccountDetailState.go_to_campaign(c.id),
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"},
               "cursor": "pointer"},
        on_click=AccountDetailState.go_to_campaign(c.id),
    )


def _campaign_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nouvelle campagne"),
            rx.dialog.description(
                "Créer une campagne médicale pour ce compte.",
                size="2",
                margin_bottom="1rem",
            ),
            rx.vstack(
                rx.cond(
                    AccountDetailState.campaign_error != "",
                    rx.callout(
                        AccountDetailState.campaign_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                rx.vstack(
                    rx.text("Nom *", size="2", weight="medium"),
                    rx.input(
                        placeholder="Ex: Bilan santé annuel 2026",
                        value=AccountDetailState.new_campaign_name,
                        on_change=AccountDetailState.set_new_campaign_name,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Date de début", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=AccountDetailState.new_campaign_start,
                            on_change=AccountDetailState.set_new_campaign_start,
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Date de fin", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=AccountDetailState.new_campaign_end,
                            on_change=AccountDetailState.set_new_campaign_end,
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Lieu", size="2", weight="medium"),
                    rx.input(
                        placeholder="Ex: Salle de réunion A",
                        value=AccountDetailState.new_campaign_location,
                        on_change=AccountDetailState.set_new_campaign_location,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # ── Médecins ────────────────────────────────────────────
                rx.grid(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("stethoscope", size=13, color="var(--blue-9)"),
                            rx.text("Médecin PSC", size="2", weight="medium"),
                            spacing="1", align="center",
                        ),
                        rx.cond(
                            AccountDetailState.psc_doctor_options.length() > 0,
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Sélectionner un médecin PSC",
                                    width="100%",
                                ),
                                rx.select.content(
                                    rx.select.item("— Aucun —", value="__none__"),
                                    rx.foreach(
                                        AccountDetailState.psc_doctor_options,
                                        lambda d: rx.select.item(d.label, value=d.id),
                                    ),
                                ),
                                value=AccountDetailState.new_campaign_psc_doctor_id,
                                on_change=AccountDetailState.set_new_campaign_psc_doctor,
                                width="100%",
                            ),
                            rx.callout(
                                "Aucun médecin PSC trouvé. Créez un utilisateur avec le rôle Médecin PSC dans l'administration.",
                                icon="info",
                                color_scheme="blue",
                                size="1",
                            ),
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("briefcase-medical", size=13, color="var(--indigo-9)"),
                            rx.text("Médecin Entreprise", size="2", weight="medium"),
                            spacing="1", align="center",
                        ),
                        rx.cond(
                            AccountDetailState.enterprise_doctor_options.length() > 0,
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Sélectionner un méd. entreprise",
                                    width="100%",
                                ),
                                rx.select.content(
                                    rx.select.item("— Aucun —", value="__none__"),
                                    rx.foreach(
                                        AccountDetailState.enterprise_doctor_options,
                                        lambda d: rx.select.item(d.label, value=d.id),
                                    ),
                                ),
                                value=AccountDetailState.new_campaign_enterprise_doctor_id,
                                on_change=AccountDetailState.set_new_campaign_enterprise_doctor,
                                width="100%",
                            ),
                            rx.callout(
                                "Aucun médecin entreprise trouvé. Créez un utilisateur avec ce rôle.",
                                icon="info",
                                color_scheme="amber",
                                size="1",
                            ),
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Annuler",
                        variant="soft",
                        color_scheme="gray",
                        on_click=AccountDetailState.close_campaign_dialog,
                        disabled=AccountDetailState.is_creating_campaign,
                    ),
                    rx.button(
                        rx.cond(
                            AccountDetailState.is_creating_campaign,
                            rx.spinner(size="2"),
                            rx.text("Créer la campagne"),
                        ),
                        on_click=AccountDetailState.create_campaign,
                        disabled=(AccountDetailState.new_campaign_name == "")
                        | AccountDetailState.is_creating_campaign,
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            on_interact_outside=AccountDetailState.close_campaign_dialog,
            on_escape_key_down=AccountDetailState.close_campaign_dialog,
            max_width="520px",
        ),
        open=AccountDetailState.campaign_dialog_open,
    )


def _campaigns_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Campagnes", size="4"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                "Nouvelle campagne",
                size="2",
                on_click=AccountDetailState.open_campaign_dialog,
            ),
            width="100%",
            align="center",
        ),
        rx.separator(width="100%"),
        rx.cond(
            AccountDetailState.campaigns.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Nom"),
                        rx.table.column_header_cell("Statut"),
                        rx.table.column_header_cell("Patients"),
                        rx.table.column_header_cell("Début"),
                        rx.table.column_header_cell("Fin"),
                        rx.table.column_header_cell("Lieu"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(AccountDetailState.campaigns, _campaign_row)
                ),
                width="100%",
                variant="surface",
                size="1",
            ),
            rx.center(
                rx.text("Aucune campagne pour ce compte.", size="2", color="var(--gray-9)"),
                padding="2rem",
            ),
        ),
        width="100%",
        spacing="3",
    )


def account_detail_page() -> rx.Component:
    """Account detail page."""
    return main_component(
        page_layout(
            rx.button(
                rx.icon("arrow-left", size=16),
                LanguageState.tr["back_to_accounts"],
                on_click=AccountDetailState.go_back,
                variant="ghost",
                size="2",
            ),
            rx.cond(
                AccountDetailState.error_message != "",
                rx.callout(
                    AccountDetailState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
            ),
            rx.cond(
                AccountDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    AccountDetailState.account,
                    rx.vstack(
                        _account_info_card(AccountDetailState.account),
                        _campaigns_section(),
                        _patients_section(),
                        width="100%",
                        spacing="5",
                    ),
                    rx.center(
                        rx.text(LanguageState.tr["account_not_found"], color="var(--gray-9)"),
                        padding="3rem",
                    ),
                ),
            ),
            _assign_patient_dialog(),
            _campaign_dialog(),
            patient_form_dialog(),
        )
    )
