from enum import Enum
from typing import TypeAlias, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PsychologicalReportContent(BaseModel):
    identification: str = Field(default="", description="")
    description: str = Field(
        default="", description="The psychological report description."
    )


class PsychologicalOpinionContent(BaseModel):
    identification: str = Field(default="", description="")
    description: str = Field(
        default="", description="The psychological report description."
    )


class ProntuaryContent(BaseModel):
    identification: str = Field(default="", description="")
    description: str = Field(
        default="", description="The psychological report description."
    )


class DocumentCategory(str, Enum):
    PRONTUARY = "prontuary"
    PSYCHOLOGICAL_REPORT = "psychological_report"
    PSYCHOLOGICAL_OPINION = "psychological_opinion"
    # APPRAISAL = "appraisal"  # laudo
    ANAMNESIS = "anamnesis"
    DECLARATION = "declaration"
    BUDGET = "budget"
    OTHER = "other"


DOCUMENT_CATEGORY_PT: dict[DocumentCategory, str] = {
    DocumentCategory.PRONTUARY: "prontuário",
    DocumentCategory.PSYCHOLOGICAL_REPORT: "relatório psicológico",
    DocumentCategory.PSYCHOLOGICAL_OPINION: "opinião psicológica",
    # DocumentCategory.APPRAISAL: "laudo",
    DocumentCategory.ANAMNESIS: "anamnese",
    DocumentCategory.DECLARATION: "declaração",
    DocumentCategory.BUDGET: "orçamento",
    DocumentCategory.OTHER: "outro",
}

DocumentContent: TypeAlias = Union[
    ProntuaryContent, PsychologicalReportContent, PsychologicalOpinionContent
]

CONTENT_MODEL_MAP: dict[DocumentCategory, type[DocumentContent]] = {
    DocumentCategory.PRONTUARY: ProntuaryContent,
    DocumentCategory.PSYCHOLOGICAL_REPORT: PsychologicalReportContent,
    DocumentCategory.PSYCHOLOGICAL_OPINION: PsychologicalOpinionContent,
    # ...add other mappings as needed...
}


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="The document ID.")
    patient_id: UUID = Field(description="The patient ID.")
    category: DocumentCategory = Field(
        default=DocumentCategory.PRONTUARY, description="The document category."
    )
    file_name: str = Field(default="", description="The document name.")
    content: DocumentContent = Field(
        default_factory=lambda: CONTENT_MODEL_MAP[DocumentCategory.PRONTUARY]()
    )

    class ConfigDict:
        from_attributes = True
