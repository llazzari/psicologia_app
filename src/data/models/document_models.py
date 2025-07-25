from enum import Enum
from typing import TypeAlias, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DeclarationContent(BaseModel):
    content: str = Field(default="", description="The content of the declaration.")


class PsychologicalReportContent(BaseModel):
    identification: str = Field(default="", description="")
    demand_description: str = Field(
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
    PRONTUARY = "Prontuário"
    DECLARATION = "Declaração"
    PSYCHOLOGICAL_CERTIFICATE = "Certificado Psicológico"
    PSYCHOLOGICAL_REPORT = "Relatório Psicológico"
    MULTIDISCIPLINARY_REPORT = "Relatório Multidisciplinar"
    PSYCHOLOGICAL_EVALUATION_REPORT = "Laudo Psicológico"
    PSYCHOLOGICAL_OPINION = "Opinião Psicológica"
    ANAMNESIS = "Anamnese"
    BUDGET = "Orçamento"
    OTHER = "Outro"


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
