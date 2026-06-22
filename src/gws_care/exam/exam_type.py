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
        return self in {
            ExamType.RADIOLOGY,
            ExamType.OPHTHALMOLOGY,
            ExamType.ORL,
            ExamType.ECG,
            ExamType.SPIROMETRY,
        }


class ExamStatus(Enum):
    """Workflow status of an exam."""

    TODO = "todo"
    IN_PROGRESS_RESULTS = "in_progress_results"
    IN_PROGRESS_INTERPRETATION = "in_progress_interpretation"
    DONE = "done"
    CANCELLED = "cancelled"

    def get_label(self) -> str:
        labels = {
            ExamStatus.TODO: "À faire",
            ExamStatus.IN_PROGRESS_RESULTS: "En cours — Résultats",
            ExamStatus.IN_PROGRESS_INTERPRETATION: "En cours — Interprétation",
            ExamStatus.DONE: "Terminé",
            ExamStatus.CANCELLED: "Annulé",
        }
        return labels.get(self, self.value)
