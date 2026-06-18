# Campagnes

## Rôles autorisés
- Opérateur
- Médecin

## À quoi ça sert
Une campagne regroupe un ensemble de visites médicales pour un compte client (ex. : Bilan annuel 2026 — Acme). Elle structure le workflow de bout en bout : terrain → résultats → validation médicale.

## Comment l'utiliser

### Créer une campagne
1. Cliquez sur **Campagnes** dans le menu de gauche, puis sur **Nouvelle campagne**.
2. Donnez un nom à la campagne.
3. Sélectionnez le compte client associé.
4. Renseignez la date de début et la date de fin.
5. Enregistrez.

### Configurer une campagne
1. Ouvrez la campagne créée.
2. Onglet **Patients** : ajoutez les patients participant à la campagne.
3. Onglet **Types d'examens** : ajoutez les types d'examens à réaliser pour cette campagne.
4. Onglet **Visites** : suivez la progression des visites générées.

### Faire avancer le cycle de vie de la campagne
1. Une fois patients et examens configurés, cliquez sur **Valider la campagne** (rôle Médecin ou Admin requis).
2. Cliquez sur **Démarrer la campagne** pour entrer en phase Terrain (rôle Opérateur).
3. Une fois les visites terrain terminées, cliquez sur **Compléter la phase terrain**.
4. Saisissez les résultats puis validez successivement : Lab → Médecin clinique → Médecin entreprise.
5. Cliquez sur **Clôturer la campagne** une fois toutes les visites validées.
6. Cliquez sur **Archiver la campagne** si elle n'est plus active.

## Astuces et points d'attention
- Chaque transition de statut est déclenchée par un bouton d'action dédié visible en haut de la fiche campagne ; les boutons disponibles dépendent du statut courant et de votre rôle.

## Voir aussi
- [visites-campagne.md](visites-campagne.md)
- [detail-visite.md](detail-visite.md)
- [terrain-qr.md](terrain-qr.md)
