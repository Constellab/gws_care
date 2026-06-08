"""DocumentText resource — extracted text from a medical document.

Extends gws_core Text with metadata about the source file so the Reflex
annotation page can link back to the original File resource.
"""

from gws_core import resource_decorator
from gws_core.impl.text.text import Text
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.primitive_r_field import StrRField


@resource_decorator(
    "CareDocumentText",
    human_name="Document Text",
    short_description="Extracted text from a medical document (PDF or image)",
    style=TypingStyle.material_icon("description", background_color="#d4e8f7"),
)
class DocumentText(Text):
    """Text resource produced by DocumentTextExtractionTask.

    ``_source_resource_id`` and ``_original_name`` are stored in the KV store
    so the Reflex annotation page can read them without querying any DB.
    """

    _source_resource_id: str = StrRField(default_value="")
    _original_name: str = StrRField(default_value="")

    @property
    def source_resource_id(self) -> str:
        return self._source_resource_id

    @source_resource_id.setter
    def source_resource_id(self, value: str) -> None:
        self._source_resource_id = value or ""

    @property
    def original_name(self) -> str:
        return self._original_name

    @original_name.setter
    def original_name(self, value: str) -> None:
        self._original_name = value or ""
