"""Consultation detail page component (/consultation/[visit_id_param])."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .consultation_detail_state import (
    CertificateRowDTO,
    ConsultationDetailState,
    ConsultationDTO,
    DrugLineDTO,
    ExamParamOption,
    ExamRowDTO,
    ExamTypeRefOption,
    PrescriptionRowDTO,
)


def _status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("scheduled", rx.badge("Planifiée", color_scheme="blue", variant="soft", size="1")),
        ("in_progress", rx.badge("En cours", color_scheme="amber", variant="soft", size="1")),
        ("done", rx.badge("Terminée", color_scheme="green", variant="soft", size="1")),
        ("cancelled", rx.badge("Annulée", color_scheme="red", variant="soft", size="1")),
        rx.badge(status, color_scheme="gray", variant="soft", size="1"),
    )


def _info_card(label: str, value: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", color="var(--gray-9)", weight="medium"),
        value,
        spacing="1",
        align="start",
    )


def _consultation_header(c: ConsultationDTO) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.text(c.visit_number, size="5", weight="bold"),
                        _status_badge(c.status),
                        spacing="2",
                        align="center",
                    ),
                    rx.text("Consultation", size="2", color="var(--gray-9)"),
                    spacing="1",
                ),
                rx.spacer(),
                # Action buttons (only for staff/doctor, not patient)
                rx.cond(
                    ~ConsultationDetailState.is_patient_user,
                    rx.hstack(
                        # "Start" button — only when SCHEDULED
                        rx.cond(
                            c.status == "scheduled",
                            rx.button(
                                rx.icon("play", size=14),
                                "Démarrer",
                                on_click=ConsultationDetailState.start_consultation,
                                loading=ConsultationDetailState.is_starting,
                                size="2",
                                color_scheme="teal",
                            ),
                            rx.fragment(),
                        ),
                        # "Close" button — when SCHEDULED or IN_PROGRESS
                        rx.cond(
                            (c.status == "scheduled") | (c.status == "in_progress"),
                            rx.button(
                                rx.icon("check", size=14),
                                "Clôturer",
                                on_click=ConsultationDetailState.open_close_dialog,
                                size="2",
                                color_scheme="green",
                                variant="soft",
                            ),
                            rx.fragment(),
                        ),
                        # "Cancel" button — when SCHEDULED or IN_PROGRESS
                        rx.cond(
                            (c.status == "scheduled") | (c.status == "in_progress"),
                            rx.button(
                                rx.icon("x", size=14),
                                "Annuler",
                                on_click=ConsultationDetailState.open_cancel_dialog,
                                size="2",
                                color_scheme="red",
                                variant="soft",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                    ),
                ),
                width="100%",
                align="start",
            ),
            rx.separator(width="100%"),
            # Cancellation reason banner — shown only when cancelled
            rx.cond(
                c.status == "cancelled",
                rx.callout.root(
                    rx.callout.icon(rx.icon("ban", size=16)),
                    rx.callout.text(
                        rx.vstack(
                            rx.text("Rendez-vous annulé", weight="bold", size="2"),
                            rx.cond(
                                c.cancellation_reason != "",
                                rx.text("Motif : " + c.cancellation_reason, size="2"),
                                rx.fragment(),
                            ),
                            spacing="0",
                        )
                    ),
                    color_scheme="red",
                    width="100%",
                ),
                rx.fragment(),
            ),
            rx.grid(
                _info_card(
                    "Patient",
                    rx.link(
                        c.patient_name,
                        on_click=lambda: ConsultationDetailState.go_back(),
                        cursor="pointer",
                        size="2",
                        weight="medium",
                    ),
                ),
                _info_card(
                    "Compte",
                    rx.cond(
                        c.account_name != "",
                        rx.text(c.account_name, size="2"),
                        rx.text("—", size="2", color="var(--gray-7)"),
                    ),
                ),
                _info_card(
                    "Date prévue",
                    rx.cond(
                        c.scheduled_at != "",
                        rx.text(c.scheduled_at[:10], size="2"),
                        rx.text("—", size="2", color="var(--gray-7)"),
                    ),
                ),
                columns="3",
                spacing="4",
                width="100%",
            ),
            spacing="3",
        ),
        width="100%",
    )


def _exam_row(exam: ExamRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(exam.exam_date, size="2")),
        rx.table.cell(rx.text(exam.exam_type_label, size="2")),
        rx.table.cell(
            rx.badge(exam.status_label, color_scheme="blue", variant="soft", size="1")
        ),
        rx.table.cell(
            rx.link(
                "Voir",
                on_click=lambda: rx.redirect(f"/exam/{exam.id}"),
                size="2",
                cursor="pointer",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _prescription_row(p: PrescriptionRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p.prescription_date, size="2")),
        rx.table.cell(
            rx.cond(
                p.diagnosis != "",
                rx.text(p.diagnosis, size="2"),
                rx.text("—", size="2", color="var(--gray-7)"),
            )
        ),
        rx.table.cell(rx.text(p.prescribed_by_name, size="2")),
        rx.table.cell(
            rx.link(
                "Voir",
                on_click=lambda: rx.redirect(f"/prescription/{p.id}"),
                size="2",
                cursor="pointer",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _certificate_row(c: CertificateRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(c.issue_date, size="2")),
        rx.table.cell(
            rx.cond(
                c.is_fit_for_work,
                rx.badge("Apte", color_scheme="green", variant="soft", size="1"),
                rx.badge("Inapte", color_scheme="red", variant="soft", size="1"),
            )
        ),
        rx.table.cell(rx.text(c.issued_by_name, size="2")),
        rx.table.cell(
            rx.link(
                "Voir",
                on_click=lambda: rx.redirect(f"/certificate/{c.id}"),
                size="2",
                cursor="pointer",
            )
        ),
        style={":hover": {"background_color": "var(--gray-2)"}},
    )


def _exams_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("activity", size=18, color="var(--accent-9)"),
            rx.heading("Examens", size="4"),
            rx.spacer(),
            rx.cond(
                (~ConsultationDetailState.is_patient_user)
                & (ConsultationDetailState.consultation.status != "cancelled"),
                rx.button(
                    rx.icon("plus", size=14),
                    "Ajouter",
                    on_click=ConsultationDetailState.open_new_exam_dialog,
                    size="1",
                    variant="soft",
                ),
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        rx.cond(
            ConsultationDetailState.exams.length() == 0,
            rx.text("Aucun examen lié à cette consultation.", size="2", color="var(--gray-8)"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(rx.text("Date", size="2")),
                        rx.table.column_header_cell(rx.text("Type", size="2")),
                        rx.table.column_header_cell(rx.text("Statut", size="2")),
                        rx.table.column_header_cell(rx.text("", size="2")),
                    )
                ),
                rx.table.body(
                    rx.foreach(ConsultationDetailState.exams, _exam_row)
                ),
                width="100%",
                variant="surface",
            ),
        ),
        spacing="3",
        width="100%",
    )


def _prescriptions_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("pill", size=18, color="var(--accent-9)"),
            rx.heading("Ordonnances", size="4"),
            rx.spacer(),
            rx.cond(
                (~ConsultationDetailState.is_patient_user)
                & (ConsultationDetailState.consultation.status != "cancelled"),
                rx.button(
                    rx.icon("plus", size=14),
                    "Ajouter",
                    on_click=ConsultationDetailState.open_new_prescription_dialog,
                    size="1",
                    variant="soft",
                ),
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        rx.cond(
            ConsultationDetailState.prescriptions.length() == 0,
            rx.text("Aucune ordonnance liée à cette consultation.", size="2", color="var(--gray-8)"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(rx.text("Date", size="2")),
                        rx.table.column_header_cell(rx.text("Diagnostic", size="2")),
                        rx.table.column_header_cell(rx.text("Médecin", size="2")),
                        rx.table.column_header_cell(rx.text("", size="2")),
                    )
                ),
                rx.table.body(
                    rx.foreach(ConsultationDetailState.prescriptions, _prescription_row)
                ),
                width="100%",
                variant="surface",
            ),
        ),
        spacing="3",
        width="100%",
    )


def _certificates_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("file-check", size=18, color="var(--accent-9)"),
            rx.heading("Certificats médicaux", size="4"),
            rx.spacer(),
            rx.cond(
                (~ConsultationDetailState.is_patient_user)
                & (ConsultationDetailState.consultation.status != "cancelled"),
                rx.button(
                    rx.icon("plus", size=14),
                    "Émettre",
                    on_click=ConsultationDetailState.open_new_certificate_dialog,
                    size="1",
                    variant="soft",
                ),
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        rx.cond(
            ConsultationDetailState.certificates.length() == 0,
            rx.text("Aucun certificat lié à cette consultation.", size="2", color="var(--gray-8)"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(rx.text("Date", size="2")),
                        rx.table.column_header_cell(rx.text("Aptitude", size="2")),
                        rx.table.column_header_cell(rx.text("Émis par", size="2")),
                        rx.table.column_header_cell(rx.text("", size="2")),
                    )
                ),
                rx.table.body(
                    rx.foreach(ConsultationDetailState.certificates, _certificate_row)
                ),
                width="100%",
                variant="surface",
            ),
        ),
        spacing="3",
        width="100%",
    )


def _cancel_consultation_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Annuler le rendez-vous"),
            rx.vstack(
                rx.text(
                    "Veuillez indiquer le motif d'annulation. Cette action est irréversible.",
                    size="2", color="var(--gray-11)",
                ),
                rx.vstack(
                    rx.text("Motif d'annulation *", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Ex : Patient absent, demande du patient, problème médical…",
                        value=ConsultationDetailState.cancel_reason,
                        on_change=ConsultationDetailState.set_cancel_reason,
                        rows="3",
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.cond(
                    ConsultationDetailState.cancel_reason_error != "",
                    rx.callout(
                        ConsultationDetailState.cancel_reason_error,
                        icon="triangle-alert", color_scheme="red", size="1",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Retour",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ConsultationDetailState.close_cancel_dialog,
                    ),
                    rx.button(
                        "Confirmer l'annulation",
                        color_scheme="red",
                        on_click=ConsultationDetailState.confirm_cancel_consultation,
                        loading=ConsultationDetailState.is_cancelling,
                    ),
                    spacing="2", width="100%",
                ),
                spacing="4", width="100%", padding_top="0.5rem",
            ),
            on_interact_outside=ConsultationDetailState.close_cancel_dialog,
            on_escape_key_down=ConsultationDetailState.close_cancel_dialog,
            max_width="480px",
        ),
        open=ConsultationDetailState.show_cancel_dialog,
    )


def _close_consultation_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Clôturer la consultation"),
            rx.alert_dialog.description(
                "Confirmer la clôture de cette consultation ? Elle passera au statut « Clôturée »."
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button("Annuler", variant="soft", color_scheme="gray", size="2"),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Confirmer",
                        on_click=ConsultationDetailState.confirm_close_consultation,
                        loading=ConsultationDetailState.is_closing,
                        size="2",
                        color_scheme="green",
                    ),
                ),
                spacing="2",
                justify="end",
            ),
        ),
        open=ConsultationDetailState.show_close_dialog,
        on_open_change=ConsultationDetailState.close_close_dialog,
    )


def _drug_row(drug: DrugLineDTO, index: int) -> rx.Component:
    return rx.hstack(
        rx.input(
            placeholder="Médicament",
            value=drug.name,
            on_change=lambda v: ConsultationDetailState.presc_set_drug_name(index, v),
            size="2",
            flex="2",
        ),
        rx.input(
            placeholder="Dosage",
            value=drug.dosage,
            on_change=lambda v: ConsultationDetailState.presc_set_drug_dosage(index, v),
            size="2",
            flex="1",
        ),
        rx.input(
            placeholder="Fréquence",
            value=drug.frequency,
            on_change=lambda v: ConsultationDetailState.presc_set_drug_frequency(index, v),
            size="2",
            flex="1",
        ),
        rx.input(
            placeholder="Durée",
            value=drug.duration,
            on_change=lambda v: ConsultationDetailState.presc_set_drug_duration(index, v),
            size="2",
            flex="1",
        ),
        rx.icon_button(
            rx.icon("trash-2", size=14),
            variant="ghost",
            color_scheme="red",
            size="2",
            on_click=lambda: ConsultationDetailState.presc_remove_drug(index),
        ),
        spacing="2",
        width="100%",
        align="center",
    )


def _exam_ref_option(opt: ExamTypeRefOption) -> rx.Component:
    return rx.select.item(opt.name, value=opt.id)


def _new_exam_param_item(param: ExamParamOption) -> rx.Component:
    return rx.flex(
        rx.cond(
            param.is_selected,
            rx.box(
                rx.icon("check", size=11, color="white"),
                width="18px", min_width="18px", height="18px",
                border_radius="3px",
                background="var(--accent-9)",
                display="flex", align_items="center", justify_content="center",
            ),
            rx.box(
                width="18px", min_width="18px", height="18px",
                border_radius="3px",
                border="2px solid var(--gray-6)",
                background="white",
            ),
        ),
        rx.flex(
            rx.hstack(
                rx.text(param.name, size="2", weight=rx.cond(param.is_selected, "medium", "regular")),
                rx.cond(
                    param.is_required,
                    rx.badge("Requis", size="1", color_scheme="red", variant="soft"),
                    rx.fragment(),
                ),
                spacing="2", align="center", flex_wrap="wrap",
            ),
            rx.cond(
                param.unit != "",
                rx.text(param.unit, size="1", color="var(--gray-9)"),
                rx.fragment(),
            ),
            direction="column", gap="0",
        ),
        rx.spacer(),
        rx.cond(
            param.is_selected,
            rx.icon("check-circle", size=14, color="var(--green-9)"),
            rx.fragment(),
        ),
        align="center", gap="3",
        padding="0.5rem 0.75rem",
        border_radius="var(--radius-2)",
        background=rx.cond(param.is_selected, "var(--accent-2)", "transparent"),
        border=rx.cond(param.is_selected, "1px solid var(--accent-6)", "1px solid var(--gray-4)"),
        width="100%", cursor="pointer",
        on_click=ConsultationDetailState.toggle_new_exam_param(param.id),
        _hover={"background": rx.cond(param.is_selected, "var(--accent-3)", "var(--gray-2)")},
    )


def _new_exam_params_section() -> rx.Component:
    return rx.cond(
        ConsultationDetailState.new_exam_type != "",
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("flask-conical", size=14, color="var(--accent-9)"),
                    rx.text("Tests inclus", size="2", weight="bold", color="var(--gray-11)"),
                    spacing="1", align="center",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.text(
                        ConsultationDetailState.new_exam_selected_param_count.to(str),
                        " / ",
                        ConsultationDetailState.new_exam_params.length().to(str),
                        " sélectionné(s)",
                        size="1", color="var(--gray-9)",
                    ),
                    rx.button(
                        "Tout cocher",
                        on_click=ConsultationDetailState.select_all_new_exam_params,
                        variant="ghost", size="1", type="button",
                    ),
                    rx.button(
                        "Tout décocher",
                        on_click=ConsultationDetailState.clear_all_new_exam_params,
                        variant="ghost", size="1", type="button", color_scheme="gray",
                    ),
                    spacing="2", align="center",
                ),
                width="100%", align="center",
            ),
            rx.cond(
                ConsultationDetailState.new_exam_params.length() > 0,
                rx.vstack(
                    rx.foreach(ConsultationDetailState.new_exam_params, _new_exam_param_item),
                    spacing="1", width="100%",
                    max_height="220px", overflow_y="auto",
                    padding="0.25rem",
                    border="1px solid var(--gray-4)",
                    border_radius="var(--radius-2)",
                    background="var(--gray-1)",
                ),
                rx.center(
                    rx.text("Aucun test défini pour ce type d'examen.", size="2", color="var(--gray-9)"),
                    padding="1rem",
                    border="1px dashed var(--gray-5)",
                    border_radius="var(--radius-2)",
                    width="100%",
                ),
            ),
            width="100%", spacing="2",
        ),
        rx.fragment(),
    )


def _new_exam_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nouvel examen"),
            rx.vstack(
                # Type d'examen — from referential
                rx.vstack(
                    rx.text("Type d'examen", size="2", weight="medium"),
                    rx.cond(
                        ConsultationDetailState.new_exam_is_loading_types,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Chargement du référentiel…", size="2", color="var(--gray-9)"),
                            spacing="2", align="center",
                        ),
                        rx.cond(
                            ConsultationDetailState.new_exam_ref_options.length() > 0,
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Sélectionner un type d'examen…",
                                    width="100%",
                                ),
                                rx.select.content(
                                    rx.foreach(ConsultationDetailState.new_exam_ref_options, _exam_ref_option),
                                ),
                                value=ConsultationDetailState.new_exam_type,
                                on_change=ConsultationDetailState.select_new_exam_type_ref,
                                size="2",
                                width="100%",
                            ),
                            rx.callout(
                                "Aucun type d'examen disponible. Créez-en dans l'onglet Référentiel des examens.",
                                icon="info", color_scheme="orange", size="1",
                            ),
                        ),
                    ),
                    spacing="1", width="100%",
                ),
                # Tests (params)
                _new_exam_params_section(),
                # Date
                rx.vstack(
                    rx.text("Date de l'examen", size="2", weight="medium"),
                    rx.input(
                        type="date",
                        value=ConsultationDetailState.new_exam_date,
                        on_change=ConsultationDetailState.set_new_exam_date,
                        size="2",
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.cond(
                    ConsultationDetailState.new_exam_error != "",
                    rx.callout(
                        ConsultationDetailState.new_exam_error,
                        icon="triangle-alert", color_scheme="red", size="1",
                    ),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Annuler",
                        variant="outline",
                        on_click=ConsultationDetailState.close_new_exam_dialog,
                    ),
                    rx.button(
                        "Créer l'examen",
                        on_click=ConsultationDetailState.save_new_exam,
                        loading=ConsultationDetailState.new_exam_is_saving,
                        disabled=(ConsultationDetailState.new_exam_type == ""),
                    ),
                    spacing="2", width="100%",
                ),
                spacing="4", width="100%", padding_top="1rem",
            ),
            on_interact_outside=ConsultationDetailState.close_new_exam_dialog,
            on_escape_key_down=ConsultationDetailState.close_new_exam_dialog,
            max_width="540px",
        ),
        open=ConsultationDetailState.show_new_exam_dialog,
    )


def _new_prescription_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nouvelle ordonnance"),
            rx.vstack(
                rx.vstack(
                    rx.text("Date", size="2", weight="medium"),
                    rx.input(
                        type="date",
                        value=ConsultationDetailState.presc_form_date,
                        on_change=ConsultationDetailState.set_presc_form_date,
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Diagnostic", size="2", weight="medium"),
                    rx.input(
                        placeholder="Diagnostic (optionnel)",
                        value=ConsultationDetailState.presc_form_diagnosis,
                        on_change=ConsultationDetailState.set_presc_form_diagnosis,
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text("Médicaments", size="2", weight="medium"),
                        rx.spacer(),
                        rx.button(
                            rx.icon("plus", size=13),
                            "Ajouter",
                            on_click=ConsultationDetailState.presc_add_drug,
                            size="1",
                            variant="ghost",
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.foreach(ConsultationDetailState.presc_form_drugs, _drug_row),
                    spacing="2",
                    width="100%",
                ),
                rx.cond(
                    ConsultationDetailState.presc_form_error != "",
                    rx.callout(
                        ConsultationDetailState.presc_form_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Annuler",
                        variant="outline",
                        on_click=ConsultationDetailState.close_new_prescription_dialog,
                    ),
                    rx.button(
                        "Créer l'ordonnance",
                        on_click=ConsultationDetailState.save_new_prescription,
                        loading=ConsultationDetailState.is_saving_prescription,
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                padding_top="1rem",
            ),
            on_interact_outside=ConsultationDetailState.close_new_prescription_dialog,
            on_escape_key_down=ConsultationDetailState.close_new_prescription_dialog,
            max_width="700px",
        ),
        open=ConsultationDetailState.show_new_prescription_dialog,
    )


def _new_certificate_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Émettre un certificat médical"),
            rx.vstack(
                rx.vstack(
                    rx.text("Date d'émission", size="2", weight="medium"),
                    rx.input(
                        type="date",
                        value=ConsultationDetailState.cert_form_issue_date,
                        on_change=ConsultationDetailState.set_cert_form_issue_date,
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Aptitude", size="2", weight="medium"),
                    rx.radio_group.root(
                        rx.hstack(
                            rx.radio_group.item(value="true"),
                            rx.text("Apte", size="2"),
                            rx.radio_group.item(value="false"),
                            rx.text("Inapte", size="2"),
                            spacing="2",
                            align="center",
                        ),
                        value=rx.cond(ConsultationDetailState.cert_form_is_fit_for_work, "true", "false"),
                        on_change=lambda v: ConsultationDetailState.set_cert_form_is_fit_for_work(v == "true"),
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Conclusion", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Conclusion médicale…",
                        value=ConsultationDetailState.cert_form_conclusion,
                        on_change=ConsultationDetailState.set_cert_form_conclusion,
                        size="2",
                        width="100%",
                        rows="3",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.cond(
                    ConsultationDetailState.cert_form_error != "",
                    rx.callout(
                        ConsultationDetailState.cert_form_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Annuler",
                        variant="outline",
                        on_click=ConsultationDetailState.close_new_certificate_dialog,
                    ),
                    rx.button(
                        "Émettre le certificat",
                        on_click=ConsultationDetailState.save_new_certificate,
                        loading=ConsultationDetailState.is_saving_certificate,
                        disabled=(ConsultationDetailState.cert_form_conclusion == ""),
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                padding_top="1rem",
            ),
            on_interact_outside=ConsultationDetailState.close_new_certificate_dialog,
            on_escape_key_down=ConsultationDetailState.close_new_certificate_dialog,
            max_width="560px",
        ),
        open=ConsultationDetailState.show_new_certificate_dialog,
    )


def consultation_detail_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.cond(
                ConsultationDetailState.is_loading,
                rx.center(rx.spinner(size="3"), padding_y="6em"),
                rx.cond(
                    ConsultationDetailState.consultation,
                    rx.vstack(
                        # Back button
                        rx.button(
                            rx.icon("arrow-left", size=14),
                            LanguageState.tr["btn_back"],
                            variant="ghost",
                            color_scheme="gray",
                            size="2",
                            on_click=ConsultationDetailState.go_back,
                        ),
                        # Messages
                        rx.cond(
                            ConsultationDetailState.error_message != "",
                            rx.callout.root(
                                rx.callout.icon(rx.icon("circle-alert", size=16)),
                                rx.callout.text(ConsultationDetailState.error_message),
                                color_scheme="red",
                            ),
                        ),
                        rx.cond(
                            ConsultationDetailState.success_message != "",
                            rx.callout.root(
                                rx.callout.icon(rx.icon("circle-check", size=16)),
                                rx.callout.text(ConsultationDetailState.success_message),
                                color_scheme="green",
                            ),
                        ),
                        # Header card
                        _consultation_header(ConsultationDetailState.consultation),
                        # Sections
                        _exams_section(),
                        _prescriptions_section(),
                        _certificates_section(),
                        # Dialogs
                        _cancel_consultation_dialog(),
                        _close_consultation_dialog(),
                        _new_exam_dialog(),
                        _new_prescription_dialog(),
                        _new_certificate_dialog(),
                        spacing="4",
                        width="100%",
                        padding="1.5em",
                    ),
                    rx.center(
                        rx.text("Consultation introuvable.", size="3", color="var(--gray-8)"),
                        padding_y="6em",
                    ),
                ),
            )
        )
    )
