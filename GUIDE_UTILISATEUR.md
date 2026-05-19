# Guide Utilisateur — Constellab Care

> **Version** : 0.10.0  
> **URL app (dev)** : `http://localhost:3000`

---

## Sommaire

1. [Connexion & rôles](#1-connexion--rôles)
2. [SUPER_ADMIN_PSC — Administration totale](#2-super_admin_psc)
3. [DIRECTEUR_PSC — Pilotage opérationnel](#3-directeur_psc)
4. [ADMIN_PSC — Gestion quotidienne](#4-admin_psc)
5. [OPERATEUR_TERRAIN — Saisie terrain](#5-operateur_terrain)
6. [OPERATEUR_LABO — Validation labo](#6-operateur_labo)
7. [MEDECIN_PSC — Validation médicale PSC](#7-medecin_psc)
8. [MEDECIN_ENTREPRISE — Consultation côté entreprise](#8-medecin_entreprise)
9. [RH_ENTREPRISE — Gestion des salariés](#9-rh_entreprise)
10. [PATIENT — Espace personnel](#10-patient)
11. [Parcours type pas-à-pas](#11-parcours-type-pas-à-pas)
12. [Suppression & désactivation — toutes les actions disponibles](#12-suppression--désactivation)

---

## 1. Connexion & rôles

1. Accédez à l'URL de l'application.
2. Connectez-vous avec vos identifiants Constellab (email + mot de passe).
3. La sidebar (barre latérale gauche) s'adapte automatiquement à votre rôle.

### Tableau des menus visibles par rôle

| Menu              | SUPER | DIRECTEUR | ADMIN | OP. TERRAIN | OP. LABO | MÉDECIN PSC | MÉD. ENTREP. | RH | PATIENT |
|-------------------|:-----:|:---------:|:-----:|:-----------:|:--------:|:-----------:|:------------:|:--:|:-------:|
| Tableau de bord   | ✅    | ✅        | ✅    | ✅          | ✅       | ✅          | ✅           | ✅ | ✅      |
| Campagnes         | ✅    | ✅        | ✅    | ✅          | ✅       | ✅          | ❌           | ❌ | ❌      |
| Comptes           | ✅    | ✅        | ✅    | ❌          | ❌       | ❌          | ❌           | ❌ | ❌      |
| Patients          | ✅    | ❌        | ✅    | ✅          | ✅       | ✅          | ❌           | ❌ | ❌      |
| Rendez-vous       | ✅    | ✅        | ✅    | ✅          | ✅       | ✅          | ✅           | ✅ | ✅      |
| Espace RH         | ❌    | ❌        | ❌    | ❌          | ❌       | ❌          | ❌           | ✅ | ❌      |
| Médecin PSC       | ✅    | ❌        | ✅    | ❌          | ❌       | ✅          | ❌           | ❌ | ❌      |
| Médecin Entreprise| ❌    | ❌        | ❌    | ❌          | ❌       | ❌          | ✅           | ❌ | ❌      |
| Notifications     | ✅    | ✅        | ✅    | ✅          | ✅       | ✅          | ✅           | ✅ | ❌      |
| Préfacturation    | ✅    | ✅        | ✅    | ❌          | ❌       | ❌          | ❌           | ❌ | ❌      |
| Référentiel exams | ✅    | ✅        | ✅    | ✅          | ✅       | ✅          | ❌           | ❌ | ❌      |
| Utilisateurs      | ✅    | ❌        | ✅    | ❌          | ❌       | ❌          | ❌           | ❌ | ❌      |
| Journal d'audit   | ✅    | ✅        | ✅    | ❌          | ❌       | ❌          | ❌           | ❌ | ❌      |
| Paramètres        | ✅    | ✅        | ✅    | ❌          | ❌       | ❌          | ❌           | ❌ | ❌      |

---

## 2. SUPER_ADMIN_PSC

**Profil** : Administrateur technique, accès total.  
**Exemple de compte** : `admin@psc.fr`

### 2.1 Configurer le référentiel d'examens (première fois)

> **Navigation** : Sidebar → **Référentiel examens**

1. Cliquer **"+ Nouveau type d'examen"**.
2. Remplir le formulaire :
   - **Nom** : `NFS` (Numération Formule Sanguine)
   - **Catégorie** : `Biologie` *(saisie libre — cliquer sur une suggestion si déjà existante)*
   - **Description** : `Bilan hématologique complet`
   - **Pièce jointe autorisée** : activer si les résultats sont envoyés en PDF
3. Cliquer **"Créer"** → le type apparaît dans la liste.
4. Cliquer sur la ligne `NFS` pour ouvrir la vue détail.
5. Cliquer **"+ Ajouter un paramètre"** :
   - **Nom** : `Globules blancs`
   - **Type de valeur** : `Numérique`
   - **Unité** : `G/L`
   - **Ref. basse** : `4.0` | **Ref. haute** : `10.0`
   - **Seuil critique bas** : `2.0` | **Seuil critique haut** : `15.0`
   - **Paramètre obligatoire** : ✅
6. Cliquer **"Ajouter le paramètre"**.
7. Répéter pour chaque paramètre (ex. `Hémoglobine`, `Plaquettes`…).
8. Cliquer **"← Retour au référentiel"** pour revenir à la liste.

**Autres types à créer** :
| Nom    | Catégorie    | Paramètre exemple         |
|--------|-------------|--------------------------|
| ECG    | Cardiologie  | Fréquence cardiaque (bpm)|
| Glycémie | Biologie  | Glucose (mmol/L)         |
| Audiométrie | ORL   | Seuil 1000 Hz (dB)       |

---

### 2.2 Créer des comptes de facturation

> **Navigation** : Sidebar → **Comptes**

1. Cliquer **"Nouveau compte"**.
2. Remplir :
   - **Nom** : `Renault Groupe`
   - **Type** : `Entreprise`
   - **Ville** : `Boulogne-Billancourt`
   - **Contact** : `Marie Dupont`
   - **Email** : `marie.dupont@renault.fr`
   - **Téléphone** : `+33 1 76 84 00 00`
3. Cliquer **"Créer"**.

---

### 2.3 Créer et assigner des utilisateurs

> **Navigation** : Sidebar → **Utilisateurs**

1. Cliquer **"Ajouter"**.
2. Remplir :
   - **Email** : `jean.martin@psc.fr` *(doit déjà exister dans Constellab)*
   - **Prénom / Nom** : Jean / Martin
   - **Rôle** : `ADMIN_PSC`
3. Cliquer **"Enregistrer"**.

> ⚠️ L'utilisateur doit être créé dans Constellab AVANT d'être ajouté ici.

---

### 2.4 Créer une campagne

> **Navigation** : Sidebar → **Campagnes** → **"+ Nouvelle campagne"**

1. **Nom** : `Bilan annuel 2026 — Renault`
2. **Types d'examens** : sélectionner `NFS`, `Glycémie` dans le menu déroulant (ils apparaissent en chips bleus)
3. **Compte de facturation** : `Renault Groupe`
4. **Date début** : `2026-06-01` | **Date fin** : `2026-06-30`
5. **Lieu** : `Siège Boulogne-Billancourt`
6. Cliquer **"Créer la campagne"** → redirige vers la page détail de la campagne.

---

## 3. DIRECTEUR_PSC

**Profil** : Direction opérationnelle, pas de gestion des utilisateurs.

### 3.1 Tableau de bord

> **Navigation** : Sidebar → **Tableau de bord**

- Vue d'ensemble : nombre de campagnes actives, patients, examens en attente.
- Cliquer sur une ligne de campagne pour accéder au détail.
- Bouton **"Actualiser"** (icône ↺) pour rafraîchir les données.

### 3.2 Suivre l'avancement d'une campagne

> **Navigation** : Sidebar → **Campagnes** → cliquer sur une ligne

La page détail affiche :
- **Statut actuel** (badge coloré)
- **Boutons d'action** selon le statut (voir tableau §11)
- **Patients inscrits** + bouton **"+ Ajouter un patient"**
- **Types d'examens** de la campagne

### 3.3 Consulter le référentiel

> **Navigation** : Sidebar → **Référentiel examens**

- Peut consulter et créer des types d'examens et paramètres.
- Peut désactiver un type d'examen (bouton 🚫 sur une ligne).

---

## 4. ADMIN_PSC

**Profil** : Gestion quotidienne — campagnes, patients, comptes, utilisateurs.

### 4.1 Créer un patient

> **Navigation** : Sidebar → **Patients** → **"+ Nouveau patient"**

1. **Numéro patient** : automatique (ex. `PAT-00042`)
2. **Nom** : `Lefebvre` | **Prénom** : `Sophie`
3. **Date de naissance** : `1985-03-14`
4. **Genre** : `F`
5. **Ville** : `Lyon`
6. **Téléphone** : `+33 6 12 34 56 78`
7. **Email** : `sophie.lefebvre@email.fr`
8. **Compte de facturation** : `Renault Groupe`
9. Cliquer **"Créer"**.

### 4.2 Ajouter un patient à une campagne

> **Navigation** : **Campagnes** → ouvrir la campagne → section **"Patients"** → **"+ Ajouter un patient"**

1. La liste des patients du compte de facturation apparaît.
2. Sélectionner `Lefebvre Sophie` dans le menu déroulant.
3. Cliquer **"Ajouter"**.

### 4.3 Faire avancer le workflow d'une campagne

> **Navigation** : page détail campagne

Chaque bouton correspond à une transition de statut :

| Bouton                        | Statut → Nouveau statut                          |
|-------------------------------|--------------------------------------------------|
| Valider opérationnellement    | BROUILLON → EN ATTENTE VALIDATION OP             |
| Valider (op.)                 | EN ATTENTE VALIDATION OP → VALIDÉE OPÉ           |
| Demander validation médicale  | VALIDÉE OPÉ → EN ATTENTE VALIDATION MÉDICALE      |
| Prêt pour convocations        | MÉDIC. VALIDÉE → PRÊTE CONVOCATIONS              |
| Envoyer convocations          | PRÊTE CONVOC. → CONVOCATIONS ENVOYÉES            |
| Démarrer terrain              | CONVOC. ENVOYÉES → TERRAIN EN COURS              |
| Clôturer terrain              | TERRAIN EN COURS → TERRAIN CLÔTURÉ               |
| Démarrer labo                 | TERRAIN CLÔTURÉ → LABO EN COURS                  |
| Valider labo                  | LABO EN COURS → LABO VALIDÉ                      |
| Valider (médecin PSC)         | LABO VALIDÉ → VALIDÉ MÉDECIN PSC                 |
| Publier médecin entreprise    | VALIDÉ PSC → PUBLIÉ MÉDECIN ENTREPRISE           |
| Publier patient               | PUBLIÉ MÉD. ENTREP. → PUBLIÉ PATIENT             |

---

## 5. OPERATEUR_TERRAIN

**Profil** : Collecte des données sur le terrain.

### 5.1 Saisir les résultats d'un examen

> **Navigation** : **Campagnes** → ouvrir la campagne → section **"Patients"** → cliquer sur le patient → onglet **"Examens"**

1. Cliquer sur l'examen (ex. `NFS`).
2. Saisir les valeurs de chaque paramètre :
   - `Globules blancs` : `7.2`
   - `Hémoglobine` : `13.5`
3. **Joindre un fichier** si nécessaire (bouton trombone).
4. Cliquer **"Enregistrer"**.

### 5.2 Consulter le référentiel

> **Navigation** : Sidebar → **Référentiel examens**

- Consulter les paramètres d'un examen : cliquer sur une ligne de la liste.
- Les opérateurs terrain **ne peuvent pas** créer ou désactiver des types (permission réservée aux ADMIN/MÉDECIN).

> *(Note : à ajuster selon politique interne)*

---

## 6. OPERATEUR_LABO

**Profil** : Validation des résultats labo.

### 6.1 Valider les résultats

> **Navigation** : **Campagnes** → ouvrir la campagne en statut *LABO EN COURS* → parcourir les patients

1. Ouvrir le dossier d'un patient → onglet **"Examens"**.
2. Vérifier les valeurs saisies par le terrain.
3. Corriger si nécessaire → cliquer **"Enregistrer"**.
4. Une fois tous les examens validés : bouton **"Valider labo"** sur la campagne.

---

## 7. MEDECIN_PSC

**Profil** : Validation médicale finale côté PSC.

### 7.1 Valider médicalement une campagne

> **Navigation** : Sidebar → **Médecin PSC**

1. Liste des campagnes en attente de validation médicale.
2. Cliquer sur une campagne.
3. Examiner les résultats patient par patient.
4. Cliquer **"Valider médicalement"** → statut passe à *VALIDÉ MÉDECIN PSC*.

### 7.2 Refuser une campagne (anomalie)

Sur la page détail campagne, bouton **"Refuser validation médicale"** :
1. Saisir le motif de refus dans la fenêtre de confirmation.
2. Cliquer **"Confirmer le refus"**.
3. La campagne est renvoyée en amont pour correction.

---

## 8. MEDECIN_ENTREPRISE

**Profil** : Médecin côté entreprise — consultation des résultats publiés.

### 8.1 Consulter les résultats publiés

> **Navigation** : Sidebar → **Médecin Entreprise**

1. Liste des campagnes publiées pour son compte entreprise.
2. Cliquer sur une campagne → liste des patients.
3. Cliquer sur un patient → onglet **"Examens"** → voir les résultats.
4. Télécharger les résultats (bouton **"Télécharger"**) si disponible.

---

## 9. RH_ENTREPRISE

**Profil** : Gestion administrative des salariés.

### 9.1 Gérer les salariés

> **Navigation** : Sidebar → **Espace RH**

1. Ajouter un salarié : cliquer **"+"** → remplir nom, prénom, email.
2. Suivre les convocations envoyées.
3. Marquer un salarié comme "convoqué" ou "présent" selon le flux.

---

## 10. PATIENT

**Profil** : Accès limité à son propre dossier.

### 10.1 Consulter son dossier

> **Navigation** : Sidebar → **Tableau de bord**

- Voir ses rendez-vous à venir.
- Consulter ses résultats d'examens publiés.
- Télécharger son certificat médical si disponible.

---

## 11. Parcours type pas-à-pas

### Cycle complet d'une campagne (résumé)

```
[SUPER_ADMIN / ADMIN_PSC]
  ↓ 1. Configurer le référentiel (types d'examens + paramètres)
  ↓ 2. Créer le compte de facturation (ex: "Renault")
  ↓ 3. Créer les patients (ou import)
  ↓ 4. Créer la campagne + sélectionner les types d'examens

[ADMIN_PSC]
  ↓ 5. Ajouter les patients à la campagne
  ↓ 6. Assigner le médecin PSC et médecin entreprise
  ↓ 7. Valider opérationnellement → "Valider opérationnellement"

[MEDECIN_PSC / ADMIN_PSC]
  ↓ 8. Valider médicalement → "Valider médicalement"

[ADMIN_PSC]
  ↓ 9. Marquer "Prêt pour convocations"
  ↓ 10. Envoyer convocations → notification auto aux patients

[OPERATEUR_TERRAIN]
  ↓ 11. Démarrer terrain sur site
  ↓ 12. Saisir résultats examens par patient
  ↓ 13. Clôturer terrain

[OPERATEUR_LABO]
  ↓ 14. Démarrer labo
  ↓ 15. Valider résultats labo

[MEDECIN_PSC]
  ↓ 16. Valider (médecin PSC)

[ADMIN_PSC]
  ↓ 17. Publier → médecin entreprise
  ↓ 18. Publier → patient
```

---

## 12. Suppression & désactivation

Toutes les suppressions/désactivations sont **soumises à confirmation** (fenêtre de dialogue). Voici le récapitulatif complet :

### Référentiel examens (`/exam-types`)

| Action                        | Bouton                 | Effet                                                         | Réversible |
|-------------------------------|------------------------|---------------------------------------------------------------|-----------|
| Désactiver un type d'examen   | 🚫 (orange) sur la ligne | Le type n'apparaît plus dans les nouvelles campagnes          | Oui (DB) |
| Supprimer un paramètre        | 🗑️ (rouge) sur la ligne param | Le paramètre est supprimé définitivement                  | **Non**   |

**Comment désactiver un type d'examen :**
1. `Référentiel examens` → trouver la ligne du type.
2. Cliquer l'icône 🚫 (orange).
3. Fenêtre : *"Désactiver ce type d'examen ?"* → cliquer **"Désactiver"**.

**Comment supprimer un paramètre :**
1. `Référentiel examens` → cliquer sur un type → vue détail.
2. Dans la table des paramètres, cliquer 🗑️ (rouge) sur la ligne.
3. Fenêtre : *"Supprimer ce paramètre ?"* → cliquer **"Supprimer"**.
   > ⚠️ Action irréversible.

---

### Campagnes (`/campaigns`)

| Action              | Bouton          | Effet                                                  | Réversible |
|---------------------|-----------------|--------------------------------------------------------|-----------|
| Archiver            | 📦 (orange) sur la ligne | Statut → ARCHIVÉE, données conservées        | Non (statut final) |

**Comment archiver une campagne :**
1. `Campagnes` → trouver la ligne.
2. Cliquer l'icône 📦 (archive, orange).
3. Fenêtre : *"Archiver cette campagne ?"* → cliquer **"Archiver"**.

---

### Comptes de facturation (`/accounts`)

| Action       | Bouton        | Effet                                        | Réversible |
|--------------|---------------|----------------------------------------------|-----------|
| Désactiver   | 🚫 (rouge) sur la ligne | Compte marqué inactif, données conservées | Oui (DB) |

**Comment désactiver un compte :**
1. `Comptes` → trouver la ligne.
2. Cliquer l'icône 🚫 (rouge).
3. Fenêtre : *"Désactiver ce compte ?"* → cliquer **"Désactiver"**.

---

### Entreprises (`/companies`)

| Action       | Bouton        | Effet                                             | Réversible |
|--------------|---------------|---------------------------------------------------|-----------|
| Désactiver   | 🚫 (rouge) sur la ligne | Entreprise marquée inactive, données conservées | Oui (DB) |

---

### Utilisateurs (`/users`)

| Action                | Bouton              | Effet                                                  | Réversible |
|-----------------------|---------------------|--------------------------------------------------------|-----------|
| Suspendre / Réactiver | ⏻ (rouge/vert)     | Bloque/débloque la connexion sans toucher aux rôles   | Oui       |
| Révoquer les rôles    | 🗑️ (rouge)         | Supprime tous les rôles Care de l'utilisateur          | Oui (ré-assigner) |

**Comment révoquer un utilisateur :**
1. `Utilisateurs` → trouver la ligne.
2. Cliquer 🗑️ (rouge).
3. Fenêtre : *"Révoquer les accès ?"* → cliquer **"Révoquer"**.
   > L'utilisateur ne pourra plus se connecter à Care jusqu'à ré-assignation d'un rôle.

---

### Patients (`/patients`)

> Les dossiers patients ne sont **pas supprimables** (données médicales — obligation légale de conservation).  
> Pour "archiver" un patient, dissocier son compte de facturation via la page détail compte.

---

*Dernière mise à jour : mai 2026 — gws_care v0.10.0*
