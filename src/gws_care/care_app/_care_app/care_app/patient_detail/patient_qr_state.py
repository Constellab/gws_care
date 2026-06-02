"""State for generating and downloading the patient identity QR code."""

import base64
import io

import reflex as rx
from gws_reflex_main import ReflexMainState


class PatientQrState(ReflexMainState):
    """Generates a base64 QR code image for a patient, on demand."""

    qr_image_data_url: str = ""   # data:image/png;base64,...

    @rx.event
    async def on_load(self) -> None:
        """Generate the QR image from the patient_id_param URL variable."""
        patient_id = self.patient_id_param  # type: ignore[attr-defined]
        if not patient_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                patient = PatientService.get_patient(patient_id)
                token = patient.qr_token or patient.patient_number
            self.qr_image_data_url = self._make_qr_data_url(token)
        except Exception as exc:
            yield rx.toast.error(f"Impossible de générer le QR : {exc}")

    @rx.event
    async def download_qr(self, patient_id: str, patient_number: str) -> None:
        """Download the QR code as a PNG file."""
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                patient = PatientService.get_patient(patient_id)
                token = patient.qr_token or patient.patient_number
            png_bytes = self._make_qr_png_bytes(token)
            filename = f"QR_{patient_number}.png"
            yield rx.download(data=png_bytes, filename=filename)
        except Exception as exc:
            yield rx.toast.error(f"Erreur export QR : {exc}")

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _make_qr_png_bytes(content: str) -> bytes:
        import qrcode  # type: ignore[import]
        buf = io.BytesIO()
        qrcode.make(content).save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def _make_qr_data_url(content: str) -> str:
        import qrcode  # type: ignore[import]
        buf = io.BytesIO()
        qrcode.make(content).save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{b64}"
