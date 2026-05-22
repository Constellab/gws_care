"""State for bulk CSV import of patients and accounts from the Admin page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel

_PATIENT_TEMPLATE = (
    "last_name,first_name,birth_name,date_of_birth,gender,"
    "address,postal_code,city,phone,email,"
    "primary_physician_name,primary_physician_phone,"
    "account_name,social_security_number,weight,height\n"
    # ── SGBCI (28 patients) ──────────────────────────────────────────────────
    "KONÉ,Aminata,,1990-04-12,F,12 Rue des Jardins,,Abidjan,+2250701000001,aminata.kone@email.ci,Dr. Bamba,+2250720000001,SGBCI,1900412CI001,62.5,165\n"
    "COULIBALY,Ibrahim,,1985-07-23,M,Cocody Ambassades,,Abidjan,+2250701000002,ibrahim.coulibaly@email.ci,,,SGBCI,1850723CI002,,178\n"
    "DIALLO,Fatou,,1993-11-05,F,Plateau Immeuble Nour,,Abidjan,+2250701000003,fatou.diallo@email.ci,,,SGBCI,1931105CI003,58,162\n"
    "YAO,Kouassi,,1978-02-14,M,Yopougon Selmer,,Abidjan,+2250701000004,kouassi.yao@email.ci,,,SGBCI,1780214CI004,,172\n"
    "BAMBA,Mariam,,1996-09-30,F,Abobo Nord,,Abidjan,+2250701000005,mariam.bamba@email.ci,Dr. Koné,+2250721000001,SGBCI,1960930CI005,70.2,168\n"
    "TRAORÉ,Moussa,,1988-06-18,M,Treichville Rue 12,,Abidjan,+2250701000006,moussa.traore@email.ci,,,SGBCI,1880618CI006,,176\n"
    "OUÉDRAOGO,Salimata,,1991-03-25,F,Riviera Palmeraie,,Abidjan,+2250701000007,salimata.ouedraogo@email.ci,,,SGBCI,1910325CI007,55,160\n"
    "SANOGO,Drissa,,1974-08-12,M,Marcory Zone 4,,Abidjan,+2250701000008,drissa.sanogo@email.ci,,,SGBCI,1740812CI008,,175\n"
    "FOFANA,Karidiatou,,1999-01-07,F,Adjamé Liberty,,Abidjan,+2250701000009,karidiatou.fofana@email.ci,,,SGBCI,1990107CI009,59,163\n"
    "TOURÉ,Adama,,1983-05-19,M,Deux Plateaux,,Abidjan,+2250701000010,adama.toure@email.ci,,,SGBCI,1830519CI010,,173\n"
    "N'DRI,Evelyne,,1992-10-28,F,Cocody II Plateaux,,Abidjan,+2250701000011,evelyne.ndri@email.ci,,,SGBCI,1921028CI011,64,167\n"
    "AKISSI,Bernadette,,1970-12-03,F,Yopougon Niangon Sud,,Abidjan,+2250701000012,bernadette.akissi@email.ci,Dr. Diallo,+2250721000002,SGBCI,1701203CI012,72,170\n"
    "GUEI,Martin,,1986-04-17,M,Port-Bouët Aéroport,,Abidjan,+2250701000013,martin.guei@email.ci,,,SGBCI,1860417CI013,,177\n"
    "ASSI,Rosalie,,1994-07-31,F,Plateau Centre,,Abidjan,+2250701000014,rosalie.assi@email.ci,,,SGBCI,1940731CI014,57,161\n"
    "YAPI,Serge,,1980-11-22,M,Koumassi Remblais,,Abidjan,+2250701000015,serge.yapi@email.ci,,,SGBCI,1801122CI015,,174\n"
    "AKA,Ghislaine,,1997-06-14,F,Treichville Avr. 14,,Abidjan,+2250701000016,ghislaine.aka@email.ci,,,SGBCI,1970614CI016,61,164\n"
    "MÉITÉ,Lamine,,1975-09-08,M,Abobo Dokui,,Abidjan,+2250701000017,lamine.meite@email.ci,,,SGBCI,1750908CI017,,171\n"
    "DOUMBIA,Nathalie,,1989-02-26,F,Riviera 3,,Abidjan,+2250701000018,nathalie.doumbia@email.ci,,,SGBCI,1890226CI018,66,166\n"
    "KOFFI,Raymond,,1967-05-30,M,Cocody Bergerville,,Abidjan,+2250701000019,raymond.koffi@email.ci,,,SGBCI,1670530CI019,,180\n"
    "N'GUESSAN,Esther,,1998-08-15,F,Yopougon Selmer,,Abidjan,+2250701000020,esther.nguessan@email.ci,,,SGBCI,1980815CI020,53,158\n"
    "KPAN,Barthélemy,,1971-11-04,M,Vridi Résidentiel,,Abidjan,+2250701000021,barthelemy.kpan@email.ci,,,SGBCI,1711104CI021,,168\n"
    "KOUAKOU,Chantal,,1985-03-11,F,Marcory Biétry,,Abidjan,+2250701000022,chantal.kouakou@email.ci,Dr. Touré,+2250721000003,SGBCI,1850311CI022,68,169\n"
    "SILUÉ,Tidiane,,1979-07-25,M,Abobo Baoulé,,Abidjan,+2250701000023,tidiane.silue@email.ci,,,SGBCI,1790725CI023,,179\n"
    "KABORÉ,Aminata,,1995-12-09,F,Cocody Angré,,Abidjan,+2250701000024,aminata.kabore@email.ci,,,SGBCI,1951209CI024,60,162\n"
    "TAPÉ,Honoré,,1963-04-20,M,Adjamé Washington,,Abidjan,+2250701000025,honore.tape@email.ci,,,SGBCI,1630420CI025,,176\n"
    "EHUI,Patricia,,1988-09-03,F,Plateau Avenues,,Abidjan,+2250701000026,patricia.ehui@email.ci,,,SGBCI,1880903CI026,63,165\n"
    "AHOURÉ,Sébastien,,1992-01-16,M,Riviera Faya,,Abidjan,+2250701000027,sebastien.ahoure@email.ci,,,SGBCI,1920116CI027,,182\n"
    "BOGUI,Valérie,,1976-06-22,F,Yopougon Mossikro,,Abidjan,+2250701000028,valerie.bogui@email.ci,,,SGBCI,1760622CI028,71,172\n"
    # ── BNPPARIBAS (10 patients) ─────────────────────────────────────────────
    "DUBOIS,Claire,,1991-03-07,F,Tour BIAO Plateau,,Abidjan,+2250701000029,claire.dubois@email.ci,,,BNPPARIBAS,1910307FR001,54,160\n"
    "MARTIN,Théodore,,1983-08-25,M,Cocody Danga,,Abidjan,+2250701000030,theodore.martin@email.ci,,,BNPPARIBAS,1830825FR002,,180\n"
    "BERNARD,Sophie,LEROY,1987-12-19,F,Riviera 2,,Abidjan,+2250701000031,sophie.bernard@email.ci,Dr. Laurent,+2250721000004,BNPPARIBAS,1871219FR003,66,170\n"
    "NGUYEN,Patrick,,1979-05-03,M,Deux Plateaux Roses,,Abidjan,+2250701000032,patrick.nguyen@email.ci,,,BNPPARIBAS,1790503FR004,,174\n"
    "LAURENT,Isabelle,,1994-10-11,F,Zone Industrielle,,Abidjan,+2250701000033,isabelle.laurent@email.ci,,,BNPPARIBAS,1941011FR005,60,163\n"
    "MOREAU,Julien,,1982-02-14,M,Marcory Sicogi,,Abidjan,+2250701000034,julien.moreau@email.ci,,,BNPPARIBAS,1820214FR006,,181\n"
    "PETIT,Aurélie,,1996-07-22,F,Plateau Immeuble Alliance,,Abidjan,+2250701000035,aurelie.petit@email.ci,,,BNPPARIBAS,1960722FR007,58,162\n"
    "LEROY,Christophe,,1977-11-08,M,Cocody Danga Faya,,Abidjan,+2250701000036,christophe.leroy@email.ci,,,BNPPARIBAS,1771108FR008,,178\n"
    "CHEVALIER,Marie,,1990-04-30,F,Riviera Golf,,Abidjan,+2250701000037,marie.chevalier@email.ci,,,BNPPARIBAS,1900430FR009,65,168\n"
    "BONNET,Éric,,1985-09-17,M,Treichville Zone 3,,Abidjan,+2250701000038,eric.bonnet@email.ci,,,BNPPARIBAS,1850917FR010,,176\n"
    # ── Total Energies CI (7 patients) ───────────────────────────────────────
    "ADJOUMANI,Serge,,1981-01-28,M,Port-Bouët Koumassi,,Abidjan,+2250701000039,serge.adjoumani@email.ci,,,Total Energies CI,1810128CI029,,171\n"
    "SORO,Dramane,,1976-09-02,M,Vridi Raffinerie,,Abidjan,+2250701000040,dramane.soro@email.ci,Dr. Diomandé,+2250721000005,Total Energies CI,1760902CI030,,169\n"
    "OUATTARA,Rachelle,,1989-04-22,F,Vridi Cité Pétrolière,,Abidjan,+2250701000041,rachelle.ouattara@email.ci,,,Total Energies CI,1890422CI031,72,167\n"
    "DEMBÉLÉ,Cheick,,1982-11-17,M,Vridi Zone Industrielle,,Abidjan,+2250701000042,cheick.dembele@email.ci,,,Total Energies CI,1821117CI032,,175\n"
    "KONAN,Adèle,,1993-08-05,F,Port-Bouët Résidentiel,,Abidjan,+2250701000043,adele.konan@email.ci,,,Total Energies CI,1930805CI033,61,165\n"
    "KADER,Moustapha,,1969-12-31,M,Treichville Avr. 7,,Abidjan,+2250701000044,moustapha.kader@email.ci,,,Total Energies CI,1691231CI034,,174\n"
    "N'GORAN,Estelle,,1995-03-18,F,Koumassi Campement,,Abidjan,+2250701000045,estelle.ngoran@email.ci,,,Total Energies CI,1950318CI035,57,161\n"
    # ── Petroci (8 patients) ─────────────────────────────────────────────────
    "DIGBEU,Casimir,,1974-03-14,M,Vridi Raffinerie Résid.,,Abidjan,+2250701000046,casimir.digbeu@email.ci,,,Petroci,1740314CI036,,170\n"
    "KOUAMÉ,Virginie,,1990-07-28,F,Plateau Immeuble Petroci,,Abidjan,+2250701000047,virginie.kouame@email.ci,,,Petroci,1900728CI037,64,166\n"
    "ASSOA,Hilaire,,1978-10-05,M,Zone Industrielle Vridi,,Abidjan,+2250701000048,hilaire.assoa@email.ci,,,Petroci,1781005CI038,,173\n"
    "BODJO,Albertine,,1986-01-19,F,Port-Bouët Aéroport Sud,,Abidjan,+2250701000049,albertine.bodjo@email.ci,Dr. Yao,+2250721000006,Petroci,1860119CI039,67,168\n"
    "AGBOU,Théophile,,1962-05-07,M,Koumassi Remblais,,Abidjan,+2250701000050,theophile.agbou@email.ci,,,Petroci,1620507CI040,,169\n"
    "KOHOU,Delphine,,1997-09-23,F,Vridi Canal,,Abidjan,+2250701000051,delphine.kohou@email.ci,,,Petroci,1970923CI041,55,159\n"
    "AMON,Léon,,1983-12-11,M,Zone Industrielle CI,,Abidjan,+2250701000052,leon.amon@email.ci,,,Petroci,1831211CI042,,176\n"
    "ABOA,Christine,,1991-04-16,F,Treichville Résid.,,Abidjan,+2250701000053,christine.aboa@email.ci,,,Petroci,1910416CI043,62,164\n"
    # ── AXA Côte d'Ivoire (5 patients) ───────────────────────────────────────
    "DURAND,Maxime,,1997-08-08,M,Cocody II Plateaux,,Abidjan,+2250701000054,maxime.durand@email.ci,,,AXA Côte d'Ivoire,1970808FR011,,183\n"
    "KONATÉ,Aïcha,,1992-02-26,F,Adjamé Liberty,,Abidjan,+2250701000055,aicha.konate@email.ci,,,AXA Côte d'Ivoire,1920226CI044,63,164\n"
    "LEPAGE,François,,1975-07-31,M,Marcory Résidentiel,,Abidjan,+2250701000056,francois.lepage@email.ci,,,AXA Côte d'Ivoire,1750731FR012,,177\n"
    "RENARD,Lucie,,1988-11-14,F,Riviera 3 Villa,,Abidjan,+2250701000057,lucie.renard@email.ci,,,AXA Côte d'Ivoire,1881114FR013,59,162\n"
    "BRETON,Pascal,,1971-03-27,M,Plateau Centre,,Abidjan,+2250701000058,pascal.breton@email.ci,,,AXA Côte d'Ivoire,1710327FR014,,179\n"
    # ── Sofitel Hôtel Ivoire (3 patients) ────────────────────────────────────
    "GIRARD,Hélène,,1985-05-06,F,Cocody Ambassades,,Abidjan,+2250701000059,helene.girard@email.ci,,,Sofitel Hôtel Ivoire,1850506FR015,65,167\n"
    "MARCHAND,Rémi,,1993-09-20,M,Riviera Palmeraie,,Abidjan,+2250701000060,remi.marchand@email.ci,,,Sofitel Hôtel Ivoire,1930920FR016,,181\n"
    "FABRE,Nathalie,,1979-01-13,F,Cocody Danga,,Abidjan,+2250701000061,nathalie.fabre@email.ci,,,Sofitel Hôtel Ivoire,1790113FR017,70,171\n"
    # ── Orange CI (2 patients) ───────────────────────────────────────────────
    "TANOH,Alphonse,,1987-06-09,M,Abobo Baoulé,,Abidjan,+2250701000062,alphonse.tanoh@email.ci,,,Orange CI,1870609CI045,,172\n"
    "GOHI,Estelle,,1994-02-17,F,Yopougon Mossikro,,Abidjan,+2250701000063,estelle.gohi@email.ci,,,Orange CI,1940217CI046,57,160\n"
    # ── MTN CI (2 patients) ──────────────────────────────────────────────────
    "KOUADIO,Denis,,1969-10-25,M,Marcory Zone 4,,Abidjan,+2250701000064,denis.kouadio@email.ci,,,MTN CI,1691025CI047,,168\n"
    "AKPA,Sandrine,,1998-05-04,F,Adjamé 220 Logts,,Abidjan,+2250701000065,sandrine.akpa@email.ci,,,MTN CI,1980504CI048,56,159\n"
    # ── No account (5 patients) ──────────────────────────────────────────────
    "CISSÉ,Karidjatou,,1986-08-21,F,Cocody Angré Star,,Abidjan,+2250701000066,karidjatou.cisse@email.ci,,,,1860821CI049,64,165\n"
    "DIABATÉ,Moussa,,1972-11-15,M,Abobo Dokui,,Abidjan,+2250701000067,moussa.diabate@email.ci,,,,1721115CI050,,176\n"
    "THOMAS,Nathalie,,1994-04-08,F,Marcory Biétry,,Abidjan,+2250701000068,nathalie.thomas@email.ci,,,,1940408FR018,61,163\n"
    "LAMBERT,Henri,,1980-07-19,M,Plateau Clozel,,Abidjan,+2250701000069,henri.lambert@email.ci,,,,1800719FR019,,180\n"
    "SÉKA,Patricia,,1991-12-03,F,Riviera 2 Rue Jardins,,Abidjan,+2250701000070,patricia.seka@email.ci,,,,1911203CI051,58,161\n"
)

_ACCOUNT_TEMPLATE = (
    "name,registration_number,address,postal_code,city,phone,email,contact_name\n"
    "SGBCI,CI-ABJ-2001-B-1234,Avenue Terrasson de Fougères,BP 1355,Abidjan,+2252021234567,contact@sgbci.ci,M. Koné\n"
    "BNPPARIBAS,CI-ABJ-2003-B-5678,Immeuble Alliance Plateau,BP 4001,Abidjan,+2252025678901,ci@bnpparibas.com,Mme. Dupont\n"
    "Total Energies CI,CI-ABJ-1999-B-2222,Zone Industrielle de Vridi,BP 1234,Abidjan,+2252022222222,totalenergies.ci@te.com,M. Coulibaly\n"
    "Petroci,CI-ABJ-1975-B-0001,Plateau Immeuble Petroci,BP 695,Abidjan,+2252020000001,info@petroci.ci,M. Yao\n"
    "AXA Côte d'Ivoire,CI-ABJ-2005-B-3344,Immeuble CRRAE-UMOA Plateau,BP 4400,Abidjan,+2252024440033,axa.ci@axa.com,M. Diallo\n"
    "Sofitel Hôtel Ivoire,CI-ABJ-1963-B-0088,Boulevard de la Corniche,BP 1088,Abidjan,+2252023338800,hi@sofitel-ivoire.ci,Mme. Martin\n"
    "Orange CI,CI-ABJ-2002-B-4455,Immeuble Orange 5e étage,BP 4100,Abidjan,+2252027000000,contact@orange.ci,Mme. N'Guessan\n"
    "MTN CI,CI-ABJ-2001-B-5566,Immeuble MTN Zone 4,BP 1600,Abidjan,+2252020100100,mtn.ci@mtn.com,M. Sanogo\n"
    "BICICI,CI-ABJ-1962-B-0002,Plateau Avenue Botreau Roussel,BP 1298,Abidjan,+2252022090090,contact@bicici.ci,M. Assoa\n"
    "Ecobank CI,CI-ABJ-1988-B-2233,Immeuble Ecobank Plateau,BP 4107,Abidjan,+2252022100100,ecobank.ci@ecobank.com,Mme. Touré\n"
    "Unilever CI,CI-ABJ-1965-B-0003,Zone Industrielle Yopougon,BP 179,Abidjan,+2252023600000,unilever.ci@unilever.com,M. Traoré\n"
    "Air Côte d'Ivoire,CI-ABJ-2012-B-7788,Aéroport Félix Houphouët-Boigny,BP 12500,Abidjan,+2252027020200,contact@aircotedivoire.ci,M. Kader\n"
    "CIE,CI-ABJ-1991-B-3300,18 Avenue Christiani,BP 1345,Abidjan,+2252024440044,cie@cie.ci,M. Koffi\n"
    "SODECI,CI-ABJ-1960-B-0004,1 Avenue Christiani,BP 1843,Abidjan,+2252024430000,sodeci@sodeci.ci,Mme. Akissi\n"
    "CFAO Côte d'Ivoire,CI-ABJ-1950-B-0005,Zone Industrielle Vridi,BP 101,Abidjan,+2252023750000,cfao.ci@cfao.com,M. Guei\n"
    "Nestlé CI,CI-ABJ-1959-B-0006,Zone Industrielle Yopougon Ext.,BP 1025,Abidjan,+2252023730000,nestle.ci@nestle.com,Mme. Bogui\n"
    "SODEFOR,CI-ABJ-1966-B-0007,Riviera 3 Cité SIR,BP 3770,Abidjan,+2252022490000,sodefor@sodefor.ci,M. Tapé\n"
    "STIE,CI-ABJ-1974-B-0008,Zone Industrielle de Yopougon,BP 8050,Abidjan,+2252023690000,stie@stie.ci,M. Digbeu\n"
    "SIFCA,CI-ABJ-1964-B-0009,Immeuble SIFCA Plateau,BP 1289,Abidjan,+2252022240000,sifca@sifca.ci,Mme. Ehui\n"
    "Versus Bank,CI-ABJ-2001-B-9900,Immeuble VERSUS Avenue Houdaille,BP 1315,Abidjan,+2252022250000,versus@versusbank.ci,M. Silué\n"
    "Bridge Bank CI,CI-ABJ-2011-B-8811,Plateau Rue du Commerce,BP 4050,Abidjan,+2252022260000,bridge@bridgebank.ci,Mme. Aboa\n"
    "SITAB,CI-ABJ-1954-B-0010,Zone Industrielle Adjamé,BP 1832,Abidjan,+2252024790000,sitab@sitab.ci,M. Amon\n"
    "Pharmacie Centrale CI,CI-ABJ-1960-B-0011,Plateau Rue Lepic,BP 2095,Abidjan,+2252022270000,pharmaCI@pharmacie.ci,Mme. Doumbia\n"
    "CHU de Cocody,CI-ABJ-1970-B-0012,Boulevard de la Corniche Cocody,BP 23,Abidjan,+2252022444000,chu.cocody@sante.ci,M. Yapi\n"
    "SIC CACAO,CI-ABJ-1978-B-1313,Zone Industrielle de Vridi Nord,BP 1393,Abidjan,+2252023460000,contact@siccacao.ci,M. Méité\n"
)


# ── DTOs ─────────────────────────────────────────────────────────────────────

class ImportRowResultDTO(BaseModel):
    """Represents one CSV row with its parsed display values and import result."""

    row_num: int
    cells: list[str]       # display values: [row_num, field1, ..., status_text]
    status: str = "pending"    # "pending" | "error" | "success"
    message: str = ""


# ── State ─────────────────────────────────────────────────────────────────────

class ImportState(ReflexMainState):
    """State for the bulk CSV import dialogs on the Admin page."""

    import_dialog_open: bool = False
    import_type: str = ""        # "patients" | "accounts"

    _raw_rows: list[dict] = []   # private — raw dicts parsed from CSV, parallel to preview_rows

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
        return rx.download(
            data=_ACCOUNT_TEMPLATE.encode("utf-8"),
            filename="accounts_import_template.csv",
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
                self.parse_error = "Impossible de lire le fichier. Veuillez l'enregistrer en UTF-8 CSV."
                return

            from gws_care.core.bulk_import_service import BulkImportService
            if self.import_type == "patients":
                parse_result = BulkImportService.parse_patients_csv(content)
            else:
                parse_result = BulkImportService.parse_accounts_csv(content)

            if parse_result.parse_error:
                self.parse_error = parse_result.parse_error
                return

            self._raw_rows = [r.row_data for r in parse_result.rows]
            self.preview_headers = (
                ["#", "Last Name", "First Name", "Date of Birth", "Gender", "Status"]
                if self.import_type == "patients"
                else ["#", "Name", "City", "Phone", "Status"]
            )
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
                from gws_care.core.bulk_import_service import BulkImportService
                for i, row_data in enumerate(rows):
                    if updated_rows[i].status != "pending":
                        continue
                    try:
                        if self.import_type == "patients":
                            BulkImportService.import_patient_row(row_data)
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
            else:
                cells = [
                    str(r.row_num),
                    r.row_data.get("name", ""),
                    r.row_data.get("city", ""),
                    r.row_data.get("phone", ""),
                    status_text,
                ]
            results.append(ImportRowResultDTO(
                row_num=r.row_num,
                cells=cells,
                status="error" if r.errors else "pending",
                message="; ".join(r.errors),
            ))
        return results
