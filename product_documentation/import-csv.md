# Import CSV en masse

## Rôles autorisés
- Opérateur
- Admin

## À quoi ça sert
L'import en masse permet de créer des centaines de dossiers patients, de comptes ou de médecins en une seule opération depuis un fichier CSV. C'est la méthode recommandée pour la migration initiale ou les mises à jour volumineuses.

## Comment l'utiliser
1. Cliquez sur **Paramètres** dans le menu utilisateur, puis sur l'onglet **Import**.
2. Sélectionnez le type de données à importer : Patients, Comptes, ou Médecins.
3. Téléchargez le modèle CSV correspondant si vous ne l'avez pas déjà.
4. Remplissez le modèle avec vos données.
5. Déposez le fichier rempli sur la zone d'import.
6. Cliquez sur **Importer**.
7. Consultez les erreurs affichées ligne par ligne et corrigez le fichier si nécessaire, puis réimportez.

## Pré-requis
- L'import nécessite que le serveur ait déjà synchronisé les utilisateurs Constellab vers la table locale des utilisateurs.
- Si un message d'erreur indique que la table des utilisateurs locaux est vide (typiquement après une réinitialisation de la base de données), redémarrez l'application et réessayez l'import.

## Voir aussi
- [liste-patients.md](liste-patients.md)
- [comptes.md](comptes.md)
- [medecins.md](medecins.md)
