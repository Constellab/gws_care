"""Service for managing exam file attachments."""

import os

import reflex as rx

from gws_care.exam.exam_file import ExamFile


class ExamFileService:
    """Manages CRUD for ExamFile records.

    Files are stored exclusively in the gws_core LocalFileStore and registered
    as UPLOADED ResourceModel entries so they are visible in Constellab.
    The Reflex upload dir is used only as a transient staging area during the
    exam-creation form flow.
    """

    @staticmethod
    def get_resource_download_url(resource_id: str) -> str:
        """Build the browser-accessible download URL for a gws_core File resource."""
        from gws_core import Settings
        base = Settings.get_lab_api_url().rstrip("/")
        core_prefix = Settings.core_api_route_path()
        return f"{base}/{core_prefix}/fs-node/{resource_id}/download"

    @classmethod
    def list_files_for_exam(cls, exam_id: str) -> list[ExamFile]:
        return list(ExamFile.select().where(ExamFile.exam == exam_id).order_by(ExamFile.id))

    @classmethod
    def _save_bytes_as_gws_resource(cls, file_bytes: bytes, original_name: str) -> tuple[str, str]:
        """Write bytes to a gws temp file, register as gws_core File resource (UPLOADED).

        Returns (resource_id, name).
        Raises on failure so callers can surface the error.
        IMPORTANT: caller must set the gws_core auth context first via
        ``with await main_state.authenticate_user():``, because ResourceModel
        (a ModelWithUser) calls CurrentUserService.get_and_check_current_user()
        in _before_insert.
        """
        import uuid

        from gws_core import File, Settings
        from gws_core.resource.resource_dto import ResourceOrigin
        from gws_core.resource.resource_model import ResourceModel

        safe_name = "".join(
            c for c in original_name
            if c in "._-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        ) or f"file_{uuid.uuid4().hex[:8]}"

        temp_dir = Settings.make_temp_dir()
        temp_path = os.path.join(temp_dir, safe_name)
        with open(temp_path, "wb") as fh:
            fh.write(file_bytes)

        gws_file = File(temp_path)
        gws_file.set_name(original_name)

        # ResourceModel.save_from_resource calls save_full() which already has
        # @GwsCoreDbManager.transaction() — no additional wrapper needed.
        resource_model = ResourceModel.save_from_resource(gws_file, origin=ResourceOrigin.UPLOADED)
        return str(resource_model.id), resource_model.name or original_name

    @classmethod
    def _tag_resource_with_document_type(cls, resource_id: str, document_type: str) -> None:
        """Apply a document_type tag to a gws_core resource. Replaces any existing value."""
        try:
            from gws_core.tag.entity_tag_list import EntityTagList
            from gws_core.tag.tag import Tag
            from gws_core.tag.tag_entity_type import TagEntityType

            entity_tags = EntityTagList.find_by_entity(TagEntityType.RESOURCE, resource_id)
            entity_tags.replace_tag(Tag(key="document_type", value=document_type))
        except Exception as err:
            from gws_core.core.utils.logger import Logger
            Logger.error(f"ExamFileService: could not tag resource '{resource_id}': {err}")

    @classmethod
    def create_file(
        cls,
        exam_id: str,
        original_name: str,
        file_bytes: bytes,
        mime_type: str | None = None,
        document_type: str | None = None,
    ) -> ExamFile:
        """Persist file bytes as a gws_core Resource and create the ExamFile record.

        Used by the exam detail page upload (file bytes are available directly).
        """
        resource_id, _stored = cls._save_bytes_as_gws_resource(file_bytes, original_name)

        if document_type and resource_id:
            cls._tag_resource_with_document_type(resource_id, document_type)

        ef = ExamFile()
        ef.exam_id = exam_id
        ef.original_name = original_name
        ef.stored_filename = ""      # not used; resource_id is the primary reference
        ef.mime_type = mime_type
        ef.file_size = len(file_bytes)
        ef.resource_id = resource_id
        ef.document_type = document_type
        ef.save()
        return ef

    @classmethod
    def update_document_type(cls, file_id: str, document_type: str) -> None:
        """Update the document_type of an ExamFile and re-tag the gws_core resource."""
        ef = ExamFile.get_or_none(ExamFile.id == file_id)
        if ef is None:
            return
        ef.document_type = document_type or None
        ef.save()
        if ef.resource_id and document_type:
            cls._tag_resource_with_document_type(ef.resource_id, document_type)

    @classmethod
    def attach_staged_file(
        cls,
        exam_id: str,
        original_name: str,
        stored_filename: str,
        mime_type: str | None = None,
        file_size: int | None = None,
        document_type: str | None = None,
    ) -> ExamFile:
        """Register a file that was staged in the Reflex upload dir as a gws_core Resource.

        Reads the bytes from the Reflex upload dir, registers in gws_core, then
        removes the upload-dir copy.
        """
        upload_path = rx.get_upload_dir() / stored_filename

        if not upload_path.exists():
            raise FileNotFoundError(f"Staged file '{stored_filename}' no longer exists.")

        file_bytes = upload_path.read_bytes()
        resource_id, _stored = cls._save_bytes_as_gws_resource(file_bytes, original_name)

        # Clean up staging copy
        try:
            os.remove(upload_path)
        except OSError:
            pass

        if document_type and resource_id:
            cls._tag_resource_with_document_type(resource_id, document_type)

        ef = ExamFile()
        ef.exam_id = exam_id
        ef.original_name = original_name
        ef.stored_filename = ""      # not used; resource_id is the primary reference
        ef.mime_type = mime_type
        ef.file_size = file_size
        ef.resource_id = resource_id
        ef.document_type = document_type
        ef.save()
        return ef

    @classmethod
    def delete_file(cls, file_id: str) -> None:
        """Delete the ExamFile record and its associated gws_core Resource."""
        ef = ExamFile.get_or_none(ExamFile.id == file_id)
        if ef is None:
            return

        if ef.resource_id:
            try:
                from gws_core.resource.resource_model import ResourceModel
                resource_model = ResourceModel.get_by_id(ef.resource_id)
                if resource_model is not None:
                    resource_model.delete_full()
            except Exception as err:
                from gws_core.core.utils.logger import Logger
                Logger.error(
                    f"ExamFileService: could not delete gws_core resource"
                    f" '{ef.resource_id}': {err}"
                )

        ef.delete_instance()

