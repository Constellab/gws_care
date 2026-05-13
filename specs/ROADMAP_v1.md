# Constellab Care — Roadmap d'implémentation

> **Version** : v1  
> **Date** : 11 mai 2026  
> **Basé sur** : SPEC_CONSTELLAB_CARE_v2.md

---

## État actuel (synthèse)

| Composant | Statut |
|---|---|
| Patient, Account, Appointment, Exam, Certificate, Role, Notification (models + services + UI) | ✅ Implémenté |
| Campaign, Visit (Visite médicale), ExamType (en tant que modèle DB) | ❌ Manquant |
| Contrôle d'accès basé sur les rôles (enforcement) | ⚠️ Partiel |
| Génération QR code | ❌ Manquant |
| Workflow de validation (Lab → Médecin Clinic → Médecin Entreprise) | ❌ Manquant |
| Scheduler de notifications (J-15, J-3, J-1) | ❌ Manquant |

---

## Phase 1 — Refactoring du modèle domaine (Fondations)

> **Objectif** : Aligner la couche données avec la spec avant d'ajouter toute nouvelle fonctionnalité. Tout dans les phases suivantes en dépend.

### Étape 1.1 — Créer `ExamType` comme modèle DB

**Pourquoi en premier** : Campagne et Visite référencent tous deux `ExamType`. Aujourd'hui c'est uniquement un enum Python — il doit devenir une vraie table DB avec des seuils.

- Nouveau modèle `ExamType` avec champs : `code`, `name`, `category` (Biologie/Imagerie/Clinique/Autre), `unit`, `threshold_low`, `threshold_high`, `threshold_critical_low`, `threshold_critical_high`, `is_active`
- Migration : peupler à partir des valeurs de l'enum `ExamType` existant
- Mise à jour du modèle `Exam` pour FK → `ExamType` (remplace la colonne enum actuelle)
- Mise à jour de `ExamService` en conséquence
- Écrire les tests pour `ExamTypeService` (CRUD, logique de seuils)

---

### Étape 1.2 — Créer le modèle `Campaign`

**Pourquoi en second** : L'objet domaine central. Toutes les fonctionnalités suivantes s'organisent autour.

- Nouveau modèle `Campaign` avec champs : `campaign_number` (auto), `name`, `account` (FK), `start_date`, `end_date`, `status` (enum : DRAFT/VALIDATED/IN_PROGRESS/LAB_DONE/DOCTOR_CLINIC_VALIDATED/DOCTOR_COMPANY_VALIDATED/ARCHIVED), `created_by`, `validated_by`, `notes`
- Many-to-many : `Campaign ↔ Patient` (seulement les patients appartenant au compte lié)
- Many-to-many : `Campaign ↔ ExamType`
- Écrire `CampaignService` avec : `create`, `update`, `list`, `get`, `validate`, `archive`, `add_patient`, `remove_patient`, `add_exam_type`
- Écrire les tests couvrant le cycle de vie complet

---

### Étape 1.3 — Créer le modèle `Visit` (Visite Médicale)

**Pourquoi en troisième** : Une fois la Campagne créée, chaque paire (Campagne, Patient) a besoin d'un conteneur Visit.

- Nouveau modèle `Visit` avec champs : `visit_number` (auto), `campaign` (FK), `patient` (FK), `status` (enum : PENDING/TERRAIN_DONE/RESULTS_ENTERED/LAB_VALIDATED/DOCTOR_CLINIC_VALIDATED/DOCTOR_COMPANY_VALIDATED), timestamps et FKs de validation pour chaque étape, `doctor_clinic_interpretation`, `doctor_company_interpretation`, `doctor_company_message`
- Auto-créer une Visit par patient quand il est ajouté à une Campaign
- Refactoriser `Exam` pour appartenir à une `Visit` (ajouter FK `visit`, conserver `patient` et `account` pour compatibilité rétrograde pendant la transition)
- Écrire `VisitService` avec : `get`, `list_for_campaign`, `list_for_patient`, `validate_lab`, `validate_doctor_clinic`, `validate_doctor_company`
- Écrire les tests couvrant chaque transition de validation et les règles de verrouillage

---

### Étape 1.4 — Aligner `Appointment` → `Visit`

**Pourquoi** : Le modèle `Appointment` existant est autonome ; il doit être lié 1-à-1 à une `Visit`.

- Ajouter `visit` (FK nullable) à `Appointment`
- Auto-créer un `Appointment` par `Visit` (date par défaut = `campaign.start_date`)
- Ajouter la règle métier : la date du RDV doit être dans `[campaign.start_date, campaign.end_date]`
- Ajouter la validation : si les dates de campagne changent, détecter les RDV incompatibles et remonter des erreurs

---

## Phase 2 — Workflow de Validation

> **Objectif** : Implémenter le workflow de verrouillage progressif décrit dans la spec. C'est le flux métier central.

### Étape 2.1 — Validation Lab (Opérateur Siège)

- `VisitService.validate_lab_visit(visit_id, user)` — verrouille les résultats d'examens, passe le statut à `LAB_VALIDATED`
- `CampaignService.validate_lab_campaign(campaign_id, user)` — vérifie que toutes les visites sont lab-validées, passe la campagne à `LAB_DONE`
- Déclencheur : notification au Médecin Clinic quand la campagne atteint `LAB_DONE`
- Règle : une fois lab-validés, les champs de résultats d'examen deviennent en lecture seule

### Étape 2.2 — Validation Médecin Clinic

- `VisitService.validate_doctor_clinic(visit_id, user, interpretation)` — enregistre l'interprétation, verrouille le dossier
- `CampaignService.validate_doctor_clinic_campaign(campaign_id, user)` — vérifie que toutes les visites sont validées Clinic
- Déclencheur : notification au Médecin Entreprise quand la campagne atteint `DOCTOR_CLINIC_VALIDATED`

### Étape 2.3 — Validation Médecin Entreprise

- `VisitService.validate_doctor_company(visit_id, user, interpretation, message)` — enregistre l'interprétation entreprise et le message patient
- Déclencheur : notification au Patient (email/SMS/WhatsApp) quand la visite est `DOCTOR_COMPANY_VALIDATED`

---

## Phase 3 — Seuils automatiques & Appréciations

> **Objectif** : Calculer automatiquement l'appréciation (Normal/Haut/Bas/Critique) depuis les seuils de `ExamType`.

### Étape 3.1 — Moteur de seuils

- Ajouter les champs `appreciation` et `appreciation_override` à `Exam` (ou `ExamResult`)
- Écrire `ThresholdService.calculate_appreciation(exam_type, value, patient)` → retourne `Enum(CRITICAL_LOW/LOW/NORMAL/HIGH/CRITICAL_HIGH)`
- Appliquer automatiquement lors de la sauvegarde des résultats

### Étape 3.2 — Override par le Médecin Clinic

- Permettre au Médecin Clinic de modifier manuellement une appréciation avant validation
- Stocker `appreciation_override = True` et conserver la valeur calculée originale

---

## Phase 4 — Génération de QR Codes

> **Objectif** : Activer le workflow terrain (OT) avec des QR codes scannables.

### Étape 4.1 — QR code patient

- Générer un QR code à la création du `Patient` (encode `patient_number`)
- Stocker en base64 ou chemin de fichier dans `Patient.qr_code`
- Exposer via `PatientService.get_qr_code(patient_id)`

### Étape 4.2 — PDF grille de QR codes tubes

- `QrCodeService.generate_tube_qr_grid(campaign_id)` → produit un PDF imprimable (A4) en grille
- Chaque ligne : nom patient, date de naissance, un QR code par type d'examen à effectuer
- PDF téléchargeable depuis l'interface Opérateur Terrain

### Étape 4.3 — Scan tube → lookup examen

- `ExamService.find_by_tube_qr(qr_code)` → retourne (Patient, Visit, liste d'Examens à effectuer)
- Utilisé dans l'interface Opérateur Terrain pour la recherche en temps réel

---

## Phase 5 — Scheduler de Notifications

> **Objectif** : Automatiser les rappels J-15, J-3, J-1 et toutes les notifications déclenchées par le workflow.

### Étape 5.1 — Inventaire des types de notifications

Compléter l'enum `NotificationType` pour couvrir les 9 événements de notification de la spec :
- `APPOINTMENT_REMINDER_15D`, `APPOINTMENT_REMINDER_3D`, `APPOINTMENT_REMINDER_1D`
- `TERRAIN_THANK_YOU`
- `RESULTS_AVAILABLE`
- `CERTIFICATE_AVAILABLE`
- `LAB_DONE` (→ Médecin Clinic)
- `CAMPAIGN_CLINIC_VALIDATED` (→ Médecin Entreprise)
- `CAMPAIGN_REPORT` (→ Médecin Entreprise)

### Étape 5.2 — Scheduler (Constellab Task)

- Créer une tâche périodique Constellab (`NotificationSchedulerTask`) qui s'exécute quotidiennement
- Pour chaque `Appointment` à venir, vérifier J-15/J-3/J-1 et envoyer si pas déjà envoyé (vérifier `NotificationLog`)
- Idempotent : ne jamais envoyer un doublon pour le même (appointment, type, channel)

### Étape 5.3 — Notifications déclenchées par le workflow

- Connecter les transitions de `CampaignService` et `VisitService` à `NotificationService`
- Chaque étape de validation déclenche la notification correspondante (voir Phase 2)

---

## Phase 6 — Contrôle d'accès basé sur les rôles (Enforcement)

> **Objectif** : Passer du stockage des rôles à leur enforcement dans les couches service et UI.

### Étape 6.1 — Matrice de permissions dans la couche service

- Créer `PermissionService.check(user, action, resource)` basé sur la matrice d'accès de la spec
- Intégrer des guards dans `VisitService`, `CampaignService`, `ExamService` :
  - Seul `OPERATOR` peut faire la validation lab
  - Seul `DOCTOR` (Clinic) peut écrire l'interprétation Clinic
  - `ACCOUNT_ADMIN` peut uniquement accéder aux données de son propre compte
  - `PATIENT` peut uniquement lire ses propres données

### Étape 6.2 — UI Reflex basée sur les rôles

- Mettre à jour `RoleState` pour exposer des flags booléens : `is_admin`, `is_doctor_clinic`, `is_operator`, `is_account_admin`, `is_rh`
- Sidebar : masquer/afficher les éléments de menu selon les flags de rôle
- Guards de page : rediriger les utilisateurs non autorisés
- Masquage des données : les pages RH n'affichent jamais les colonnes de résultats médicaux

---

## Phase 7 — Nouvelles pages UI Reflex

> **Objectif** : Construire les pages manquantes pour le workflow Campagne et les opérations terrain.

### Étape 7.1 — Page liste des campagnes (`/campaigns`)

- Tableau : nom campagne, compte, dates, badge statut, # patients, # examens
- Filtres : compte, statut, plage de dates
- Actions : créer, voir, archiver

### Étape 7.2 — Page détail campagne (`/campaign/[id]`)

- En-tête : infos campagne, statut, boutons de validation (gated par rôle)
- Section liste patients : ajouter/retirer patients, statut présence/absence
- Section types d'examens : sélectionner les types d'examens pour la campagne
- Barre de progression : X/N visites validées à chaque étape
- Bouton impression grille QR

### Étape 7.3 — Page détail visite/dossier (`/visit/[id]`)

- Section résultats médicaux (lecture seule après validation lab)
- Colonne appréciation avec code couleur (Critique 🔴 / Haut 🟠 / Normal 🟢 / Bas 🔵)
- Sections d'interprétation (Clinic, Entreprise) — modifiables par les médecins respectifs
- Boutons d'action de validation (gated par rôle, séquentiels)
- Bouton génération certificat (Médecin Entreprise uniquement)

### Étape 7.4 — Page terrain (`/terrain/[campaign_id]`)

- Layout optimisé mobile
- Composant scanner QR (caméra)
- Confirmation d'identification patient
- Checklist d'examens (cocher chaque examen terminé)
- Bouton impression grille QR

### Étape 7.5 — Pages portail patient

- Mes résultats (`/my-results`) — vue patient, résultats + historique
- Mes rendez-vous (`/my-appointments`)
- Mes messages (`/my-messages`)
- Mes documents/certificats (`/my-documents`)

---

## Phase 8 — Génération PDF

> **Objectif** : Générer des PDFs officiels pour les certificats et rapports.

### Étape 8.1 — PDF certificat médical

- `CertificateService.generate_pdf(certificate_id)` → produit un PDF signé
- Contenu : identité patient, date examen, conclusion, bloc signature médecin, logo PSC

### Étape 8.2 — PDF rapport de campagne

- `CampaignService.generate_report(campaign_id)` → PDF agrégé
- Contenu : résumé campagne, liste de présence (sans données médicales individuelles), taux de présence

### Étape 8.3 — PDF résultats patient

- `VisitService.generate_results_pdf(visit_id)` → PDF lisible par le patient de ses propres résultats

---

## Phase 9 — Tests & Qualité

> **Objectif** : S'assurer que chaque nouveau morceau est couvert avant de passer à la phase suivante.

- **Tests Phase 1** : `ExamTypeService`, `CampaignService`, `VisitService`, alignement appointment-visit
- **Tests Phase 2** : chaque transition de validation, règles de verrouillage, rejet des accès non autorisés
- **Tests Phase 3** : calculs de seuils sur les cas limites (valeurs aux frontières, valeurs manquantes)
- **Tests Phase 5** : idempotence du scheduler, calcul correct des J-15/J-3/J-1
- **Tests Phase 6** : guards de permission pour chaque combinaison rôle/action

---

## Séquencement recommandé

```
Phase 1 (Étapes 1.1 → 1.4)   ← Commencer ici, tout en dépend
    ↓
Phase 2 (Étapes 2.1 → 2.3)   ← Workflow métier central
    ↓
Phase 3                        ← Moteur de seuils (court, haute valeur)
    ↓
Phase 6 (Étape 6.1 d'abord)   ← Guards de permission avant de construire l'UI
    ↓
Phase 7 (Étapes 7.1 → 7.3)   ← UI interne PSC/Clinic
    ↓
Phase 4                        ← QR codes (active le workflow terrain)
    ↓
Phase 7.4                      ← UI Terrain
    ↓
Phase 5                        ← Notifications (nécessite le workflow en place)
    ↓
Phase 8                        ← PDFs
    ↓
Phase 7.5                      ← Portail patient (en dernier, priorité plus faible)
    ↓
Phase 9                        ← Continue, idéalement par phase
```

---

## Principes clés à respecter tout au long

1. **Ne jamais casser l'application existante** — chaque étape doit être additive ou rétrocompatible ; conserver les anciennes colonnes `Exam` pendant la transition
2. **Tester avant de passer à l'étape suivante** — lancer `gws server test` après chaque étape
3. **Migrer les données, pas seulement le schéma** — chaque migration doit préserver les enregistrements existants
4. **Guard au niveau service d'abord, UI ensuite** — ne jamais compter uniquement sur le masquage UI pour la sécurité
