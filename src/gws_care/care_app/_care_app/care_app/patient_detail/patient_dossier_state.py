"""State for patient dossier documents and doctor notes (patient-level, exam-independent)."""

import uuid as _uuid
from pathlib import Path

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class PatientDocRowDTO(BaseModel):
    """Row DTO for a document in the patient dossier."""

    id: str
    original_name: str
    type_label: str
    uploaded_by_name: str
    created_at: str
    stored_filename: str
    file_size_kb: str


class PatientNoteRowDTO(BaseModel):
    """Row DTO for a doctor note in the patient dossier."""

    id: str
    author_name: str
    content: str
    created_at: str


# Document type options for the dropdown (value, label)
PATIENT_DOC_TYPE_OPTIONS: list[tuple[str, str]] = [
    ("identite", "Pièce d'identité"),
    ("ordonnance", "Ordonnance"),
    ("resultat_anterieur", "Résultats antérieurs"),
    ("radio", "Radiographie"),
    ("scanner", "Scanner / IRM"),
    ("certificat", "Certificat médical"),
    ("autre", "Autre"),
]


class PatientDossierState(ReflexMainState):
    """Manages patient-level documents and doctor notes."""

    # ── Documents ─────────────────────────────────────────────────────────────
    patient_docs: list[PatientDocRowDTO] = []
    is_uploading_doc: bool = False
    selected_doc_type: str = "autre"

    # ── Notes ─────────────────────────────────────────────────────────────────
    patient_notes: list[PatientNoteRowDTO] = []
    new_note_text: str = ""
    is_saving_note: bool = False
    show_note_input: bool = False

    # ── Load ──────────────────────────────────────────────────────────────────

    @rx.event
    async def load_dossier(self):
        """Load documents and notes for the current patient (URL param patient_id_param)."""
        if not await self.check_authentication():
            return
        patient_id = self.patient_id_param
        if not patient_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_document import PatientDocument
                from gws_care.patient.patient_note import PatientNote

                docs = list(
                    PatientDocument.select()
                    .where(PatientDocument.patient == patient_id)
                    .order_by(PatientDocument.created_at.desc())
                )
                self.patient_docs = [
                    PatientDocRowDTO(
                        id=str(d.id),
                        original_name=d.original_name,
                        type_label=d.get_type_label(),
                        uploaded_by_name=d.uploaded_by_name or "—",
                        created_at=str(d.created_at)[:16].replace("T", " "),
                        stored_filename=d.stored_filename,
                        file_size_kb=(
                            f"{round(d.file_size / 1024, 1)} Ko" if d.file_size else "—"
                        ),
                    )
                    for d in docs
                ]

                notes = list(
                    PatientNote.select()
                    .where(PatientNote.patient == patient_id)
                    .order_by(PatientNote.created_at.desc())
                )
                self.patient_notes = [
                    PatientNoteRowDTO(
                        id=str(n.id),
                        author_name=n.author_name or "Médecin",
                        content=n.content,
                        created_at=str(n.created_at)[:16].replace("T", " "),
                    )
                    for n in notes
                ]
        except Exception as e:
            print(f"[PatientDossierState] load_dossier error: {e}")

    # ── Documents ─────────────────────────────────────────────────────────────

    @rx.event
    def set_selected_doc_type(self, value: str):
        self.selected_doc_type = value

    @rx.event
    async def handle_doc_upload(self, files: list[rx.UploadFile]):
        """Upload one or more files to the patient dossier."""
        if not await self.check_authentication():
            return
        patient_id = self.patient_id_param
        if not patient_id:
            yield rx.toast.error("Identifiant patient manquant.")
            return

        self.is_uploading_doc = True
        yield

        try:
            uploads: list[tuple[str, bytes, str]] = []
            for uf in files:
                data = await uf.read()
                mime = uf.content_type or "application/octet-stream"
                uploads.append((uf.filename or "document", data, mime))

            with await self.authenticate_user() as auth_user:
                # Resolve the author name
                author_name = ""
                try:
                    from gws_care.user.user import User
                    local_user = User.get_or_none(User.id == str(auth_user.id))
                    if local_user:
                        author_name = f"{local_user.first_name} {local_user.last_name}".strip()
                    if not author_name:
                        author_name = getattr(auth_user, "email", "")
                except Exception:
                    author_name = ""

                upload_dir = rx.get_upload_dir()
                from gws_care.patient.patient_document import PatientDocument

                for original_name, file_bytes, mime in uploads:
                    stored_name = f"{_uuid.uuid4()!s}_{original_name}"
                    (Path(upload_dir) / stored_name).write_bytes(file_bytes)
                    doc = PatientDocument()
                    doc.patient = patient_id
                    doc.original_name = original_name
                    doc.stored_filename = stored_name
                    doc.mime_type = mime
                    doc.file_size = len(file_bytes)
                    doc.document_type = self.selected_doc_type
                    doc.uploaded_by_name = author_name
                    doc.save(force_insert=True)

            yield rx.toast.success(f"{len(uploads)} document(s) ajouté(s) au dossier.")
            await self.load_dossier()
        except Exception as e:
            yield rx.toast.error(f"Erreur d'upload : {e}")
        finally:
            self.is_uploading_doc = False

    @rx.event
    async def delete_patient_doc(self, doc_id: str):
        """Delete a patient document (DB record + file on disk)."""
        if not await self.check_authentication():
            return
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_document import PatientDocument
                doc = PatientDocument.get_or_none(PatientDocument.id == doc_id)
                if doc:
                    try:
                        upload_dir = rx.get_upload_dir()
                        (Path(upload_dir) / doc.stored_filename).unlink(missing_ok=True)
                    except Exception:
                        pass
                    doc.delete_instance()
            await self.load_dossier()
        except Exception as e:
            yield rx.toast.error(f"Erreur suppression document : {e}")

    # ── Notes ─────────────────────────────────────────────────────────────────

    @rx.event
    def set_new_note_text(self, value: str):
        self.new_note_text = value

    @rx.event
    def toggle_note_input(self):
        self.show_note_input = not self.show_note_input
        if not self.show_note_input:
            self.new_note_text = ""

    @rx.event
    async def add_patient_note(self):
        """Save a new doctor note for the current patient."""
        if not self.new_note_text.strip():
            yield rx.toast.error("La note ne peut pas être vide.")
            return
        if not await self.check_authentication():
            return
        patient_id = self.patient_id_param
        if not patient_id:
            yield rx.toast.error("Identifiant patient manquant.")
            return

        self.is_saving_note = True
        yield

        try:
            with await self.authenticate_user() as auth_user:
                author_name = ""
                try:
                    from gws_care.user.user import User
                    local_user = User.get_or_none(User.id == str(auth_user.id))
                    if local_user:
                        author_name = f"{local_user.first_name} {local_user.last_name}".strip()
                    if not author_name:
                        author_name = getattr(auth_user, "email", "Médecin")
                except Exception:
                    author_name = "Médecin"

                from gws_care.patient.patient_note import PatientNote
                note = PatientNote()
                note.patient = patient_id
                note.author_name = author_name
                note.content = self.new_note_text.strip()
                note.save(force_insert=True)

            self.new_note_text = ""
            self.show_note_input = False
            yield rx.toast.success("Note ajoutée au dossier.")
            await self.load_dossier()
        except Exception as e:
            yield rx.toast.error(f"Erreur sauvegarde note : {e}")
        finally:
            self.is_saving_note = False

    @rx.event
    async def delete_patient_note(self, note_id: str):
        """Delete a patient note."""
        if not await self.check_authentication():
            return
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_note import PatientNote
                note = PatientNote.get_or_none(PatientNote.id == note_id)
                if note:
                    note.delete_instance()
            await self.load_dossier()
        except Exception as e:
            yield rx.toast.error(f"Erreur suppression note : {e}")
