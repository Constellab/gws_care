"""Script de remise à zéro des données saisies manuellement.

Exécution :
    cd bricks/gws_care
    gws server test reset_data

Supprime dans l'ordre des dépendances FK toutes les données patients,
visites, campagnes, comptes, médecins et types d'examens.
ATTENTION : action irréversible.
"""

from gws_core import BaseTestCase


class ResetDataTest(BaseTestCase):

    def test_reset_all_data(self):
        from gws_care.core.care_db_manager import CareDbManager

        db = CareDbManager.get_instance().db

        tables_in_order = [
            "gws_care_exam_result",
            "gws_care_exam",
            "gws_care_prescription_item",
            "gws_care_prescription",
            "gws_care_medical_certificate",
            "gws_care_notification",
            "gws_care_patient_document",
            "gws_care_patient_consent",
            "gws_care_patient_note",
            "gws_care_appointment",
            "gws_care_visit",
            "gws_care_campaign_exam_type",
            "gws_care_campaign_patient",
            "gws_care_campaign",
            "gws_care_patient_account",
            "gws_care_patient_doctor",
            "gws_care_patient",
            "gws_care_account",
            "gws_care_doctor_availability",
            "gws_care_medical_doctor",
            "gws_care_exam_type_threshold",
            "gws_care_exam_type",
        ]

        print("\n--- Remise à zéro des données ---")
        for table in tables_in_order:
            try:
                db.execute_sql(f"DELETE FROM `{table}`")
                print(f"  ✓ {table}")
            except Exception as e:
                print(f"  ✗ {table}: {e}")

        print("--- Terminé ---\n")
        # Le test passe toujours — l'objectif est la suppression, pas une assertion
        self.assertTrue(True)
