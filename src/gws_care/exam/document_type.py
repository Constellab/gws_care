"""Document type enum for exam file attachments."""

from enum import Enum


class DocumentType(Enum):
    """Types of medical documents that can be attached to an exam."""

    MEDICAL_CERTIFICATE = "medical_certificate"
    MEDICAL_REPORT = "medical_report"
    LETTER = "letter"
    MEDICAL_ANALYSIS = "medical_analysis"
    PRESCRIPTION = "prescription"
    MRI = "mri"
    CT_SCAN = "ct_scan"
    XRAY = "xray"
    ULTRASOUND = "ultrasound"
    OTHER = "other"

    def get_label(self) -> str:
        labels = {
            DocumentType.MEDICAL_CERTIFICATE: "Medical Certificate",
            DocumentType.MEDICAL_REPORT: "Medical Report",
            DocumentType.LETTER: "Letter",
            DocumentType.MEDICAL_ANALYSIS: "Medical Analysis",
            DocumentType.PRESCRIPTION: "Prescription",
            DocumentType.MRI: "MRI",
            DocumentType.CT_SCAN: "CT Scan",
            DocumentType.XRAY: "X-Ray",
            DocumentType.ULTRASOUND: "Ultrasound",
            DocumentType.OTHER: "Other",
        }
        return labels[self]
