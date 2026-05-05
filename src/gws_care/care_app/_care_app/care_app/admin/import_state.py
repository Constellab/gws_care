"""State for bulk CSV import of patients and accounts from the Admin page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel

_PATIENT_TEMPLATE = (
    "last_name,first_name,birth_name,date_of_birth,gender,"
    "address,postal_code,city,phone,email,primary_physician_name,primary_physician_phone,account_name\n"
    "DUPONT,Jean,,1985-03-15,M,12 rue de la Paix,75001,Paris,0612345678,jean.dupont@example.com,,,\n"
    "MARTIN,Sophie,LECLERC,1992-07-22,F,5 boulevard Haussmann,75008,Paris,0623456789,sophie.martin@example.com,,,\n"
)

_ACCOUNT_TEMPLATE = (
    "name,registration_number,address,postal_code,city,phone,email,contact_name\n"
    "Entreprise XYZ,123456789,15 avenue des Champs,75008,Paris,0123456789,contact@xyz.com,M. Dupont\n"
    "Société ABC,987654321,8 rue de Rivoli,75001,Paris,0187654321,info@abc.fr,Mme. Martin\n"
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
                self.parse_error = "Could not decode the file. Please save it as UTF-8 CSV."
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
            self.parse_error = f"Parse error: {e}"
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
            self.parse_error = f"Authentication or DB error: {e}"

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
