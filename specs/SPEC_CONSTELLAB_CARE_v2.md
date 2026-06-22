# Constellab Care — Spécification Produit

> **Source** : Document "Constellab Care - Flux" (mai 2026)  
> **Client** : PS Consulting (PSC) — médecine du travail  
> **Rédacteur** : Analyse automatisée (GitHub Copilot)  
> **Date** : 11 mai 2026  
> **Version** : v2 — Médecin PSC → Médecin Clinic · Labo/labo → Lab/lab

---

## TABLE DES MATIÈRES

1. [Analyse des rôles clés](#1-analyse-des-rôles-clés)
2. [Modèle objet métier](#2-modèle-objet-métier)
3. [Interfaces et gestion des droits](#3-interfaces-et-gestion-des-droits)

---

## 1. ANALYSE DES RÔLES CLÉS

### 1.1 Super Administrateur PSC

| Attribut | Détail |
|---|---|
| **Organisation** | PSC (prestataire d'analyses médicales) |
| **Profil type** | Dirigeant ou responsable IT de PSC |

**Responsabilités principales**
1. Gérer l'ensemble des comptes entreprises et patients dans l'application
2. Configurer les droits d'accès de tous les utilisateurs (internes et externes)
3. Superviser les campagnes de toutes les entreprises clientes
4. Accéder aux statistiques globales multi-entreprises
5. Administrer les types d'examens disponibles dans le catalogue

**Accès autorisés**
- Tableau de bord global (toutes entreprises cumulées ou filtrées)
- Gestion des comptes de facturation (création, modification, désactivation)
- Gestion des utilisateurs et des rôles
- Accès en lecture/écriture sur toutes les données (y compris médicales)
- Configuration de l'application (catalogue d'examens, seuils de référence, modèles notification)

**Accès interdits**
- Aucune restriction technique (rôle maximal)

**Besoins prioritaires**
- Vision consolidée de l'activité (métriques clés par entreprise)
- Gestion fine des droits pour protéger les données médicales vis-à-vis des RH
- Traçabilité complète des actions utilisateurs

---

### 1.2 Opérateur Terrain PSC (OT)

| Attribut | Détail |
|---|---|
| **Organisation** | PSC |
| **Profil type** | Technicien de laboratoire mobile, se déplace sur site chez les entreprises |
| **Contexte d'usage** | Terrain, tablette ou mobile, conditions parfois difficiles (connexion limitée) |

**Responsabilités principales**
1. Identifier et accueillir les employés lors des campagnes sur site
2. Scanner les QR codes des employés pour valider leur identité
3. Imprimer et gérer les QR codes associés aux tubes d'analyse
4. Associer chaque tube à l'analyse correspondante (scan QR → liste d'examens)
5. Marquer les analyses comme terminées au fur et à mesure

**Accès autorisés**
- Consultation de la liste des employés d'une campagne
- Génération et impression de la grille QR codes (PDF A4)
- Scanner QR code → affichage de la liste des analyses à réaliser
- Marquage des examens comme réalisés ("coché terminé")
- Notifications aux employés après passage

**Accès interdits**
- Résultats d'analyses (données médicales chiffrées)
- Interprétations médicales
- Données de facturation
- Gestion des campagnes (création, validation)

**Besoins prioritaires**
- Interface rapide, usage tactile optimisé (tablette)
- Scan QR code natif ou via caméra
- Fonctionnement en mode dégradé (offline ou faible connectivité)
- Impression PDF directe depuis l'application

---

### 1.3 Opérateur Siège PSC (OS)

| Attribut | Détail |
|---|---|
| **Organisation** | PSC |
| **Profil type** | Technicien de laboratoire fixe, travaille au siège |
| **Contexte d'usage** | Bureau, desktop |

**Responsabilités principales**
1. Créer et configurer les campagnes (liste d'employés, types d'examens, dates)
2. Importer les listes d'employés fourmes par les entreprises
3. Saisir les résultats d'analyses dans les dossiers patients
4. Effectuer la "Validation Lab / Employé" (résultats saisis et vérifiés)
5. Effectuer la "Validation Lab / Campagne" une fois tous les résultats saisis (données verrouillées)

**Accès autorisés**
- Création et modification de campagnes (avant validation)
- Saisie des résultats d'examens (données brutes)
- Import CSV/Excel de listes d'employés
- Impression de la liste complète des patients avec QR codes (PDF)
- Validation lab (employé et campagne)

**Accès interdits**
- Validation médicale (réservée aux médecins)
- Modification des données après validation lab
- Données de facturation

**Besoins prioritaires**
- Saisie rapide des résultats avec les unités et valeurs de référence pré-remplies
- Affichage automatique des appréciations sur les seuils (Critique / Haut / Bas / Normal)
- Import en masse des patients depuis un fichier
- Historique de saisie et correction avant validation

---

### 1.4 Médecin Clinic

| Attribut | Détail |
|---|---|
| **Organisation** | PSC |
| **Profil type** | Médecin salarié ou contractant de PSC |
| **Contexte d'usage** | Bureau, desktop |

**Responsabilités principales**
1. Vérifier et valider les campagnes avant leur démarrage (optionnel selon flux)
2. Interpréter les résultats d'analyses après validation lab
3. Remplir la case "Interprétation du médecin Clinic"
4. Modifier si nécessaire les appréciations automatiques sur les seuils
5. Effectuer la "Validation Médecin / Employé" puis "Validation Médecin / Campagne"

**Accès autorisés**
- Accès complet aux dossiers médicaux des patients (toutes données médicales)
- Validation et modification des appréciations automatiques
- Saisie des interprétations médicales
- Validation médicale (employé et campagne)
- Vue en lecture sur les campagnes de toutes les entreprises clientes

**Accès interdits**
- Gestion des comptes /utilisateurs
- Données de facturation
- Modification des données après "Validation Médecin / Campagne"

**Besoins prioritaires**
- Affichage clair des seuils avec alertes visuelles (couleurs : Critique / Haut / Bas)
- Accès rapide à l'historique patient pour comparaison inter-campagnes
- Workflow de validation clair avec statut visuel par dossier
- Notification dès que la validation lab d'une campagne est complète

---

### 1.5 Médecin Référent Entreprise

| Attribut | Détail |
|---|---|
| **Organisation** | Entreprise cliente (externe à PSC) |
| **Profil type** | Médecin du travail interne à l'entreprise |
| **Contexte d'usage** | Bureau, desktop |

**Responsabilités principales**
1. Consulter les dossiers médicaux des employés de son entreprise après validation PSC
2. Ajouter ses propres remarques dans "Interprétation médecin entreprise"
3. Valider le dossier employé (côté entreprise)
4. Générer les certificats médicaux si nécessaire
5. Communiquer les résultats aux employés via l'application

**Accès autorisés**
- Dossiers médicaux complets des employés de **son entreprise uniquement**
- Saisie de l'interprétation médecin entreprise
- Génération de certificats médicaux
- Envoi de messages aux employés
- Statistiques agrégées de santé de son entreprise

**Accès interdits**
- Données des employés d'autres entreprises
- Création ou modification de campagnes
- Paramétrage de l'application

**Besoins prioritaires**
- Notification lors de la disponibilité des résultats d'une campagne
- Interface de validation et commentaire rapide dossier par dossier
- Génération de certificats en un clic (PDF)

---

### 1.6 Responsable RH Entreprise

| Attribut | Détail |
|---|---|
| **Organisation** | Entreprise cliente (externe à PSC) |
| **Profil type** | Responsable des ressources humaines |
| **Contexte d'usage** | Bureau, desktop |

**Responsabilités principales**
1. Suivre les statuts de participation des employés aux campagnes
2. Envoyer des messages aux employés via l'application
3. Consulter les statistiques de présence (absents / présents)
4. Gérer la liste des employés rattachés à l'entreprise

**Accès autorisés**
- Liste des employés et leurs statuts de rendez-vous (présent/absent)
- Statistiques agrégées de présence (🟠 données agrégées uniquement)
- Messagerie interne vers les employés
- Rapports de campagne (comptage, présence — sans données médicales)

**Accès interdits** ⛔ (réglementaire — RGPD / Secret médical)
- Aucun accès aux dossiers médicaux individuels
- Aucun accès aux résultats d'examens
- Aucun accès aux interprétations médicales
- Aucun accès aux certificats médicaux

**Besoins prioritaires**
- Tableau de bord simple de suivi de campagne (présence/absence)
- Messagerie employés intégrée
- Export de rapports logistiques (liste de présence, etc.)

---

### 1.7 Employé / Patient

| Attribut | Détail |
|---|---|
| **Organisation** | Entreprise cliente (externe à PSC) |
| **Profil type** | Employé convoqué à une visite médicale |
| **Contexte d'usage** | Mobile ou desktop, usage personnel |

**Responsabilités principales**
1. Consulter ses convocations et rendez-vous à venir
2. Accéder à ses résultats d'analyses médicales
3. Télécharger et imprimer ses résultats
4. Consulter les messages de son médecin du travail
5. Mettre à jour ses informations personnelles

**Accès autorisés**
- Ses propres données médicales uniquement
- Historique de ses analyses (10 ans)
- Téléchargement PDF de ses résultats
- Messagerie avec le médecin référent entreprise
- Notifications (email, SMS, WhatsApp)

**Accès interdits**
- Données d'autres patients
- Données d'autres entreprises
- Fonctions d'administration

**Besoins prioritaires**
- Interface simple, accessible sur mobile
- Notifications claires sur les convocations (J-15, J-3, J-1)
- Accès rapide aux résultats après traitement
- Confidentialité et sécurité perçue forte

---

## 2. MODÈLE OBJET MÉTIER

### 2.1 Objets métier

---

#### 2.1.1 Patient (Employé)

> Représente une personne physique dont les données médicales sont gérées dans l'application.

**Attributs**

| Champ | Type | Obligatoire | Notes |
|---|---|---|---|
| `patient_number` | String | ✅ | Identifiant unique auto-généré (ex: PAT-XXXXXXXX) |
| `last_name` | String | ✅ | |
| `first_name` | String | ✅ | |
| `birth_date` | Date | ✅ | |
| `phone` | String | ✅ | Téléphone principal |
| `email` | String | ✅ | Pour les notifications |
| `social_security_number` | String | ⬜ Optionnel | NNir — données sensibles |
| `weight` | Decimal | ⬜ Optionnel | kg |
| `height` | Decimal | ⬜ Optionnel | cm |
| `sex` | Enum (M/F/Autre) | ⬜ Optionnel | |
| `qr_code` | Binary/URL | ✅ | Généré automatiquement, lié au dossier patient |
| `notification_preferences` | JSON | ⬜ Optionnel | Email / SMS / WhatsApp |
| `created_at` | DateTime | ✅ | Auto |
| `is_active` | Boolean | ✅ | Permet la désactivation sans suppression |

**Relations**
- Un Patient appartient à **un ou plusieurs Comptes de facturation**
- Un Patient a **zéro ou plusieurs Rendez-vous**
- Un Patient a **zéro ou plusieurs Examens**
- Un Patient reçoit **zéro ou plusieurs Notifications**
- Un Patient peut avoir **zéro ou plusieurs Certificats**

**Cycle de vie**

```
Actif → Inactif (changement d'entreprise, départ)
```

**Règles métier**
- Le `patient_number` est unique et immuable
- Le QR code est généré à la création et ne change jamais
- Un patient peut être rattaché à plusieurs entreprises (cumul d'emploi)
- Si un patient change d'entreprise gérée par PSC, son historique doit être préservé
- Distinction entre entreprise **active** et **ancienne entreprise** dans le profil patient

**⚠️ Questions ouvertes**
- Comment gérer la fusion de doublons (même patient enregistré deux fois) ?
- Quel est le processus de suppression RGPD à la demande d'un patient ?
- L'adresse postale est-elle nécessaire ?

---

#### 2.1.2 Compte de Facturation (Entreprise)

> Représente une entité cliente de PSC — soit une entreprise (personne morale) soit un patient individuel (clinique).

**Attributs**

| Champ | Type | Obligatoire | Notes |
|---|---|---|---|
| `account_number` | String | ✅ | Identifiant unique auto-généré |
| `name` | String | ✅ | Raison sociale ou nom |
| `account_type` | Enum (Entreprise / Clinique / Individuel) | ✅ | |
| `siret` | String | ⬜ Optionnel | Pour les personnes morales |
| `address` | String | ✅ | |
| `billing_contact_name` | String | ✅ | |
| `billing_contact_email` | String | ✅ | |
| `billing_contact_phone` | String | ✅ | |
| `payment_data` | JSON | ⬜ Optionnel | IBAN, conditions de paiement |
| `is_active` | Boolean | ✅ | |
| `created_at` | DateTime | ✅ | Auto |

**Relations**
- Un Compte de facturation a **zéro ou plusieurs Patients**
- Un Compte de facturation a **zéro ou plusieurs Campagnes**
- Un Compte de facturation a **zéro ou plusieurs Utilisateurs** (RH, médecin référent)
- Un Compte de facturation a **zéro ou plusieurs Factures** (gérées par une autre application)

**Règles métier**
- Un Patient peut être associé à plusieurs Comptes (cumul d'emploi)
- Les factures sont gérées par une application externe (`gws_care_billing`)
- Un compte de type "Individuel" permet l'usage clinique (pas de campagnes groupées)

**⚠️ Questions ouvertes**
- Comment PSC onboarde-t-il un nouveau client ? Formulaire en ligne ou import ?
- Y a-t-il un contrat ou des conditions tarifaires à associer au compte ?
- La gestion multi-établissements (une entreprise avec plusieurs sites) est-elle prévue ?

---

#### 2.1.3 Campagne

> Représente un ensemble organisé de visites médicales planifié par PSC pour les employés d'un compte de facturation.

**Attributs**

| Champ | Type | Obligatoire | Notes |
|---|---|---|---|
| `campaign_number` | String | ✅ | Auto-généré |
| `name` | String | ✅ | Nom de la campagne (ex: "Bilan annuel 2026 - Acme") |
| `account_id` | FK → Compte | ✅ | |
| `start_date` | Date | ✅ | |
| `end_date` | Date | ✅ | |
| `exam_types` | List<FK → TypeExamen> | ✅ | Types d'examens à réaliser |
| `patients` | List<FK → Patient> | ✅ | Tous doivent appartenir au compte |
| `status` | Enum | ✅ | Voir cycle de vie |
| `created_by` | FK → User (PSC) | ✅ | Opérateur créateur |
| `validated_by` | FK → User (Médecin/Admin) | ⬜ Optionnel | |
| `validated_at` | DateTime | ⬜ Optionnel | |
| `notes` | Text | ⬜ Optionnel | |

**Cycle de vie**

```
Brouillon → Validée → En cours → Lab terminé → Médecin Clinic validé → Médecin Entreprise validé → Archivée
```

| Statut | Déclencheur | Acteur |
|---|---|---|
| Brouillon | Création | Opérateur Siège |
| Validée | Validation de la campagne | Médecin Clinic ou Admin |
| En cours | Date de début atteinte / début terrain | Opérateur Terrain |
| Lab terminé | Validation Lab / Campagne | Opérateur Siège |
| Médecin Clinic validé | Validation Médecin / Campagne | Médecin Clinic |
| Médecin Entreprise validé | Validation par médecin référent | Médecin Entreprise |
| Archivée | Action manuelle ou délai | Admin |

**Relations**
- Une Campagne appartient à **un seul Compte de facturation**
- Une Campagne contient **une ou plusieurs Visites médicales**
- Une Campagne est associée à **un ou plusieurs Types d'examen**
- Une Campagne génère **un ou plusieurs Rendez-vous**

**Règles métier**
- Tous les patients d'une campagne doivent appartenir au compte de facturation lié
- Si la date de début de campagne change, vérifier la cohérence de tous les RDV
- Si des RDV sont incohérents après changement de date, afficher une erreur et demander confirmation pour écraser les dates

**⚠️ Questions ouvertes**
- Peut-on ajouter des patients à une campagne déjà validée ?
- Quelle est la durée d'archivage réglementaire pour les données de campagne ?
- Peut-on cloner une campagne d'une année sur l'autre ?

---

#### 2.1.4 Visite Médicale

> Représente l'ensemble des examens réalisés pour **un patient** dans le cadre d'**une campagne**.

**Attributs**

| Champ | Type | Obligatoire | Notes |
|---|---|---|---|
| `visit_number` | String | ✅ | Auto-généré |
| `campaign_id` | FK → Campagne | ✅ | |
| `patient_id` | FK → Patient | ✅ | |
| `status` | Enum | ✅ | Voir cycle de vie |
| `lab_validated_by` | FK → User | ⬜ Optionnel | |
| `lab_validated_at` | DateTime | ⬜ Optionnel | |
| `doctor_clinic_validated_by` | FK → User | ⬜ Optionnel | |
| `doctor_clinic_validated_at` | DateTime | ⬜ Optionnel | |
| `doctor_company_validated_by` | FK → User | ⬜ Optionnel | |
| `doctor_company_validated_at` | DateTime | ⬜ Optionnel | |
| `doctor_clinic_interpretation` | Text | ⬜ Optionnel | |
| `doctor_company_interpretation` | Text | ⬜ Optionnel | |
| `doctor_company_message` | Text | ⬜ Optionnel | Message transmis à l'employé |

**Cycle de vie**

```
En attente → Terrain terminé → Résultats saisis → Lab validé → Médecin Clinic validé → Médecin Entreprise validé
```

**Relations**
- Une Visite médicale appartient à **une seule Campagne**
- Une Visite médicale appartient à **un seul Patient**
- Une Visite médicale contient **un ou plusieurs Examens**
- Une Visite médicale est associée à **un Rendez-vous**
- Une Visite médicale peut générer **zéro ou un Certificat**

**Règles métier**
- Après "Validation Lab/Employé", les données sont verrouillées pour modification
- Après "Validation Médecin Clinic/Employé", le dossier ne peut plus être modifié
- Le médecin Clinic peut modifier les appréciations automatiques (seuils) avant validation

**⚠️ Questions ouvertes**
- Que se passe-t-il si un patient est absent le jour J — la visite reste-t-elle dans la campagne avec un statut "absent" ?
- Peut-on rouvrir une visite après validation (en cas d'erreur) ? Si oui, qui a ce droit ?

---

#### 2.1.5 Examen

> Représente une analyse médicale unitaire réalisée pour un patient dans une visite.

**Attributs**

| Champ | Type | Obligatoire | Notes |
|---|---|---|---|
| `exam_number` | String | ✅ | Auto-généré |
| `visit_id` | FK → Visite médicale | ✅ | |
| `exam_type_id` | FK → TypeExamen | ✅ | |
| `tube_qr_code` | String | ⬜ Optionnel | QR code collé sur le tube |
| `status` | Enum | ✅ | |
| `is_done_terrain` | Boolean | ✅ | Coché par l'OT lors de la campagne terrain |
| `result_value` | JSON/Text | ⬜ Optionnel | Valeur saisie par OS |
| `result_unit` | String | ⬜ Optionnel | |
| `appreciation` | Enum (Normal/Bas/Haut/Critique) | ⬜ Optionnel | Auto-calculé ou saisi |
| `appreciation_override` | Boolean | ✅ | Indique si l'appréciation a été modifiée manuellement |
| `image_url` | String | ⬜ Optionnel | Pour examens imagerie |
| `notes` | Text | ⬜ Optionnel | |

**Sous-types d'examens**
- **Biologie** : saisie de valeurs chiffrées (glycémie, NFS, etc.)
- **Imagerie** : radiographie, ophtalmologie, ORL, ECG, spirométrie → association image/tracé
- **Clinique** : examen physique, constantes vitales
- **Autre** : hormonologie, bactériologie, tests de drogues, etc.

**Relations**
- Un Examen appartient à **une seule Visite médicale**
- Un Examen est d'**un seul Type d'examen**
- Un Examen peut avoir **une image rattachée** (examens imagerie)

**Règles métier**
- L'appréciation automatique est calculée selon les seuils définis dans le Type d'examen
- Si le médecin modifie l'appréciation, `appreciation_override = true` et la version originale est conservée
- Le QR code du tube est attribué lors de la phase terrain et tracé dans le système

**⚠️ Questions ouvertes**
- Comment gérer les examens avec plusieurs valeurs (ex: NFS avec plusieurs sous-résultats) ?
- Les seuils de référence varient-ils selon l'âge/sexe du patient ?
- Comment stocker les images d'examens (taille, format, durée de rétention) ?

---

#### 2.1.6 Type d'Examen

> Représente un modèle d'examen pré-configuré, utilisé pour définir les campagnes et normaliser la saisie.

**Attributs**

| Champ | Type | Obligatoire | Notes |
|---|---|---|---|
| `code` | String | ✅ | Code unique |
| `name` | String | ✅ | |
| `category` | Enum (Biologie/Imagerie/Clinique/Autre) | ✅ | |
| `description` | Text | ⬜ Optionnel | |
| `unit` | String | ⬜ Optionnel | Unité de mesure (ex: mmol/L) |
| `threshold_low` | Decimal | ⬜ Optionnel | Seuil bas |
| `threshold_high` | Decimal | ⬜ Optionnel | Seuil haut |
| `threshold_critical_low` | Decimal | ⬜ Optionnel | Seuil critique bas |
| `threshold_critical_high` | Decimal | ⬜ Optionnel | Seuil critique haut |
| `is_active` | Boolean | ✅ | |

**Relations**
- Un Type d'examen est utilisé dans **zéro ou plusieurs Campagnes**
- Un Type d'examen génère **zéro ou plusieurs Examens**

**Règles métier**
- Les seuils peuvent varier par sexe ou tranche d'âge (à confirmer)
- Un type d'examen désactivé ne peut plus être ajouté à une nouvelle campagne mais reste visible dans les historiques

---

#### 2.1.7 Rendez-vous

> Représente la convocation d'un patient à une campagne à une date et heure précises.

**Attributs**

| Champ | Type | Obligatoire | Notes |
|---|---|---|---|
| `rdv_number` | String | ✅ | Auto-généré |
| `campaign_id` | FK → Campagne | ✅ | |
| `patient_id` | FK → Patient | ✅ | |
| `visit_id` | FK → Visite médicale | ✅ | |
| `scheduled_date` | Date | ✅ | Doit être dans la plage dates campagne |
| `scheduled_time` | Time | ⬜ Optionnel | |
| `status` | Enum (Planifié/Présent/Absent/Reporté) | ✅ | |
| `notes` | Text | ⬜ Optionnel | |

**Relations**
- Un Rendez-vous appartient à **une seule Campagne**
- Un Rendez-vous appartient à **un seul Patient**
- Un Rendez-vous est lié à **une seule Visite médicale**

**Règles métier**
- Un RDV est créé automatiquement pour chaque patient ajouté à une campagne
- La date du RDV est alignée par défaut sur la date de début de la campagne
- Si la date de la campagne change : vérifier la cohérence des RDV et alerter si incompatibles
- Des notifications automatiques sont envoyées à J-15, J-3, J-1

**⚠️ Questions ouvertes**
- Peut-on planifier plusieurs créneaux horaires par journée de campagne ?
- Comment gérer les absents : RDV reporté ou statut définitif "absent" après la campagne ?

---

#### 2.1.8 Certificat Médical

> Document officiel généré par le médecin référent entreprise attestant de l'aptitude (ou inaptitude) d'un employé.

**Attributs**

| Champ | Type | Obligatoire | Notes |
|---|---|---|---|
| `certificate_number` | String | ✅ | Auto-généré |
| `visit_id` | FK → Visite médicale | ✅ | |
| `patient_id` | FK → Patient | ✅ | |
| `generated_by` | FK → User (Médecin Entreprise) | ✅ | |
| `generated_at` | DateTime | ✅ | |
| `certificate_type` | Enum | ✅ | Ex: Aptitude / Inaptitude / Aptitude avec réserve |
| `content` | Text | ⬜ Optionnel | Contenu textuel |
| `pdf_url` | String | ✅ | URL du PDF généré |
| `is_sent_to_patient` | Boolean | ✅ | |
| `sent_at` | DateTime | ⬜ Optionnel | |

**Relations**
- Un Certificat est lié à **une Visite médicale**
- Un Certificat est généré par **un Médecin Entreprise**
- Un Certificat est associé à **un Patient**

**Règles métier**
- Seul le médecin référent entreprise peut générer un certificat
- La génération d'un certificat déclenche une notification à l'employé

---

#### 2.1.9 Notification

> Message automatique ou manuel envoyé à un acteur du système.

**Attributs**

| Champ | Type | Obligatoire | Notes |
|---|---|---|---|
| `notification_id` | UUID | ✅ | |
| `recipient_id` | FK → User/Patient | ✅ | |
| `recipient_type` | Enum (Patient/Médecin/RH/OS/OT) | ✅ | |
| `channel` | Enum (Email/SMS/WhatsApp/In-app) | ✅ | |
| `type` | Enum | ✅ | Voir liste ci-dessous |
| `content` | Text | ✅ | |
| `sent_at` | DateTime | ⬜ Optionnel | Null si non encore envoyée |
| `status` | Enum (En attente/Envoyée/Echec) | ✅ | |

**Types de notifications**
- Convocation J-15, J-3, J-1 (→ Patient)
- Remerciement après passage terrain (→ Patient)
- Résultats disponibles (→ Patient)
- Certificat disponible (→ Patient)
- Validation lab terminée (→ Médecin Clinic)
- Campagne interprétée par Clinic (→ Médecin Entreprise)
- Rapport de campagne (→ Médecin Entreprise)

---

### 2.2 Schéma des relations (Entity-Relationship simplifié)

```
Compte de Facturation ──< Campagne
Compte de Facturation ──< Patient
Patient ><──< Compte de Facturation  (many-to-many via PatientCompte)

Campagne ──< Visite Médicale
Campagne ──< Rendez-vous
Campagne ><──< Type d'Examen  (many-to-many via CampagneExamenType)

Patient ──< Visite Médicale
Patient ──< Rendez-vous

Visite Médicale ──< Examen
Visite Médicale ──1 Rendez-vous  (1-to-1)
Visite Médicale ──<(0,1) Certificat

Examen >──1 Type d'Examen

Patient ──< Notification
User ──< Notification
```

**Légende**
- `──<` : un-à-plusieurs
- `><──<` : plusieurs-à-plusieurs
- `──1` : un-à-un

---

## 3. INTERFACES ET GESTION DES DROITS

### 3.1 Interface Super Administrateur PSC

| Attribut | Détail |
|---|---|
| **Utilisateurs cibles** | Super Administrateur PSC |
| **Canal d'accès** | Web desktop |
| **Langue** | Français |
| **Contexte d'usage** | Bureau, ordinateur fixe ou portable |
| **Sensibilité des données** | 🔴 Données médicales individuelles + 🟠 Agrégées + 🟢 Administratives |

**Périmètre fonctionnel**

- Tableau de bord global (métriques toutes entreprises)
- Gestion des Comptes de facturation (CRUD)
- Gestion des utilisateurs et rôles (création, modification, désactivation)
- Gestion du catalogue de Types d'examens (CRUD + seuils)
- Vue de toutes les campagnes (toutes entreprises)
- Accès à tous les dossiers médicaux
- Configuration des notifications automatiques
- Rapports et exports globaux

**Ce qui est interdit / masqué**
- Rien (rôle maximal)

**Besoins UX**
- Tableaux de données denses avec filtres avancés
- Navigation rapide multi-entreprises
- Alertes d'intégrité (campagnes en anomalie, dossiers bloqués)

**User Stories**

| ID | En tant que | Je veux | Afin de |
|---|---|---|---|
| SA-01 | Super Admin | voir le tableau de bord global filtrable par entreprise | avoir une vision consolidée de l'activité |
| SA-02 | Super Admin | créer un nouveau Compte de facturation | onboarder un nouveau client |
| SA-03 | Super Admin | créer des utilisateurs et leur attribuer un rôle | gérer les accès à l'application |
| SA-04 | Super Admin | désactiver un utilisateur | gérer les départs |
| SA-05 | Super Admin | gérer le catalogue d'examens (créer, modifier, désactiver un type) | maintenir le référentiel médical |
| SA-06 | Super Admin | configurer les seuils de référence par type d'examen | permettre le calcul automatique des appréciations |
| SA-07 | Super Admin | voir toutes les campagnes de toutes les entreprises | superviser l'activité |
| SA-08 | Super Admin | accéder à n'importe quel dossier médical | auditer ou corriger en cas de problème |
| SA-09 | Super Admin | exporter les données en CSV/Excel | produire des rapports |
| SA-10 | Super Admin | configurer les templates de notification (email, SMS) | personnaliser la communication |

---

### 3.2 Interface Opérateur Siège PSC

| Attribut | Détail |
|---|---|
| **Utilisateurs cibles** | Opérateur Siège (OS) |
| **Canal d'accès** | Web desktop |
| **Langue** | Français |
| **Contexte d'usage** | Bureau, saisie intensive de données |
| **Sensibilité des données** | 🔴 Données médicales (résultats bruts) + 🟢 Administratives |

**Périmètre fonctionnel**

- Gestion des campagnes (création, modification avant validation)
- Import de liste d'employés (CSV/Excel) et rattachement à un compte
- Gestion des patients (CRUD)
- Saisie des résultats d'examens
- Impression PDF liste patients + QR codes
- Validation Lab / Employé et Lab / Campagne
- Suivi de l'état d'avancement des saisies

**Ce qui est interdit / masqué**
- Validation médicale (réservée aux médecins)
- Génération de certificats
- Gestion des rôles / comptes
- Données de facturation

**Besoins UX**
- Formulaire de saisie de résultats ergonomique (navigation au clavier, unités pré-remplies)
- Affichage automatique de l'appréciation colorée en temps réel lors de la saisie
- Raccourcis pour passer rapidement d'un patient au suivant
- Indicateur de progression de la saisie (X/N dossiers complets)

**User Stories**

| ID | En tant que | Je veux | Afin de |
|---|---|---|---|
| OS-01 | Opérateur Siège | créer une nouvelle campagne pour un compte | planifier une visite médicale d'entreprise |
| OS-02 | Opérateur Siège | importer une liste d'employés depuis un fichier CSV/Excel | éviter la saisie manuelle |
| OS-03 | Opérateur Siège | ajouter / retirer des patients d'une campagne | ajuster la liste des convoqués |
| OS-04 | Opérateur Siège | ajouter des types d'examens à une campagne | définir les analyses à réaliser |
| OS-05 | Opérateur Siège | imprimer la liste complète des patients avec QR codes (PDF A4) | préparer le terrain |
| OS-06 | Opérateur Siège | saisir les résultats d'un examen pour un patient | remplir les dossiers médicaux |
| OS-07 | Opérateur Siège | voir l'appréciation automatique (Normal/Haut/Bas/Critique) en temps réel | vérifier la cohérence des résultats |
| OS-08 | Opérateur Siège | valider un dossier patient (Validation Lab / Employé) | verrouiller les données saisies |
| OS-09 | Opérateur Siège | valider une campagne entière (Validation Lab / Campagne) | notifier le médecin Clinic |
| OS-10 | Opérateur Siège | voir le statut de chaque dossier dans la campagne | savoir quels dossiers restent à saisir |
| OS-11 | Opérateur Siège | créer ou modifier un patient | maintenir le référentiel patients |
| OS-12 | Opérateur Siège | scanner un QR code de tube pour retrouver la fiche patient | faciliter la saisie au laboratoire |
| OS-13 | Opérateur Siège | voir les résultats déjà saisis avant validation | relire et corriger si besoin |

---

### 3.3 Interface Opérateur Terrain PSC

| Attribut | Détail |
|---|---|
| **Utilisateurs cibles** | Opérateur Terrain (OT) |
| **Canal d'accès** | Web mobile (tablette ou smartphone) — potentiellement mode offline |
| **Langue** | Français |
| **Contexte d'usage** | Terrain, laboratoire mobile, conditions variables (bruit, luminosité, gants) |
| **Sensibilité des données** | 🟢 Données logistiques uniquement (identité + liste d'examens) |

**Périmètre fonctionnel**

- Consultation de la liste des patients d'une campagne
- Identification d'un patient (QR code ou recherche manuelle nom/prénom)
- Génération et impression de la grille QR codes (PDF A4) pour les tubes
- Scan QR code tube → affichage des analyses à effectuer
- Marquage des analyses comme réalisées
- Envoi d'une notification de remerciement à l'employé

**Ce qui est interdit / masqué**
- Résultats d'analyses chiffrés
- Interprétations médicales
- Données de facturation
- Gestion des campagnes

**Besoins UX**
- Interface ultra-simplifiée, gros boutons, adapté tactile
- Scan QR code via caméra intégrée
- Fonctionne en offline ou faible connectivité (synchronisation différée)
- Haute lisibilité (contraste élevé, texte large)
- Réduction des erreurs de manipulation (confirmation avant action irréversible)

**User Stories**

| ID | En tant que | Je veux | Afin de |
|---|---|---|---|
| OT-01 | Opérateur Terrain | voir la liste des patients de la campagne en cours | savoir qui est attendu aujourd'hui |
| OT-02 | Opérateur Terrain | rechercher un patient par nom/prénom | l'identifier rapidement |
| OT-03 | Opérateur Terrain | scanner le QR code d'un patient pour accéder à son dossier | valider son identité sans erreur |
| OT-04 | Opérateur Terrain | générer et imprimer la grille QR codes pour les tubes (PDF) | préparer les étiquettes |
| OT-05 | Opérateur Terrain | scanner un QR code de tube et voir la liste des analyses associées | savoir quels tubes prélever |
| OT-06 | Opérateur Terrain | cocher chaque analyse comme "terminée" | tracer les prélèvements réalisés |
| OT-07 | Opérateur Terrain | envoyer une notification de remerciement à l'employé | informer l'employé après son passage |
| OT-08 | Opérateur Terrain | voir le statut de présence des patients (présent/absent) | suivre l'avancement de la journée |
| OT-09 | Opérateur Terrain | utiliser l'application sans connexion internet stable | travailler dans des zones avec faible réseau |
| OT-10 | Opérateur Terrain | synchroniser les données quand la connexion est rétablie | ne perdre aucune donnée de terrain |

---

### 3.4 Interface Médecin Clinic

| Attribut | Détail |
|---|---|
| **Utilisateurs cibles** | Médecin Clinic |
| **Canal d'accès** | Web desktop |
| **Langue** | Français |
| **Contexte d'usage** | Bureau, interprétation médicale, travail de concentration |
| **Sensibilité des données** | 🔴 Données médicales individuelles complètes |

**Périmètre fonctionnel**

- Réception des notifications de campagnes prêtes à interpréter
- Vue de la liste des dossiers à interpréter (filtrée par campagne ou patient)
- Visualisation des résultats d'examens avec appréciations automatiques
- Modification des appréciations si nécessaire
- Saisie de l'interprétation médicale Clinic
- Validation Médecin / Employé (par dossier)
- Validation Médecin / Campagne (globale)
- Accès à l'historique médical du patient (inter-campagnes)
- Validation optionnelle des campagnes avant démarrage

**Ce qui est interdit / masqué**
- Gestion des comptes et utilisateurs
- Données de facturation
- Modification après validation complète

**Besoins UX**
- Affichage centré sur le dossier médical (résultats clairs, seuils colorés)
- Historique patient accessible en sidebar ou onglet
- Navigation fluide dossier par dossier dans une campagne
- Zone de saisie d'interprétation avec mise en forme basique (gras, listes)
- Confirmation explicite avant validation (irréversible)

**User Stories**

| ID | En tant que | Je veux | Afin de |
|---|---|---|---|
| MP-01 | Médecin Clinic | recevoir une notification quand une campagne est prête pour interprétation | savoir quand commencer |
| MP-02 | Médecin Clinic | voir la liste de tous les dossiers à interpréter | m'organiser dans mon travail |
| MP-03 | Médecin Clinic | accéder au dossier complet d'un patient (examens, résultats, appréciations) | analyser ses résultats |
| MP-04 | Médecin Clinic | voir l'historique médical du patient sur ses campagnes précédentes | détecter des évolutions |
| MP-05 | Médecin Clinic | voir les appréciations automatiques (Normal/Haut/Bas/Critique) avec codes couleur | repérer rapidement les anomalies |
| MP-06 | Médecin Clinic | modifier l'appréciation automatique d'un examen | corriger les calculs si besoin |
| MP-07 | Médecin Clinic | saisir mon interprétation médicale pour chaque dossier | documenter mon analyse |
| MP-08 | Médecin Clinic | valider un dossier patient (Validation Médecin / Employé) | verrouiller le dossier |
| MP-09 | Médecin Clinic | valider l'ensemble d'une campagne (Validation Médecin / Campagne) | notifier le médecin entreprise |
| MP-10 | Médecin Clinic | visualiser les images d'examens (radio, ECG, spiro) | interpréter les examens imagerie |
| MP-11 | Médecin Clinic | filtrer les dossiers par statut (à interpréter / validé) | me concentrer sur ce qui reste à faire |
| MP-12 | Médecin Clinic | valider (ou refuser) une campagne avant son démarrage | vérifier que les examens prévus sont corrects |

---

### 3.5 Interface Médecin Référent Entreprise

| Attribut | Détail |
|---|---|
| **Utilisateurs cibles** | Médecin Référent Entreprise |
| **Canal d'accès** | Web desktop |
| **Langue** | Français |
| **Contexte d'usage** | Bureau, accès externe sécurisé |
| **Sensibilité des données** | 🔴 Données médicales individuelles (employés de son entreprise uniquement) |

**Périmètre fonctionnel**

- Réception de notification : campagne Clinic interprétée et disponible
- Liste des dossiers à valider (filtré : son entreprise uniquement)
- Consultation des résultats + interprétation Clinic
- Saisie de l'interprétation médecin entreprise
- Validation du dossier employé
- Génération de certificats médicaux (PDF)
- Envoi de messages aux employés
- Statistiques agrégées de santé de son entreprise

**Ce qui est interdit / masqué**
- Dossiers des employés d'autres entreprises
- Accès aux campagnes d'autres entreprises
- Création ou modification de campagnes
- Paramétrage de l'application

**Besoins UX**
- Interface similaire au médecin Clinic mais scoped sur une entreprise
- Génération de certificat en un clic à partir du dossier
- Messagerie intégrée vers l'employé (depuis le dossier)

**User Stories**

| ID | En tant que | Je veux | Afin de |
|---|---|---|---|
| ME-01 | Médecin Entreprise | recevoir une notification quand les résultats de ma campagne sont prêts | savoir quand commencer l'analyse |
| ME-02 | Médecin Entreprise | voir la liste des dossiers de mes employés à valider | m'organiser |
| ME-03 | Médecin Entreprise | consulter les résultats et l'interprétation du médecin Clinic | prendre connaissance des analyses |
| ME-04 | Médecin Entreprise | saisir mon interprétation dans le dossier de l'employé | ajouter ma valeur médicale |
| ME-05 | Médecin Entreprise | valider le dossier de l'employé | déclencher la notification à l'employé |
| ME-06 | Médecin Entreprise | générer un certificat médical pour un employé | lui fournir un document officiel |
| ME-07 | Médecin Entreprise | envoyer un message à un employé depuis son dossier | lui communiquer des informations |
| ME-08 | Médecin Entreprise | voir les statistiques agrégées de santé de mon entreprise | identifier des tendances collectives |
| ME-09 | Médecin Entreprise | consulter l'historique médical d'un employé sur ses anciennes campagnes | avoir une vision longitudinale |
| ME-10 | Médecin Entreprise | recevoir une notification quand une campagne est terminée, avec un rapport | avoir le bilan de présence |
| ME-11 | Médecin Entreprise | filtrer les dossiers par statut (à valider / validé) | suivre ma progression |

---

### 3.6 Interface RH Entreprise

| Attribut | Détail |
|---|---|
| **Utilisateurs cibles** | Responsable RH Entreprise |
| **Canal d'accès** | Web desktop |
| **Langue** | Français |
| **Contexte d'usage** | Bureau, accès externe sécurisé, usage logistique |
| **Sensibilité des données** | 🟠 Données agrégées uniquement + 🟢 Logistiques et administratives |

**Périmètre fonctionnel**

- Vue de la liste des employés de l'entreprise
- Suivi du statut de participation aux campagnes (présent / absent / en attente)
- Rapport de campagne : nombre de présents / absents (sans données médicales)
- Messagerie vers les employés
- Export de la liste de présence (PDF / Excel)

**Ce qui est interdit / masqué** ⛔ (impératif réglementaire)
- Aucun accès aux dossiers médicaux
- Aucun résultat d'examen visible
- Aucun accès aux interprétations médicales
- Aucun certificat médical

**Besoins UX**
- Interface épurée, axée gestion logistique
- Distinction visuelle claire entre données accessibles et données médicales confidentielles
- Export simple en un clic

**User Stories**

| ID | En tant que | Je veux | Afin de |
|---|---|---|---|
| RH-01 | RH Entreprise | voir la liste complète de mes employés | gérer le suivi des convocations |
| RH-02 | RH Entreprise | voir le statut de participation de chaque employé à la campagne | savoir qui est présent / absent |
| RH-03 | RH Entreprise | envoyer un message à un ou plusieurs employés | les relancer ou leur communiquer des informations |
| RH-04 | RH Entreprise | voir un rapport de présence de la campagne (agrégé) | avoir un bilan logistique |
| RH-05 | RH Entreprise | exporter la liste de présence en PDF ou Excel | archiver ou partager le bilan |
| RH-06 | RH Entreprise | consulter le planning des campagnes à venir | anticiper l'organisation |

---

### 3.7 Interface Patient (Employé)

| Attribut | Détail |
|---|---|
| **Utilisateurs cibles** | Employé / Patient |
| **Canal d'accès** | Web mobile + Web desktop |
| **Langue** | Français |
| **Contexte d'usage** | Usage personnel, depuis domicile ou smartphone |
| **Sensibilité des données** | 🔴 Ses propres données médicales uniquement |

**Périmètre fonctionnel**

- Consultation de son profil personnel
- Consultation de ses rendez-vous à venir
- Historique de ses visites médicales (10 ans)
- Consultation de ses résultats d'examens
- Téléchargement / impression de ses résultats (PDF)
- Consultation des certificats médicaux générés en son nom
- Réception et lecture des messages de son médecin du travail
- Notification (email, SMS, WhatsApp) pour convocations et résultats

**Ce qui est interdit / masqué**
- Données d'autres patients
- Fonctions d'administration ou de gestion de campagne

**Besoins UX**
- Interface optimisée mobile first
- Langage accessible (pas de jargon médical non expliqué)
- Téléchargement PDF simple et rapide
- Sécurité perçue forte (connexion sécurisée, affichage explicite des données protégées)

**User Stories**

| ID | En tant que | Je veux | Afin de |
|---|---|---|---|
| PAT-01 | Patient | recevoir une notification de convocation à J-15, J-3 et J-1 | ne pas oublier mon rendez-vous |
| PAT-02 | Patient | consulter mes rendez-vous à venir | savoir quand et où me présenter |
| PAT-03 | Patient | recevoir une notification quand mes résultats sont disponibles | savoir quand les consulter |
| PAT-04 | Patient | consulter mes résultats d'analyses médicales | prendre connaissance de mon bilan de santé |
| PAT-05 | Patient | comprendre mes résultats (appréciations expliquées simplement) | ne pas m'inquiéter inutilement |
| PAT-06 | Patient | télécharger mes résultats en PDF | les conserver ou les partager avec mon médecin traitant |
| PAT-07 | Patient | consulter mes résultats historiques (jusqu'à 10 ans) | suivre l'évolution de ma santé |
| PAT-08 | Patient | lire les messages de mon médecin du travail | prendre connaissance de ses recommandations |
| PAT-09 | Patient | télécharger mon certificat médical | avoir un document officiel |
| PAT-10 | Patient | recevoir une notification quand un certificat est généré | savoir qu'il est disponible |
| PAT-11 | Patient | mettre à jour mes informations personnelles (téléphone, email) | rester joignable |
| PAT-12 | Patient | choisir mes préférences de notification (email / SMS / WhatsApp) | recevoir les alertes comme je le souhaite |
| PAT-13 | Patient | me connecter de façon sécurisée | protéger mes données médicales |

---

## 4. MATRICE DE DROITS D'ACCÈS (SYNTHÈSE)

| Fonctionnalité | Super Admin | OS | OT | Médecin Clinic | Médecin Entreprise | RH Entreprise | Patient |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Gestion utilisateurs / rôles | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Gestion comptes de facturation | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Catalogue types d'examens | ✅ | 👁️ | ❌ | 👁️ | ❌ | ❌ | ❌ |
| Création campagne | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Validation campagne (avant démarrage) | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Gestion patients (CRUD) | ✅ | ✅ | ❌ | 👁️ | 👁️ entreprise | ❌ | 👁️ soi-même |
| Terrain : scan QR + marquage examens | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Saisie résultats d'examens | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Validation Lab | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Interprétation médicale Clinic | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Validation Médecin Clinic | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Interprétation médicale Entreprise | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Validation Médecin Entreprise | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Génération de certificats | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Messagerie vers employés | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | 👁️ lecture |
| Tableau de bord global | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Statistiques entreprise (agrégées) | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Présence / absence campagne | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Consultation résultats médicaux | ✅ | ✅ (saisie) | ❌ | ✅ | ✅ (son entreprise) | ❌ | ✅ (soi-même) |
| Factures | Autre app | Autre app | ❌ | ❌ | ❌ | ❌ | ❌ |

**Légende** : ✅ Accès complet · 👁️ Lecture seule · ❌ Aucun accès

---

## 5. QUESTIONS OUVERTES CONSOLIDÉES ⚠️

| # | Thème | Question |
|---|---|---|
| Q-01 | Patient | Comment gérer les doublons de patients ? |
| Q-02 | Patient | Quel est le processus de suppression RGPD sur demande d'un patient ? |
| Q-03 | Patient | L'adresse postale est-elle un champ nécessaire ? |
| Q-04 | Compte | Comment se déroule l'onboarding d'un nouveau client (formulaire, import) ? |
| Q-05 | Compte | Y a-t-il des contrats ou conditions tarifaires à associer au compte ? |
| Q-06 | Compte | La gestion multi-établissements (une entreprise, plusieurs sites) est-elle prévue ? |
| Q-07 | Campagne | Peut-on ajouter des patients à une campagne déjà validée ? |
| Q-08 | Campagne | Durée d'archivage réglementaire pour les données de campagne médicale ? |
| Q-09 | Campagne | Peut-on cloner une campagne d'une année sur l'autre ? |
| Q-10 | Visite | Que se passe-t-il si un patient est absent le jour J ? Statut définitif ou RDV reporté ? |
| Q-11 | Visite | Peut-on rouvrir une visite après validation ? Si oui, par qui et avec quel audit trail ? |
| Q-12 | Examen | Comment gérer les examens multi-valeurs (ex: NFS, bilan lipidique complet) ? |
| Q-13 | Examen | Les seuils de référence varient-ils par âge/sexe ? |
| Q-14 | Examen | Comment stocker les images (format, taille max, durée de rétention) ? |
| Q-15 | RDV | Peut-on définir des créneaux horaires précis dans une journée de campagne ? |
| Q-16 | Offline | Quel est le niveau de fonctionnalité offline attendu pour les OT ? |
| Q-17 | Notification | Quels prestataires SMS/WhatsApp sont prévus ? |
| Q-18 | Clinique | À quel horizon la version "Clinique" (usage individuel sans campagne) doit-elle être développée ? |
| Q-19 | Facturation | Quelle est l'interface (API ?) entre `gws_care` et `gws_care_billing` ? |
| Q-20 | Sécurité | Quel niveau de traçabilité (audit log) est requis réglementairement ? |
