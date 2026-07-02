"""Campaign detail dialog components — extracted to keep campaign_detail_component.py manageable.

Dialogs: refuse, add_patient, add_exam_type, psc, enterprise, edit.
"""

import reflex as rx

from .campaign_detail_state import CampaignDetailState


def _refuse_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Refus de validation médicale"),
            rx.vstack(
                rx.text("Motif de refus *", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Expliquez la raison du refus…",
                    value=CampaignDetailState.refuse_reason,
                    on_change=CampaignDetailState.set_refuse_reason,
                    width="100%",
                    rows="4",
                ),
                rx.cond(
                    CampaignDetailState.refuse_error != "",
                    rx.callout(
                        CampaignDetailState.refuse_error,
                        icon="info", color_scheme="red", size="1",
                    ),
                ),
                spacing="2",
                width="100%",
                margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray")),
                rx.button("Confirmer le refus", color_scheme="red",
                          on_click=CampaignDetailState.confirm_refuse_medical),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="480px",
        ),
        open=CampaignDetailState.refuse_dialog_open,
        on_open_change=lambda _: CampaignDetailState.dismiss_error(),
    )


def _add_patient_dialog() -> rx.Component:
    def _patient_row(p) -> rx.Component:
        is_selected = CampaignDetailState.selected_patient_ids.contains(p.id)
        return rx.hstack(
            rx.checkbox(
                checked=is_selected,
                on_change=lambda _: CampaignDetailState.toggle_patient_selection(p.id),
                size="2",
            ),
            rx.text(p.label, size="2"),
            spacing="2",
            align="center",
            width="100%",
            padding="0.35rem 0.5rem",
            border_radius="var(--radius-1)",
            background=rx.cond(is_selected, "var(--accent-3)", "transparent"),
            _hover={"background": rx.cond(is_selected, "var(--accent-4)", "var(--gray-2)")},
            cursor="pointer",
            on_click=CampaignDetailState.toggle_patient_selection(p.id),
        )

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajouter des patients à la campagne"),
            rx.dialog.description(
                "Patients actifs affiliés au compte de l'entreprise de cette campagne.",
                size="2", color="var(--gray-9)",
            ),
            rx.vstack(
                rx.hstack(
                    rx.input(
                        placeholder="Filtrer par nom, prénom ou n° dossier…",
                        value=CampaignDetailState.patient_search,
                        on_change=CampaignDetailState.search_patients,
                        width="100%",
                        flex="1",
                    ),
                    rx.cond(
                        CampaignDetailState.selected_patient_ids.length() > 0,
                        rx.badge(
                            CampaignDetailState.selected_patient_ids.length(),
                            " sélectionné(s)",
                            color_scheme="blue",
                            size="2",
                        ),
                    ),
                    spacing="2",
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    CampaignDetailState.patient_options.length() > 0,
                    rx.box(
                        rx.foreach(
                            CampaignDetailState.patient_options,
                            _patient_row,
                        ),
                        max_height="280px",
                        overflow_y="auto",
                        border="1px solid var(--gray-4)",
                        border_radius="var(--radius-2)",
                        padding="0.25rem",
                        width="100%",
                    ),
                    rx.callout(
                        rx.cond(
                            CampaignDetailState.patient_search != "",
                            "Aucun résultat pour cette recherche.",
                            "Aucun patient disponible — vérifiez que des employés sont affiliés à ce compte entreprise.",
                        ),
                        icon="info",
                        color_scheme="orange",
                        size="1",
                    ),
                ),
                rx.text(
                    "Cliquez sur les patients pour les sélectionner / désélectionner.",
                    size="1",
                    color="var(--gray-9)",
                ),
                spacing="3", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=CampaignDetailState.close_add_patient_dialog)),
                rx.button(
                    rx.icon("user-plus", size=14),
                    rx.cond(
                        CampaignDetailState.selected_patient_ids.length() > 0,
                        "Ajouter (" + CampaignDetailState.selected_patient_ids.length().to_string() + ")",
                        "Ajouter",
                    ),
                    on_click=CampaignDetailState.confirm_add_patient,
                    loading=CampaignDetailState.is_adding_patient,
                    disabled=CampaignDetailState.selected_patient_ids.length() == 0,
                ),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="520px",
        ),
        open=CampaignDetailState.add_patient_dialog_open,
        on_open_change=lambda _: CampaignDetailState.close_add_patient_dialog(),
    )


def _add_exam_type_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajouter un type d'examen"),
            rx.vstack(
                rx.cond(
                    CampaignDetailState.exam_type_options.length() > 0,
                    rx.select.root(
                        rx.select.trigger(placeholder="Sélectionner un type d'examen…", width="100%"),
                        rx.select.content(
                            rx.foreach(
                                CampaignDetailState.exam_type_options,
                                lambda e: rx.select.item(e.label, value=e.id),
                            )
                        ),
                        value=CampaignDetailState.selected_exam_type_id,
                        on_change=CampaignDetailState.set_selected_exam_type,
                    ),
                    rx.callout(
                        "Aucun type d'examen disponible. Créez-en dans l'onglet Référentiel des examens.",
                        icon="info", color_scheme="orange", size="1",
                    ),
                ),
                spacing="3", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=CampaignDetailState.close_add_exam_type_dialog)),
                rx.button("Ajouter", on_click=CampaignDetailState.confirm_add_exam_type,
                          loading=CampaignDetailState.is_adding_exam_type,
                          disabled=CampaignDetailState.selected_exam_type_id == ""),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="480px",
        ),
        open=CampaignDetailState.add_exam_type_dialog_open,
        on_open_change=lambda _: CampaignDetailState.close_add_exam_type_dialog(),
    )


def _psc_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text("Interprétation PSC — "),
                    rx.text(CampaignDetailState.psc_dialog_patient_name, weight="bold"),
                    spacing="1",
                )
            ),
            rx.vstack(
                rx.text("Interprétation / Conclusion *", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Saisir l'interprétation médicale PSC…",
                    value=CampaignDetailState.psc_notes_input,
                    on_change=CampaignDetailState.set_psc_notes,
                    width="100%",
                    rows="5",
                ),
                spacing="2", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=CampaignDetailState.close_psc_dialog)),
                rx.button("Enregistrer l'interprétation",
                          on_click=CampaignDetailState.save_psc_interpretation),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="600px",
        ),
        open=CampaignDetailState.psc_dialog_open,
        on_open_change=lambda _: CampaignDetailState.close_psc_dialog(),
    )


def _enterprise_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text("Interprétation entreprise — "),
                    rx.text(CampaignDetailState.enterprise_dialog_patient_name, weight="bold"),
                    spacing="1",
                )
            ),
            rx.vstack(
                rx.text("Commentaire interne", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Notes internes (non visibles par le patient)…",
                    value=CampaignDetailState.enterprise_notes_input,
                    on_change=CampaignDetailState.set_enterprise_notes,
                    width="100%",
                    rows="3",
                ),
                rx.text("Message destiné au patient *", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Message qui sera visible par le patient…",
                    value=CampaignDetailState.patient_message_input,
                    on_change=CampaignDetailState.set_patient_message,
                    width="100%",
                    rows="4",
                ),
                rx.callout(
                    "Ce message sera visible par le patient après publication.",
                    icon="info",
                    color_scheme="blue",
                    size="1",
                ),
                spacing="2", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=CampaignDetailState.close_enterprise_dialog)),
                rx.button("Enregistrer", on_click=CampaignDetailState.save_enterprise_interpretation),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="600px",
        ),
        open=CampaignDetailState.enterprise_dialog_open,
        on_open_change=lambda _: CampaignDetailState.close_enterprise_dialog(),
    )


def _edit_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Modifier la campagne"),
            rx.vstack(
                rx.vstack(
                    rx.text("Nom *", size="2", weight="medium"),
                    rx.input(
                        value=CampaignDetailState.edit_name,
                        on_change=CampaignDetailState.set_edit_name,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Date début", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=CampaignDetailState.edit_start,
                            on_change=CampaignDetailState.set_edit_start,
                            width="100%",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Date fin", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=CampaignDetailState.edit_end,
                            on_change=CampaignDetailState.set_edit_end,
                            width="100%",
                        ),
                        spacing="1",
                    ),
                    columns="2", spacing="4", width="100%",
                ),
                rx.vstack(
                    rx.text("Lieu", size="2", weight="medium"),
                    rx.input(
                        value=CampaignDetailState.edit_location,
                        on_change=CampaignDetailState.set_edit_location,
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.hstack(
                    rx.text("Revue médicale requise", size="2"),
                    rx.switch(
                        checked=CampaignDetailState.edit_requires_medical_review,
                        on_change=CampaignDetailState.set_edit_requires_medical_review,
                    ),
                    spacing="2", align="center",
                ),
                rx.vstack(
                    rx.text("Notes internes", size="2", weight="medium"),
                    rx.text_area(
                        value=CampaignDetailState.edit_notes,
                        on_change=CampaignDetailState.set_edit_notes,
                        width="100%",
                        rows="3",
                    ),
                    spacing="1", width="100%",
                ),
                rx.cond(
                    CampaignDetailState.edit_error != "",
                    rx.callout(CampaignDetailState.edit_error, icon="info",
                               color_scheme="red", size="1"),
                ),
                spacing="3", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(rx.button("Annuler", variant="soft", color_scheme="gray",
                                          on_click=CampaignDetailState.close_edit_dialog)),
                rx.button("Enregistrer",
                          on_click=CampaignDetailState.save_edit,
                          loading=CampaignDetailState.is_saving_edit),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="520px",
        ),
        open=CampaignDetailState.edit_dialog_open,
        on_open_change=lambda _: CampaignDetailState.close_edit_dialog(),
    )


def _assign_doctor_dialog() -> rx.Component:
    """Dialog for assigning one or more doctors to an exam type within a campaign."""

    def _doctor_row(d) -> rx.Component:
        is_selected = CampaignDetailState.assign_doctor_selected_ids.contains(d.id)
        return rx.hstack(
            rx.checkbox(
                checked=is_selected,
                on_change=lambda _: CampaignDetailState.toggle_assign_doctor_selection(d.id),
                size="2",
            ),
            rx.text(d.label, size="2"),
            spacing="2",
            align="center",
            width="100%",
            padding="0.3rem 0.5rem",
            border_radius="var(--radius-1)",
            background=rx.cond(is_selected, "var(--accent-3)", "transparent"),
            _hover={"background": rx.cond(is_selected, "var(--accent-4)", "var(--gray-2)")},
            cursor="pointer",
            on_click=CampaignDetailState.toggle_assign_doctor_selection(d.id),
        )

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("stethoscope", size=18),
                    rx.text("Assigner des médecins — "),
                    rx.text(CampaignDetailState.assign_doctor_exam_name, weight="bold"),
                    spacing="1", align="center",
                )
            ),
            rx.dialog.description(
                "Les médecins assignés pourront accéder aux résultats de cet examen. "
                "Ils seront également ajoutés à l'onglet Médecins de la campagne.",
                size="2", color="var(--gray-9)",
            ),
            rx.vstack(
                # Specialty filter
                rx.cond(
                    CampaignDetailState.specialty_options_for_assign.length() > 0,
                    rx.vstack(
                        rx.text("Filtrer par spécialité", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(width="100%", placeholder="Toutes les spécialités"),
                            rx.select.content(
                                rx.select.item("Toutes les spécialités", value="_all_"),
                                rx.foreach(
                                    CampaignDetailState.specialty_options_for_assign,
                                    lambda s: rx.select.item(s, value=s),
                                ),
                            ),
                            value=rx.cond(
                                CampaignDetailState.assign_doctor_specialty_filter != "",
                                CampaignDetailState.assign_doctor_specialty_filter,
                                "_all_",
                            ),
                            on_change=CampaignDetailState.set_assign_doctor_specialty_filter,
                            size="2",
                            width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.fragment(),
                ),
                # Doctor checklist
                rx.vstack(
                    rx.hstack(
                        rx.text("Médecins", size="2", weight="medium"),
                        rx.cond(
                            CampaignDetailState.assign_doctor_selected_ids.length() > 0,
                            rx.badge(
                                CampaignDetailState.assign_doctor_selected_ids.length().to_string(),
                                color_scheme="blue", size="1",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2", align="center",
                    ),
                    rx.cond(
                        CampaignDetailState.doctor_options_for_assign.length() == 0,
                        rx.text("Chargement…", size="2", color="var(--gray-9)"),
                        rx.scroll_area(
                            rx.vstack(
                                rx.foreach(
                                    CampaignDetailState.doctor_options_for_assign,
                                    _doctor_row,
                                ),
                                spacing="1", width="100%",
                            ),
                            max_height="280px",
                            width="100%",
                        ),
                    ),
                    spacing="2", width="100%",
                ),
                spacing="3", width="100%", margin_top="1rem",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Annuler", variant="soft", color_scheme="gray",
                              on_click=CampaignDetailState.close_assign_doctor_dialog)
                ),
                rx.button(
                    rx.icon("check", size=14),
                    "Confirmer",
                    on_click=CampaignDetailState.confirm_assign_doctor,
                    loading=CampaignDetailState.is_assigning_doctor,
                ),
                spacing="2", justify="end", margin_top="1rem", width="100%",
            ),
            max_width="500px",
            on_interact_outside=CampaignDetailState.close_assign_doctor_dialog,
            on_escape_key_down=CampaignDetailState.close_assign_doctor_dialog,
        ),
        open=CampaignDetailState.assign_doctor_dialog_open,
    )


def campaign_detail_dialogs() -> rx.Component:
    """Render all campaign detail dialogs in one call (used in campaign_detail_page)."""
    return rx.fragment(
        _refuse_dialog(),
        _add_patient_dialog(),
        _add_exam_type_dialog(),
        _psc_dialog(),
        _enterprise_dialog(),
        _edit_dialog(),
        _assign_doctor_dialog(),
    )
