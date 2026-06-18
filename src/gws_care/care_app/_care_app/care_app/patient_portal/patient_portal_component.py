"""Patient portal page component — the patient's personal space."""

import reflex as rx

from ..common.page_layout import page_layout
from .patient_portal_state import (
    BookingDoctorDTO,
    BookingExamTypeDTO,
    PatientPortalState,
    PortalAppointmentDTO,
    PortalCertificateDTO,
    PortalExamRowDTO,
    PrescribedFollowUpDTO,
)


# ── Status badges ─────────────────────────────────────────────────────────────

def _exam_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("draft", rx.badge("En cours", color_scheme="gray", variant="soft", size="1")),
        ("pending", rx.badge("À interpréter", color_scheme="orange", variant="soft", size="1")),
        ("interpreted", rx.badge("Résultats disponibles", color_scheme="green", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _appt_status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("SCHEDULED", rx.badge("Planifié", color_scheme="blue", variant="soft", size="1")),
        ("DONE", rx.badge("Effectué", color_scheme="green", variant="soft", size="1")),
        ("CANCELLED", rx.badge("Annulé", color_scheme="red", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


# ── Identity card ─────────────────────────────────────────────────────────────

def _identity_card() -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon("user-circle", size=48, color="var(--accent-9)"),
            padding="0.5rem",
        ),
        rx.vstack(
            rx.heading(PatientPortalState.patient_name, size="5"),
            rx.hstack(
                rx.badge(PatientPortalState.patient_number, variant="outline", size="2"),
                rx.text("·", color="var(--gray-7)"),
                rx.text(PatientPortalState.date_of_birth, size="2", color="var(--gray-9)"),
                spacing="2",
                align="center",
            ),
            spacing="1",
        ),
        rx.spacer(),
        # Unread messages badge
        rx.cond(
            PatientPortalState.unread_messages > 0,
            rx.button(
                rx.icon("message-circle", size=16),
                rx.badge(
                    PatientPortalState.unread_messages.to_string(),
                    color_scheme="red",
                    variant="solid",
                    size="1",
                    radius="full",
                ),
                " Messages",
                variant="soft",
                color_scheme="blue",
                size="2",
                on_click=PatientPortalState.set_tab("messages"),
            ),
            rx.fragment(),
        ),
        width="100%",
        align="center",
        padding="1.25rem",
        border="1px solid var(--gray-4)",
        border_radius="12px",
        background="var(--gray-1)",
    )


# ── Tab navigation ────────────────────────────────────────────────────────────

def _tab_btn(label: str, icon_tag: str, tab_id: str) -> rx.Component:
    is_active = PatientPortalState.active_tab == tab_id
    return rx.button(
        rx.icon(icon_tag, size=15),
        label,
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=rx.cond(is_active, "blue", "gray"),
        size="2",
        on_click=PatientPortalState.set_tab(tab_id),
    )


# ── Exams tab ─────────────────────────────────────────────────────────────────

def _exam_row(exam: PortalExamRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(exam.exam_date, size="2")),
        rx.table.cell(rx.text(exam.exam_type_label, size="2", weight="medium")),
        rx.table.cell(_exam_status_badge(exam.status)),
        rx.table.cell(
            rx.cond(
                exam.has_results & (exam.conclusion != ""),
                rx.text(exam.conclusion, size="1", color="var(--gray-11)", max_width="300px",
                        overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
                rx.cond(
                    exam.has_results,
                    rx.text("Résultats disponibles", size="1", color="var(--green-9)"),
                    rx.text("—", size="1", color="var(--gray-7)"),
                ),
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _exams_tab() -> rx.Component:
    return rx.cond(
        PatientPortalState.exams.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Date"),
                    rx.table.column_header_cell("Type d'examen"),
                    rx.table.column_header_cell("Statut"),
                    rx.table.column_header_cell("Compte-rendu"),
                )
            ),
            rx.table.body(rx.foreach(PatientPortalState.exams, _exam_row)),
            width="100%",
            variant="surface",
            size="2",
        ),
        rx.center(
            rx.vstack(
                rx.icon("flask-conical", size=36, color="var(--gray-6)"),
                rx.text("Aucun examen pour l'instant", size="2", color="var(--gray-9)"),
                align="center",
                spacing="2",
            ),
            padding="3rem",
        ),
    )


# ── Appointments tab ──────────────────────────────────────────────────────────

def _appt_row(appt: PortalAppointmentDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(appt.scheduled_at, size="2")),
        rx.table.cell(
            rx.cond(
                appt.exam_type_label != "",
                rx.text(appt.exam_type_label, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(_appt_status_badge(appt.status)),
        rx.table.cell(
            rx.cond(
                appt.status == "SCHEDULED",
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("x", size=14),
                        variant="ghost",
                        size="1",
                        color_scheme="red",
                        on_click=PatientPortalState.cancel_appointment(appt.id),
                    ),
                    content="Annuler ce rendez-vous",
                ),
                rx.fragment(),
            ),
        ),
        _hover={"background": "var(--gray-2)"},
    )


# ── Booking dialog ────────────────────────────────────────────────────────────

def _prescr_followup_row(item: PrescribedFollowUpDTO) -> rx.Component:
    """One row for a prescribed follow-up exam with a 'Book' button."""
    return rx.hstack(
        rx.vstack(
            rx.text(item.ref_name, size="2", weight="medium"),
            rx.hstack(
                rx.text("Prescrit le " + item.exam_date, size="1", color="var(--gray-9)"),
                rx.cond(
                    item.prescribing_doctor != "",
                    rx.text("par " + item.prescribing_doctor, size="1", color="var(--gray-9)"),
                    rx.fragment(),
                ),
                spacing="1",
            ),
            spacing="0",
            flex="1",
        ),
        rx.cond(
            item.has_appointment,
            rx.badge("RDV pris", color_scheme="green", variant="soft", size="1"),
            rx.button(
                rx.icon("calendar-plus", size=13),
                "Prendre RDV",
                size="1",
                color_scheme="blue",
                variant="soft",
                on_click=lambda: PatientPortalState.open_booking_for_prescription(item.ref_id, item.ref_name),
            ),
        ),
        width="100%",
        align="center",
        padding="0.5rem 0.75rem",
        border="1px solid var(--gray-4)",
        border_radius="8px",
        spacing="3",
    )


def _prescribed_followups_section() -> rx.Component:
    """Section showing prescribed follow-up exams that still need an appointment."""
    return rx.cond(
        PatientPortalState.prescribed_followups.length() > 0,
        rx.vstack(
            rx.hstack(
                rx.icon("clipboard-list", size=16, color="var(--orange-9)"),
                rx.heading("Examens prescrits par votre médecin", size="4"),
                spacing="2",
                align="center",
            ),
            rx.text(
                "Votre médecin a prescrit les examens suivants. Prenez rendez-vous ou contactez le secrétariat.",
                size="2",
                color="var(--gray-9)",
            ),
            rx.vstack(
                rx.foreach(PatientPortalState.prescribed_followups, _prescr_followup_row),
                spacing="2",
                width="100%",
            ),
            spacing="3",
            width="100%",
            padding="1rem",
            border="1px solid var(--orange-5)",
            border_radius="10px",
            background="var(--orange-2)",
        ),
        rx.fragment(),
    )


def _booking_exam_type_option(opt: BookingExamTypeDTO) -> rx.Component:
    return rx.select.item(opt.name, value=opt.id)


def _booking_doctor_option(opt: BookingDoctorDTO) -> rx.Component:
    return rx.select.item(
        rx.cond(opt.specialty != "", opt.name + " — " + opt.specialty, opt.name),
        value=opt.id,
    )


def _booking_slot_option(slot: str) -> rx.Component:
    return rx.select.item(slot[11:16], value=slot)


def _booking_dialog() -> rx.Component:
    """Appointment booking modal for patients (open from appointments tab)."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("calendar-plus", size=18, color="var(--accent-9)"),
                    rx.text("Prendre un rendez-vous"),
                    spacing="2",
                    align="center",
                )
            ),
            rx.vstack(
                # Error callout
                rx.cond(
                    PatientPortalState.booking_error != "",
                    rx.callout(
                        PatientPortalState.booking_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="2",
                    ),
                    rx.fragment(),
                ),
                # Exam type (optional)
                rx.vstack(
                    rx.hstack(
                        rx.text("Type d'examen", size="2", weight="medium"),
                        rx.badge("optionnel", color_scheme="gray", variant="soft", size="1"),
                        spacing="2", align="center",
                    ),
                    rx.select.root(
                        rx.select.trigger(placeholder="Sélectionner un type d'examen (optionnel)", width="100%"),
                        rx.select.content(
                            rx.select.item("— Consultation générale —", value="__none__"),
                            rx.foreach(PatientPortalState.booking_exam_types, _booking_exam_type_option),
                        ),
                        value=rx.cond(
                            PatientPortalState.booking_exam_type_ref_id != "",
                            PatientPortalState.booking_exam_type_ref_id,
                            "__none__",
                        ),
                        on_change=PatientPortalState.set_booking_exam_type,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Doctor
                rx.vstack(
                    rx.text("Spécialité (filtrer)", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Toutes les spécialités", width="100%"),
                        rx.select.content(
                            rx.select.item("Toutes les spécialités", value="__all__"),
                            rx.foreach(
                                PatientPortalState.booking_specialty_options,
                                lambda s: rx.select.item(s, value=s),
                            ),
                        ),
                        value=rx.cond(
                            PatientPortalState.booking_specialty != "",
                            PatientPortalState.booking_specialty,
                            "__all__",
                        ),
                        on_change=PatientPortalState.set_booking_specialty,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Médecin *", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Sélectionner un médecin", width="100%"),
                        rx.select.content(
                            rx.foreach(PatientPortalState.filtered_booking_doctors, _booking_doctor_option),
                        ),
                        value=PatientPortalState.booking_doctor_id,
                        on_change=PatientPortalState.set_booking_doctor,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Date
                rx.vstack(
                    rx.text("Date souhaitée *", size="2", weight="medium"),
                    rx.input(
                        type="date",
                        value=PatientPortalState.booking_date,
                        on_change=PatientPortalState.set_booking_date,
                        width="100%",
                        size="2",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Time slot
                rx.cond(
                    PatientPortalState.booking_slots.length() > 0,
                    rx.vstack(
                        rx.text("Créneau disponible *", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(placeholder="Choisir un créneau", width="100%"),
                            rx.select.content(
                                rx.foreach(PatientPortalState.booking_slots, _booking_slot_option),
                            ),
                            value=PatientPortalState.booking_slot,
                            on_change=PatientPortalState.set_booking_slot,
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.cond(
                        (PatientPortalState.booking_doctor_id != "")
                        & (PatientPortalState.booking_date != ""),
                        rx.callout(
                            "Aucun créneau disponible pour ce médecin à cette date.",
                            icon="calendar-x",
                            color_scheme="orange",
                            size="2",
                        ),
                        rx.fragment(),
                    ),
                ),
                # Notes
                rx.vstack(
                    rx.text("Notes / motif (optionnel)", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Décrivez brièvement le motif de votre visite...",
                        value=PatientPortalState.booking_notes,
                        on_change=PatientPortalState.set_booking_notes,
                        width="100%",
                        rows="2",
                    ),
                    spacing="1",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Annuler",
                        variant="soft",
                        color_scheme="gray",
                        on_click=PatientPortalState.close_booking_dialog,
                    ),
                ),
                rx.button(
                    rx.cond(
                        PatientPortalState.booking_is_loading,
                        rx.spinner(size="2"),
                        rx.icon("check", size=15),
                    ),
                    "Confirmer le rendez-vous",
                    on_click=PatientPortalState.confirm_booking,
                    color_scheme="blue",
                    disabled=PatientPortalState.booking_is_loading,
                ),
                spacing="2",
                justify="end",
                margin_top="1rem",
                width="100%",
            ),
            max_width="520px",
        ),
        open=PatientPortalState.booking_open,
        on_open_change=lambda _: PatientPortalState.close_booking_dialog(),
    )


def _appointments_tab() -> rx.Component:
    return rx.vstack(
        # Success callout
        rx.cond(
            PatientPortalState.booking_success,
            rx.callout(
                "Votre rendez-vous a été enregistré avec succès !",
                icon="check-circle",
                color_scheme="green",
                size="2",
            ),
            rx.fragment(),
        ),
        # Prescribed follow-up exams alert
        _prescribed_followups_section(),
        # Header row with booking button
        rx.hstack(
            rx.heading("Mes rendez-vous", size="4"),
            rx.spacer(),
            rx.button(
                rx.icon("calendar-plus", size=15),
                "Prendre un rendez-vous",
                on_click=PatientPortalState.open_booking_dialog,
                size="2",
                color_scheme="blue",
            ),
            width="100%",
            align="center",
        ),
        rx.cond(
            PatientPortalState.appointments.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Date & heure"),
                        rx.table.column_header_cell("Examen"),
                        rx.table.column_header_cell("Statut"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(rx.foreach(PatientPortalState.appointments, _appt_row)),
                width="100%",
                variant="surface",
                size="2",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("calendar", size=36, color="var(--gray-6)"),
                    rx.text("Aucun rendez-vous pour l'instant", size="2", color="var(--gray-9)"),
                    rx.text(
                        "Utilisez le bouton ci-dessus pour prendre votre premier rendez-vous.",
                        size="1", color="var(--gray-7)", text_align="center",
                    ),
                    align="center",
                    spacing="2",
                ),
                padding="3rem",
            ),
        ),
        spacing="3",
        width="100%",
    )


# ── Certificates tab ──────────────────────────────────────────────────────────

def _cert_row(cert: PortalCertificateDTO) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon("file-check-2", size=20, color="var(--blue-9)"),
                padding="0.5rem",
                background="var(--blue-2)",
                border_radius="8px",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text(cert.issue_date, size="2", weight="medium"),
                    rx.cond(
                        cert.is_fit_for_work,
                        rx.badge("Apte", color_scheme="green", variant="soft", size="1"),
                        rx.badge("Inapte", color_scheme="red", variant="soft", size="1"),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(cert.conclusion, size="2", color="var(--gray-11)"),
                rx.cond(
                    cert.restrictions != "",
                    rx.text(
                        "Restrictions : ",
                        rx.text.span(cert.restrictions, color="var(--orange-9)"),
                        size="1",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align_items="start",
            ),
            spacing="3",
            align="start",
        ),
        padding="0.75rem 1rem",
        border="1px solid var(--gray-4)",
        border_radius="8px",
        width="100%",
    )


def _certificates_tab() -> rx.Component:
    return rx.cond(
        PatientPortalState.certificates.length() > 0,
        rx.vstack(
            rx.foreach(PatientPortalState.certificates, _cert_row),
            spacing="2",
            width="100%",
        ),
        rx.center(
            rx.vstack(
                rx.icon("file-check-2", size=36, color="var(--gray-6)"),
                rx.text("Aucun certificat médical disponible", size="2", color="var(--gray-9)"),
                align="center",
                spacing="2",
            ),
            padding="3rem",
        ),
    )


# ── Messages tab (shortcut) ───────────────────────────────────────────────────

def _messages_tab() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon("message-circle", size=48, color="var(--accent-9)"),
            rx.text("Messagerie directe", size="4", weight="medium"),
            rx.text(
                "Échangez directement avec votre médecin.",
                size="2",
                color="var(--gray-9)",
            ),
            rx.button(
                rx.icon("arrow-right", size=15),
                "Accéder à la messagerie",
                size="3",
                color_scheme="blue",
                on_click=rx.redirect("/messages"),
            ),
            align="center",
            spacing="3",
        ),
        padding="4rem",
    )


# ── Main page ─────────────────────────────────────────────────────────────────

def patient_portal_page() -> rx.Component:
    return page_layout(
        _booking_dialog(),
        rx.cond(
            PatientPortalState.is_loading,
            rx.center(rx.spinner(size="3"), padding="4rem"),
            rx.cond(
                PatientPortalState.error != "",
                rx.callout.root(
                    rx.callout.icon(rx.icon("triangle-alert", size=16)),
                    rx.callout.text(PatientPortalState.error),
                    color_scheme="red",
                    width="100%",
                ),
                rx.vstack(
                    _identity_card(),
                    # Standard rx.tabs navigation (replaces custom button tabs)
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger(
                                rx.hstack(rx.icon("flask-conical", size=14), rx.text("Mes examens"), spacing="2", align="center"),
                                value="exams",
                            ),
                            rx.tabs.trigger(
                                rx.hstack(rx.icon("calendar", size=14), rx.text("Rendez-vous"), spacing="2", align="center"),
                                value="appointments",
                            ),
                            rx.tabs.trigger(
                                rx.hstack(rx.icon("file-check-2", size=14), rx.text("Certificats"), spacing="2", align="center"),
                                value="certificates",
                            ),
                            rx.tabs.trigger(
                                rx.hstack(
                                    rx.icon("message-circle", size=14),
                                    rx.text("Messages"),
                                    rx.cond(
                                        PatientPortalState.unread_messages > 0,
                                        rx.badge(
                                            PatientPortalState.unread_messages.to_string(),
                                            color_scheme="red", variant="solid", size="1", radius="full",
                                        ),
                                        rx.fragment(),
                                    ),
                                    spacing="2", align="center",
                                ),
                                value="messages",
                            ),
                        ),
                        rx.tabs.content(_exams_tab(), value="exams", padding_top="1rem"),
                        rx.tabs.content(_appointments_tab(), value="appointments", padding_top="1rem"),
                        rx.tabs.content(_certificates_tab(), value="certificates", padding_top="1rem"),
                        rx.tabs.content(_messages_tab(), value="messages", padding_top="1rem"),
                        value=PatientPortalState.active_tab,
                        on_change=PatientPortalState.set_tab,
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
            ),
        ),
    )

