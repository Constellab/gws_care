"""Task 1 — DocumentBulkImportTask.

Takes a Folder resource containing PDF/image files and registers each file
individually as a File resource, returning them as a ResourceSet.

This runs in a dedicated worker process, fully isolated from the Reflex app.
"""

from gws_core import (
    ConfigParams,
    ConfigSpecs,
    File,
    Folder,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    Task,
    TaskInputs,
    TaskOutputs,
    task_decorator,
)
from gws_core.config.param.param_spec import StrParam
from gws_core.resource.resource_set.resource_set import ResourceSet

_DEFAULT_EXTENSIONS = ".pdf,.png,.jpg,.jpeg,.bmp,.tiff,.webp"


@task_decorator(
    "CareDocumentBulkImport",
    human_name="Care — Bulk Document Import",
    short_description="Import all files from a folder as individual File resources",
)
class DocumentBulkImportTask(Task):
    """Register each file in a Folder as a separate File resource.

    The output ResourceSet can be wired directly into DocumentTextExtractionTask
    to extract text from every imported file in one pipeline.

    Supported extensions are configurable; defaults cover common medical document
    formats (PDF, JPEG, PNG, TIFF, BMP, WebP).
    """

    input_specs = InputSpecs({
        "folder": InputSpec(Folder, human_name="Document folder"),
    })
    output_specs = OutputSpecs({
        "files": OutputSpec(ResourceSet, human_name="Imported files"),
    })
    config_specs = ConfigSpecs({
        "extensions": StrParam(
            default_value=_DEFAULT_EXTENSIONS,
            human_name="File extensions",
            short_description=(
                "Comma-separated list of extensions to import (e.g. .pdf,.png). "
                "Leave blank to import all files."
            ),
            optional=True,
        ),
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        folder: Folder = inputs.get("folder")
        ext_filter = params.get_value("extensions") or ""
        allowed_exts = {
            e.strip().lower()
            for e in ext_filter.split(",")
            if e.strip()
        }

        all_paths = folder.list_all_file_paths()
        if not all_paths:
            raise ValueError(f"The folder '{folder.path}' contains no files.")

        resource_set = ResourceSet()
        imported = 0
        skipped = 0

        for i, path in enumerate(sorted(all_paths)):
            import os
            filename = os.path.basename(path)
            _, ext = os.path.splitext(filename)
            ext_lower = ext.lower()

            if allowed_exts and ext_lower not in allowed_exts:
                self.log_info_message(f"Skipping '{filename}' (extension '{ext_lower}' not in filter)")
                skipped += 1
                continue

            self.update_progress_value(
                (i + 1) / len(all_paths) * 100,
                f"Importing {filename} ({i + 1}/{len(all_paths)})",
            )

            file_resource = File(path)
            file_resource.name = filename
            resource_set.add_resource(file_resource, unique_name=filename)
            imported += 1

        if imported == 0:
            raise ValueError(
                f"No files matched the extension filter '{ext_filter}' in the folder."
            )

        self.log_info_message(
            f"Import complete: {imported} file(s) imported, {skipped} skipped."
        )
        return {"files": resource_set}
