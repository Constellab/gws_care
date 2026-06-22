"""Unit tests for BulkImportService — CSV parsing, validation and DB insertion."""

import re
from datetime import date, timedelta

from gws_care.account.account import Account
from gws_care.account.account_dto import SaveAccountDTO
from gws_care.account.account_service import AccountService
from gws_care.core.bulk_import_service import BulkImportService, CsvParseResult
from gws_care.patient.patient import Patient
from gws_care.patient.patient_service import PatientService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_core import BadRequestException, BaseTestCase, UserGroup

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_patient_csv(*rows: str) -> str:
    header = (
        "last_name,first_name,birth_name,date_of_birth,gender,"
        "address,postal_code,city,phone,email,"
        "primary_physician_name,primary_physician_phone,account_name"
    )
    return "\n".join([header] + list(rows))


def _make_account_csv(*rows: str) -> str:
    header = "name,registration_number,address,postal_code,city,phone,email,contact_name"
    return "\n".join([header] + list(rows))


# ── Test class ────────────────────────────────────────────────────────────────

class TestBulkImportService(BaseTestCase):
    """Tests for BulkImportService.

    Covers:
      - CSV parsing (valid, empty, missing columns, BOM)
      - Patient row validation (required fields, date format, gender values)
      - Account row validation (required name)
      - DB insertion of patients and accounts
      - Optional account-name resolution on patient import
      - Duplicate / overlapping CSV content
    """

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        # Sync gws_core users into the local care user table so DB FK constraints resolve
        CareUserSyncService().sync_all_users()

    # ── Patient CSV parsing ───────────────────────────────────────────────────

    def test_parse_patients_csv_valid(self):
        """All required fields present → result has no parse_error and one valid row."""
        csv = _make_patient_csv(
            "DUPONT,Jean,,1985-03-15,M,12 rue de la Paix,75001,Paris,0612345678,,,"
        )
        result = BulkImportService.parse_patients_csv(csv)

        self.assertEqual(result.parse_error, "")
        self.assertEqual(len(result.rows), 1)
        self.assertTrue(result.rows[0].is_valid)
        self.assertEqual(result.rows[0].errors, [])

    def test_parse_patients_csv_multiple_valid_rows(self):
        """Two valid rows → both marked valid."""
        csv = _make_patient_csv(
            "DUPONT,Jean,,1985-03-15,M,,,,,,,",
            "MARTIN,Sophie,LECLERC,1992-07-22,F,,,,,,,",
        )
        result = BulkImportService.parse_patients_csv(csv)

        self.assertEqual(result.parse_error, "")
        self.assertEqual(len(result.valid_rows), 2)
        self.assertEqual(len(result.invalid_rows), 0)

    def test_parse_patients_csv_empty(self):
        """Header-only CSV → parse_error set, no rows."""
        csv = "last_name,first_name,birth_name,date_of_birth,gender"
        result = BulkImportService.parse_patients_csv(csv)

        self.assertNotEqual(result.parse_error, "")
        self.assertEqual(len(result.rows), 0)

    def test_parse_patients_csv_missing_required_column(self):
        """CSV missing 'gender' column → parse_error mentions it."""
        csv = "last_name,first_name,date_of_birth\nDUPONT,Jean,1985-03-15"
        result = BulkImportService.parse_patients_csv(csv)

        self.assertIn("gender", result.parse_error)

    def test_parse_patients_csv_bom(self):
        """CSV with UTF-8 BOM is parsed correctly."""
        csv = "\ufefflast_name,first_name,birth_name,date_of_birth,gender\nDUPONT,Jean,,1985-03-15,M"
        result = BulkImportService.parse_patients_csv(csv)

        self.assertEqual(result.parse_error, "")
        self.assertEqual(len(result.rows), 1)
        self.assertTrue(result.rows[0].is_valid)

    # ── Patient row validation ────────────────────────────────────────────────

    def test_patient_row_missing_last_name(self):
        csv = _make_patient_csv(",Jean,,1985-03-15,M,,,,,,,")
        result = BulkImportService.parse_patients_csv(csv)

        self.assertFalse(result.rows[0].is_valid)
        self.assertIn("last_name required", result.rows[0].errors)

    def test_patient_row_missing_first_name(self):
        csv = _make_patient_csv("DUPONT,,,1985-03-15,M,,,,,,,")
        result = BulkImportService.parse_patients_csv(csv)

        self.assertFalse(result.rows[0].is_valid)
        self.assertIn("first_name required", result.rows[0].errors)

    def test_patient_row_missing_date_of_birth(self):
        csv = _make_patient_csv("DUPONT,Jean,,,M,,,,,,,")
        result = BulkImportService.parse_patients_csv(csv)

        self.assertFalse(result.rows[0].is_valid)
        self.assertIn("date_of_birth required", result.rows[0].errors)

    def test_patient_row_invalid_date_format(self):
        """Date given as DD/MM/YYYY instead of YYYY-MM-DD → validation error."""
        csv = _make_patient_csv("DUPONT,Jean,,15/03/1985,M,,,,,,,")
        result = BulkImportService.parse_patients_csv(csv)

        self.assertFalse(result.rows[0].is_valid)
        self.assertIn("date_of_birth must be YYYY-MM-DD", result.rows[0].errors)

    def test_patient_row_invalid_gender(self):
        """Gender value 'male' is not in allowed set → validation error."""
        csv = _make_patient_csv("DUPONT,Jean,,1985-03-15,male,,,,,,,")
        result = BulkImportService.parse_patients_csv(csv)

        self.assertFalse(result.rows[0].is_valid)
        self.assertIn("gender must be M, F or Other", result.rows[0].errors)

    def test_patient_row_gender_other_valid(self):
        """Gender value 'Other' is accepted."""
        csv = _make_patient_csv("DUPONT,Jean,,1985-03-15,Other,,,,,,,")
        result = BulkImportService.parse_patients_csv(csv)

        self.assertTrue(result.rows[0].is_valid)

    def test_patient_row_multiple_errors_collected(self):
        """Missing last_name and invalid date both reported on the same row."""
        csv = _make_patient_csv(",Jean,,not-a-date,M,,,,,,,")
        result = BulkImportService.parse_patients_csv(csv)

        self.assertFalse(result.rows[0].is_valid)
        self.assertEqual(len(result.rows[0].errors), 2)

    def test_mixed_valid_and_invalid_rows(self):
        """One valid row + one invalid row → valid/invalid counts are correct."""
        csv = _make_patient_csv(
            "DUPONT,Jean,,1985-03-15,M,,,,,,,",   # valid
            ",Jean,,1985-03-15,M,,,,,,,",          # invalid (no last_name)
        )
        result = BulkImportService.parse_patients_csv(csv)

        self.assertEqual(len(result.valid_rows), 1)
        self.assertEqual(len(result.invalid_rows), 1)

    # ── Account CSV parsing ───────────────────────────────────────────────────

    def test_parse_accounts_csv_valid(self):
        """Valid account row with all optional fields."""
        csv = _make_account_csv(
            "Entreprise XYZ,123456789,15 avenue,75008,Paris,0123456789,contact@xyz.com,M. Dupont"
        )
        result = BulkImportService.parse_accounts_csv(csv)

        self.assertEqual(result.parse_error, "")
        self.assertEqual(len(result.rows), 1)
        self.assertTrue(result.rows[0].is_valid)

    def test_parse_accounts_csv_name_only(self):
        """Minimal account: only name column filled."""
        csv = "name\nMA Société"
        result = BulkImportService.parse_accounts_csv(csv)

        self.assertEqual(result.parse_error, "")
        self.assertTrue(result.rows[0].is_valid)

    def test_parse_accounts_csv_missing_name_column(self):
        """CSV without a 'name' column → parse_error."""
        csv = "city,phone\nParis,0123456789"
        result = BulkImportService.parse_accounts_csv(csv)

        self.assertIn("name", result.parse_error)

    def test_parse_accounts_csv_empty_name_value(self):
        """Name column present but blank → row validation error."""
        csv = _make_account_csv(",,,,,,,")
        result = BulkImportService.parse_accounts_csv(csv)

        self.assertFalse(result.rows[0].is_valid)
        self.assertIn("name required", result.rows[0].errors)

    def test_parse_accounts_csv_empty_file(self):
        """Header only → parse_error."""
        csv = "name,city"
        result = BulkImportService.parse_accounts_csv(csv)

        self.assertNotEqual(result.parse_error, "")

    # ── DB insertion — patients ───────────────────────────────────────────────

    def test_import_patient_row_creates_patient(self):
        """import_patient_row correctly persists a patient to the DB."""
        row = {
            "last_name": "IMPORT",
            "first_name": "Test",
            "birth_name": "",
            "date_of_birth": "1990-06-01",
            "gender": "M",
            "address": "1 rue Test",
            "postal_code": "75000",
            "city": "Paris",
            "phone": "0600000001",
            "email": "import@test.com",
            "primary_physician_name": "",
            "primary_physician_phone": "",
            "account_name": "",
        }

        BulkImportService.import_patient_row(row)

        created = Patient.get_or_none(Patient.last_name == "IMPORT")
        self.assertIsNotNone(created)
        self.assertEqual(created.first_name, "Test")
        self.assertEqual(created.date_of_birth, date(1990, 6, 1))
        self.assertEqual(created.gender, "M")
        self.assertEqual(created.city, "Paris")
        from gws_care.patient.patient_account import PatientAccount
        self.assertEqual(PatientAccount.select().where(PatientAccount.patient == created.id).count(), 0)

    def test_import_patient_row_links_account_by_name(self):
        """When account_name matches an existing account, the patient is linked."""
        account = AccountService.create_account(
            SaveAccountDTO(name="Société Test Import")
        )

        row = {
            "last_name": "LINKED",
            "first_name": "Patient",
            "birth_name": "",
            "date_of_birth": "1988-01-15",
            "gender": "F",
            "address": "",
            "postal_code": "",
            "city": "",
            "phone": "",
            "email": "",
            "primary_physician_name": "",
            "primary_physician_phone": "",
            "account_name": "Société Test Import",
        }

        BulkImportService.import_patient_row(row)

        created = Patient.get_or_none(Patient.last_name == "LINKED")
        self.assertIsNotNone(created)
        from gws_care.patient.patient_account import PatientAccount
        link = PatientAccount.get_or_none(
            (PatientAccount.patient == created.id)
            & (PatientAccount.account == account.id)
        )
        self.assertIsNotNone(link)

    def test_import_patient_row_unknown_account_name_is_ignored(self):
        """An account_name that doesn't match any record → patient created without account."""
        row = {
            "last_name": "NOACCOUNT",
            "first_name": "Patient",
            "birth_name": "",
            "date_of_birth": "2000-05-20",
            "gender": "M",
            "address": "", "postal_code": "", "city": "", "phone": "", "email": "",
            "primary_physician_name": "", "primary_physician_phone": "",
            "account_name": "Non Existent Company XYZ",
        }

        BulkImportService.import_patient_row(row)

        created = Patient.get_or_none(Patient.last_name == "NOACCOUNT")
        self.assertIsNotNone(created)
        from gws_care.patient.patient_account import PatientAccount
        self.assertEqual(PatientAccount.select().where(PatientAccount.patient == created.id).count(), 0)

    def test_import_patient_row_service_validates_data(self):
        """Passing an invalid gender through import_patient_row raises an exception."""
        row = {
            "last_name": "INVALID",
            "first_name": "Gender",
            "birth_name": "",
            "date_of_birth": "1990-01-01",
            "gender": "X",   # invalid
            "address": "", "postal_code": "", "city": "", "phone": "", "email": "",
            "primary_physician_name": "", "primary_physician_phone": "",
            "account_name": "",
        }

        with self.assertRaises(BadRequestException):
            BulkImportService.import_patient_row(row)

    # ── DB insertion — accounts ───────────────────────────────────────────────

    def test_import_account_row_creates_account(self):
        """import_account_row correctly persists an account to the DB."""
        row = {
            "name": "Entreprise Import SA",
            "registration_number": "987654321",
            "address": "10 rue Import",
            "postal_code": "69000",
            "city": "Lyon",
            "phone": "0400000001",
            "email": "info@import.fr",
            "contact_name": "M. Import",
        }

        BulkImportService.import_account_row(row)

        created = Account.get_or_none(Account.name == "Entreprise Import SA")
        self.assertIsNotNone(created)
        self.assertEqual(created.city, "Lyon")
        self.assertEqual(created.registration_number, "987654321")
        self.assertTrue(created.is_active)

    def test_import_account_row_minimal(self):
        """Account can be created with name only (all other fields blank)."""
        row = {
            "name": "Minimal Account",
            "registration_number": "",
            "address": "",
            "postal_code": "",
            "city": "",
            "phone": "",
            "email": "",
            "contact_name": "",
        }

        BulkImportService.import_account_row(row)

        created = Account.get_or_none(Account.name == "Minimal Account")
        self.assertIsNotNone(created)
        self.assertIsNone(created.city)

    def test_import_account_row_empty_name_raises(self):
        """Blank account name should be rejected by AccountService."""
        row = {"name": "", "registration_number": "", "address": "",
               "postal_code": "", "city": "", "phone": "", "email": "", "contact_name": ""}

        with self.assertRaises(BadRequestException):
            BulkImportService.import_account_row(row)

    # ── Row numbering ─────────────────────────────────────────────────────────

    def test_row_numbers_are_sequential(self):
        """row_num on each result starts at 1 and increments."""
        csv = _make_patient_csv(
            "A,B,,1990-01-01,M,,,,,,,",
            "C,D,,1991-02-02,F,,,,,,,",
            "E,F,,1992-03-03,Other,,,,,,,",
        )
        result = BulkImportService.parse_patients_csv(csv)

        self.assertEqual([r.row_num for r in result.rows], [1, 2, 3])

    # ── Patient field persistence ─────────────────────────────────────────────

    def test_import_patient_last_name_is_uppercased(self):
        """PatientService uppercases last_name regardless of input case."""
        row = {
            "last_name": "dupont", "first_name": "Jean", "birth_name": "",
            "date_of_birth": "1985-01-01", "gender": "M",
            "address": "", "postal_code": "", "city": "", "phone": "", "email": "",
            "primary_physician_name": "", "primary_physician_phone": "", "account_name": "",
        }
        BulkImportService.import_patient_row(row)

        created = Patient.get_or_none(Patient.last_name == "DUPONT")
        self.assertIsNotNone(created)

    def test_import_patient_last_name_whitespace_stripped(self):
        """Leading/trailing whitespace on last_name is stripped."""
        row = {
            "last_name": "  BERNARD  ", "first_name": "Alice", "birth_name": "",
            "date_of_birth": "1975-06-10", "gender": "F",
            "address": "", "postal_code": "", "city": "", "phone": "", "email": "",
            "primary_physician_name": "", "primary_physician_phone": "", "account_name": "",
        }
        BulkImportService.import_patient_row(row)

        created = Patient.get_or_none(Patient.last_name == "BERNARD")
        self.assertIsNotNone(created)

    def test_import_patient_birth_name_is_stored(self):
        """Optional birth_name field is persisted when provided."""
        row = {
            "last_name": "MOREAU", "first_name": "Claire", "birth_name": "LECLERC",
            "date_of_birth": "1980-04-22", "gender": "F",
            "address": "", "postal_code": "", "city": "", "phone": "", "email": "",
            "primary_physician_name": "", "primary_physician_phone": "", "account_name": "",
        }
        BulkImportService.import_patient_row(row)

        created = Patient.get_or_none(Patient.last_name == "MOREAU")
        self.assertIsNotNone(created)
        self.assertEqual(created.birth_name, "LECLERC")

    def test_import_patient_physician_fields_stored(self):
        """primary_physician_name and primary_physician_phone are persisted."""
        row = {
            "last_name": "PETIT", "first_name": "Marc", "birth_name": "",
            "date_of_birth": "1962-11-30", "gender": "M",
            "address": "", "postal_code": "", "city": "", "phone": "", "email": "",
            "primary_physician_name": "Dr. Leblanc",
            "primary_physician_phone": "0145000000",
            "account_name": "",
        }
        BulkImportService.import_patient_row(row)

        created = Patient.get_or_none(Patient.last_name == "PETIT")
        self.assertIsNotNone(created)
        self.assertEqual(created.primary_physician_name, "Dr. Leblanc")
        self.assertEqual(created.primary_physician_phone, "0145000000")

    def test_import_patient_number_format(self):
        """Auto-generated patient_number matches PAT-XXXXXXXX format."""
        row = {
            "last_name": "PATNUM", "first_name": "Test", "birth_name": "",
            "date_of_birth": "1999-12-31", "gender": "M",
            "address": "", "postal_code": "", "city": "", "phone": "", "email": "",
            "primary_physician_name": "", "primary_physician_phone": "", "account_name": "",
        }
        BulkImportService.import_patient_row(row)

        created = Patient.get_or_none(Patient.last_name == "PATNUM")
        self.assertIsNotNone(created)
        self.assertRegex(created.patient_number, r"^PAT-[0-9A-F]{8}$")

    # ── Date boundary tests ───────────────────────────────────────────────────

    def test_import_patient_future_dob_raises(self):
        """A date_of_birth strictly in the future is rejected by PatientService."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        row = {
            "last_name": "FUTURE", "first_name": "Born", "birth_name": "",
            "date_of_birth": tomorrow, "gender": "M",
            "address": "", "postal_code": "", "city": "", "phone": "", "email": "",
            "primary_physician_name": "", "primary_physician_phone": "", "account_name": "",
        }

        with self.assertRaises(BadRequestException):
            BulkImportService.import_patient_row(row)

    def test_import_patient_today_dob_is_valid(self):
        """A date_of_birth equal to today is accepted (boundary: > today is rejected)."""
        today = date.today().isoformat()
        row = {
            "last_name": "TODAY", "first_name": "Born", "birth_name": "",
            "date_of_birth": today, "gender": "F",
            "address": "", "postal_code": "", "city": "", "phone": "", "email": "",
            "primary_physician_name": "", "primary_physician_phone": "", "account_name": "",
        }
        BulkImportService.import_patient_row(row)

        created = Patient.get_or_none(Patient.last_name == "TODAY")
        self.assertIsNotNone(created)

    def test_patient_row_leap_year_date_valid(self):
        """Leap-year date 1992-02-29 is accepted by both the validator and the service."""
        csv = _make_patient_csv("LEAP,Year,,1992-02-29,M,,,,,,,")
        result = BulkImportService.parse_patients_csv(csv)
        self.assertTrue(result.rows[0].is_valid)

        row = result.rows[0].row_data
        BulkImportService.import_patient_row(row)

        created = Patient.get_or_none(Patient.last_name == "LEAP")
        self.assertIsNotNone(created)
        self.assertEqual(created.date_of_birth, date(1992, 2, 29))

    # ── CSV format robustness ─────────────────────────────────────────────────

    def test_parse_patients_csv_crlf_line_endings(self):
        """Windows-style \\r\\n line endings are handled without error."""
        header = "last_name,first_name,birth_name,date_of_birth,gender,address,postal_code,city,phone,email,primary_physician_name,primary_physician_phone,account_name"
        row = "CRLF,Test,,1990-01-01,M,,,,,,,"
        csv = header + "\r\n" + row
        result = BulkImportService.parse_patients_csv(csv)

        self.assertEqual(result.parse_error, "")
        self.assertEqual(len(result.rows), 1)
        self.assertTrue(result.rows[0].is_valid)

    def test_parse_patients_csv_whitespace_only_last_name(self):
        """A last_name containing only spaces is treated as missing."""
        csv = _make_patient_csv("   ,Jean,,1985-03-15,M,,,,,,,")
        result = BulkImportService.parse_patients_csv(csv)

        self.assertFalse(result.rows[0].is_valid)
        self.assertIn("last_name required", result.rows[0].errors)

    def test_parse_patients_csv_extra_columns_ignored(self):
        """Additional unknown columns in the CSV do not cause errors."""
        csv = (
            "last_name,first_name,birth_name,date_of_birth,gender,extra_col\n"
            "EXTRA,Test,,1990-01-01,M,some_extra_value"
        )
        result = BulkImportService.parse_patients_csv(csv)

        self.assertEqual(result.parse_error, "")
        self.assertTrue(result.rows[0].is_valid)

    def test_parse_accounts_csv_whitespace_only_name(self):
        """An account name containing only spaces is treated as missing."""
        csv = _make_account_csv("   ,,,,,,,")
        result = BulkImportService.parse_accounts_csv(csv)

        self.assertFalse(result.rows[0].is_valid)
        self.assertIn("name required", result.rows[0].errors)

    def test_parse_accounts_csv_crlf_line_endings(self):
        """Windows-style \\r\\n line endings are handled for accounts."""
        csv = "name,city\r\nCRLF Account,Paris"
        result = BulkImportService.parse_accounts_csv(csv)

        self.assertEqual(result.parse_error, "")
        self.assertEqual(len(result.rows), 1)
        self.assertTrue(result.rows[0].is_valid)

    # ── Account field persistence ─────────────────────────────────────────────

    def test_import_account_all_fields_stored(self):
        """All optional account fields are persisted correctly."""
        row = {
            "name": "Full Account Corp",
            "registration_number": "112233445",
            "address": "99 avenue des Tests",
            "postal_code": "13000",
            "city": "Marseille",
            "phone": "0491000000",
            "email": "full@corp.fr",
            "contact_name": "Mme. Complète",
        }
        BulkImportService.import_account_row(row)

        created = Account.get_or_none(Account.name == "Full Account Corp")
        self.assertIsNotNone(created)
        self.assertEqual(created.registration_number, "112233445")
        self.assertEqual(created.address, "99 avenue des Tests")
        self.assertEqual(created.postal_code, "13000")
        self.assertEqual(created.email, "full@corp.fr")
        self.assertEqual(created.contact_name, "Mme. Complète")
        self.assertTrue(created.is_active)

    def test_import_account_is_active_by_default(self):
        """A newly imported account is active."""
        row = {
            "name": "Active Check Corp", "registration_number": "",
            "address": "", "postal_code": "", "city": "", "phone": "", "email": "", "contact_name": "",
        }
        BulkImportService.import_account_row(row)

        created = Account.get_or_none(Account.name == "Active Check Corp")
        self.assertIsNotNone(created)
        self.assertTrue(created.is_active)

    # ── Scale and counts ──────────────────────────────────────────────────────

    def test_parse_patients_csv_100_valid_rows(self):
        """100 valid rows all pass validation."""
        rows = [f"PATIENT{i:03d},First,,1985-01-01,M,,,,,,," for i in range(100)]
        csv = _make_patient_csv(*rows)
        result = BulkImportService.parse_patients_csv(csv)

        self.assertEqual(result.parse_error, "")
        self.assertEqual(len(result.valid_rows), 100)
        self.assertEqual(len(result.invalid_rows), 0)

    def test_parse_patients_csv_mixed_50_valid_50_invalid(self):
        """50 valid + 50 invalid rows produce correct counts."""
        valid_rows = [f"VALID{i:03d},First,,1985-01-01,M,,,,,,," for i in range(50)]
        invalid_rows = [f",First,,1985-01-01,M,,,,,,," for _ in range(50)]   # no last_name
        csv = _make_patient_csv(*(valid_rows + invalid_rows))
        result = BulkImportService.parse_patients_csv(csv)

        self.assertEqual(len(result.valid_rows), 50)
        self.assertEqual(len(result.invalid_rows), 50)

    # ── Duplicate accounts ────────────────────────────────────────────────────

    def test_import_two_accounts_same_name_skips_duplicate(self):
        """Importing the same account name twice creates only one DB record."""
        row = {
            "name": "Duplicate Corp", "registration_number": "", "address": "",
            "postal_code": "", "city": "", "phone": "", "email": "", "contact_name": "",
        }
        BulkImportService.import_account_row(row)
        BulkImportService.import_account_row(row)

        count = Account.select().where(Account.name == "Duplicate Corp").count()
        self.assertEqual(count, 1)

    # ── End-to-end: accounts then patients ────────────────────────────────────

    def test_import_accounts_then_patients_links_correctly(self):
        """Accounts created via import_account_row can be referenced by patient import."""
        # Step 1: import two accounts
        BulkImportService.import_account_row({
            "name": "E2E Company", "registration_number": "", "address": "",
            "postal_code": "", "city": "", "phone": "", "email": "", "contact_name": "",
        })

        # Step 2: import a patient referencing that account
        BulkImportService.import_patient_row({
            "last_name": "E2EPATIENT", "first_name": "Link", "birth_name": "",
            "date_of_birth": "1990-01-01", "gender": "M",
            "address": "", "postal_code": "", "city": "", "phone": "", "email": "",
            "primary_physician_name": "", "primary_physician_phone": "",
            "account_name": "E2E Company",
        })

        patient = Patient.get_or_none(Patient.last_name == "E2EPATIENT")
        account = Account.get_or_none(Account.name == "E2E Company")
        self.assertIsNotNone(patient)
        self.assertIsNotNone(account)
        from gws_care.patient.patient_account import PatientAccount
        link = PatientAccount.get_or_none(
            (PatientAccount.patient == patient.id)
            & (PatientAccount.account == account.id)
        )
        self.assertIsNotNone(link)

    # ── row_data immutability ─────────────────────────────────────────────────

    def test_parse_result_row_data_contains_raw_values(self):
        """row_data on a RowValidationResult stores the original CSV values unchanged."""
        csv = _make_patient_csv("dupont,jean,,1985-03-15,M,,,,,,,")
        result = BulkImportService.parse_patients_csv(csv)

        # Validation does NOT mutate the raw row_data
        self.assertEqual(result.rows[0].row_data["last_name"], "dupont")
        self.assertEqual(result.rows[0].row_data["first_name"], "jean")

    def test_parse_result_parse_error_empty_string_on_success(self):
        """parse_error is an empty string (not None) when parsing succeeds."""
        csv = _make_patient_csv("DUPONT,Jean,,1985-03-15,M,,,,,,,")
        result = BulkImportService.parse_patients_csv(csv)

        self.assertIsInstance(result.parse_error, str)
        self.assertEqual(result.parse_error, "")
