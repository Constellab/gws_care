"""Task 2 — DocumentTextExtractionTask.

Takes a ResourceSet of File resources (output of DocumentBulkImportTask) and
extracts the text content of each file, producing one DocumentText resource per
file.  The resulting ResourceSet[DocumentText] is the input to the Reflex
annotation page.

Text extraction uses the same hybrid pipeline as DocumentAnalysisService:
  - pdfplumber for PDF files (text layer only, no OCR)
  - Images: empty string produced, the user fills manually in the app
"""

from gws_core import (
    ConfigParams,
    ConfigSpecs,
    File,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    Task,
    TaskInputs,
    TaskOutputs,
    task_decorator,
)
from gws_core.config.param.param_spec import IntParam
from gws_core.resource.resource_set.resource_set import ResourceSet

from .document_text import DocumentText


@task_decorator(
    "CareDocumentTextExtraction",
    human_name="Care — Document Text Extraction",
    short_description="Extract text from medical documents (PDF/images) into Text resources",
)
class DocumentTextExtractionTask(Task):
    """Extract text from each File in the input ResourceSet.

    For each File resource:
    - If it is a PDF with a text layer, pdfplumber extracts up to ``max_pages``
      pages of text.
    - If it is an image (or an encrypted/scanned PDF with no text layer), the
      DocumentText resource is created with an empty string — the user will fill
      in the annotation form manually.

    The output is a ResourceSet of DocumentText resources.  Each DocumentText
    stores:
    - The extracted text (``get_data()``)
    - The original filename (``original_name`` property)
    - The gws_core resource model id of the source File (``source_resource_id``
      property) so the Reflex app can reference the original file for download.
    """

    input_specs = InputSpecs({
        "files": InputSpec(ResourceSet, human_name="File resources to process"),
    })
    output_specs = OutputSpecs({
        "texts": OutputSpec(ResourceSet, human_name="Extracted text documents"),
    })
    config_specs = ConfigSpecs({
        "max_pages": IntParam(
            default_value=10,
            min_value=1,
            max_value=100,
            human_name="Max pages per PDF",
            short_description="Maximum number of pages to extract text from for each PDF.",
            optional=True,
        ),
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file_set: ResourceSet = inputs.get("files")
        max_pages: int = params.get_value("max_pages") or 10

        resources = file_set.get_resources()
        if not resources:
            raise ValueError("The input ResourceSet is empty.")

        output_set = ResourceSet()
        total = len(resources)

        for i, (name, resource) in enumerate(resources.items()):
            if not isinstance(resource, File):
                self.log_info_message(
                    f"Skipping '{name}': not a File resource (got {type(resource).__name__})"
                )
                continue

            self.update_progress_value(
                (i + 1) / total * 100,
                f"Extracting text from '{name}' ({i + 1}/{total})",
            )

            text_content = self._extract_text(resource, max_pages)

            doc_text = DocumentText(text_content)
            doc_text.name = name
            doc_text.original_name = name
            # Store the model id of the source File resource so the Reflex app
            # can reference the original file (e.g. for download or storage).
            doc_text.source_resource_id = resource.get_model_id() or ""

            if text_content:
                self.log_info_message(
                    f"  '{name}': extracted {len(text_content)} characters"
                )
            else:
                self.log_info_message(
                    f"  '{name}': no text extracted (image or encrypted PDF)"
                )

            output_set.add_resource(doc_text, unique_name=name)

        self.log_info_message(
            f"Text extraction complete: {len(output_set)} document(s) processed."
        )
        return {"texts": output_set}

    def _extract_text(self, file_resource: File, max_pages: int) -> str:
        """Extract text from a File resource using pdfplumber (PDF) or return empty."""
        import io
        import os

        path = file_resource.path
        if not path or not os.path.exists(path):
            self.log_info_message(f"  File path not found: {path}")
            return ""

        _, ext = os.path.splitext(path)
        ext = ext.lower()

        if ext == ".pdf":
            return self._extract_pdf(path, max_pages)

        # Images and other formats: no OCR available — return empty
        return ""

    @staticmethod
    def _extract_pdf(path: str, max_pages: int) -> str:
        """Extract text from a PDF file using pdfplumber."""
        import io
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                pages_text = []
                for page in pdf.pages[:max_pages]:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
                return "\n".join(pages_text)
        except ImportError:
            return ""
        except Exception:
            return ""
