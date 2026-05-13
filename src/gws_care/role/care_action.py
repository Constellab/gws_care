"""CareAction — enumeration of all service-layer actions that require permission checks."""

from enum import Enum


class CareAction(str, Enum):
    """Actions a user might attempt in the system.

    Naming convention: <DOMAIN>_<VERB>
    """

    # ── MedicalProgram management ───────────────────────────────────────────────────
    CAMPAIGN_CREATE = "program:create"
    CAMPAIGN_UPDATE = "program:update"
    CAMPAIGN_VALIDATE_INITIAL = "program:validate_initial"   # DRAFT → VALIDATED (Clinic Doctor / Admin)
    CAMPAIGN_START = "program:start"                         # VALIDATED → IN_PROGRESS (Operator)
    CAMPAIGN_VALIDATE_LAB = "program:validate_lab"           # IN_PROGRESS → LAB_DONE (Operator)
    CAMPAIGN_VALIDATE_CLINIC = "program:validate_clinic"     # LAB_DONE → DOCTOR_CLINIC_VALIDATED (Doctor)
    CAMPAIGN_ARCHIVE = "program:archive"

    # ── Visit management ─────────────────────────────────────────────────────
    VISIT_READ = "visit:read"
    VISIT_MARK_TERRAIN_DONE = "visit:mark_on-site_done"       # Operator
    VISIT_MARK_RESULTS_ENTERED = "visit:mark_results_entered" # Operator
    VISIT_VALIDATE_LAB = "visit:validate_lab"                 # Operator
    VISIT_VALIDATE_CLINIC = "visit:validate_clinic"           # Doctor (Clinic)
    VISIT_VALIDATE_COMPANY = "visit:validate_company"         # Account Admin (Company Doctor)

    # ── Exam results ─────────────────────────────────────────────────────────
    EXAM_RESULT_WRITE = "exam_result:write"                   # Operator (before lab validation)
    EXAM_APPRECIATION_OVERRIDE = "exam_appreciation:override" # Doctor (Clinic)
    EXAM_INTERPRET = "exam:interpret"                         # Doctor

    # ── Patient data ─────────────────────────────────────────────────────────
    PATIENT_READ = "patient:read"
    PATIENT_READ_OWN = "patient:read_own"
    PATIENT_WRITE = "patient:write"

    # ── Account data ─────────────────────────────────────────────────────────
    ACCOUNT_READ = "account:read"
    ACCOUNT_WRITE = "account:write"

    # ── Certificate ──────────────────────────────────────────────────────────
    CERTIFICATE_GENERATE = "certificate:generate"             # Account Admin (Company Doctor)

    # ── Notifications ─────────────────────────────────────────────────────────
    NOTIFICATION_SEND = "notification:send"

    # ── Administration ────────────────────────────────────────────────────────
    USER_MANAGE = "user:manage"
    EXAM_TYPE_MANAGE = "exam_type:manage"
