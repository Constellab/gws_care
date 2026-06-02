"""Exam type and status enumerations."""

from enum import Enum


class ExamType(Enum):
    """Type of medical exam."""

    BIOLOGY = "biology"
    RADIOLOGY = "radiology"
    OPHTHALMOLOGY = "ophthalmology"
    ORL = "orl"
    ECG = "ecg"
    SPIROMETRY = "spirometry"
    CLINICAL = "clinical"
    HORMONES = "hormones"
    HEMATOLOGY = "hematology"
    BACTERIOLOGY = "bacteriology"
    PARASITOLOGY = "parasitology"
    DRUG_TEST = "drug_test"
    IMMUNOLOGY = "immunology"
    HEPATIC_MARKERS = "hepatic_markers"
    OTHER = "other"

    def get_label(self) -> str:
        """Return a human-readable label for the exam type."""
        labels = {
            ExamType.BIOLOGY: "Biology",
            ExamType.RADIOLOGY: "Radiology",
            ExamType.OPHTHALMOLOGY: "Ophthalmology",
            ExamType.ORL: "ORL",
            ExamType.ECG: "ECG",
            ExamType.SPIROMETRY: "Spirometry",
            ExamType.CLINICAL: "Clinical Exam",
            ExamType.HORMONES: "Hormones",
            ExamType.HEMATOLOGY: "Hematology",
            ExamType.BACTERIOLOGY: "Bacteriology",
            ExamType.PARASITOLOGY: "Parasitology",
            ExamType.DRUG_TEST: "Drug Test",
            ExamType.IMMUNOLOGY: "Immunology",
            ExamType.HEPATIC_MARKERS: "Hepatic Markers",
            ExamType.OTHER: "Other",
        }
        return labels.get(self, self.value)

    def has_image_attachments(self) -> bool:
        """Return True if this exam type supports image/trace attachments."""
        return self in {
            ExamType.RADIOLOGY,
            ExamType.OPHTHALMOLOGY,
            ExamType.ORL,
            ExamType.ECG,
            ExamType.SPIROMETRY,
        }


class ExamStatus(Enum):
    """Interpretation status of an exam."""

    DRAFT = "draft"                # Exam session created, results not yet entered
    COLLECTED = "collected"        # Sample collected by terrain operator
    LAB_RECEIVED = "lab_received"  # Sample received by the lab
    LAB_VALIDATED = "lab_validated"  # Lab has validated the results — awaiting doctor
    PENDING = "pending"            # Results entered, awaiting doctor interpretation
    INTERPRETED = "interpreted"    # Doctor has written interpretation
    CANCELLED = "cancelled"        # Exam cancelled / voided
