"""Static help article definitions for the help center."""

from pydantic import BaseModel


class HelpSectionDTO(BaseModel):
    heading: str
    content: str


class HelpArticleDTO(BaseModel):
    id: str
    title: str
    short_description: str
    icon: str
    tags: list[str]
    roles: list[str]
    sections: list[HelpSectionDTO]


ARTICLES: list[HelpArticleDTO] = [
    # ── Staff / Admin ─────────────────────────────────────────────────────────
    HelpArticleDTO(
        id="tableau-de-bord",
        title="Tableau de bord",
        short_description="Vue d'ensemble de l'activité : patients, rendez-vous, examens et certificats en un coup d'œil.",
        icon="layout-dashboard",
        tags=["dashboard", "statistiques", "kpi", "activité", "vue d'ensemble"],
        roles=["Opérateur", "Médecin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Le tableau de bord centralise les indicateurs clés (KPIs) de la plateforme : nombre de patients actifs, de rendez-vous planifiés, d'examens réalisés et de certificats émis.",
            ),
            HelpSectionDTO(
                heading="Comment ça fonctionne",
                content="Cliquez sur « Tableau de bord » dans le menu de gauche. Les chiffres sont calculés en temps réel à chaque chargement. Cliquez sur un indicateur pour accéder directement à la liste correspondante.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="liste-patients",
        title="Liste des patients",
        short_description="Recherchez, filtrez et créez des dossiers patients depuis la page principale.",
        icon="users",
        tags=["patients", "recherche", "dossier", "liste", "filtres", "nouveau patient"],
        roles=["Opérateur", "Médecin", "Admin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La liste des patients est l'écran principal de la plateforme. Elle affiche tous les patients enregistrés avec leur numéro de dossier (PAT-XXXXXXXX), leur date de naissance et le compte associé.",
            ),
            HelpSectionDTO(
                heading="Rechercher un patient",
                content="Utilisez la barre de recherche pour filtrer par nom, numéro de dossier ou téléphone. Les résultats se mettent à jour en temps réel. Cliquez sur une ligne pour ouvrir la fiche du patient.",
            ),
            HelpSectionDTO(
                heading="Créer un patient",
                content="Cliquez sur « Nouveau patient » en haut à droite. Renseignez le nom, prénom, date de naissance et sexe (champs obligatoires). Le numéro de dossier est généré automatiquement. Le patient peut être lié à un compte lors de la création.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="detail-patient",
        title="Fiche patient",
        short_description="Accédez à l'ensemble des données cliniques et administratives d'un patient via des onglets dédiés.",
        icon="user-round",
        tags=["fiche", "patient", "dossier", "onglets", "examens", "ordonnances", "certificats", "visites", "documents"],
        roles=["Opérateur", "Médecin", "Admin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La fiche patient regroupe toutes les informations d'un patient : données personnelles, médecins rattachés, comptes associés, historique des visites, examens, ordonnances, certificats et documents.",
            ),
            HelpSectionDTO(
                heading="Onglets disponibles",
                content="Visites · Examens · Ordonnances · Certificats · Médecins · Comptes · Documents · Carte patient. Chaque onglet se charge à la demande au premier clic.",
            ),
            HelpSectionDTO(
                heading="Modifier les informations",
                content="Cliquez sur le bouton « Modifier » dans l'en-tête de la fiche pour mettre à jour les coordonnées, la date de naissance, le sexe ou le médecin traitant.",
            ),
            HelpSectionDTO(
                heading="Carte patient et QR code",
                content="L'onglet « Carte patient » génère une carte récapitulative avec un QR code unique. Elle peut être imprimée ou téléchargée en PDF pour identifier rapidement le patient lors des sessions terrain.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="rendez-vous",
        title="Rendez-vous",
        short_description="Planifiez et suivez tous les rendez-vous médicaux, tous patients confondus.",
        icon="calendar-clock",
        tags=["rendez-vous", "planning", "agenda", "annuler", "statut", "créer"],
        roles=["Opérateur", "Médecin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La page Rendez-vous liste l'ensemble des rendez-vous planifiés sur la plateforme, tous patients confondus. Filtrez par date, statut et campagne pour retrouver rapidement un rendez-vous.",
            ),
            HelpSectionDTO(
                heading="Créer un rendez-vous",
                content="Depuis la liste ou la fiche d'un patient, cliquez sur « Nouveau rendez-vous ». Sélectionnez le patient, la date/heure, le type d'examen et éventuellement un médecin. Ajoutez des notes si nécessaire.",
            ),
            HelpSectionDTO(
                heading="Statuts d'un rendez-vous",
                content="Planifié → En cours → Terminé / Annulé. Utilisez les boutons d'action dans la liste pour faire avancer ou annuler un rendez-vous. Un rendez-vous terminé est lié à la consultation correspondante.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="consultations",
        title="Consultations",
        short_description="Retrouvez toutes les consultations médicales réalisées, avec leurs résultats et leurs validations.",
        icon="stethoscope",
        tags=["consultations", "visites", "médical", "résultats", "liste", "filtre"],
        roles=["Opérateur", "Médecin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La page Consultations liste les visites de type consultation médicale. Vous pouvez filtrer par date, médecin et statut de validation.",
            ),
            HelpSectionDTO(
                heading="Accéder au détail",
                content="Cliquez sur une ligne pour ouvrir le détail de la consultation : examens réalisés, ordonnances, certificats émis et interprétations médicales. Les opérateurs peuvent consulter, les médecins peuvent saisir et valider.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="detail-consultation",
        title="Détail d'une consultation",
        short_description="Enregistrez examens, ordonnances et certificats dans l'espace dédié à chaque consultation médicale.",
        icon="clipboard-list",
        tags=["consultation", "examen", "résultats", "ordonnance", "certificat", "interprétation", "workflow"],
        roles=["Médecin", "Opérateur"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Le détail d'une consultation est l'espace de travail du médecin pour une visite donnée. Il regroupe les résultats des examens, les ordonnances et les certificats d'aptitude.",
            ),
            HelpSectionDTO(
                heading="Enregistrer des résultats d'examen",
                content="Dans la section « Résultats d'examens », cliquez sur « Ajouter un examen ». Sélectionnez le type, saisissez la valeur et joignez éventuellement un fichier (PDF ou image). Chaque résultat est enregistré individuellement.",
            ),
            HelpSectionDTO(
                heading="Émettre une ordonnance",
                content="Cliquez sur « Nouvelle ordonnance » pour créer une ordonnance avec les médicaments, posologies et durées. Elle est téléchargeable en PDF après enregistrement.",
            ),
            HelpSectionDTO(
                heading="Émettre un certificat d'aptitude",
                content="Cliquez sur « Nouveau certificat ». Sélectionnez le type (aptitude, arrêt de travail, vaccination…), renseignez la conclusion et les éventuelles restrictions. Le certificat est archivable et téléchargeable en PDF.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="campagnes",
        title="Campagnes",
        short_description="Organisez les bilans de santé en masse pour une entreprise via des campagnes médicales structurées.",
        icon="clipboard-list",
        tags=["campagnes", "programme", "entreprise", "bilan", "collectif", "workflow"],
        roles=["Opérateur", "Médecin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Une campagne regroupe un ensemble de visites médicales pour un compte client (ex. : Bilan annuel 2026 — Acme). Elle structure le workflow de bout en bout : terrain → résultats → validation médicale.",
            ),
            HelpSectionDTO(
                heading="Créer une campagne",
                content="Cliquez sur « Nouvelle campagne ». Donnez un nom, sélectionnez le compte client, la date de début et de fin. Ajoutez ensuite les patients et les types d'examens à réaliser.",
            ),
            HelpSectionDTO(
                heading="Cycle de vie d'une campagne",
                content="Brouillon → Validée → Terrain → Analyse → Lab validé → Médecin clinique validé → Médecin entreprise validé → Clôturée → Archivée. Chaque transition est déclenchée par un bouton d'action dans la fiche campagne.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="visites-campagne",
        title="Visites de campagne",
        short_description="Suivez l'avancement de chaque visite patient au sein des campagnes médicales actives.",
        icon="calendar",
        tags=["visites", "campagne", "terrain", "suivi", "statut", "liste"],
        roles=["Opérateur", "Médecin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La page Visites de campagne liste toutes les visites liées aux campagnes, tous comptes confondus. Filtrez par campagne, statut et date pour retrouver rapidement une visite.",
            ),
            HelpSectionDTO(
                heading="Accéder au détail d'une visite",
                content="Cliquez sur une ligne pour ouvrir la fiche de visite. Vous y trouverez les informations du patient, le statut et les actions disponibles pour faire avancer la visite.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="detail-visite",
        title="Détail d'une visite",
        short_description="Consultez et faites avancer le statut d'une visite de campagne, de la collecte terrain à la validation finale.",
        icon="calendar-check",
        tags=["visite", "statut", "validation", "terrain", "résultats", "workflow", "avancer"],
        roles=["Opérateur", "Médecin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La fiche d'une visite affiche le patient, la campagne associée, le statut en cours et les actions disponibles selon ce statut.",
            ),
            HelpSectionDTO(
                heading="Avancer le statut",
                content="Utilisez les boutons d'action en haut de la fiche pour faire progresser la visite : Marquer la visite terrain comme terminée → Saisir les résultats → Valider côté lab → Valider côté médecin clinique → Valider côté médecin entreprise.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="resultats-examens",
        title="Résultats d'examens",
        short_description="Saisissez et consultez les résultats d'examens biologiques, radiologiques et cliniques pour chaque visite.",
        icon="flask-conical",
        tags=["examens", "résultats", "biologie", "laboratoire", "valeur", "appréciation", "fichier"],
        roles=["Médecin", "Opérateur"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La section Résultats d'examens permet de saisir les valeurs obtenues pour chaque type d'examen prévu dans une visite (biologie, radiologie, audiométrie, ECG, etc.).",
            ),
            HelpSectionDTO(
                heading="Saisir un résultat",
                content="Depuis le détail d'une consultation ou d'une visite, cliquez sur « Ajouter un examen ». Sélectionnez le type, saisissez la valeur et l'appréciation (Normal, Bas, Haut, Critique bas, Critique haut). Vous pouvez joindre un fichier de résultat.",
            ),
            HelpSectionDTO(
                heading="Code couleur des appréciations",
                content="L'appréciation est saisie manuellement et s'affiche avec un code couleur dans le tableau récapitulatif : vert pour Normal, orange pour Bas/Haut, rouge pour les valeurs critiques.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="ordonnances",
        title="Ordonnances",
        short_description="Rédigez et archivez des ordonnances médicales pour un patient, téléchargeables en PDF.",
        icon="file-text",
        tags=["ordonnance", "médicaments", "prescription", "pdf", "posologie", "durée", "archiver"],
        roles=["Médecin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La fonction Ordonnances permet au médecin d'émettre une ordonnance médicale lors d'une consultation. Elle liste les médicaments, posologies, fréquences et durées de traitement.",
            ),
            HelpSectionDTO(
                heading="Créer une ordonnance",
                content="Depuis le détail d'une consultation, cliquez sur « Nouvelle ordonnance ». Saisissez le diagnostic, ajoutez un ou plusieurs médicaments avec leur posologie, puis enregistrez. L'ordonnance est disponible en PDF immédiatement.",
            ),
            HelpSectionDTO(
                heading="Archiver une ordonnance",
                content="Les ordonnances peuvent être archivées depuis leur page de détail. Les ordonnances archivées restent consultables mais sont masquées par défaut dans la liste du patient.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="certificats",
        title="Certificats médicaux",
        short_description="Émettez des certificats d'aptitude, d'arrêt de travail ou de vaccination, téléchargeables en PDF.",
        icon="badge-check",
        tags=["certificat", "aptitude", "arrêt de travail", "vaccination", "pdf", "apte", "inapte", "SIR"],
        roles=["Médecin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Les certificats médicaux formalisent les conclusions cliniques : aptitude au poste, arrêt de travail, visite de pré-embauche, SIR (Suivi Individuel Renforcé), vaccination, etc.",
            ),
            HelpSectionDTO(
                heading="Types de certificats disponibles",
                content="Certificat d'aptitude · Arrêt de travail · Visite d'embauche · Visite périodique · Accident du travail / Maladie professionnelle · Suivi Individuel Renforcé (SIR) · Vaccination.",
            ),
            HelpSectionDTO(
                heading="Émettre un certificat",
                content="Depuis le détail d'une consultation ou la fiche patient, cliquez sur « Nouveau certificat ». Sélectionnez le type, renseignez les dates et la conclusion. Le certificat est téléchargeable en PDF et peut être envoyé par email au patient.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="documents",
        title="Gestion des documents",
        short_description="Consultez et gérez tous les documents patients téléversés sur la plateforme.",
        icon="folder-open",
        tags=["documents", "fichiers", "pdf", "image", "gestion", "archive", "recherche"],
        roles=["Opérateur", "Médecin", "Admin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La page Documents regroupe tous les fichiers téléversés pour l'ensemble des patients : rapports médicaux, analyses, ordonnances scannées, radiographies, etc.",
            ),
            HelpSectionDTO(
                heading="Filtrer et rechercher",
                content="Filtrez par patient, type de document (ordonnance, certificat, rapport…) ou période. Cliquez sur un document pour ouvrir l'aperçu intégré ou télécharger le fichier.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="upload-documents",
        title="Téléverser un document",
        short_description="Importez un fichier (PDF ou image) dans le dossier d'un patient avec analyse automatique par IA.",
        icon="upload",
        tags=["upload", "document", "pdf", "image", "ia", "analyse", "téléverser", "lab", "dossier"],
        roles=["Opérateur", "Médecin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Le téléversement de document permet d'ajouter n'importe quel fichier médical au dossier d'un patient : résultats d'analyses, comptes rendus, radiographies, ordonnances scannées.",
            ),
            HelpSectionDTO(
                heading="Comment ça fonctionne",
                content="Cliquez sur « Téléverser un document » depuis la page Documents. Déposez ou sélectionnez le fichier. L'IA analyse automatiquement le contenu pour détecter le type, la date et le patient. Vérifiez et corrigez les informations avant d'enregistrer.",
            ),
            HelpSectionDTO(
                heading="Import depuis le lab Constellab",
                content="Si des fichiers sont déjà disponibles dans un dossier Constellab Lab, utilisez l'option « Importer depuis le dossier lab » pour traiter plusieurs documents en une seule opération.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="notifications",
        title="Notifications",
        short_description="Envoyez et recevez des messages internes entre l'équipe médicale et les patients ou comptes.",
        icon="bell",
        tags=["notifications", "messages", "inbox", "envoi", "patient", "compte", "communication", "répondre"],
        roles=["Opérateur", "Médecin", "Admin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Le module Notifications permet d'envoyer des messages aux patients (individuellement ou via leur compte) et aux médecins. Les messages entrants s'affichent dans la boîte de réception.",
            ),
            HelpSectionDTO(
                heading="Envoyer un message",
                content="Accédez à Notifications → onglet Composer. Sélectionnez le destinataire (patient, compte ou médecin), le canal (email, SMS, WhatsApp), l'objet et le contenu. Cliquez sur Envoyer.",
            ),
            HelpSectionDTO(
                heading="Boîte de réception",
                content="Les messages reçus apparaissent dans l'onglet Reçus. L'icône cloche dans la barre latérale affiche le nombre de messages non lus. Cliquez sur un message pour le lire et utiliser le bouton « Répondre ».",
            ),
        ],
    ),
    HelpArticleDTO(
        id="comptes",
        title="Comptes clients",
        short_description="Gérez les comptes entreprise et individuels qui financent ou supervisent les bilans médicaux.",
        icon="building-2",
        tags=["comptes", "entreprise", "individuel", "facturation", "rh", "patient", "compte médecin"],
        roles=["Opérateur", "Médecin", "Admin", "Responsable de compte"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Un compte représente l'entité porteuse d'un ou plusieurs patients : une entreprise (compte Entreprise) ou une personne physique (compte Individuel). Les comptes sont utilisés pour la facturation et le suivi RH.",
            ),
            HelpSectionDTO(
                heading="Types de comptes",
                content="Compte Entreprise : lié à une entreprise cliente, peut regrouper plusieurs patients.\nCompte Individuel : lié à une personne physique, pour les patients sans lien entreprise.",
            ),
            HelpSectionDTO(
                heading="Gérer les patients d'un compte",
                content="Depuis la fiche d'un compte, l'onglet Patients liste les patients associés. Vous pouvez ajouter un patient existant ou en créer un nouveau directement depuis cette vue.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="medecins",
        title="Médecins",
        short_description="Gérez le registre des médecins disponibles et associez-les aux patients.",
        icon="user-round-check",
        tags=["médecins", "rpps", "spécialité", "registre", "médecin traitant", "lier"],
        roles=["Opérateur", "Admin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Le registre des médecins répertorie tous les médecins pouvant être associés à des patients ou assignés à des consultations. Un médecin doit aussi avoir un compte utilisateur Constellab pour se connecter à l'application.",
            ),
            HelpSectionDTO(
                heading="Ajouter un médecin",
                content="Cliquez sur « Nouveau médecin ». Renseignez le nom, le prénom, la spécialité et le numéro RPPS. Liez le médecin à son compte Constellab via le champ « Médecin lié ».",
            ),
            HelpSectionDTO(
                heading="Associer un médecin à un patient",
                content="Depuis la fiche patient, onglet Médecins, cliquez sur « Associer un médecin ». Vous pouvez désigner un médecin traitant principal pour le patient.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="terrain-qr",
        title="Mode terrain et QR code",
        short_description="Sur le terrain, scannez les QR codes patients pour accéder instantanément à leur fiche et valider les visites.",
        icon="qr-code",
        tags=["terrain", "qr code", "scan", "mobile", "visite", "collecte", "opérateur terrain", "caméra"],
        roles=["Médecin", "Opérateur"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Le mode terrain est une interface mobile optimisée pour les opérateurs sur site. Il permet de scanner le QR code d'un patient ou d'un tube pour accéder rapidement à sa fiche et valider sa visite.",
            ),
            HelpSectionDTO(
                heading="Accéder au mode terrain",
                content="Depuis la fiche d'une campagne en phase Terrain, cliquez sur le bouton « Aller sur le terrain ». L'URL est spécifique à chaque campagne.",
            ),
            HelpSectionDTO(
                heading="Scanner un QR code",
                content="Activez la caméra via le bouton « Scan caméra ». Pointez vers le QR code de la carte patient ou du tube. La fiche du patient s'ouvre automatiquement. Vous pouvez aussi saisir manuellement le numéro de dossier si la caméra n'est pas disponible.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="import-csv",
        title="Import CSV en masse",
        short_description="Importez rapidement des patients, des comptes ou des médecins depuis un fichier CSV ou Excel.",
        icon="file-spreadsheet",
        tags=["import", "csv", "excel", "masse", "patients", "comptes", "médecins", "migration", "bulk"],
        roles=["Opérateur", "Admin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="L'import en masse permet de créer des centaines de dossiers patients, de comptes ou de médecins en une seule opération depuis un fichier CSV. C'est la méthode recommandée pour la migration initiale ou les mises à jour volumineuses.",
            ),
            HelpSectionDTO(
                heading="Comment ça fonctionne",
                content="Accédez à Paramètres → onglet Import. Sélectionnez le type de données (Patients, Comptes ou Médecins). Téléchargez le modèle CSV si nécessaire, remplissez-le et déposez-le. Le système valide chaque ligne et affiche les erreurs ligne par ligne.",
            ),
            HelpSectionDTO(
                heading="Pré-requis",
                content="L'import nécessite que le serveur ait synchronisé les utilisateurs Constellab. Si vous voyez un message d'erreur indiquant que la table des utilisateurs est vide, redémarrez l'application et réessayez.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="parametres",
        title="Paramètres administrateur",
        short_description="Configurez l'apparence de l'application, la langue, et gérez les rôles des utilisateurs.",
        icon="settings",
        tags=["paramètres", "admin", "thème", "couleur", "langue", "logo", "rôles", "utilisateurs", "configuration"],
        roles=["Admin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La page Paramètres est réservée aux administrateurs. Elle permet de configurer l'apparence globale de l'application et de gérer les rôles attribués aux utilisateurs Constellab.",
            ),
            HelpSectionDTO(
                heading="Onglet Général",
                content="Personnalisez la couleur du thème, la langue (FR/EN) et le logo de l'application. Les modifications sont appliquées immédiatement pour tous les utilisateurs connectés.",
            ),
            HelpSectionDTO(
                heading="Onglet Rôles utilisateurs",
                content="Attribuez ou retirez les rôles (Admin, Médecin, Opérateur, Responsable de compte, Patient) à chaque utilisateur Constellab. Pour les rôles Responsable de compte et Patient, sélectionnez l'entité liée après activation.",
            ),
            HelpSectionDTO(
                heading="Onglet Import",
                content="Accédez aux outils d'import en masse de données. Voir l'article « Import CSV en masse » pour le détail de la procédure.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="changer-role",
        title="Changer de rôle",
        short_description="Si vous avez plusieurs rôles, basculez facilement de l'un à l'autre depuis le menu utilisateur.",
        icon="repeat-2",
        tags=["rôle", "admin", "médecin", "opérateur", "patient", "basculer", "switcher", "multi-rôle"],
        roles=["Tous les rôles"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Certains utilisateurs disposent de plusieurs rôles (ex. : un médecin qui est aussi administrateur). La fonction « Changer de rôle » permet de basculer entre ces rôles sans se déconnecter.",
            ),
            HelpSectionDTO(
                heading="Comment ça fonctionne",
                content="Cliquez sur votre avatar en bas de la barre latérale pour ouvrir le menu utilisateur. Si vous avez plusieurs rôles, cliquez sur « Changer de rôle ». Sélectionnez le rôle souhaité : la navigation se met à jour immédiatement.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="carte-patient",
        title="Carte patient et QR code",
        short_description="Générez et imprimez la carte d'identité patient avec son QR code unique pour les sessions terrain.",
        icon="credit-card",
        tags=["carte patient", "qr code", "identité", "impression", "terrain", "pdf", "imprimer"],
        roles=["Opérateur", "Médecin", "Admin"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La carte patient est un document récapitulatif qui identifie le patient grâce à un QR code unique. Elle est utilisée lors des sessions terrain pour scanner rapidement le dossier.",
            ),
            HelpSectionDTO(
                heading="Générer la carte",
                content="Depuis la fiche patient, cliquez sur l'onglet « Carte patient ». La carte s'affiche avec le nom, le numéro de dossier, la date de naissance et le QR code. Cliquez sur « Imprimer » ou « Télécharger le fichier » pour l'obtenir en PDF.",
            ),
            HelpSectionDTO(
                heading="Utilisation sur le terrain",
                content="L'opérateur terrain scanne le QR code depuis le mode terrain pour accéder instantanément à la fiche du patient. Voir l'article « Mode terrain et QR code » pour plus de détails.",
            ),
        ],
    ),
    # ── Portail patient ───────────────────────────────────────────────────────
    HelpArticleDTO(
        id="portail-tableau-de-bord",
        title="Mon tableau de bord",
        short_description="Votre espace personnel avec un résumé de vos consultations, rendez-vous et notifications récentes.",
        icon="layout-dashboard",
        tags=["portail", "patient", "dashboard", "tableau de bord", "résumé", "personnel"],
        roles=["Patient"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Le tableau de bord patient est votre page d'accueil personnelle. Il affiche un résumé de votre activité médicale : prochain rendez-vous, dernières consultations et notifications non lues.",
            ),
            HelpSectionDTO(
                heading="Navigation rapide",
                content="Cliquez sur les cartes pour accéder directement à chaque section (Rendez-vous, Consultations, Notifications). Les indicateurs se mettent à jour à chaque connexion.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="mes-rendez-vous",
        title="Mes rendez-vous",
        short_description="Consultez vos rendez-vous médicaux planifiés et demandez un nouveau rendez-vous.",
        icon="calendar-plus",
        tags=["rendez-vous", "patient", "portail", "planifier", "agenda", "demande"],
        roles=["Patient"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La page Mes rendez-vous liste tous vos rendez-vous médicaux (passés, en cours et à venir) avec la date, l'heure, le médecin et le lieu.",
            ),
            HelpSectionDTO(
                heading="Demander un rendez-vous",
                content="Cliquez sur « Planifier un rendez-vous ». Sélectionnez une date, un médecin (optionnel) et un mode (en entreprise, à domicile, visio, hôpital). Ajoutez un message si nécessaire. Votre demande sera confirmée par l'équipe médicale.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="mes-consultations",
        title="Mes consultations",
        short_description="Accédez à l'historique de vos consultations médicales et consultez leurs résultats.",
        icon="stethoscope",
        tags=["consultations", "patient", "portail", "historique", "résultats", "calendrier"],
        roles=["Patient"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La page Mes consultations liste toutes vos consultations médicales réalisées, avec la date, le médecin responsable et le statut.",
            ),
            HelpSectionDTO(
                heading="Vue liste et vue calendrier",
                content="Basculez entre la vue liste (chronologique) et la vue calendrier pour visualiser vos consultations selon le format qui vous convient. Cliquez sur une consultation pour voir le détail.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="mes-ordonnances",
        title="Mes ordonnances",
        short_description="Consultez et téléchargez vos ordonnances médicales en PDF.",
        icon="file-text",
        tags=["ordonnances", "patient", "portail", "médicaments", "pdf", "télécharger"],
        roles=["Patient"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La page Mes ordonnances liste toutes les ordonnances émises lors de vos consultations, avec la date, le médecin prescripteur et la liste des médicaments.",
            ),
            HelpSectionDTO(
                heading="Télécharger une ordonnance",
                content="Cliquez sur une ordonnance puis sur « Télécharger le fichier » pour obtenir le PDF. Vous pouvez aussi demander à l'équipe médicale de vous l'envoyer par email via le bouton correspondant.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="mes-documents",
        title="Mes documents",
        short_description="Retrouvez tous vos documents médicaux : analyses, comptes rendus, certificats et ordonnances.",
        icon="folder-open",
        tags=["documents", "patient", "portail", "pdf", "analyse", "certificat", "télécharger"],
        roles=["Patient"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La page Mes documents centralise tous les fichiers médicaux disponibles dans votre dossier : résultats d'analyses, comptes rendus, ordonnances scannées, certificats médicaux.",
            ),
            HelpSectionDTO(
                heading="Filtrer et consulter",
                content="Filtrez par type de document (examen, ordonnance, certificat) ou par date. Cliquez sur un document pour l'afficher en aperçu ou le télécharger.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="mes-notifications",
        title="Mes notifications",
        short_description="Recevez et envoyez des messages avec l'équipe médicale directement depuis le portail patient.",
        icon="bell",
        tags=["notifications", "patient", "portail", "messages", "inbox", "répondre", "communication"],
        roles=["Patient"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La messagerie patient vous permet d'échanger des messages avec l'équipe médicale de manière sécurisée. Vous recevez des rappels de rendez-vous, des résultats et des communications de l'équipe.",
            ),
            HelpSectionDTO(
                heading="Répondre à un message",
                content="Dans l'onglet Reçus, cliquez sur un message puis sur « Répondre ». Votre réponse sera envoyée directement à l'équipe médicale.",
            ),
            HelpSectionDTO(
                heading="Envoyer un nouveau message",
                content="Utilisez l'onglet Composer pour initier un message vers l'équipe médicale (clinique) sans répondre à un message existant.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="mes-comptes",
        title="Mes comptes",
        short_description="Consultez les comptes (entreprise ou individuel) associés à votre dossier patient.",
        icon="building-2",
        tags=["comptes", "patient", "portail", "entreprise", "individuel", "facturation"],
        roles=["Patient"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="Cette page affiche les comptes liés à votre dossier patient : compte entreprise (si votre employeur finance les bilans) ou compte individuel (compte personnel de facturation).",
            ),
            HelpSectionDTO(
                heading="Créer un compte personnel",
                content="Si aucun compte n'est encore associé, vous pouvez créer un compte individuel en cliquant sur « Nouveau compte personnel ». Renseignez vos coordonnées de facturation.",
            ),
        ],
    ),
    HelpArticleDTO(
        id="mon-profil",
        title="Mon profil",
        short_description="Consultez vos informations personnelles et médicales enregistrées dans votre dossier.",
        icon="user",
        tags=["profil", "patient", "portail", "informations personnelles", "données médicales", "modifier"],
        roles=["Patient"],
        sections=[
            HelpSectionDTO(
                heading="À quoi ça sert",
                content="La page Mon profil affiche vos données personnelles (nom, prénom, date de naissance, sexe, coordonnées) et médicales (poids, taille, numéro de sécurité sociale) enregistrées dans votre dossier.",
            ),
            HelpSectionDTO(
                heading="Modifier mes informations",
                content="Les informations de votre profil sont gérées par l'équipe médicale. Si vous souhaitez corriger des données, contactez la clinique via la messagerie (Mes notifications).",
            ),
        ],
    ),
]
