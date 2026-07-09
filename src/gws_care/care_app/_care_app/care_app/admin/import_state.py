"""State for bulk CSV import of patients and accounts from the Admin page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel

_PATIENT_TEMPLATE = (
    "last_name,first_name,birth_name,date_of_birth,gender,"
    "address,address_complement,postal_code,city,country,"
    "phone,email,social_security_number\n"
    # ── Exemples (numéro sécu FR : genre(1) + AA(2) + MM(2) + dép(2) + commune(3) + ordre(3) + clé(2)) ──
    "DUPONT,Marie,,1985-03-15,F,12 Rue de la Paix,,75001,Paris,France,"
    "+33612345678,marie.dupont@email.fr,2850375108234 56\n"
    "MARTIN,Jean,,1978-07-22,M,5 Avenue Victor Hugo,,69002,Lyon,France,"
    "+33698765432,jean.martin@email.fr,1780769123456 89\n"
    "BERNARD,Sophie,LEROY,1992-11-03,F,8 Rue Nationale,,13001,Marseille,France,"
    "+33791234567,sophie.bernard@email.fr,2921113123456 78\n"
    "LEFEVRE,Thomas,,1987-06-18,M,23 Boulevard Haussmann,Apt 4B,75009,Paris,France,"
    "+33614567890,thomas.lefevre@email.fr,1870675012345 67\n"
    "MOREAU,Claire,SIMON,1995-02-27,F,14 Rue du Général de Gaulle,,67000,Strasbourg,France,"
    "+33756789012,claire.moreau@email.fr,2950267034567 12\n"
    "NDOYE,Ibrahima,,1983-09-10,M,45 Rue de la République,,93100,Montreuil,France,"
    "+33678901234,ibrahima.ndoye@email.fr,\n"
    "PETIT,Laura,,2000-05-14,F,3 Impasse des Lilas,,31000,Toulouse,France,"
    "+33698012345,laura.petit@email.fr,2000531012345 34\n"
    "GARCIA,Carlos,,1975-12-01,M,7 Avenue Jean Jaurès,,44000,Nantes,France,"
    "+33623456789,carlos.garcia@email.fr,1751244056789 45\n"
    "KONÉ,Aminata,,1990-04-12,F,Rue des Jardins,,BP 01,Abidjan,Côte d'Ivoire,"
    "+2250701000001,aminata.kone@email.ci,\n"
    "TRAORÉ,Moussa,,1988-08-25,M,Cocody Riviera 3,,, Abidjan,Côte d'Ivoire,"
    "+2250505678901,moussa.traore@email.ci,\n"
    "OUEDRAOGO,Fatou,,1993-01-19,F,Secteur 15 Gounghin,,, Ouagadougou,Burkina Faso,"
    "+22670123456,fatou.ouedraogo@email.bf,\n"
    "DIALLO,Mamadou,,1980-07-30,M,HLM Grand Yoff,,, Dakar,Sénégal,"
    "+221771234567,mamadou.diallo@email.sn,\n"
    "LAMBERT,Émilie,GIRARD,1997-04-08,F,56 Rue Victor Hugo,Résidence Les Pins,06000,Nice,France,"
    "+33745678901,emilie.lambert@email.fr,2970406034561 23\n"
    "ROUSSEAU,Pierre,,1969-10-22,M,2 Chemin du Moulin,,59000,Lille,France,"
    "+33667890123,pierre.rousseau@email.fr,1691059089012 56\n"
)

_ACCOUNT_COMPANY_TEMPLATE = (
    "name,registration_number,address,postal_code,city,"
    "contact_first_name,contact_last_name,phone,email\n"
    # ── Exemples ──────────────────────────────────────────────────────────────
    "Subway France,FR-75-2023-B-001,123 Rue de Rivoli,75001,Paris,"
    "Sophie,Martin,+33145678901,contact@subway.fr\n"
    "Total Energies SE,FR-92-2022-B-002,2 Place Jean Millier,92078,Paris La Défense,"
    "Pierre,Dubois,+33147448046,contact@totalenergies.com\n"
    "KFC France,FR-75-2020-B-003,44 Avenue George V,75008,Paris,"
    "Marie,Leclerc,+33145678903,contact@kfc.fr\n"
    "McDonald's France,FR-75-2019-B-004,1 Rue du Débarcadère,75017,Paris,"
    "Jean,Dupont,+33145678904,contact@mcdonalds.fr\n"
)

_ACCOUNT_INDIVIDUAL_TEMPLATE = (
    "contact_last_name,contact_first_name,address,postal_code,city,phone,email\n"
    # ── Exemples (les mêmes personnes que dans le template patients) ──────────
    "DUPONT,Marie,12 Rue de la Paix,75001,Paris,+33612345678,marie.dupont@email.fr\n"
    "MARTIN,Jean,5 Avenue Victor Hugo,69002,Lyon,+33698765432,jean.martin@email.fr\n"
    "KONÉ,Aminata,12 Rue des Jardins,,,+2250701000001,aminata.kone@email.ci\n"
)


_DOCTOR_TEMPLATE = (
    "last_name,first_name,specialization,phone,email,rpps_number\n"
    # ── 1 cardiologue ─────────────────────────────────────────────────────────
    "FONTAINE,Henri,Cardiologie,+33145670001,henri.fontaine@medecin.fr,10345678901\n"
    # ── 3 médecins du travail ─────────────────────────────────────────────────
    "CHEVALIER,Isabelle,Médecine du travail,+33472110001,isabelle.chevalier@medecin.fr,10345678902\n"
    "RENARD,Philippe,Médecine du travail,+33467110002,philippe.renard@medecin.fr,10345678903\n"
    "DIOP,Oumar,Médecine du travail,+221775110001,oumar.diop@medecin.sn,\n"
    # ── 1 diabétologue ────────────────────────────────────────────────────────
    "BONNET,Laurent,Diabétologie,+33156770001,laurent.bonnet@medecin.fr,10345678904\n"
    # ── 2 médecins généralistes ───────────────────────────────────────────────
    "GARNIER,Nathalie,Médecine générale,+33467880001,nathalie.garnier@medecin.fr,10345678905\n"
    "COULIBALY,Seydou,Médecine générale,+2250707110001,seydou.coulibaly@medecin.ci,\n"
)

def _exam_row(
    exam_type: str,
    category: str,
    department: str = "",
    description: str = "",
    parameter: str = "",
    code: str = "",
    value_type: str = "NUMERIC",
    unit: str = "",
    is_computed: str = "false",
    formula: str = "",
    age_min: str = "",
    age_max: str = "",
    age_gender: str = "",
    ref_low: str = "",
    ref_high: str = "",
    critical_low: str = "",
    critical_high: str = "",
    label_normal: str = "",
    label_low: str = "",
    label_high: str = "",
    label_critical_low: str = "",
    label_critical_high: str = "",
) -> str:
    """Return one CSV row with exactly 22 columns."""
    return ",".join([
        exam_type, category, department, description, parameter, code, value_type, unit,
        is_computed, formula,
        age_min, age_max, age_gender,
        ref_low, ref_high, critical_low, critical_high,
        label_normal, label_low, label_high, label_critical_low, label_critical_high,
    ]) + "\n"


# Columns (22 total — indices 0-21):
#  0  exam_type     : exam type name (required)
#  1  category      : BIOLOGY | CLINICAL | IMAGING | ECG | ORL | URINE | OTHER (required)
#  2  department    : free text
#  3  description   : free text
#  4  parameter     : parameter name (leave blank to create the exam type only)
#  5  code          : short identifier (lowercase)
#  6  value_type    : NUMERIC | TEXT | BOOLEAN
#  7  unit          : unit of measure
#  8  is_computed   : true | false  — computed from formula, not entered manually
#  9  formula       : e.g. poids/(taille/100)^2  (used when is_computed=true, codes in lowercase)
# 10  age_min       : minimum age inclusive (blank = no lower bound)
# 11  age_max       : maximum age inclusive (blank = no upper bound)
# 12  age_gender    : ALL | M | F  — leave blank if no threshold for this parameter
# 13  ref_low       : lower reference bound
# 14  ref_high      : upper reference bound
# 15  critical_low  : critical lower bound
# 16  critical_high : critical upper bound
# 17  label_normal  : label when value is in normal range
# 18  label_low     : label when value is below ref_low
# 19  label_high    : label when value is above ref_high
# 20  label_critical_low  : label when below critical_low
# 21  label_critical_high : label when above critical_high
#
# Pattern: une ligne par paramètre × tranche age/genre.
#   • Pas de seuils          : laisser age_gender vide → une seule ligne
#   • Seuils identiques M/F  : age_gender=ALL → une seule ligne
#   • Seuils différents M/F  : une ligne avec age_gender=M + une ligne avec age_gender=F
#   • Tranches d'âge         : une ligne par tranche (age_min/age_max + age_gender)
#   Les colonnes 0-9 (définition) se répètent sur chaque ligne du même paramètre.
_EXAM_TYPE_TEMPLATE = (
    "exam_type,category,department,description,parameter,code,value_type,unit,"
    "is_computed,formula,"
    "age_min,age_max,age_gender,"
    "ref_low,ref_high,critical_low,critical_high,"
    "label_normal,label_low,label_high,label_critical_low,label_critical_high\n"
    # ── Bilan lipidique ───────────────────────────────────────────────────────
    + _exam_row("Bilan lipidique", "BIOLOGY", "Biologie", parameter="Triglycerides", code="tg", unit="g/L",
                age_gender="ALL", ref_high="1.5")
    + _exam_row("Bilan lipidique", "BIOLOGY", "Biologie", parameter="LDL", code="ldl", unit="g/L")
    + _exam_row("Bilan lipidique", "BIOLOGY", "Biologie", parameter="HDL", code="hdl", unit="g/L",
                age_gender="M", ref_low="0.4")
    + _exam_row("Bilan lipidique", "BIOLOGY", "Biologie", parameter="HDL", code="hdl", unit="g/L",
                age_gender="F", ref_low="0.5")
    + _exam_row("Bilan lipidique", "BIOLOGY", "Biologie", parameter="Cholesterol total", code="chol", unit="g/L",
                age_gender="ALL", ref_high="2.0")
    # ── Serologies infectieuses ───────────────────────────────────────────────
    + _exam_row("Serologies infectieuses", "BIOLOGY", "Biologie", parameter="TPHA (Syphilis)", code="tpha", value_type="BOOLEAN")
    + _exam_row("Serologies infectieuses", "BIOLOGY", "Biologie", parameter="Ac anti-HBs (Hepatite B - anticorps)", code="achbs", value_type="BOOLEAN")
    + _exam_row("Serologies infectieuses", "BIOLOGY", "Biologie", parameter="Serologie VIH (Ag/Ac combines)", code="vih", value_type="BOOLEAN")
    + _exam_row("Serologies infectieuses", "BIOLOGY", "Biologie", parameter="Ac anti-HBc (Hepatite B - core)", code="achbc", value_type="BOOLEAN")
    + _exam_row("Serologies infectieuses", "BIOLOGY", "Biologie", parameter="Ac anti-VHC (Hepatite C)", code="acvhc", value_type="BOOLEAN")
    + _exam_row("Serologies infectieuses", "BIOLOGY", "Biologie", parameter="AgHBs (Hepatite B - antigene surface)", code="aghbs", value_type="BOOLEAN")
    # ── Bilan ophtalmologique ─────────────────────────────────────────────────
    + _exam_row("Bilan ophtalmologique", "CLINICAL", "Ophtalmologie", parameter="Acuite visuelle OD (sans correction)", code="avod_sc", value_type="TEXT")
    + _exam_row("Bilan ophtalmologique", "CLINICAL", "Ophtalmologie", parameter="Acuite visuelle OG (sans correction)", code="avog_sc", value_type="TEXT")
    + _exam_row("Bilan ophtalmologique", "CLINICAL", "Ophtalmologie", parameter="Acuite visuelle OD (avec correction)", code="avod_ac", value_type="TEXT")
    + _exam_row("Bilan ophtalmologique", "CLINICAL", "Ophtalmologie", parameter="Acuite visuelle OG (avec correction)", code="avog_ac", value_type="TEXT")
    + _exam_row("Bilan ophtalmologique", "CLINICAL", "Ophtalmologie", parameter="Vision des couleurs", code="vdc", value_type="TEXT")
    + _exam_row("Bilan ophtalmologique", "CLINICAL", "Ophtalmologie", parameter="Champ visuel", code="champvis", value_type="TEXT")
    + _exam_row("Bilan ophtalmologique", "CLINICAL", "Ophtalmologie", parameter="Tension oculaire OD", code="tiod", unit="mmHg",
                age_gender="ALL", ref_low="10.0", ref_high="21.0", critical_high="30.0")
    + _exam_row("Bilan ophtalmologique", "CLINICAL", "Ophtalmologie", parameter="Tension oculaire OG", code="tiog", unit="mmHg",
                age_gender="ALL", ref_low="10.0", ref_high="21.0", critical_high="30.0")
    # ── Constantes vitales ────────────────────────────────────────────────────
    + _exam_row("Constantes vitales", "CLINICAL", "Medecine du travail", parameter="Taille", code="taille", unit="cm")
    + _exam_row("Constantes vitales", "CLINICAL", "Medecine du travail", parameter="Poids", code="poids", unit="kg")
    + _exam_row("Constantes vitales", "CLINICAL", "Medecine du travail", parameter="IMC", code="imc", unit="kg/m2",
                is_computed="true", formula="poids/(taille/100)^2",
                age_min="0", age_max="17", age_gender="ALL",
                ref_low="14.0", ref_high="25.0", critical_low="10.0", critical_high="35.0",
                label_normal="Poids normal", label_low="Insuffisance ponderale", label_high="Surpoids",
                label_critical_low="Denutrition severe", label_critical_high="Obesite severe")
    + _exam_row("Constantes vitales", "CLINICAL", "Medecine du travail", parameter="IMC", code="imc", unit="kg/m2",
                is_computed="true", formula="poids/(taille/100)^2",
                age_min="18", age_gender="ALL",
                ref_low="18.5", ref_high="25.0", critical_low="13.0", critical_high="40.0",
                label_normal="Poids normal", label_low="Insuffisance ponderale", label_high="Surpoids",
                label_critical_low="Denutrition severe", label_critical_high="Obesite morbide")
    + _exam_row("Constantes vitales", "CLINICAL", "Medecine du travail", parameter="Frequence cardiaque", code="fc", unit="bpm",
                age_gender="ALL", ref_low="50.0", ref_high="100.0", critical_low="30.0", critical_high="150.0")
    + _exam_row("Constantes vitales", "CLINICAL", "Medecine du travail", parameter="Tension systolique", code="pas", unit="mmHg",
                age_gender="ALL", ref_low="90.0", ref_high="140.0", critical_low="70.0", critical_high="180.0")
    + _exam_row("Constantes vitales", "CLINICAL", "Medecine du travail", parameter="SpO2", code="spo2", unit="%",
                age_gender="ALL", ref_low="95.0", ref_high="100.0", critical_low="88.0")
    + _exam_row("Constantes vitales", "CLINICAL", "Medecine du travail", parameter="Temperature", code="temp", unit="C",
                age_gender="ALL", ref_low="36.1", ref_high="37.5", critical_low="34.0", critical_high="40.0")
    # ── NFS Hemogramme ────────────────────────────────────────────────────────
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="Globules blancs (GB)", code="gb", unit="G/L",
                age_gender="ALL", ref_low="4.0", ref_high="10.0", critical_low="2.0", critical_high="30.0",
                label_normal="GB normal", label_low="Leucopenie", label_high="Leucocytose",
                label_critical_low="Agranulocytose", label_critical_high="Leucocytose severe")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="Globules rouges (GR)", code="gr", unit="T/L",
                age_gender="M", ref_low="4.5", ref_high="5.9", critical_low="2.0", critical_high="7.0")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="Globules rouges (GR)", code="gr", unit="T/L",
                age_gender="F", ref_low="4.0", ref_high="5.2", critical_low="2.0", critical_high="7.0")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="Hemoglobine", code="hgb", unit="g/dL",
                age_gender="M", ref_low="13.0", ref_high="17.5", critical_low="7.0", critical_high="20.0",
                label_normal="Hemoglobine normale", label_low="Anemie", label_high="Polyglobulie",
                label_critical_low="Anemie severe", label_critical_high="Polyglobulie severe")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="Hemoglobine", code="hgb", unit="g/dL",
                age_gender="F", ref_low="12.0", ref_high="16.0", critical_low="7.0", critical_high="20.0",
                label_normal="Hemoglobine normale", label_low="Anemie", label_high="Polyglobulie",
                label_critical_low="Anemie severe", label_critical_high="Polyglobulie severe")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="Hematocrite", code="hct", unit="%",
                age_gender="M", ref_low="40.0", ref_high="54.0", critical_low="20.0", critical_high="60.0")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="Hematocrite", code="hct", unit="%",
                age_gender="F", ref_low="36.0", ref_high="48.0", critical_low="20.0", critical_high="60.0")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="Plaquettes", code="plq", unit="G/L",
                age_gender="ALL", ref_low="150.0", ref_high="400.0", critical_low="50.0", critical_high="1000.0")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="VGM", code="vgm", unit="fL",
                age_gender="ALL", ref_low="80.0", ref_high="100.0")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="TCMH", code="tcmh", unit="pg",
                age_gender="ALL", ref_low="27.0", ref_high="32.0")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="CCMH", code="ccmh", unit="g/dL",
                age_gender="ALL", ref_low="32.0", ref_high="36.0")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="Neutrophiles %", code="neutro", unit="%",
                age_gender="ALL", ref_low="40.0", ref_high="75.0")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="Lymphocytes %", code="lympho", unit="%",
                age_gender="ALL", ref_low="20.0", ref_high="45.0")
    + _exam_row("NFS Hemogramme", "BIOLOGY", "Biologie", parameter="Monocytes %", code="mono", unit="%",
                age_gender="ALL", ref_low="2.0", ref_high="10.0")
)


# ── DTOs ─────────────────────────────────────────────────────────────────────


class ImportRowResultDTO(BaseModel):
    """Represents one CSV row with its parsed display values and import result."""

    row_num: int
    cells: list[str]  # display values: [row_num, field1, ..., status_text]
    status: str = "pending"  # "pending" | "error" | "success"
    message: str = ""


# ── State ─────────────────────────────────────────────────────────────────────


class ImportState(ReflexMainState):
    """State for the bulk CSV import dialogs on the Admin page."""

    import_dialog_open: bool = False
    import_type: str = ""  # "patients" | "accounts"

    _raw_rows: list[dict] = []  # private — raw dicts parsed from CSV, parallel to preview_rows

    preview_rows: list[ImportRowResultDTO] = []
    preview_headers: list[str] = []

    is_parsing: bool = False
    parse_error: str = ""

    is_importing: bool = False
    import_done: bool = False
    success_count: int = 0
    error_count: int = 0

    # ── Computed vars ─────────────────────────────────────────────────────────

    @rx.var
    def valid_row_count(self) -> int:
        """Number of rows that passed validation and are ready to import."""
        return sum(1 for r in self.preview_rows if r.status == "pending")

    @rx.var
    def can_import(self) -> bool:
        """True when there are valid rows and no import is in progress."""
        return self.valid_row_count > 0 and not self.is_importing and not self.import_done

    @rx.var
    def has_preview(self) -> bool:
        return len(self.preview_rows) > 0

    # ── Events ────────────────────────────────────────────────────────────────

    @rx.event
    def open_import_dialog(self, import_type: str):
        """Open the import dialog for the given entity type."""
        self.import_type = import_type
        self.import_dialog_open = True
        self._reset_import()

    @rx.event
    def close_import_dialog(self):
        """Close the import dialog."""
        self.import_dialog_open = False

    @rx.event
    def download_template(self):
        """Download a CSV template file for the current import type."""
        if self.import_type == "patients":
            return rx.download(
                data=_PATIENT_TEMPLATE.encode("utf-8"),
                filename="patients_import_template.csv",
            )
        if self.import_type == "doctors":
            return rx.download(
                data=_DOCTOR_TEMPLATE.encode("utf-8"),
                filename="doctors_import_template.csv",
            )
        if self.import_type == "accounts_individual":
            return rx.download(
                data=_ACCOUNT_INDIVIDUAL_TEMPLATE.encode("utf-8"),
                filename="accounts_individual_import_template.csv",
            )
        if self.import_type == "exam_types":
            return rx.download(
                data=_EXAM_TYPE_TEMPLATE.encode("utf-8"),
                filename="examens_referentiel_import_template.csv",
            )
        return rx.download(
            data=_ACCOUNT_COMPANY_TEMPLATE.encode("utf-8"),
            filename="accounts_company_import_template.csv",
        )

    @rx.event
    async def handle_csv_upload(self, files: list[rx.UploadFile]):
        """Parse an uploaded CSV file and populate the preview table."""
        self._reset_import()
        self.is_parsing = True
        yield

        try:
            raw_bytes = b""
            for file in files:
                raw_bytes = await file.read()

            try:
                content = raw_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                self.parse_error = (
                    "Impossible de lire le fichier. Veuillez l'enregistrer en UTF-8 CSV."
                )
                return

            from gws_care.core.bulk_import_service import BulkImportService

            if self.import_type == "patients":
                parse_result = BulkImportService.parse_patients_csv(content)
            elif self.import_type == "doctors":
                parse_result = BulkImportService.parse_doctors_csv(content)
            elif self.import_type == "accounts_individual":
                parse_result = BulkImportService.parse_accounts_individual_csv(content)
            elif self.import_type == "exam_types":
                parse_result = BulkImportService.parse_exam_types_csv(content)
            else:
                parse_result = BulkImportService.parse_accounts_csv(content)

            if parse_result.parse_error:
                self.parse_error = parse_result.parse_error
                return

            self._raw_rows = [r.row_data for r in parse_result.rows]
            if self.import_type == "patients":
                self.preview_headers = ["#", "Nom", "Prénom", "Date naissance", "Genre", "Statut"]
            elif self.import_type == "doctors":
                self.preview_headers = ["#", "Nom", "Prénom", "Spécialisation", "Statut"]
            elif self.import_type == "accounts_individual":
                self.preview_headers = ["#", "Nom", "Prénom", "Ville", "Téléphone", "Statut"]
            elif self.import_type == "exam_types":
                self.preview_headers = ["#", "Examen", "Catégorie", "Paramètre", "Statut"]
            else:
                self.preview_headers = [
                    "#",
                    "Nom entreprise",
                    "Contact",
                    "Ville",
                    "Téléphone",
                    "Statut",
                ]
            self.preview_rows = self._build_preview_rows(parse_result)
        except Exception as e:
            self.parse_error = f"Erreur de lecture : {e}"
        finally:
            self.is_parsing = False

    @rx.event
    async def start_import(self):
        """Import all valid (pending) rows into the database."""
        if self.is_importing or self.import_done:
            return

        self.is_importing = True
        self.success_count = 0
        self.error_count = 0
        yield

        rows = list(self._raw_rows)
        updated_rows = list(self.preview_rows)
        success = 0
        errors = 0

        try:
            with await self.authenticate_user():
                from gws_care.user.user import User

                if User.select().count() == 0:
                    self.parse_error = (
                        "⚠ La table des utilisateurs locaux est vide — "
                        "le serveur n'a pas encore synchronisé les utilisateurs Constellab. "
                        "Veuillez redémarrer l'application et réessayer."
                    )
                    self.is_importing = False
                    return

                from gws_care.core.bulk_import_service import BulkImportService

                for i, row_data in enumerate(rows):
                    if updated_rows[i].status != "pending":
                        continue
                    try:
                        if self.import_type == "patients":
                            BulkImportService.import_patient_row(row_data)
                        elif self.import_type == "doctors":
                            BulkImportService.import_doctor_row(row_data)
                        elif self.import_type == "accounts_individual":
                            BulkImportService.import_individual_account_row(row_data)
                        elif self.import_type == "exam_types":
                            BulkImportService.import_exam_type_row(row_data)
                        else:
                            BulkImportService.import_account_row(row_data)

                        # Update cells: replace the status cell (last one) with "✓ Imported"
                        new_cells = list(updated_rows[i].cells)
                        new_cells[-1] = "✓ Imported"
                        updated_rows[i] = ImportRowResultDTO(
                            row_num=updated_rows[i].row_num,
                            cells=new_cells,
                            status="success",
                            message="",
                        )
                        success += 1
                    except Exception as e:
                        new_cells = list(updated_rows[i].cells)
                        new_cells[-1] = f"⚠ {e}"
                        updated_rows[i] = ImportRowResultDTO(
                            row_num=updated_rows[i].row_num,
                            cells=new_cells,
                            status="error",
                            message=str(e),
                        )
                        errors += 1

        except Exception as e:
            self.parse_error = f"Erreur d'authentification ou de base de données : {e}"

        self.preview_rows = updated_rows
        self.success_count = success
        self.error_count = errors
        self.import_done = True
        self.is_importing = False

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _reset_import(self) -> None:
        self._raw_rows = []
        self.preview_rows = []
        self.preview_headers = []
        self.parse_error = ""
        self.import_done = False
        self.success_count = 0
        self.error_count = 0

    def _build_preview_rows(self, parse_result) -> list[ImportRowResultDTO]:
        """Convert BulkImportService parse results into frontend DTOs."""
        from gws_care.core.bulk_import_service import CsvParseResult

        results: list[ImportRowResultDTO] = []
        for r in parse_result.rows:
            status_text = ("⚠ " + "; ".join(r.errors)) if r.errors else "Ready"
            if self.import_type == "patients":
                gender = r.row_data.get("gender", "").strip()
                cells = [
                    str(r.row_num),
                    r.row_data.get("last_name", ""),
                    r.row_data.get("first_name", ""),
                    r.row_data.get("date_of_birth", ""),
                    gender,
                    status_text,
                ]
            elif self.import_type == "doctors":
                cells = [
                    str(r.row_num),
                    r.row_data.get("last_name", ""),
                    r.row_data.get("first_name", ""),
                    r.row_data.get("specialization", ""),
                    status_text,
                ]
            elif self.import_type == "accounts_individual":
                cells = [
                    str(r.row_num),
                    r.row_data.get("contact_last_name", ""),
                    r.row_data.get("contact_first_name", ""),
                    r.row_data.get("city", ""),
                    r.row_data.get("phone", ""),
                    status_text,
                ]
            elif self.import_type == "exam_types":
                cells = [
                    str(r.row_num),
                    r.row_data.get("exam_type", ""),
                    r.row_data.get("category", ""),
                    r.row_data.get("parameter", "") or "—",
                    status_text,
                ]
            else:
                first = r.row_data.get("contact_first_name", "").strip()
                last = r.row_data.get("contact_last_name", "").strip()
                contact = f"{first} {last}".strip() or "—"
                cells = [
                    str(r.row_num),
                    r.row_data.get("name", ""),
                    contact,
                    r.row_data.get("city", ""),
                    r.row_data.get("phone", ""),
                    status_text,
                ]
            results.append(
                ImportRowResultDTO(
                    row_num=r.row_num,
                    cells=cells,
                    status="error" if r.errors else "pending",
                    message="; ".join(r.errors),
                )
            )
        return results
