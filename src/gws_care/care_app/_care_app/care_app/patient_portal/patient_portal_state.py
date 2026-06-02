"""State for the patient portal — the patient's personal space."""

from pydantic import BaseModel
import reflex as rx
from gws_reflex_main import ReflexMainState


class PortalExamRowDTO(BaseModel):
    exam_id: str = ""
    exam_type_label: str = ""
    exam_date: str = ""
    status: str = ""
    status_label: str = ""
    has_results: bool = False
    conclusion: str = ""


class PortalAppointmentDTO(BaseModel):
    id: str = ""
    scheduled_at: str = ""
    exam_type_label: str = ""
    status: str = ""
    status_label: str = ""
    campaign_name: str = ""


class PortalCertificateDTO(BaseModel):
    id: str = ""
    issue_date: str = ""
    conclusion: str = ""
    is_fit_for_work: bool = True
    restrictions: str = ""


class BookingExamTypeDTO(BaseModel):
    id: str = ""
    name: str = ""


class BookingDoctorDTO(BaseModel):
    id: str = ""
    name: str = ""
    specialty: str = ""  # from UserCareRole.specialty


class PrescribedFollowUpDTO(BaseModel):
    """A follow-up exam prescribed by a doctor during a consultation."""

    exam_id: str = ""          # source Exam.id
    exam_date: str = ""        # date of the originating consultation
    prescribing_doctor: str = ""
    ref_id: str = ""           # ExamTypeRef.id
    ref_name: str = ""         # ExamTypeRef.name
    has_appointment: bool = False  # is there already a booked appointment for this?
    appointment_id: str = ""


class PatientPortalState(ReflexMainState):
    """Patient personal portal state."""

    patient_id: str = ""
    patient_name: str = ""
    patient_number: str = ""
    date_of_birth: str = ""
    gender: str = ""

    exams: list[PortalExamRowDTO] = []
    appointments: list[PortalAppointmentDTO] = []
    certificates: list[PortalCertificateDTO] = []
    prescribed_followups: list[PrescribedFollowUpDTO] = []

    unread_messages: int = 0

    is_loading: bool = False
    error: str = ""

    # Active tab
    active_tab: str = "exams"  # "exams" | "appointments" | "certificates" | "messages"

    # ── Booking form ──────────────────────────────────────────────────────────
    booking_open: bool = False
    booking_exam_type_ref_id: str = ""
    booking_doctor_id: str = ""
    booking_date: str = ""          # YYYY-MM-DD (min = today)
    booking_slot: str = ""          # "YYYY-MM-DDTHH:MM"
    booking_notes: str = ""
    booking_error: str = ""
    booking_success: bool = False
    booking_is_loading: bool = False
    # Reference data for booking selectors
    booking_exam_types: list[BookingExamTypeDTO] = []
    booking_doctors: list[BookingDoctorDTO] = []
    booking_specialty: str = ""      # selected specialty filter
    booking_specialty_options: list[str] = []
    booking_slots: list[str] = []   # available slot strings "YYYY-MM-DDTHH:MM"

    @rx.event
    async def on_load(self):
        self.is_loading = True
        self.error = ""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.role.user_role_service import UserRoleService
                linked_id = UserRoleService.get_linked_patient_id(str(auth_user.id)) or ""
                if not linked_id:
                    self.error = "Aucun dossier patient associé à votre compte."
                    return
                self.patient_id = linked_id
                await self._load_all(linked_id)
        except Exception as exc:
            self.error = str(exc)
        finally:
            self.is_loading = False

    @rx.event
    def set_tab(self, tab: str):
        self.active_tab = tab

    # ── Booking events ────────────────────────────────────────────────────────

    @rx.event
    async def open_booking_dialog(self):
        """Open booking dialog and load reference data (exam types + doctors)."""
        self.booking_exam_type_ref_id = ""
        self.booking_doctor_id = ""
        self.booking_date = ""
        self.booking_slot = ""
        self.booking_notes = ""
        self.booking_error = ""
        self.booking_success = False
        self.booking_slots = []
        self.booking_exam_types = []
        self.booking_doctors = []
        self.booking_specialty = ""
        self.booking_specialty_options = []
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                refs = list(
                    ExamTypeRef.select()
                    .where(ExamTypeRef.is_active == True)  # noqa: E712
                    .order_by(ExamTypeRef.category, ExamTypeRef.name)
                )
                self.booking_exam_types = [
                    BookingExamTypeDTO(id=str(r.id), name=r.name) for r in refs
                ]
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_care_role import UserCareRole
                from gws_care.user.user import User
                doctor_roles = [CareRole.MEDECIN_PSC.value, CareRole.MEDECIN_ENTREPRISE.value]
                rows = (
                    UserCareRole.select(UserCareRole, User)
                    .join(User)
                    .where(UserCareRole.role.in_(doctor_roles))
                )
                seen: set[str] = set()
                doctors: list[BookingDoctorDTO] = []
                specialties: set[str] = set()
                for row in rows:
                    uid = str(row.user.id)
                    if uid not in seen:
                        seen.add(uid)
                        sp = row.specialty or ""
                        name = f"Dr {row.user.first_name} {row.user.last_name}".strip()
                        doctors.append(BookingDoctorDTO(id=uid, name=name, specialty=sp))
                        if sp:
                            specialties.add(sp)
                self.booking_doctors = doctors
                self.booking_specialty_options = sorted(specialties)
        except Exception as exc:
            self.booking_error = str(exc)
        self.booking_open = True

    @rx.event
    def close_booking_dialog(self):
        self.booking_open = False

    @rx.var
    def filtered_booking_doctors(self) -> list[BookingDoctorDTO]:
        """Doctors filtered by selected specialty (or all if no filter)."""
        if not self.booking_specialty or self.booking_specialty == "__all__":
            return self.booking_doctors
        return [d for d in self.booking_doctors if d.specialty == self.booking_specialty]

    @rx.event
    def set_booking_exam_type(self, ref_id: str):
        self.booking_exam_type_ref_id = ref_id

    @rx.event
    def set_booking_specialty(self, specialty: str):
        self.booking_specialty = "" if specialty == "__all__" else specialty
        # Reset doctor when specialty changes
        self.booking_doctor_id = ""
        self.booking_slots = []
        self.booking_slot = ""

    @rx.event
    async def open_booking_for_prescription(self, ref_id: str, ref_name: str):
        """Open the booking dialog pre-set to a specific prescribed exam type."""
        await self.open_booking_dialog()
        # Pre-select the prescribed exam type after loading
        self.booking_exam_type_ref_id = ref_id
        self.booking_notes = f"Suivi prescrit : {ref_name}"

    @rx.event
    async def set_booking_doctor(self, doctor_id: str):
        self.booking_doctor_id = doctor_id
        await self._load_booking_slots()

    @rx.event
    async def set_booking_date(self, date_str: str):
        self.booking_date = date_str
        await self._load_booking_slots()

    @rx.event
    def set_booking_slot(self, slot: str):
        self.booking_slot = slot

    @rx.event
    def set_booking_notes(self, notes: str):
        self.booking_notes = notes

    @rx.event
    async def confirm_booking(self):
        """Create the appointment from the portal booking form."""
        self.booking_error = ""
        if not self.booking_exam_type_ref_id:
            self.booking_error = "Veuillez sélectionner un type d'examen."
            return
        if not self.booking_doctor_id:
            self.booking_error = "Veuillez sélectionner un médecin."
            return
        if not self.booking_slot:
            self.booking_error = "Veuillez sélectionner un créneau disponible."
            return
        self.booking_is_loading = True
        try:
            with await self.authenticate_user():
                from gws_care.appointment.appointment_dto import SaveAppointmentDTO
                from gws_care.appointment.appointment_service import AppointmentService
                from gws_care.patient.patient import Patient

                patient = Patient.get_by_id(self.patient_id)
                account_id = str(patient.billing_account_id) if patient.billing_account_id else None

                dto = SaveAppointmentDTO(
                    patient_id=self.patient_id,
                    account_id=account_id,
                    scheduled_at=self.booking_slot,
                    exam_type="other",
                    exam_type_ref_id=self.booking_exam_type_ref_id,
                    notes=self.booking_notes or None,
                    assigned_doctor_id=self.booking_doctor_id,
                    duration_minutes=30,
                    room=None,
                )
                AppointmentService.create_appointment(dto)
            self.booking_open = False
            self.booking_success = True
            # Reload portal appointments
            with await self.authenticate_user():
                await self._load_all(self.patient_id)
        except Exception as exc:
            self.booking_error = str(exc)
        finally:
            self.booking_is_loading = False

    async def _load_booking_slots(self):
        """Load available time slots for the selected doctor + date."""
        if not self.booking_doctor_id or not self.booking_date:
            self.booking_slots = []
            self.booking_slot = ""
            return
        try:
            with await self.authenticate_user():
                from datetime import date
                from gws_care.scheduling.doctor_schedule import DoctorScheduleService
                d = date.fromisoformat(self.booking_date)
                slots = DoctorScheduleService.available_slots(self.booking_doctor_id, d)
                self.booking_slots = [s.strftime("%Y-%m-%dT%H:%M") for s in slots]
                self.booking_slot = self.booking_slots[0] if self.booking_slots else ""
        except Exception as exc:
            self.booking_slots = []
            self.booking_slot = ""
            self.booking_error = str(exc)

    # ── Internals ─────────────────────────────────────────────────────────────

    async def _load_all(self, patient_id: str):
        from gws_care.patient.patient import Patient
        from gws_care.exam.exam import Exam
        from gws_care.exam.exam_type import ExamStatus
        from gws_care.appointment.appointment import Appointment
        from gws_care.certificate.medical_certificate import MedicalCertificate
        from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
        from gws_care.messaging.patient_message import PatientMessageService

        p = Patient.get_by_id(patient_id)
        self.patient_name = p.get_full_name()
        self.patient_number = p.patient_number
        self.date_of_birth = p.date_of_birth.strftime("%d/%m/%Y") if p.date_of_birth else ""
        self.gender = p.gender

        # Build label lookup
        ref_labels = {str(r.id): r.name for r in ExamTypeRef.select(ExamTypeRef.id, ExamTypeRef.name)}

        # Exams — only show results that have been published (status = interpreted)
        # SECURITY: never expose draft or pending results to the patient
        published_statuses = {ExamStatus.INTERPRETED.value}
        exams_raw = list(
            Exam.select()
            .where(
                (Exam.patient == patient_id)
                & (Exam.status == ExamStatus.INTERPRETED.value)
            )
            .order_by(Exam.exam_date.desc())
            .limit(500)
        )
        self.exams = []
        for ex in exams_raw:
            try:
                st = ExamStatus(ex.status)
                st_label = st.get_label()
            except Exception as exc:
                st_label = ex.status
            lbl = ref_labels.get(str(ex.exam_type_ref_id), "") or ex.exam_type
            self.exams.append(PortalExamRowDTO(
                exam_id=str(ex.id),
                exam_type_label=lbl,
                exam_date=ex.exam_date.strftime("%d/%m/%Y") if ex.exam_date else "",
                status=ex.status,
                status_label=st_label,
                has_results=ex.status in published_statuses,
                conclusion=ex.conclusion or "",
            ))

        # Appointments
        appts_raw = list(
            Appointment.select()
            .where(Appointment.patient == patient_id)
            .order_by(Appointment.scheduled_at.desc())
            .limit(200)
        )
        self.appointments = []
        for a in appts_raw:
            try:
                from gws_care.appointment.appointment import AppointmentStatus
                st_label = AppointmentStatus(a.status).get_label()
            except Exception as exc:
                st_label = a.status
            lbl = ref_labels.get(str(getattr(a, "exam_type_ref_id", "")), "") or ""
            self.appointments.append(PortalAppointmentDTO(
                id=str(a.id),
                scheduled_at=a.scheduled_at.strftime("%d/%m/%Y %H:%M") if a.scheduled_at else "",
                exam_type_label=lbl,
                status=a.status.value if hasattr(a.status, "value") else str(a.status),
                status_label=st_label,
                campaign_name="",
            ))

        # Certificates
        certs_raw = list(
            MedicalCertificate.select()
            .where(MedicalCertificate.patient == patient_id)
            .order_by(MedicalCertificate.issue_date.desc())
            .limit(100)
        )
        self.certificates = [
            PortalCertificateDTO(
                id=str(c.id),
                issue_date=c.issue_date.strftime("%d/%m/%Y") if c.issue_date else "",
                conclusion=c.conclusion or "",
                is_fit_for_work=c.is_fit_for_work,
                restrictions=c.restrictions or "",
            )
            for c in certs_raw
        ]

        # Unread messages (sent by doctor, not yet read by patient)
        self.unread_messages = PatientMessageService.unread_count_for_doctor(patient_id)

        # Prescribed follow-up exams — load from all interpreted exams that have prescriptions
        # Load all exams with prescribed_exam_ref_ids (any status — prescription may come before interpretation)
        exams_with_prescriptions = list(
            Exam.select()
            .where(
                (Exam.patient == patient_id)
                & (Exam.prescribed_exam_ref_ids.is_null(False))
            )
            .order_by(Exam.exam_date.desc())
            .limit(200)
        )
        # Build a set of already-booked appointment exam_type_ref_ids for this patient
        # (tagged with APPT: or with exam_type_ref_id matching)
        booked_ref_ids: set[str] = set()
        from gws_care.appointment.appointment_status import AppointmentStatus as AStatus
        active_appts = list(
            Appointment.select()
            .where(
                (Appointment.patient == patient_id)
                & (Appointment.status != AStatus.CANCELLED.value)
            )
        )
        for a in active_appts:
            if a.exam_type_ref_id:
                booked_ref_ids.add(f"{str(a.exam_type_ref_id)}")

        followups: list[PrescribedFollowUpDTO] = []
        for ex in exams_with_prescriptions:
            prescribed = ex.prescribed_exam_ref_ids or []
            if not prescribed:
                continue
            # Resolve doctor name
            doctor_name = ""
            if ex.created_by_id:
                from gws_care.user.user import User
                doc = User.get_or_none(User.id == ex.created_by_id)
                if doc:
                    doctor_name = f"Dr {doc.first_name} {doc.last_name}".strip()
            for ref_id in prescribed:
                ref_name = ref_labels.get(str(ref_id), str(ref_id))
                has_apt = str(ref_id) in booked_ref_ids
                followups.append(PrescribedFollowUpDTO(
                    exam_id=str(ex.id),
                    exam_date=ex.exam_date.strftime("%d/%m/%Y") if ex.exam_date else "",
                    prescribing_doctor=doctor_name,
                    ref_id=str(ref_id),
                    ref_name=ref_name,
                    has_appointment=has_apt,
                ))
        self.prescribed_followups = followups
