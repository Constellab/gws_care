"""Certificate detail page component."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.language_state import LanguageState
from ..common.page_layout import page_layout
from .certificate_detail_state import CertificateDetailDTO, CertificateDetailState


def _info_row(label: str, value: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="2", weight="medium", color="var(--gray-9)", min_width="180px", flex_shrink="0"),
        rx.cond(
            value != "",
            rx.text(value, size="2"),
            rx.text("—", size="2", color="var(--gray-7)"),
        ),
        spacing="4",
        align="start",
        padding_y="0.3rem",
        width="100%",
    )


def _opt_info_row(label: str, value: rx.Var) -> rx.Component:
    return rx.cond(
        value != "",
        _info_row(label, value),
    )


def _cert_info_card() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("award", size=20, color="var(--accent-9)"),
                    rx.heading(
                        rx.cond(
                            CertificateDetailState.certificate,
                            CertificateDetailState.certificate.certificate_type_label,
                            "Certificat médical",
                        ),
                        size="5",
                    ),
                    rx.cond(
                        CertificateDetailState.certificate & CertificateDetailState.certificate.is_archived,
                        rx.badge(
                            LanguageState.tr["archived_badge"],
                            color_scheme="gray",
                            variant="soft",
                            size="1",
                        ),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    CertificateDetailState.certificate,
                    rx.hstack(
                        rx.icon("user", size=13, color="var(--gray-9)"),
                        rx.text(
                            CertificateDetailState.certificate.patient_name,
                            size="2",
                            color="var(--gray-9)",
                        ),
                        spacing="1",
                        align="center",
                    ),
                ),
                spacing="1",
                align_items="start",
            ),
            width="100%",
            align="start",
        ),
        width="100%",
    )


def certificate_detail_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                # ── Back button ───────────────────────────────────────────────
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=14),
                        LanguageState.tr["btn_back"],
                        on_click=CertificateDetailState.go_back_to_patient,
                        variant="ghost",
                        size="2",
                    ),
                    width="100%",
                    align="center",
                ),

                # ── Error ─────────────────────────────────────────────────────
                rx.cond(
                    CertificateDetailState.error_message != "",
                    rx.callout(
                        CertificateDetailState.error_message,
                        color_scheme="red",
                        size="2",
                        icon="triangle-alert",
                    ),
                ),

                # ── Loading / content ─────────────────────────────────────────
                rx.cond(
                    CertificateDetailState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="3rem"),
                    rx.cond(
                        CertificateDetailState.certificate,
                        rx.vstack(
                            # ── Info card ─────────────────────────────────────
                            _cert_info_card(),

                            # ── Action buttons ────────────────────────────────
                            rx.hstack(
                                rx.button(
                                    rx.icon("eye", size=14),
                                    LanguageState.tr["view_pdf_btn"],
                                    on_click=CertificateDetailState.view_pdf,
                                    variant="soft",
                                    size="2",
                                ),
                                rx.button(
                                    rx.icon("download", size=14),
                                    LanguageState.tr["download_pdf_btn"],
                                    on_click=CertificateDetailState.download_pdf,
                                    variant="soft",
                                    size="2",
                                ),
                                spacing="2",
                                width="100%",
                            ),

                            # ── Patient / certificate metadata card ────────────
                            rx.card(
                                rx.vstack(
                                    rx.text(
                                        LanguageState.tr["certificate_info_section"],
                                        size="2",
                                        weight="bold",
                                        color="var(--gray-11)",
                                        margin_bottom="0.5rem",
                                    ),
                                    _info_row(
                                        LanguageState.tr["cert_form_date_label"],
                                        CertificateDetailState.certificate.issue_date,
                                    ),
                                    _info_row(
                                        LanguageState.tr["col_cert_type"],
                                        CertificateDetailState.certificate.certificate_type_label,
                                    ),
                                    rx.hstack(
                                        rx.text(
                                            LanguageState.tr["field_patient"],
                                            size="2",
                                            weight="medium",
                                            color="var(--gray-9)",
                                            min_width="180px",
                                            flex_shrink="0",
                                        ),
                                        rx.hstack(
                                            rx.icon("user", size=13, color="var(--gray-9)"),
                                            rx.text(CertificateDetailState.certificate.patient_name, size="2"),
                                            spacing="1",
                                            align="center",
                                        ),
                                        spacing="4",
                                        align="start",
                                        padding_y="0.3rem",
                                        width="100%",
                                    ),
                                    _info_row(
                                        LanguageState.tr["col_patient_number"],
                                        CertificateDetailState.certificate.patient_number,
                                    ),
                                    _info_row(
                                        LanguageState.tr["col_date_of_birth"],
                                        CertificateDetailState.certificate.patient_date_of_birth,
                                    ),
                                    _info_row(
                                        LanguageState.tr["col_issued_by"],
                                        CertificateDetailState.certificate.issued_by_name,
                                    ),
                                    # Fitness badge
                                    rx.hstack(
                                        rx.text(
                                            LanguageState.tr["cert_form_fit_label"],
                                            size="2",
                                            weight="medium",
                                            color="var(--gray-9)",
                                            min_width="180px",
                                            flex_shrink="0",
                                        ),
                                        rx.cond(
                                            CertificateDetailState.certificate.is_fit_for_work,
                                            rx.badge(LanguageState.tr["cert_fit_yes"], color_scheme="green", variant="soft", size="1"),
                                            rx.badge(LanguageState.tr["cert_fit_no"], color_scheme="red", variant="soft", size="1"),
                                        ),
                                        spacing="4",
                                        align="center",
                                        padding_y="0.3rem",
                                    ),
                                    _opt_info_row(
                                        LanguageState.tr["cert_form_restrictions_label"],
                                        CertificateDetailState.certificate.restrictions,
                                    ),
                                    width="100%",
                                    spacing="0",
                                ),
                                width="100%",
                            ),

                            # ── Conclusion card ────────────────────────────────
                            rx.card(
                                rx.vstack(
                                    rx.text(
                                        LanguageState.tr["cert_form_conclusion_label"],
                                        size="2",
                                        weight="bold",
                                        color="var(--gray-11)",
                                        margin_bottom="0.5rem",
                                    ),
                                    rx.text(
                                        CertificateDetailState.certificate.conclusion,
                                        size="2",
                                        white_space="pre-wrap",
                                    ),
                                    width="100%",
                                    spacing="1",
                                ),
                                width="100%",
                            ),

                            # ── Type-specific fields card ──────────────────────
                            rx.cond(
                                (CertificateDetailState.certificate.start_date != "")
                                | (CertificateDetailState.certificate.accident_date != "")
                                | (CertificateDetailState.certificate.vaccine_name != "")
                                | (CertificateDetailState.certificate.exposure_type != ""),
                                rx.card(
                                    rx.vstack(
                                        rx.text(
                                            LanguageState.tr["cert_type_specific_section"],
                                            size="2",
                                            weight="bold",
                                            color="var(--gray-11)",
                                            margin_bottom="0.5rem",
                                        ),
                                        _opt_info_row(LanguageState.tr["cert_form_start_date"], CertificateDetailState.certificate.start_date),
                                        _opt_info_row(LanguageState.tr["cert_form_end_date"], CertificateDetailState.certificate.end_date),
                                        _opt_info_row(LanguageState.tr["cert_form_return_date"], CertificateDetailState.certificate.return_date),
                                        _opt_info_row(LanguageState.tr["cert_form_accident_date"], CertificateDetailState.certificate.accident_date),
                                        _opt_info_row(LanguageState.tr["cert_form_body_part"], CertificateDetailState.certificate.body_part),
                                        _opt_info_row(LanguageState.tr["cert_form_exposure_type"], CertificateDetailState.certificate.exposure_type),
                                        _opt_info_row(LanguageState.tr["cert_form_vaccine_name"], CertificateDetailState.certificate.vaccine_name),
                                        _opt_info_row(LanguageState.tr["cert_form_vaccine_lot"], CertificateDetailState.certificate.vaccine_lot),
                                        _opt_info_row(LanguageState.tr["cert_form_next_booster"], CertificateDetailState.certificate.next_booster),
                                        _opt_info_row(LanguageState.tr["cert_form_visit_subtype"], CertificateDetailState.certificate.visit_subtype),
                                        width="100%",
                                        spacing="0",
                                    ),
                                    width="100%",
                                ),
                            ),

                            width="100%",
                            spacing="4",
                        ),
                        # Not found
                        rx.center(
                            rx.vstack(
                                rx.icon("file-x", size=40, color="var(--gray-6)"),
                                rx.text("Certificat introuvable.", color="var(--gray-8)", size="2"),
                                align="center",
                                spacing="2",
                            ),
                            padding="3rem",
                        ),
                    ),
                ),

                width="100%",
                spacing="4",
            ),
        )
    )
