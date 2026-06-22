"""My Details page component for the patient portal (/my-details)."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from ..patient_detail.patient_doctor_tab_state import LinkedDoctorRowDTO, PatientDoctorTabState
from .patient_accounts_component import accounts_section_for_details
from .patient_details_state import PatientDetailsState, PatientOwnDetailsDTO, PrescriptionCalDayDTO


# ── Shared helpers ────────────────────────────────────────────────────────────

def _info_row(label: str | rx.Var, value: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="2", weight="medium", color="var(--gray-9)", min_width="200px", flex_shrink="0"),
        rx.cond(
            value != "",
            rx.text(value, size="2", overflow_wrap="break-word", word_break="break-word", min_width="0", flex="1"),
            rx.text("—", size="2", color="var(--gray-7)"),
        ),
        spacing="4",
        align="start",
        padding_y="0.4rem",
        width="100%",
    )


def _section(title: str | rx.Var, *rows: rx.Component) -> rx.Component:
    return rx.box(
        rx.text(title, size="2", weight="bold", color="var(--gray-9)", margin_bottom="0.5rem"),
        rx.separator(width="100%", margin_bottom="0.75rem"),
        rx.vstack(*rows, width="100%", spacing="1"),
        width="100%",
        padding="1rem",
        border="1px solid var(--gray-4)",
        border_radius="8px",
        background="var(--gray-1)",
        overflow="hidden",
    )


# ── ID card visual ────────────────────────────────────────────────────────────

def _id_card_visual() -> rx.Component:
    return rx.box(
        rx.box(
            rx.hstack(
                rx.hstack(
                    rx.icon("heart-pulse", size=16, color="var(--accent-9)"),
                    rx.text("CONSTELLAB CARE — PS CONSULTING", size="1", weight="bold", color="var(--accent-9)"),
                    spacing="2", align="center",
                ),
                rx.spacer(),
                rx.text(PatientDetailsState.patient.patient_number, size="1", color="var(--accent-9)", weight="medium"),
                width="100%", align="center",
            ),
            background="var(--accent-2)",
            padding="0.5rem 1rem",
            border_radius="8px 8px 0 0",
        ),
        rx.hstack(
            rx.vstack(
                rx.text(PatientDetailsState.patient.last_name, size="6", weight="bold", color="white", letter_spacing="0.05em"),
                rx.text(PatientDetailsState.patient.first_name, size="4", color="var(--accent-5)"),
                rx.separator(width="100%", margin_y="0.4rem", color="var(--accent-5)"),
                rx.vstack(
                    rx.text(LanguageState.tr["info_dob"], size="1", color="var(--accent-5)", weight="medium"),
                    rx.text(PatientDetailsState.patient.date_of_birth, size="3", color="white", weight="bold"),
                    spacing="0", align_items="start",
                ),
                rx.vstack(
                    rx.text(LanguageState.tr["field_ssn"], size="1", color="var(--accent-5)", weight="medium"),
                    rx.cond(
                        PatientDetailsState.patient.social_security_number != "",
                        rx.text(PatientDetailsState.patient.social_security_number, size="3", color="white", weight="bold", font_family="monospace"),
                        rx.text("—", size="3", color="var(--accent-5)"),
                    ),
                    spacing="0", align_items="start",
                ),
                spacing="3", align_items="start", flex="1", padding="1.25rem",
            ),
            background="var(--accent-9)",
            border_radius="0 0 8px 8px",
            width="100%",
        ),
        border_radius="8px",
        box_shadow="0 4px 16px var(--gray-a4)",
        width="100%",
        max_width="480px",
    )


# ── ID card dialog ────────────────────────────────────────────────────────────

def _id_card_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["id_card_title"]),
            rx.dialog.description(LanguageState.tr["id_card_desc"]),
            rx.vstack(
                _id_card_visual(),
                rx.hstack(
                    rx.button(rx.icon("printer", size=15), LanguageState.tr["print_btn"],
                              on_click=rx.call_script("window.print()"), variant="outline", size="2"),
                    rx.button(rx.icon("file-down", size=15), LanguageState.tr["download_pdf_btn"],
                              on_click=PatientDetailsState.download_id_card_pdf, size="2"),
                    rx.button(LanguageState.tr["close_btn"], on_click=PatientDetailsState.close_id_card,
                              variant="soft", color_scheme="gray", size="2"),
                    spacing="2", justify="end", width="100%", padding_top="0.75rem",
                ),
                spacing="4", align="center", margin_top="1rem",
            ),
            max_width="540px",
            on_interact_outside=PatientDetailsState.close_id_card,
            on_escape_key_down=PatientDetailsState.close_id_card,
        ),
        open=PatientDetailsState.show_id_card,
    )


# ── Edit contact dialog ───────────────────────────────────────────────────────

def _edit_dialog() -> rx.Component:
    def _field(label: rx.Var, value: rx.Var, on_change) -> rx.Component:
        return rx.vstack(
            rx.text(label, size="2", weight="medium"),
            rx.input(value=value, on_change=on_change, size="2", width="100%"),
            spacing="1", width="100%",
        )
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(LanguageState.tr["edit_btn"]),
            rx.vstack(
                rx.grid(
                    _field(LanguageState.tr["info_phone"], PatientDetailsState.edit_phone, PatientDetailsState.set_edit_phone),
                    _field(LanguageState.tr["info_email"], PatientDetailsState.edit_email, PatientDetailsState.set_edit_email),
                    _field(LanguageState.tr["info_address"], PatientDetailsState.edit_address, PatientDetailsState.set_edit_address),
                    _field(LanguageState.tr["info_postal_code"], PatientDetailsState.edit_postal_code, PatientDetailsState.set_edit_postal_code),
                    _field(LanguageState.tr["info_city"], PatientDetailsState.edit_city, PatientDetailsState.set_edit_city),
                    columns="2", spacing="3", width="100%",
                ),
                rx.cond(
                    PatientDetailsState.edit_error != "",
                    rx.callout(PatientDetailsState.edit_error, icon="alert-circle", color_scheme="red", size="1"),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(LanguageState.tr["cancel_btn"], variant="outline", color_scheme="gray",
                              on_click=PatientDetailsState.close_edit_dialog),
                    rx.button(
                        rx.cond(PatientDetailsState.edit_is_saving, rx.spinner(size="2"),
                                rx.hstack(rx.icon("save", size=14), rx.text(LanguageState.tr["save_changes_btn"]), spacing="1")),
                        on_click=PatientDetailsState.save_edit,
                        disabled=PatientDetailsState.edit_is_saving,
                        color_scheme="teal",
                    ),
                    justify="end", width="100%", spacing="3",
                ),
                spacing="4", width="100%",
            ),
            max_width="520px",
            on_interact_outside=PatientDetailsState.close_edit_dialog,
            on_escape_key_down=PatientDetailsState.close_edit_dialog,
        ),
        open=PatientDetailsState.show_edit_dialog,
    )


# ── Patient header (name + badges + action buttons) ───────────────────────────

def _patient_header(p: PatientOwnDetailsDTO) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.heading(
                rx.cond(p.first_name + p.last_name != "", p.first_name + " " + p.last_name, "—"),
                size="7",
            ),
            rx.hstack(
                rx.badge(p.patient_number, variant="outline", size="2"),
                rx.match(
                    p.gender,
                    ("M", rx.badge(LanguageState.tr["gender_male_badge"], color_scheme="blue", variant="soft", size="2")),
                    ("F", rx.badge(LanguageState.tr["gender_female_badge"], color_scheme="pink", variant="soft", size="2")),
                    rx.cond(p.gender != "", rx.badge(p.gender, color_scheme="gray", variant="soft", size="2"), rx.fragment()),
                ),
                spacing="2", align="center", flex_wrap="wrap",
            ),
            spacing="2", align_items="start",
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(rx.icon("id-card", size=15), LanguageState.tr["btn_id_card"],
                      on_click=PatientDetailsState.open_id_card, variant="outline", size="2"),
            rx.button(rx.icon("pencil", size=15), LanguageState.tr["edit_btn"],
                      on_click=PatientDetailsState.open_edit_dialog, variant="outline", size="2"),
            spacing="2",
        ),
        align="center",
        width="100%",
    )


# ── Doctors tab — read-only for patient ───────────────────────────────────────

def _doctor_row(doc: LinkedDoctorRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    doc.is_referent,
                    rx.tooltip(
                        rx.icon("star", size=13, color="var(--amber-9)"),
                        content=LanguageState.tr["doctor_referent_label"],
                    ),
                    rx.fragment(),
                ),
                rx.text(doc.full_name, size="2", weight="medium"),
                spacing="2", align="center",
            )
        ),
        rx.table.cell(rx.cond(doc.specialization != "", rx.text(doc.specialization, size="2"), rx.text("—", size="2", color="var(--gray-8)"))),
        rx.table.cell(rx.cond(doc.phone != "", rx.text(doc.phone, size="2"), rx.text("—", size="2", color="var(--gray-8)"))),
        rx.table.cell(rx.cond(doc.email != "", rx.text(doc.email, size="2"), rx.text("—", size="2", color="var(--gray-8)"))),
    )


def _doctors_tab() -> rx.Component:
    return rx.cond(
        PatientDoctorTabState.is_loading,
        rx.center(rx.spinner(size="2"), padding="2rem"),
        rx.cond(
            PatientDoctorTabState.linked_doctors.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(LanguageState.tr["col_name"]),
                        rx.table.column_header_cell(LanguageState.tr["col_specialization"]),
                        rx.table.column_header_cell(LanguageState.tr["col_phone"]),
                        rx.table.column_header_cell(LanguageState.tr["col_email"]),
                    )
                ),
                rx.table.body(rx.foreach(PatientDoctorTabState.linked_doctors, _doctor_row)),
                width="100%", variant="surface",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("user-round-x", size=36, color="var(--gray-7)"),
                    rx.text(LanguageState.tr["no_doctors_linked"], size="2", color="var(--gray-9)"),
                    spacing="2", align="center",
                ),
                padding="3rem",
            ),
        ),
    )




# ── My Info tab ───────────────────────────────────────────────────────────────

def _my_info_tab(p: PatientOwnDetailsDTO) -> rx.Component:
    return rx.vstack(
        rx.grid(
            _section(
                LanguageState.tr["section_personal_info"],
                _info_row(LanguageState.tr["field_ssn"], p.social_security_number),
                _info_row(LanguageState.tr["info_dob"], p.date_of_birth),
                _info_row(LanguageState.tr["info_birth_name"], p.birth_name),
                _info_row(LanguageState.tr["info_gender"], p.gender),
            ),
            _section(
                LanguageState.tr["section_contact"],
                _info_row(LanguageState.tr["info_phone"], p.phone),
                _info_row(LanguageState.tr["info_email"], p.email),
                _info_row(LanguageState.tr["info_address"], p.address),
                _info_row(LanguageState.tr["info_postal_code"], p.postal_code),
                _info_row(LanguageState.tr["info_city"], p.city),
            ),
            columns="2",
            spacing="4",
            width="100%",
        ),
        width="100%",
        spacing="4",
    )


# ── Prescription calendar ────────────────────────────────────────────────────

def _presc_pill(day: PrescriptionCalDayDTO, idx: int) -> rx.Component:
    """One prescription label chip inside a calendar day cell."""
    return rx.box(
        rx.text(
            day.prescription_labels[idx],
            size="1",
            color="var(--teal-11)",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        background="var(--teal-3)",
        border_radius="3px",
        padding="1px 4px",
        width="100%",
        overflow="hidden",
        cursor="pointer",
        on_click=rx.redirect("/my-prescriptions"),
    )


def _presc_cal_day(day: PrescriptionCalDayDTO) -> rx.Component:
    return rx.box(
        rx.cond(
            day.day_num > 0,
            rx.vstack(
                rx.box(
                    rx.text(
                        day.day_num,
                        size="1",
                        weight=rx.cond(day.is_today, "bold", "regular"),
                        color=rx.cond(day.is_today, "white", "var(--gray-11)"),
                        text_align="center",
                        line_height="1.4rem",
                        width="1.4rem",
                    ),
                    border_radius="50%",
                    background=rx.cond(day.is_today, "var(--accent-9)", "transparent"),
                    width="fit-content",
                ),
                rx.vstack(
                    rx.foreach(
                        day.prescription_labels,
                        lambda label: rx.box(
                            rx.text(label, size="1", color="var(--teal-11)",
                                    overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
                            background="var(--teal-3)", border_radius="3px",
                            padding="1px 4px", width="100%", overflow="hidden",
                            cursor="pointer", on_click=rx.redirect("/my-prescriptions"),
                        ),
                    ),
                    spacing="1", width="100%", overflow="hidden",
                ),
                spacing="1", width="100%", align="start",
            ),
            rx.fragment(),
        ),
        min_height="80px",
        border="1px solid var(--gray-4)",
        padding="4px",
        background=rx.cond(day.is_current_month, "var(--gray-1)", "var(--gray-2)"),
        overflow="hidden",
    )


def _prescriptions_calendar_tab() -> rx.Component:
    return rx.vstack(
        # Month navigation
        rx.hstack(
            rx.icon_button(rx.icon("chevron-left", size=16), variant="ghost", size="2",
                           on_click=PatientDetailsState.presc_cal_prev_month),
            rx.text(PatientDetailsState.presc_cal_label, size="4", weight="medium",
                    min_width="180px", text_align="center"),
            rx.icon_button(rx.icon("chevron-right", size=16), variant="ghost", size="2",
                           on_click=PatientDetailsState.presc_cal_next_month),
            rx.spacer(),
            rx.link(
                rx.button(rx.icon("list", size=13), LanguageState.tr["view_list"],
                          variant="outline", size="1"),
                href="/my-prescriptions",
            ),
            spacing="2", align="center", width="100%",
        ),
        rx.cond(
            PatientDetailsState.presc_cal_loading,
            rx.center(rx.spinner(size="2"), padding="2rem"),
            rx.vstack(
                # Weekday header
                rx.grid(
                    rx.text(LanguageState.tr["cal_mon"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
                    rx.text(LanguageState.tr["cal_tue"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
                    rx.text(LanguageState.tr["cal_wed"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
                    rx.text(LanguageState.tr["cal_thu"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
                    rx.text(LanguageState.tr["cal_fri"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
                    rx.text(LanguageState.tr["cal_sat"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
                    rx.text(LanguageState.tr["cal_sun"], size="1", weight="medium", color="var(--gray-9)", text_align="center", padding_y="4px"),
                    columns="7", width="100%",
                ),
                rx.grid(
                    rx.foreach(PatientDetailsState.presc_cal_days, _presc_cal_day),
                    columns="7", width="100%",
                ),
                spacing="2", width="100%",
            ),
        ),
        width="100%", spacing="3",
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def patient_details_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.cond(
                PatientDetailsState.error_message != "",
                rx.callout(PatientDetailsState.error_message, icon="triangle-alert", color_scheme="red"),
            ),
            rx.cond(
                PatientDetailsState.is_loading,
                rx.center(rx.spinner(size="3"), padding="3rem"),
                rx.cond(
                    PatientDetailsState.patient.id != "",
                    rx.vstack(
                        _patient_header(PatientDetailsState.patient),
                        rx.separator(width="100%"),
                        _my_info_tab(PatientDetailsState.patient),
                        rx.tabs.root(
                            rx.tabs.list(
                                rx.tabs.trigger(
                                    rx.hstack(rx.icon("user-round-check", size=15), rx.text(LanguageState.tr["tab_doctors"]), spacing="1", align="center"),
                                    value="doctors",
                                ),
                                rx.tabs.trigger(
                                    rx.hstack(rx.icon("building-2", size=15), rx.text(LanguageState.tr["tab_accounts"]), spacing="1", align="center"),
                                    value="accounts",
                                ),
                            ),
                            rx.tabs.content(_doctors_tab(), value="doctors", padding_top="1rem"),
                            rx.tabs.content(accounts_section_for_details(), value="accounts", padding_top="1rem"),
                            default_value="doctors",
                            width="100%",
                        ),
                        width="100%",
                        spacing="4",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("user-x", size=40, color="var(--gray-7)"),
                            rx.text("No patient profile linked to your account.", size="3", color="var(--gray-9)"),
                            spacing="3", align="center",
                        ),
                        padding="4rem",
                    ),
                ),
            ),
        ),
        _id_card_dialog(),
        _edit_dialog(),
    )
