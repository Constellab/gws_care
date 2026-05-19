"""Campaign status enum — 15 lifecycle states."""

from enum import Enum


class CampaignStatus(str, Enum):
    """Full lifecycle of a medical campaign at PSC."""

    DRAFT = "DRAFT"
    AWAITING_OP_VALIDATION = "AWAITING_OP_VALIDATION"
    OPERATIONALLY_VALIDATED = "OPERATIONALLY_VALIDATED"
    AWAITING_MEDICAL_VALIDATION = "AWAITING_MEDICAL_VALIDATION"
    MEDICALLY_VALIDATED = "MEDICALLY_VALIDATED"
    READY_FOR_CONVOCATION = "READY_FOR_CONVOCATION"
    CONVOCATIONS_SENT = "CONVOCATIONS_SENT"
    TERRAIN_EN_COURS = "TERRAIN_EN_COURS"
    TERRAIN_CLOTURE = "TERRAIN_CLOTURE"
    LABO_EN_COURS = "LABO_EN_COURS"
    LABO_VALIDE = "LABO_VALIDE"
    VALIDE_MEDECIN_PSC = "VALIDE_MEDECIN_PSC"
    PUBLIE_MEDECIN_ENTREPRISE = "PUBLIE_MEDECIN_ENTREPRISE"
    PUBLIE_PATIENT = "PUBLIE_PATIENT"
    ARCHIVED = "ARCHIVED"

    def get_label(self) -> str:
        labels = {
            CampaignStatus.DRAFT: "Brouillon",
            CampaignStatus.AWAITING_OP_VALIDATION: "En attente validation opérationnelle",
            CampaignStatus.OPERATIONALLY_VALIDATED: "Validée opérationnellement",
            CampaignStatus.AWAITING_MEDICAL_VALIDATION: "En attente validation médicale",
            CampaignStatus.MEDICALLY_VALIDATED: "Validée médicalement",
            CampaignStatus.READY_FOR_CONVOCATION: "Prête pour convocation",
            CampaignStatus.CONVOCATIONS_SENT: "Convocations envoyées",
            CampaignStatus.TERRAIN_EN_COURS: "Terrain en cours",
            CampaignStatus.TERRAIN_CLOTURE: "Terrain clôturé",
            CampaignStatus.LABO_EN_COURS: "Labo en cours",
            CampaignStatus.LABO_VALIDE: "Labo validé",
            CampaignStatus.VALIDE_MEDECIN_PSC: "Validée médecin PSC",
            CampaignStatus.PUBLIE_MEDECIN_ENTREPRISE: "Publiée médecin entreprise",
            CampaignStatus.PUBLIE_PATIENT: "Publiée patient",
            CampaignStatus.ARCHIVED: "Archivée",
        }
        return labels[self]

    def get_color(self) -> str:
        """Return a Radix color scheme name for this status."""
        colors = {
            CampaignStatus.DRAFT: "gray",
            CampaignStatus.AWAITING_OP_VALIDATION: "blue",
            CampaignStatus.OPERATIONALLY_VALIDATED: "cyan",
            CampaignStatus.AWAITING_MEDICAL_VALIDATION: "violet",
            CampaignStatus.MEDICALLY_VALIDATED: "purple",
            CampaignStatus.READY_FOR_CONVOCATION: "indigo",
            CampaignStatus.CONVOCATIONS_SENT: "sky",
            CampaignStatus.TERRAIN_EN_COURS: "orange",
            CampaignStatus.TERRAIN_CLOTURE: "amber",
            CampaignStatus.LABO_EN_COURS: "yellow",
            CampaignStatus.LABO_VALIDE: "lime",
            CampaignStatus.VALIDE_MEDECIN_PSC: "teal",
            CampaignStatus.PUBLIE_MEDECIN_ENTREPRISE: "mint",
            CampaignStatus.PUBLIE_PATIENT: "green",
            CampaignStatus.ARCHIVED: "gray",
        }
        return colors[self]
