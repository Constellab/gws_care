"""State for the doctor's assigned-exams page.

Role-based task dashboard:
  - Doctors (via CampaignExamDoctor): see their assigned exam/patient rows
  - OPERATEUR: see all LAB_ENTERED patients (grouped under "Labo")
  - MEDECIN: see all LAB_VALIDATED + LAB_ENTERED patients (internal interpretation queue)
  - ADMIN: see all doctor assignments

Filter values in filter_assignee:
  "__all__"  → show all rows
  "__lab__"  → only lab rows
  "__psc__"  → only internal-interpretation queue rows
  "{doctor_id}" → only rows for that specific doctor
"""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class AssignedDoctorOption(BaseModel):
    """Entry for the assignee filter dropdown."""

    id: str   # doctor ID, "__lab__", or "__psc__"
    name: str


class AssignedExamRowDTO(BaseModel):
    """One row in the assigned-exams table."""

    # "doctor" | "lab" | "psc"
    row_type: str = "doctor"
    # "campaign" | "private"
    source: str = "campaign"

    # Assigned doctor / special label
    assigned_doctor_id: str = ""
    assigned_doctor_name: str = ""

    # Campaign context
    campaign_id: str = ""
    campaign_name: str = ""
    campaign_number: str = ""
    campaign_status: str = ""
    campaign_status_label: str = ""

    # Exam type (may be "Tous les examens" for lab/psc rows)
    exam_type_id: str = ""
    exam_type_name: str = ""
    exam_category: str = ""

    # Patient
    patient_id: str = ""
    patient_name: str = ""
    patient_number: str = ""

    # Medical status
    medical_status: str = "PENDING"
    medical_status_label: str = "En attente"
    medical_status_color: str = "gray"

    # Pending task
    pending_task: str = ""
    pending_task_color: str = "gray"

    # Appointment date (YYYY-MM-DD or empty)
    scheduled_at: str = ""

    # Deep-link to exam entry page
    action_url: str = ""
    can_act: bool = True


class DoctorAssignedExamsState(ReflexMainState):
    rows: list[AssignedExamRowDTO] = []
    available_assignees: list[AssignedDoctorOption] = []
    is_loading: bool = False
    error: str = ""

    my_doctor_id: str = ""
    is_lab: bool = False
    is_psc: bool = False
    is_admin: bool = False

    # "__all__" | "__lab__" | "__psc__" | doctor_id
    filter_assignee: str = "__all__"
    filter_status: str = "__all__"
    filter_source: str = "__all__"
    filter_search: str = ""

    @rx.var
    def filtered_rows(self) -> list[AssignedExamRowDTO]:
        result = self.rows
        fa = self.filter_assignee
        if fa == "__lab__":
            result = [r for r in result if r.row_type == "lab"]
        elif fa == "__psc__":
            result = [r for r in result if r.row_type == "psc"]
        elif fa != "__all__":
            result = [r for r in result if r.row_type == "doctor" and r.assigned_doctor_id == fa]
        if self.filter_status != "__all__":
            result = [r for r in result if r.medical_status == self.filter_status]
        if self.filter_source != "__all__":
            result = [r for r in result if r.source == self.filter_source]
        if self.filter_search.strip():
            q = self.filter_search.strip().lower()
            result = [
                r for r in result
                if q in r.patient_name.lower()
                or q in r.patient_number.lower()
                or q in r.exam_type_name.lower()
                or q in r.campaign_name.lower()
                or q in r.assigned_doctor_name.lower()
            ]
        return result

    @rx.event
    def set_filter_assignee(self, value: str):
        self.filter_assignee = value

    @rx.event
    def set_filter_status(self, value: str):
        self.filter_status = value

    @rx.event
    def set_filter_source(self, value: str):
        self.filter_source = value
        self.filter_status = "__all__"  # reset status filter when source changes

    @rx.event
    def set_filter_search(self, value: str):
        self.filter_search = value

    # backward-compat alias used by older component code
    @rx.event
    def set_filter_doctor_id(self, value: str):
        self.filter_assignee = value

    @rx.var
    def filter_doctor_id(self) -> str:
        return self.filter_assignee

    @rx.event
    async def on_load(self):
        self.is_loading = True
        self.error = ""
        try:
            from ..admin.general_settings_state import GeneralSettingsState
            org_acronym = (await self.get_state(GeneralSettingsState)).org_acronym
            with await self.authenticate_user() as auth_user:
                self._load_rows(auth_user.id, org_acronym)
        except Exception as exc:
            self.error = str(exc)
        finally:
            self.is_loading = False

    def _load_rows(self, auth_user_id, org_acronym: str) -> None:
        from gws_care.campaign.campaign import Campaign
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.campaign.campaign_exam_doctor import CampaignExamDoctor
        from gws_care.campaign.campaign_patient import CampaignPatient, MedicalRecordStatus
        from gws_care.doctor.medical_doctor import MedicalDoctor
        from gws_care.exam.exam import Exam
        from gws_care.exam.exam_type import ExamStatus
        from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
        from gws_care.patient.patient import Patient
        from gws_care.role.care_role import CareRole
        from gws_care.role.user_role_service import UserRoleService
        from gws_care.visit.visit import Visit

        # Detect doctor identity and roles
        me = MedicalDoctor.get_or_none(
            (MedicalDoctor.user == auth_user_id)
            & (MedicalDoctor.is_active == True)
            & (MedicalDoctor.is_archived == False)
        )
        self.my_doctor_id = str(me.id) if me else ""
        roles = UserRoleService.get_roles_for_user(str(auth_user_id))
        role_vals = [r.value if hasattr(r, "value") else str(r) for r in roles]

        self.is_lab = CareRole.OPERATEUR.value in role_vals
        self.is_psc = any(r in role_vals for r in [
            CareRole.MEDECIN.value,
            CareRole.ADMIN.value,
        ])
        is_admin = CareRole.ADMIN.value in role_vals
        self.is_admin = is_admin

        _status_labels = {
            "draft": "Brouillon", "validated": "Validée",
            "terrain_exam": "Terrain", "sample_analysis": "Analyse",
            "lab_done": "Labo terminé", "closed": "Clôturée", "archived": "Archivée",
        }
        _task_map: dict[str, tuple[str, str]] = {
            "PENDING":                     ("Saisir les résultats",        "orange"),
            "LAB_ENTERED":                 ("Valider résultats labo",      "amber"),
            "LAB_VALIDATED":               (f"Interprétation {org_acronym}", "blue"),
            "PSC_INTERPRETED":             (f"Valider {org_acronym}",      "blue"),
            "PSC_VALIDATED":               ("Valider médecin de travail",  "teal"),
            "TRANSMITTED_TREATING_DOCTOR": ("Valider médecin de travail",  "teal"),
            "ENTERPRISE_VALIDATED":        ("Clôturer le dossier",         "green"),
            "PUBLISHED":                   ("Terminé",                     "green"),
        }

        result: list[AssignedExamRowDTO] = []
        doctor_map: dict[str, str] = {}

        # ── 1. Doctor rows via CampaignExamDoctor ─────────────────────────────
        # CampaignExamDoctor → MedicalDoctor + CampaignExam → Campaign + ExamTypeRef
        ced_query = (
            CampaignExamDoctor.select(
                CampaignExamDoctor, MedicalDoctor, CampaignExam, Campaign, ExamTypeRef
            )
            .join(MedicalDoctor)
            .switch(CampaignExamDoctor)
            .join(CampaignExam)
            .join(Campaign, on=(CampaignExam.campaign == Campaign.id))
            .switch(CampaignExam)
            .join(ExamTypeRef, on=(CampaignExam.exam_type_ref == ExamTypeRef.id))
        )

        # Non-admin doctors only see their own assignments
        if not is_admin:
            if me:
                ced_query = ced_query.where(CampaignExamDoctor.doctor == me.id)
            else:
                ced_query = None  # Not a doctor, no doctor rows

        assigned_ceds = list(ced_query) if ced_query is not None else []

        # Collect doctor names for dropdown
        for ced in assigned_ceds:
            doc = ced.doctor
            did = str(doc.id)
            if did not in doctor_map:
                doctor_map[did] = doc.get_full_name()

        # Preload patients for all involved campaigns
        ced_camp_ids = list({str(ced.campaign_exam.campaign_id) for ced in assigned_ceds})
        campaign_patients: dict[str, list] = {}
        for cid in ced_camp_ids:
            campaign_patients[cid] = list(
                CampaignPatient.select(CampaignPatient, Patient)
                .join(Patient, on=(CampaignPatient.patient == Patient.id))
                .where(CampaignPatient.campaign == cid)
            )

        # Build one row per (doctor, exam_type, patient)
        for ced in assigned_ceds:
            ce = ced.campaign_exam
            camp = ce.campaign
            cid = str(camp.id)
            doc = ced.doctor
            did = str(doc.id)
            camp_status = camp.status.value if hasattr(camp.status, "value") else str(camp.status)
            camp_status_label = _status_labels.get(camp_status, camp_status)

            for cp in campaign_patients.get(cid, []):
                patient = cp.patient
                ms = cp.medical_status or MedicalRecordStatus.PENDING.value
                try:
                    msr = MedicalRecordStatus(ms)
                    ms_label = msr.get_label(org_acronym)
                    ms_color = msr.get_color()
                except Exception:
                    ms_label = ms
                    ms_color = "gray"

                try:
                    exam_category = (
                        ce.exam_type_ref.get_category_label()
                        if hasattr(ce.exam_type_ref, "get_category_label")
                        else (ce.exam_type_ref.category or "")
                    )
                except Exception:
                    exam_category = ""

                result.append(AssignedExamRowDTO(
                    row_type="doctor",
                    assigned_doctor_id=did,
                    assigned_doctor_name=doc.get_full_name(),
                    campaign_id=cid,
                    campaign_name=camp.name,
                    campaign_number=camp.campaign_number,
                    campaign_status=camp_status,
                    campaign_status_label=camp_status_label,
                    exam_type_id=str(ce.exam_type_ref_id),
                    exam_type_name=ce.exam_type_ref.name,
                    exam_category=exam_category,
                    patient_id=str(patient.id),
                    patient_name=patient.get_full_name(),
                    patient_number=patient.patient_number,
                    medical_status=ms,
                    medical_status_label=ms_label,
                    medical_status_color=ms_color,
                    pending_task=_task_map.get(ms, ("", "gray"))[0],
                    pending_task_color=_task_map.get(ms, ("", "gray"))[1],
                    action_url=f"/campaign-patient/{cid}/{patient.id}",
                    can_act=camp_status in ("terrain_exam", "sample_analysis", "lab_done"),
                ))

        # ── 2. Internal interpretation queue ──────────────────────────────────
        if self.is_psc:
            psc_statuses = [
                MedicalRecordStatus.LAB_VALIDATED.value,
            ]
            psc_cps = list(
                CampaignPatient.select(CampaignPatient, Patient, Campaign)
                .join(Patient, on=(CampaignPatient.patient == Patient.id))
                .switch(CampaignPatient)
                .join(Campaign, on=(CampaignPatient.campaign == Campaign.id))
                .where(CampaignPatient.medical_status.in_(psc_statuses))
                .order_by(Campaign.name, Patient.last_name, Patient.first_name)
            )
            for cp in psc_cps:
                patient = cp.patient
                camp = cp.campaign
                cid = str(camp.id)
                camp_status = camp.status.value if hasattr(camp.status, "value") else str(camp.status)
                camp_status_label = _status_labels.get(camp_status, camp_status)
                ms = cp.medical_status or MedicalRecordStatus.PENDING.value
                try:
                    msr = MedicalRecordStatus(ms)
                    ms_label = msr.get_label(org_acronym)
                    ms_color = msr.get_color()
                except Exception:
                    ms_label = ms
                    ms_color = "gray"
                result.append(AssignedExamRowDTO(
                    row_type="psc",
                    assigned_doctor_id="__psc__",
                    assigned_doctor_name=f"Médecin {org_acronym}",
                    campaign_id=cid,
                    campaign_name=camp.name,
                    campaign_number=camp.campaign_number,
                    campaign_status=camp_status,
                    campaign_status_label=camp_status_label,
                    exam_type_id="",
                    exam_type_name="Tous les examens",
                    exam_category="",
                    patient_id=str(patient.id),
                    patient_name=patient.get_full_name(),
                    patient_number=patient.patient_number,
                    medical_status=ms,
                    medical_status_label=ms_label,
                    medical_status_color=ms_color,
                    pending_task=_task_map.get(ms, ("", "gray"))[0],
                    pending_task_color=_task_map.get(ms, ("", "gray"))[1],
                    action_url=f"/campaign-patient/{cid}/{patient.id}",
                    can_act=True,
                ))

        # ── 3. Lab rows ───────────────────────────────────────────────────────
        if self.is_lab or is_admin:
            lab_cps = list(
                CampaignPatient.select(CampaignPatient, Patient, Campaign)
                .join(Patient, on=(CampaignPatient.patient == Patient.id))
                .switch(CampaignPatient)
                .join(Campaign, on=(CampaignPatient.campaign == Campaign.id))
                .where(CampaignPatient.medical_status == MedicalRecordStatus.LAB_ENTERED.value)
                .order_by(Campaign.name, Patient.last_name, Patient.first_name)
            )
            for cp in lab_cps:
                patient = cp.patient
                camp = cp.campaign
                cid = str(camp.id)
                camp_status = camp.status.value if hasattr(camp.status, "value") else str(camp.status)
                camp_status_label = _status_labels.get(camp_status, camp_status)
                result.append(AssignedExamRowDTO(
                    row_type="lab",
                    assigned_doctor_id="__lab__",
                    assigned_doctor_name=f"Laboratoire {org_acronym}",
                    campaign_id=cid,
                    campaign_name=camp.name,
                    campaign_number=camp.campaign_number,
                    campaign_status=camp_status,
                    campaign_status_label=camp_status_label,
                    exam_type_id="",
                    exam_type_name="Tous les examens",
                    exam_category="",
                    patient_id=str(patient.id),
                    patient_name=patient.get_full_name(),
                    patient_number=patient.patient_number,
                    medical_status=MedicalRecordStatus.LAB_ENTERED.value,
                    medical_status_label="Résultats saisis",
                    medical_status_color="amber",
                    pending_task="Valider résultats labo",
                    pending_task_color="amber",
                    action_url=f"/campaign-patient/{cid}/{patient.id}",
                    can_act=camp_status in ("terrain_exam", "sample_analysis", "lab_done"),
                ))

        # ── 4. Private consultation exam rows (no campaign) ───────────────────
        _exam_status_label = {
            "todo": "À faire",
            "in_progress_results": "En cours — Résultats",
            "transmitted_to_lab": "Transmis au labo",
            "in_progress_interpretation": "En cours — Interprétation",
            "done": "Terminé",
        }
        _exam_status_color = {
            "todo": "gray",
            "in_progress_results": "orange",
            "transmitted_to_lab": "amber",
            "in_progress_interpretation": "blue",
            "done": "green",
        }
        _exam_pending_task = {
            "todo": ("Saisir résultats", "orange"),
            "in_progress_results": ("Compléter résultats", "orange"),
            "transmitted_to_lab": ("Saisir au labo", "amber"),
            "in_progress_interpretation": ("Interpréter résultats", "blue"),
            "done": ("Terminé", "green"),
        }

        # Doctor rows — private visits assigned to current doctor (or all for admin)
        private_visit_q = Visit.select().where(Visit.campaign.is_null(True))
        if not is_admin:
            if me:
                private_visit_q = private_visit_q.where(Visit.doctor == me.id)
            else:
                private_visit_q = None

        for visit in (list(private_visit_q) if private_visit_q is not None else []):
            try:
                patient = visit.patient
                if not patient:
                    continue
            except Exception:
                continue
            p_exams = list(
                Exam.select()
                .where(
                    (Exam.visit == visit.id)
                    & (Exam.status != ExamStatus.CANCELLED)
                    & (Exam.status != ExamStatus.TRANSMITTED_TO_LAB)
                )
            )
            for exam in p_exams:
                exam_type_name = ""
                try:
                    if exam.exam_type_ref_id:
                        ref = ExamTypeRef.get_or_none(ExamTypeRef.id == exam.exam_type_ref_id)
                        if ref:
                            exam_type_name = ref.name
                    if not exam_type_name:
                        exam_type_name = (
                            exam.exam_type.get_label()
                            if hasattr(exam.exam_type, "get_label")
                            else exam.exam_type.value
                        )
                except Exception:
                    exam_type_name = ""
                doc_id = ""
                doc_name = ""
                try:
                    if visit.doctor_id:
                        doc = visit.doctor
                        doc_id = str(visit.doctor_id)
                        doc_name = doc.get_full_name()
                        if doc_id not in doctor_map:
                            doctor_map[doc_id] = doc_name
                except Exception:
                    pass
                exam_st = exam.status.value
                is_doctor_active = exam_st not in (ExamStatus.DONE.value, ExamStatus.CANCELLED.value)
                result.append(AssignedExamRowDTO(
                    row_type="doctor",
                    source="private",
                    assigned_doctor_id=doc_id,
                    assigned_doctor_name=doc_name or "Non assigné",
                    campaign_id="",
                    campaign_name="Consultation privée",
                    campaign_number=visit.visit_number,
                    campaign_status="",
                    campaign_status_label="",
                    exam_type_id=str(exam.exam_type_ref_id) if exam.exam_type_ref_id else "",
                    exam_type_name=exam_type_name,
                    exam_category="",
                    patient_id=str(patient.id),
                    patient_name=patient.get_full_name(),
                    patient_number=patient.patient_number,
                    medical_status=exam_st,
                    medical_status_label=_exam_status_label.get(exam_st, exam_st),
                    medical_status_color=_exam_status_color.get(exam_st, "gray"),
                    pending_task=_exam_pending_task.get(exam_st, ("", "gray"))[0],
                    pending_task_color=_exam_pending_task.get(exam_st, ("", "gray"))[1],
                    scheduled_at=visit.scheduled_at.strftime("%d/%m/%Y") if visit.scheduled_at else "",
                    action_url=f"/consultation/{visit.id}/exam/{exam.id}",
                    can_act=is_doctor_active,
                ))

        # Lab rows — private consultation exams transmitted to lab (or beyond)
        if self.is_lab or is_admin:
            try:
                from gws_care.exam.exam_audit_entry import ExamAuditAction, ExamAuditEntry

                # Only exams that were actually sent to the lab (have a TRANSMIT_TO_LAB audit entry)
                lab_transmitted_ids = {
                    str(entry.exam_id)
                    for entry in ExamAuditEntry.select(ExamAuditEntry.exam).where(
                        ExamAuditEntry.action == ExamAuditAction.TRANSMIT_TO_LAB.value
                    )
                }
                lab_priv_exams = [
                    e for e in Exam.select(Exam, Visit)
                    .join(Visit, on=(Exam.visit == Visit.id))
                    .where(
                        (Visit.campaign.is_null(True))
                        & (Exam.status.in_([
                            ExamStatus.TRANSMITTED_TO_LAB,
                            ExamStatus.IN_PROGRESS_INTERPRETATION,
                            ExamStatus.DONE,
                        ]))
                    )
                    if str(e.id) in lab_transmitted_ids
                ]
                for exam in lab_priv_exams:
                    visit = exam.visit
                    try:
                        patient = visit.patient
                        if not patient:
                            continue
                    except Exception:
                        continue
                    exam_type_name = ""
                    try:
                        if exam.exam_type_ref_id:
                            ref = ExamTypeRef.get_or_none(ExamTypeRef.id == exam.exam_type_ref_id)
                            if ref:
                                exam_type_name = ref.name
                        if not exam_type_name:
                            exam_type_name = (
                                exam.exam_type.get_label()
                                if hasattr(exam.exam_type, "get_label")
                                else exam.exam_type.value
                            )
                    except Exception:
                        pass
                    exam_st = exam.status.value
                    is_lab_active = exam_st == ExamStatus.TRANSMITTED_TO_LAB.value
                    result.append(AssignedExamRowDTO(
                        row_type="lab",
                        source="private",
                        assigned_doctor_id="__lab__",
                        assigned_doctor_name=f"Laboratoire {org_acronym}",
                        campaign_id="",
                        campaign_name="Consultation privée",
                        campaign_number=visit.visit_number,
                        campaign_status="",
                        campaign_status_label="",
                        exam_type_id=str(exam.exam_type_ref_id) if exam.exam_type_ref_id else "",
                        exam_type_name=exam_type_name,
                        exam_category="",
                        patient_id=str(patient.id),
                        patient_name=patient.get_full_name(),
                        patient_number=patient.patient_number,
                        medical_status=exam_st,
                        medical_status_label=_exam_status_label.get(exam_st, exam_st),
                        medical_status_color=_exam_status_color.get(exam_st, "gray"),
                        pending_task=_exam_pending_task.get(exam_st, ("", "gray"))[0],
                        pending_task_color=_exam_pending_task.get(exam_st, ("", "gray"))[1],
                        scheduled_at=visit.scheduled_at.strftime("%d/%m/%Y") if visit.scheduled_at else "",
                        action_url=f"/consultation/{visit.id}/exam/{exam.id}",
                        can_act=is_lab_active,
                    ))
            except Exception:
                pass

        # ── Build assignee dropdown ───────────────────────────────────────────
        assignee_list: list[AssignedDoctorOption] = []
        if self.is_lab or is_admin:
            assignee_list.append(AssignedDoctorOption(id="__lab__", name="Labo"))
        if self.is_psc:
            assignee_list.append(AssignedDoctorOption(id="__psc__", name=f"Médecin {org_acronym}"))
        for did, dname in sorted(doctor_map.items(), key=lambda x: x[1]):
            assignee_list.append(AssignedDoctorOption(id=did, name=dname))
        self.available_assignees = assignee_list

        # Sort: actionable first, then lab/psc (most urgent), then name
        result.sort(key=lambda r: (
            0 if r.can_act else 1,
            0 if r.row_type in ("lab", "psc") else 1,
            r.assigned_doctor_name,
            r.campaign_name,
            r.patient_name,
        ))
        self.rows = result
