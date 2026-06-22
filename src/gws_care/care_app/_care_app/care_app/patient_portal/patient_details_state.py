"""State for the My Details patient portal page (/my-details).

Shows the logged-in patient's own information in read-only mode.
Doctor assignment is not shown (patient cannot change their assigned doctor).
"""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class PrescriptionCalDayDTO(BaseModel):
    date: str = ""
    day_num: int = 0
    is_current_month: bool = False
    is_today: bool = False
    prescription_ids: list[str] = []
    prescription_labels: list[str] = []  # short label per prescription


class PatientOwnDetailsDTO(BaseModel):
    """Read-only patient details for the patient portal."""

    id: str = ""
    patient_number: str = ""
    last_name: str = ""
    first_name: str = ""
    birth_name: str = ""
    date_of_birth: str = ""
    gender: str = ""
    social_security_number: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    postal_code: str = ""
    city: str = ""
    account_name: str = ""
    account_id: str = ""
    notification_preferences: list[str] = []
    # Primary physician (médecin traitant)
    primary_physician_full_name: str = ""
    primary_physician_specialization: str = ""
    primary_physician_phone: str = ""
    primary_physician_email: str = ""


class PatientDetailsState(RoleState):
    """State for the /my-details page."""

    patient: PatientOwnDetailsDTO = PatientOwnDetailsDTO()
    is_loading: bool = False
    error_message: str = ""

    # ── ID card dialog ────────────────────────────────────────────────────────
    show_id_card: bool = False

    # ── Prescription calendar ─────────────────────────────────────────────────
    presc_cal_year: int = 2026
    presc_cal_month: int = 1
    presc_cal_label: str = ""
    presc_cal_days: list[PrescriptionCalDayDTO] = []
    presc_cal_loading: bool = False

    # ── Edit dialog ───────────────────────────────────────────────────────────
    show_edit_dialog: bool = False
    edit_phone: str = ""
    edit_email: str = ""
    edit_address: str = ""
    edit_postal_code: str = ""
    edit_city: str = ""
    edit_error: str = ""
    edit_is_saving: bool = False

    # ── Page guard ────────────────────────────────────────────────────────

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user, redirect_to="/dashboard")
        if redirect:
            yield redirect
            return
        await self._load_patient()
        from datetime import date
        today = date.today()
        self.presc_cal_year = today.year
        self.presc_cal_month = today.month
        await self._load_prescriptions()
        patient_id = self._linked_patient_id
        if patient_id:
            from ..patient_detail.patient_doctor_tab_state import PatientDoctorTabState
            yield PatientDoctorTabState.load(patient_id)

    # ── Prescription calendar events ─────────────────────────────────────────

    @rx.event
    async def presc_cal_prev_month(self):
        if self.presc_cal_month == 1:
            self.presc_cal_month = 12
            self.presc_cal_year -= 1
        else:
            self.presc_cal_month -= 1
        await self._load_prescriptions()

    @rx.event
    async def presc_cal_next_month(self):
        if self.presc_cal_month == 12:
            self.presc_cal_month = 1
            self.presc_cal_year += 1
        else:
            self.presc_cal_month += 1
        await self._load_prescriptions()

    # ── Data loader ────────────────────────────────────────────────────────

    async def _load_patient(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            return

        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                p = PatientService.get_patient(patient_id)

                # Resolve account
                account_name = ""
                account_id = ""
                try:
                    from gws_care.patient.patient_account import PatientAccount
                    links = list(PatientAccount.select().where(PatientAccount.patient == patient_id))
                    if links:
                        account_name = links[0].account.name
                        account_id = str(links[0].account_id)
                except Exception:
                    pass

                # Notification preferences
                notif_prefs: list[str] = []
                try:
                    if hasattr(p, "notification_preferences") and p.notification_preferences:
                        notif_prefs = list(p.notification_preferences)
                except Exception:
                    pass

                # Resolve primary physician (médecin traitant) from PatientDoctor table
                physician_full_name = ""
                physician_specialization = ""
                physician_phone = ""
                physician_email = ""
                try:
                    from gws_care.patient.patient_doctor_service import PatientDoctorService
                    referent = PatientDoctorService.get_referent(patient_id)
                    if referent:
                        physician_full_name = referent.get_full_name()
                        physician_specialization = referent.specialization or ""
                        physician_phone = referent.phone or ""
                        physician_email = referent.email or ""
                except Exception:
                    pass

                self.patient = PatientOwnDetailsDTO(
                    id=str(p.id),
                    patient_number=p.patient_number,
                    last_name=p.last_name,
                    first_name=p.first_name,
                    birth_name=p.birth_name or "",
                    date_of_birth=p.date_of_birth.isoformat() if p.date_of_birth else "",
                    gender=p.gender or "",
                    social_security_number=p.social_security_number or "",
                    phone=p.phone or "",
                    email=p.email or "",
                    address=p.address or "",
                    postal_code=p.postal_code or "",
                    city=p.city or "",
                    account_name=account_name,
                    account_id=account_id,
                    notification_preferences=notif_prefs,
                    primary_physician_full_name=physician_full_name,
                    primary_physician_specialization=physician_specialization,
                    primary_physician_phone=physician_phone,
                    primary_physician_email=physician_email,
                )
        except Exception as e:
            self.error_message = f"Error loading patient details: {e}"
        finally:
            self.is_loading = False

    # ── ID card events ────────────────────────────────────────────────────────

    @rx.event
    def open_id_card(self):
        self.show_id_card = True

    @rx.event
    def close_id_card(self):
        self.show_id_card = False

    @rx.event
    async def download_id_card_pdf(self):
        patient_id = self._linked_patient_id
        if not patient_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.pdf import generate_patient_id_card_pdf
                pdf_bytes = generate_patient_id_card_pdf(patient_id)
            filename = f"carte_patient_{self.patient.patient_number}.pdf"
            return rx.download(data=pdf_bytes, filename=filename)
        except Exception as e:
            self.error_message = f"PDF generation error: {e}"

    # ── Edit dialog events ────────────────────────────────────────────────────

    @rx.event
    def open_edit_dialog(self):
        self.edit_phone = self.patient.phone
        self.edit_email = self.patient.email
        self.edit_address = self.patient.address
        self.edit_postal_code = self.patient.postal_code
        self.edit_city = self.patient.city
        self.edit_error = ""
        self.edit_is_saving = False
        self.show_edit_dialog = True

    @rx.event
    def close_edit_dialog(self):
        self.show_edit_dialog = False

    @rx.event
    def set_edit_phone(self, value: str):
        self.edit_phone = value

    @rx.event
    def set_edit_email(self, value: str):
        self.edit_email = value

    @rx.event
    def set_edit_address(self, value: str):
        self.edit_address = value

    @rx.event
    def set_edit_postal_code(self, value: str):
        self.edit_postal_code = value

    @rx.event
    def set_edit_city(self, value: str):
        self.edit_city = value

    @rx.event
    async def save_edit(self):
        patient_id = self._linked_patient_id
        if not patient_id:
            return
        self.edit_error = ""
        self.edit_is_saving = True
        try:
            with await self.authenticate_user():
                from datetime import date
                from gws_care.patient.patient_dto import SavePatientDTO
                from gws_care.patient.patient_service import PatientService
                p = PatientService.get_patient(patient_id)
                dto = SavePatientDTO(
                    last_name=p.last_name,
                    first_name=p.first_name,
                    birth_name=p.birth_name,
                    date_of_birth=p.date_of_birth,
                    gender=p.gender or "",
                    social_security_number=p.social_security_number,
                    phone=self.edit_phone or None,
                    email=self.edit_email or None,
                    address=self.edit_address or None,
                    postal_code=self.edit_postal_code or None,
                    city=self.edit_city or None,
                )
                PatientService.update_patient(patient_id, dto)
            self.show_edit_dialog = False
            await self._load_patient()
        except Exception as e:
            self.edit_error = str(e)
        finally:
            self.edit_is_saving = False

    # ── Prescription calendar ─────────────────────────────────────────────────

    async def _load_prescriptions(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.presc_cal_days = []
            return
        self.presc_cal_loading = True
        try:
            with await self.authenticate_user():
                from gws_care.prescription.prescription import PrescriptionService
                rows = PrescriptionService.list_for_patient(patient_id, include_archived=False)
                self._build_presc_calendar(rows)
        except Exception:
            self.presc_cal_days = []
        finally:
            self.presc_cal_loading = False

    def _build_presc_calendar(self, rows) -> None:
        import calendar
        from datetime import date

        _MONTHS = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        self.presc_cal_label = f"{_MONTHS[self.presc_cal_month - 1]} {self.presc_cal_year}"

        by_date: dict[str, list] = {}
        for r in rows:
            if not r.prescription_date:
                continue
            key = r.prescription_date.isoformat()[:10]
            if key not in by_date:
                by_date[key] = []
            label = r.diagnosis[:30] + "…" if r.diagnosis and len(r.diagnosis) > 30 else (r.diagnosis or "Prescription")
            by_date[key].append((str(r.id), label))

        today_str = date.today().isoformat()
        first_weekday, num_days = calendar.monthrange(self.presc_cal_year, self.presc_cal_month)
        days: list[PrescriptionCalDayDTO] = []
        for _ in range(first_weekday):
            days.append(PrescriptionCalDayDTO())
        for d in range(1, num_days + 1):
            date_str = f"{self.presc_cal_year:04d}-{self.presc_cal_month:02d}-{d:02d}"
            entries = by_date.get(date_str, [])
            days.append(PrescriptionCalDayDTO(
                date=date_str,
                day_num=d,
                is_current_month=True,
                is_today=(date_str == today_str),
                prescription_ids=[e[0] for e in entries],
                prescription_labels=[e[1] for e in entries],
            ))
        remainder = len(days) % 7
        if remainder:
            for _ in range(7 - remainder):
                days.append(PrescriptionCalDayDTO())
        self.presc_cal_days = days
