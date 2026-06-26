-- Script de suppression des données de test saisies manuellement
-- ATTENTION : action irréversible — faire une sauvegarde avant exécution
--
-- Ordre d'exécution : supprimer d'abord les tables dépendantes (FK),
-- puis les tables principales.

-- Visites et données médicales liées
DELETE FROM gws_care_exam_result;
DELETE FROM gws_care_prescription_item;
DELETE FROM gws_care_prescription;
DELETE FROM gws_care_medical_certificate;
DELETE FROM gws_care_visit;

-- Notifications, documents, consentements
DELETE FROM gws_care_notification;
DELETE FROM gws_care_patient_document;
DELETE FROM gws_care_patient_consent;
DELETE FROM gws_care_patient_note;

-- Rendez-vous (table Appointment séparée)
DELETE FROM gws_care_appointment;

-- Liens patient ↔ compte et patient ↔ médecin
DELETE FROM gws_care_patient_account;
DELETE FROM gws_care_patient_doctor;

-- Patients
DELETE FROM gws_care_patient;
