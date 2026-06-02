"""SampleCollectionState — gestion des prélèvements / flacons (TubeQR) par patient."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import AsyncGenerator

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


SAMPLE_TYPE_OPTIONS = [
    ("Sang total (EDTA)", "Sang total"),
    ("Urine (flacon stérile)", "Urine"),
    ("Urine 24h (bidon)", "Urine 24h"),
    ("Salive", "Salive"),
    ("Écouvillon naso-pharyngé", "Écouvillon naso-pharyngé"),
    ("Selles (coproculture)", "Selles"),
    ("LCR", "LCR"),
    ("Autre", "Autre"),
]


class TubeRowDTO(BaseModel):
    id: str
    short_id: str
    qr_code: str
    status: str
    status_label: str
    status_color: str
    exam_type_label: str
    sample_type: str
    volume_ml: str          # str so "" works in Reflex
    collector_notes: str
    associated_at: str
    collected_at: str
    campaign_name: str


class ExamTypeOption(BaseModel):
    id: str
    name: str
    category_label: str
    required_sample_type: str = ""


class SampleCollectionState(ReflexMainState):
    """State for the sample-collection panel (patient-level, optional campaign context)."""

    # Loaded tubes for the current patient
    tubes: list[TubeRowDTO] = []
    is_loading_tubes: bool = False
    tubes_error: str = ""

    # Exam type options for the create dialog
    exam_type_options: list[ExamTypeOption] = []

    # ── Create dialog ────────────────────────────────────────────────────
    show_create_dialog: bool = False
    create_exam_type_id: str = ""
    create_sample_type: str = ""
    create_volume_ml: str = ""
    create_notes: str = ""
    create_campaign_id: str = ""   # optional — pre-filled when called from campaign page
    create_error: str = ""
    is_creating: bool = False

    # ── Cancel dialog ────────────────────────────────────────────────────
    show_cancel_dialog: bool = False
    cancel_tube_id: str = ""
    cancel_reason: str = ""
    cancel_error: str = ""

    # Shared context
    _current_patient_id: str = ""
    _current_campaign_id: str = ""  # optional campaign context

    # ── Page on_load ─────────────────────────────────────────────────────

    @rx.event
    async def on_load(self) -> None:
        """Called from the patient detail page route on_load."""
        patient_id = self.patient_id_param  # URL param from ReflexMainState
        if patient_id:
            await self.load_for_patient(patient_id)

    @rx.event
    async def on_load_campaign_patient(self) -> None:
        """Called from the campaign-patient page route on_load."""
        patient_id = self.cp_patient_id      # URL param
        campaign_id = self.cp_campaign_id    # URL param
        if patient_id:
            await self.load_for_patient(patient_id, campaign_id)

    # ── Loaders ──────────────────────────────────────────────────────────

    @rx.event
    async def load_for_patient(self, patient_id: str, campaign_id: str = "") -> None:
        """Load all tubes for a given patient (filtered by campaign if provided)."""
        self._current_patient_id = patient_id
        self._current_campaign_id = campaign_id
        self.is_loading_tubes = True
        self.tubes_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.tube_qr.tube_qr import TubeQR, TubeQRStatus

                q = TubeQR.select().where(TubeQR.patient == patient_id)
                if campaign_id:
                    q = q.where(TubeQR.campaign == campaign_id)
                q = q.order_by(TubeQR.created_at.desc())

                rows = []
                for t in q:
                    try:
                        s = TubeQRStatus(t.status)
                        status_label = s.get_label()
                        status_color = s.get_color()
                    except ValueError:
                        status_label = t.status
                        status_color = "gray"
                    exam_label = ""
                    if t.exam_type_ref_id:
                        try:
                            exam_label = t.exam_type_ref.name
                        except Exception as exc:
                            pass
                    camp_name = ""
                    if t.campaign_id:
                        try:
                            camp_name = t.campaign.name
                        except Exception as exc:
                            pass
                    rows.append(TubeRowDTO(
                        id=str(t.id),
                        short_id=t.short_id or "",
                        qr_code=t.qr_code or "",
                        status=t.status,
                        status_label=status_label,
                        status_color=status_color,
                        exam_type_label=exam_label,
                        sample_type=t.sample_type or "",
                        volume_ml=str(t.volume_ml) if t.volume_ml else "",
                        collector_notes=t.collector_notes or "",
                        associated_at=t.associated_at.strftime("%d/%m/%Y %H:%M") if t.associated_at else "",
                        collected_at=t.collected_at.strftime("%d/%m/%Y %H:%M") if t.collected_at else "",
                        campaign_name=camp_name,
                    ))
                self.tubes = rows
        except Exception as e:
            self.tubes_error = str(e)
        finally:
            self.is_loading_tubes = False

    # ── Create dialog ────────────────────────────────────────────────────

    @rx.event
    async def open_create_dialog(self, campaign_id: str = "") -> None:
        self.create_exam_type_id = ""
        self.create_sample_type = ""
        self.create_volume_ml = ""
        self.create_notes = ""
        self.create_campaign_id = campaign_id or self._current_campaign_id
        self.create_error = ""
        self.show_create_dialog = True
        # Load exam type options
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                from gws_care.campaign.campaign_exam import CampaignExam

                if self.create_campaign_id:
                    # Only show exams linked to this campaign
                    # Use prefetch join to avoid N+1 on exam_type_ref
                    ces = list(
                        CampaignExam.select(CampaignExam, ExamTypeRef)
                        .join(ExamTypeRef, on=(CampaignExam.exam_type_ref == ExamTypeRef.id))
                        .where(CampaignExam.campaign == self.create_campaign_id)
                    )
                    options = []
                    for ce in ces:
                        try:
                            r = ce.exam_type_ref
                            if r:
                                options.append(ExamTypeOption(
                                    id=str(r.id),
                                    name=r.name,
                                    category_label=r.get_category_label(),
                                ))
                        except Exception as exc:
                            print(f"[sample_collection] exam_type_ref for CampaignExam {ce.id}: {exc}")
                    self.exam_type_options = options
                else:
                    refs = (
                        ExamTypeRef.select()
                        .where(ExamTypeRef.is_active == True)
                        .order_by(ExamTypeRef.category, ExamTypeRef.name)
                    )
                    self.exam_type_options = [
                        ExamTypeOption(
                            id=str(r.id),
                            name=r.name,
                            category_label=r.get_category_label(),
                            required_sample_type=r.required_sample_type or "",
                        )
                        for r in refs
                    ]
        except Exception as exc:
            self.exam_type_options = []

    @rx.event
    def close_create_dialog(self) -> None:
        self.show_create_dialog = False
        self.create_error = ""

    @rx.event
    def set_create_exam_type_id(self, v: str) -> None:
        self.create_exam_type_id = v
        # Auto-fill sample type from the exam type referential if defined
        if v:
            for opt in self.exam_type_options:
                if opt.id == v:
                    if hasattr(opt, 'required_sample_type') and opt.required_sample_type:
                        self.create_sample_type = opt.required_sample_type
                    break

    @rx.event
    def set_create_sample_type(self, v: str) -> None:
        self.create_sample_type = v

    @rx.event
    def set_create_volume_ml(self, v: str) -> None:
        self.create_volume_ml = v

    @rx.event
    def set_create_notes(self, v: str) -> None:
        self.create_notes = v

    @rx.event
    async def submit_create(self) -> AsyncGenerator:
        """Generate a new tube and associate it immediately to the current patient."""
        self.create_error = ""
        if not self.create_exam_type_id:
            self.create_error = "Veuillez sélectionner un type d'examen."
            return
        if not self.create_sample_type:
            self.create_error = "Veuillez sélectionner le type de prélèvement."
            return
        self.is_creating = True
        try:
            with await self.authenticate_user():
                from gws_care.tube_qr.tube_qr import TubeQR, TubeQRStatus
                from gws_care.patient.patient import Patient
                from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef

                tube = TubeQR()
                tube.qr_code = str(uuid.uuid4())
                tube.short_id = tube.qr_code.replace("-", "")[:6].upper()
                tube.status = TubeQRStatus.ASSOCIATED.value
                tube.patient = Patient.get_by_id_and_check(self._current_patient_id)
                tube.exam_type_ref = ExamTypeRef.get_by_id_and_check(self.create_exam_type_id)
                tube.sample_type = self.create_sample_type
                tube.associated_at = datetime.now()
                if self.create_campaign_id:
                    from gws_care.campaign.campaign import Campaign
                    tube.campaign = Campaign.get_by_id_and_check(self.create_campaign_id)
                if self.create_volume_ml:
                    try:
                        tube.volume_ml = float(self.create_volume_ml)
                    except ValueError:
                        pass
                if self.create_notes.strip():
                    tube.collector_notes = self.create_notes.strip()
                tube.save()

            self.show_create_dialog = False
            yield rx.toast.success(f"Tube {tube.short_id} généré et prêt à l'étiquetage.")
            yield SampleCollectionState.load_for_patient(
                self._current_patient_id, self._current_campaign_id
            )
        except Exception as e:
            self.create_error = str(e)
        finally:
            self.is_creating = False

    # ── Mark collected ───────────────────────────────────────────────────

    @rx.event
    async def mark_collected(self, tube_id: str) -> AsyncGenerator:
        try:
            with await self.authenticate_user():
                from gws_care.tube_qr.tube_qr import TubeQR, TubeQRStatus
                tube = TubeQR.get_by_id_and_check(tube_id)
                tube.status = TubeQRStatus.COLLECTED.value
                tube.collected_at = datetime.now()
                tube.save()
            yield rx.toast.success("Prélèvement marqué effectué.")
            yield SampleCollectionState.load_for_patient(
                self._current_patient_id, self._current_campaign_id
            )
        except Exception as e:
            yield rx.toast.error(str(e))

    # ── Cancel dialog ────────────────────────────────────────────────────

    @rx.event
    def open_cancel_dialog(self, tube_id: str) -> None:
        self.cancel_tube_id = tube_id
        self.cancel_reason = ""
        self.cancel_error = ""
        self.show_cancel_dialog = True

    @rx.event
    def close_cancel_dialog(self) -> None:
        self.show_cancel_dialog = False
        self.cancel_error = ""

    @rx.event
    def set_cancel_reason(self, v: str) -> None:
        self.cancel_reason = v

    @rx.event
    async def confirm_cancel(self) -> AsyncGenerator:
        if not self.cancel_reason.strip():
            self.cancel_error = "Le motif d'annulation est obligatoire."
            return
        tube_id = self.cancel_tube_id
        try:
            with await self.authenticate_user():
                from gws_care.tube_qr.tube_qr import TubeQR, TubeQRStatus
                tube = TubeQR.get_by_id_and_check(tube_id)
                tube.status = TubeQRStatus.CANCELLED.value
                tube.cancelled_reason = self.cancel_reason.strip()
                tube.save()
            self.show_cancel_dialog = False
            yield rx.toast.success("Tube annulé.")
            yield SampleCollectionState.load_for_patient(
                self._current_patient_id, self._current_campaign_id
            )
        except Exception as e:
            self.cancel_error = str(e)
