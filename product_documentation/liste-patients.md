# Liste des patients

## Rôles autorisés
- Opérateur
- Médecin
- Admin

## À quoi ça sert
La liste des patients est l'écran principal de la plateforme. Elle affiche tous les patients enregistrés avec leur numéro de dossier (format `PAT-XXXXXXXX`), leur date de naissance et le compte associé.

## Comment l'utiliser

### Rechercher un patient
1. Ouvrez la page d'accueil (icône **Patients** dans le menu de gauche).
2. Saisissez un nom, un numéro de dossier ou un numéro de téléphone dans la barre de recherche.
3. Les résultats se filtrent automatiquement pendant la saisie.
4. Cliquez sur une ligne du tableau pour ouvrir la fiche complète du patient.

### Créer un nouveau patient
1. Cliquez sur le bouton **Nouveau patient** en haut à droite de la liste.
2. Renseignez les champs obligatoires : nom, prénom, date de naissance, sexe.
3. Renseignez les coordonnées (téléphone, email, adresse) si disponibles.
4. Optionnel : liez le patient à un compte existant (entreprise ou individuel) via le champ Compte.
5. Cliquez sur **Créer le patient**. Le numéro de dossier est généré automatiquement.

## Astuces et points d'attention
- Le numéro de dossier ne peut pas être modifié après création.
- Un patient sans compte associé ne pourra pas être inscrit dans une visite tant qu'un compte ne lui est pas assigné (voir [comptes.md](comptes.md)).

## Voir aussi
- [fiche-patient.md](fiche-patient.md)
- [comptes.md](comptes.md)
- [import-csv.md](import-csv.md)
