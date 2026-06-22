"""Unit tests for PatientService."""

import re
from datetime import date, timedelta

from gws_care.account.account_dto import SaveAccountDTO
from gws_care.account.account_service import AccountService
from gws_care.patient.patient_dto import SavePatientDTO
from gws_care.patient.patient_service import PatientService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_core import BadRequestException, BaseTestCase, NotFoundException

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_patient_dto(**kwargs) -> SavePatientDTO:
    """Return a valid SavePatientDTO, overridable via kwargs."""
    defaults = {
        "last_name": "Dupont",
        "first_name": "Jean",
        "date_of_birth": date(1985, 3, 15),
        "gender": "M",
    }
    defaults.update(kwargs)
    return SavePatientDTO(**defaults)


def _make_account(name: str = "AcmeCorp"):
    return AccountService.create_account(SaveAccountDTO(name=name))


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPatientService(BaseTestCase):
    """Tests for PatientService CRUD, validation and search."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    # ── create_patient ────────────────────────────────────────────────────────

    def test_create_patient_happy_path(self):
        """Patient is created with all provided fields persisted."""
        dto = _make_patient_dto(
            last_name="Martin",
            first_name="Sophie",
            date_of_birth=date(1990, 7, 20),
            gender="F",
            phone="0612345678",
            email="sophie@example.com",
        )
        patient = PatientService.create_patient(dto)

        self.assertIsNotNone(patient.id)
        # last_name is uppercased by _apply_dto
        self.assertEqual(patient.last_name, "MARTIN")
        self.assertEqual(patient.first_name, "Sophie")
        self.assertEqual(patient.date_of_birth, date(1990, 7, 20))
        self.assertEqual(patient.gender, "F")
        self.assertEqual(patient.phone, "0612345678")
        self.assertEqual(patient.email, "sophie@example.com")

    def test_create_patient_number_format(self):
        """Generated patient_number matches PAT-XXXXXXXX pattern."""
        patient = PatientService.create_patient(_make_patient_dto())
        self.assertRegex(patient.patient_number, r"^PAT-[0-9A-F]{8}$")

    def test_create_patient_number_is_unique(self):
        """Each created patient gets a distinct patient_number."""
        p1 = PatientService.create_patient(_make_patient_dto(first_name="Alice"))
        p2 = PatientService.create_patient(_make_patient_dto(first_name="Bob"))
        self.assertNotEqual(p1.patient_number, p2.patient_number)

    def test_create_patient_last_name_uppercased(self):
        """_apply_dto uppercases last_name regardless of input case."""
        patient = PatientService.create_patient(_make_patient_dto(last_name="dupont"))
        self.assertEqual(patient.last_name, "DUPONT")

    def test_create_patient_missing_last_name(self):
        """Empty last_name raises BadRequestException."""
        with self.assertRaises(BadRequestException):
            PatientService.create_patient(_make_patient_dto(last_name=""))

    def test_create_patient_whitespace_last_name(self):
        """Whitespace-only last_name raises BadRequestException."""
        with self.assertRaises(BadRequestException):
            PatientService.create_patient(_make_patient_dto(last_name="   "))

    def test_create_patient_missing_first_name(self):
        """Empty first_name raises BadRequestException."""
        with self.assertRaises(BadRequestException):
            PatientService.create_patient(_make_patient_dto(first_name=""))

    def test_create_patient_invalid_gender(self):
        """Gender not in {M, F, Other} raises BadRequestException."""
        with self.assertRaises(BadRequestException):
            PatientService.create_patient(_make_patient_dto(gender="X"))

    def test_create_patient_future_dob(self):
        """DOB in the future raises BadRequestException."""
        future = date.today() + timedelta(days=1)
        with self.assertRaises(BadRequestException):
            PatientService.create_patient(_make_patient_dto(date_of_birth=future))

    def test_create_patient_today_dob_ok(self):
        """DOB equal to today is accepted (boundary)."""
        patient = PatientService.create_patient(_make_patient_dto(date_of_birth=date.today()))
        self.assertIsNotNone(patient.id)

    def test_create_patient_gender_other(self):
        """Gender 'Other' is a valid value."""
        patient = PatientService.create_patient(_make_patient_dto(gender="Other"))
        self.assertEqual(patient.gender, "Other")

    # ── update_patient ────────────────────────────────────────────────────────

    def test_update_patient(self):
        """update_patient changes fields and preserves patient_number."""
        patient = PatientService.create_patient(_make_patient_dto())
        original_number = patient.patient_number

        updated = PatientService.update_patient(
            str(patient.id),
            _make_patient_dto(first_name="Pierre", phone="0699887766"),
        )

        self.assertEqual(updated.first_name, "Pierre")
        self.assertEqual(updated.phone, "0699887766")
        self.assertEqual(updated.patient_number, original_number)

    def test_update_patient_validates(self):
        """update_patient rejects invalid DTO (empty first_name)."""
        patient = PatientService.create_patient(_make_patient_dto())
        with self.assertRaises(BadRequestException):
            PatientService.update_patient(str(patient.id), _make_patient_dto(first_name=""))

    # ── get_patient / get_patient_by_number ───────────────────────────────────

    def test_get_patient_not_found(self):
        """get_patient raises NotFoundException for unknown id."""
        with self.assertRaises(NotFoundException):
            PatientService.get_patient("00000000-0000-0000-0000-000000000000")

    def test_get_patient_by_number_not_found(self):
        """get_patient_by_number raises NotFoundException for unknown number."""
        with self.assertRaises(NotFoundException):
            PatientService.get_patient_by_number("PAT-00000000")

    def test_get_patient_by_number_found(self):
        """get_patient_by_number returns the correct patient."""
        patient = PatientService.create_patient(_make_patient_dto(first_name="GetByNum"))
        found = PatientService.get_patient_by_number(patient.patient_number)
        self.assertEqual(str(found.id), str(patient.id))

    # ── search_patients ───────────────────────────────────────────────────────

    def test_search_patients_no_filters_returns_all(self):
        """No filters → all created patients are returned."""
        PatientService.create_patient(_make_patient_dto(first_name="SearchA"))
        PatientService.create_patient(_make_patient_dto(first_name="SearchB"))
        results = PatientService.search_patients()
        self.assertGreaterEqual(len(results), 2)

    def test_search_patients_by_last_name_partial(self):
        """Partial last_name match (case-insensitive contains)."""
        PatientService.create_patient(_make_patient_dto(last_name="Beaumont", first_name="X"))
        results = PatientService.search_patients(name="eaumo")
        names = [p.last_name for p in results]
        self.assertIn("BEAUMONT", names)

    def test_search_patients_by_first_name_partial(self):
        """Partial first_name match also works via the OR condition."""
        PatientService.create_patient(_make_patient_dto(last_name="Xxx", first_name="Celestine"))
        results = PatientService.search_patients(name="elesti")
        first_names = [p.first_name for p in results]
        self.assertIn("Celestine", first_names)

    def test_search_patients_by_patient_number(self):
        """Exact patient_number filter returns only that patient."""
        p = PatientService.create_patient(_make_patient_dto(first_name="ByNumber"))
        results = PatientService.search_patients(patient_number=p.patient_number)
        self.assertEqual(len(results), 1)
        self.assertEqual(str(results[0].id), str(p.id))

    def test_search_patients_by_phone(self):
        """Exact phone filter returns only matching patients."""
        PatientService.create_patient(_make_patient_dto(first_name="PhoneUser", phone="0111111111"))
        PatientService.create_patient(_make_patient_dto(first_name="OtherUser", phone="0999999999"))
        results = PatientService.search_patients(phone="0111111111")
        phones = [p.phone for p in results]
        for ph in phones:
            self.assertEqual(ph, "0111111111")
        self.assertTrue(any(p.first_name == "PhoneUser" for p in results))

    def test_search_patients_by_account_id(self):
        """account_id filter returns only patients linked to that account."""
        account = _make_account("SearchAcct")
        dto_linked = _make_patient_dto(first_name="Linked", account_id=str(account.id))
        dto_free = _make_patient_dto(first_name="Free")
        PatientService.create_patient(dto_linked)
        PatientService.create_patient(dto_free)

        results = PatientService.search_patients(account_id=str(account.id))
        first_names = [p.first_name for p in results]
        self.assertIn("Linked", first_names)
        self.assertNotIn("Free", first_names)

    def test_search_patients_by_dob_from(self):
        """dob_from filters out patients born before the date."""
        PatientService.create_patient(_make_patient_dto(first_name="Old", date_of_birth=date(1950, 1, 1)))
        PatientService.create_patient(_make_patient_dto(first_name="Young", date_of_birth=date(2000, 6, 1)))
        results = PatientService.search_patients(dob_from="1990-01-01")
        for p in results:
            self.assertGreaterEqual(p.date_of_birth, date(1990, 1, 1))

    def test_search_patients_by_dob_to(self):
        """dob_to filters out patients born after the date."""
        PatientService.create_patient(_make_patient_dto(first_name="OldDobTo", date_of_birth=date(1960, 3, 1)))
        PatientService.create_patient(_make_patient_dto(first_name="YoungDobTo", date_of_birth=date(2005, 3, 1)))
        results = PatientService.search_patients(dob_to="1980-12-31")
        for p in results:
            self.assertLessEqual(p.date_of_birth, date(1980, 12, 31))

    def test_search_patients_combined_filters(self):
        """Multiple filters are ANDed together."""
        account = _make_account("ComboAcct")
        PatientService.create_patient(
            _make_patient_dto(first_name="Combo", last_name="Leroy", account_id=str(account.id))
        )
        PatientService.create_patient(
            _make_patient_dto(first_name="Combo", last_name="Moreau")
        )
        results = PatientService.search_patients(name="Combo", account_id=str(account.id))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].last_name, "LEROY")

    # ── list_patients_for_account ─────────────────────────────────────────────

    def test_list_patients_for_account(self):
        """Returns only patients for the given account, ordered by last/first name."""
        account = _make_account("ListAcct")
        PatientService.create_patient(_make_patient_dto(last_name="Zidane", first_name="Zinedine", account_id=str(account.id)))
        PatientService.create_patient(_make_patient_dto(last_name="Albert", first_name="Marc", account_id=str(account.id)))
        PatientService.create_patient(_make_patient_dto(first_name="NoAcct"))

        results = PatientService.list_patients_for_account(str(account.id))
        self.assertEqual(len(results), 2)
        # Ordered by last_name
        self.assertEqual(results[0].last_name, "ALBERT")
        self.assertEqual(results[1].last_name, "ZIDANE")

    # ── add_account / remove_account ──────────────────────────────────────────

    def test_add_account(self):
        """add_account links a patient to an account."""
        from gws_care.patient.patient_account import PatientAccount
        patient = PatientService.create_patient(_make_patient_dto(first_name="ToLink"))
        account = _make_account("LinkAcct")

        PatientService.add_account(str(patient.id), str(account.id))
        link = PatientAccount.get_or_none(
            (PatientAccount.patient_id == patient.id)
            & (PatientAccount.account_id == account.id)
        )
        self.assertIsNotNone(link)

    def test_remove_account(self):
        """remove_account unlinks a patient from an account."""
        from gws_care.patient.patient_account import PatientAccount
        account = _make_account("UnlinkAcct")
        dto = _make_patient_dto(first_name="ToUnlink", account_id=str(account.id))
        patient = PatientService.create_patient(dto)
        # Verify link exists
        link = PatientAccount.get_or_none(
            (PatientAccount.patient_id == patient.id)
            & (PatientAccount.account_id == account.id)
        )
        self.assertIsNotNone(link)

        PatientService.remove_account(str(patient.id), str(account.id))
        link_after = PatientAccount.get_or_none(
            (PatientAccount.patient_id == patient.id)
            & (PatientAccount.account_id == account.id)
        )
        self.assertIsNone(link_after)

    def test_add_account_multiple(self):
        """A patient can be linked to multiple accounts."""
        from gws_care.patient.patient_account import PatientAccount
        patient = PatientService.create_patient(_make_patient_dto(first_name="MultiAcct"))
        acc1 = _make_account("Acc1Multi")
        acc2 = _make_account("Acc2Multi")

        PatientService.add_account(str(patient.id), str(acc1.id))
        PatientService.add_account(str(patient.id), str(acc2.id))

        links = list(PatientAccount.select().where(PatientAccount.patient_id == patient.id))
        self.assertEqual(len(links), 2)

    def test_add_account_idempotent(self):
        """add_account called twice for the same pair does not raise."""
        account = _make_account("IdempAcct")
        patient = PatientService.create_patient(_make_patient_dto(first_name="Idemp"))
        PatientService.add_account(str(patient.id), str(account.id))
        # Should not raise
        PatientService.add_account(str(patient.id), str(account.id))

    def test_add_account_unknown_account_raises(self):
        """add_account raises NotFoundException for unknown account_id."""
        patient = PatientService.create_patient(_make_patient_dto(first_name="NoAcctAssign"))
        with self.assertRaises(NotFoundException):
            PatientService.add_account(
                str(patient.id), "00000000-0000-0000-0000-000000000000"
            )

    def test_add_account_unknown_patient_raises(self):
        """add_account raises NotFoundException for unknown patient_id."""
        account = _make_account("AssignUnknownPat")
        with self.assertRaises(NotFoundException):
            PatientService.add_account(
                "00000000-0000-0000-0000-000000000000", str(account.id)
            )
