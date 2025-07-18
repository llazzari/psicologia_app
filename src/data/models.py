from datetime import date, datetime, time
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class PatientStatus(str, Enum):
    ACTIVE = "active"
    IN_TESTING = "in testing"
    LEAD = "lead"
    INACTIVE = "inactive"


PATIENT_STATUS_PT: dict[PatientStatus, str] = {
    PatientStatus.ACTIVE: "ativos",
    PatientStatus.IN_TESTING: "em avaliação",
    PatientStatus.LEAD: "em potencial",
    PatientStatus.INACTIVE: "inativos",
}
PATIENT_STATUS_PT_SINGULAR: dict[PatientStatus, str] = {
    PatientStatus.ACTIVE: "ativo",
    PatientStatus.IN_TESTING: "em avaliação",
    PatientStatus.LEAD: "em potencial",
    PatientStatus.INACTIVE: "inativo",
}


class Patient(BaseModel):
    """
    Pydantic model for a patient.
    Provides data validation for patient records.
    """

    # Allow id to be None when creating a new patient, but it will be set by the DB.
    # The default_factory ensures a new UUID is generated if no id is provided.
    id: UUID = Field(default_factory=uuid4)

    name: str
    address: Optional[str] = None
    contact: Optional[str] = None  # Phone number or other contact info
    birthdate: Optional[date] = None
    is_child: bool = True

    cpf_cnpj: Optional[str] = None

    school: Optional[str] = None
    tutor_cpf_cnpj: Optional[str] = None
    status: PatientStatus = PatientStatus.ACTIVE
    contract: Optional[str] = None

    class ConfigDict:
        """
        Pydantic configuration options.
        'from_attributes = True' allows the model to be created from ORM objects.
        """

        from_attributes = True


class AppointmentStatus(str, Enum):
    DONE = "done"
    TO_RECOVER = "to recover"
    CANCELLED = "cancelled"


APPOINTMENT_STATUS_PT: dict[str, str] = {
    AppointmentStatus.DONE: "realizadas",
    AppointmentStatus.TO_RECOVER: "a recuperar",
    AppointmentStatus.CANCELLED: "canceladas",
}


class Appointment(BaseModel):
    """
    Pydantic model for an individual appointment/session.
    """

    id: UUID = Field(default_factory=uuid4)
    patient_id: UUID
    patient_name: str
    appointment_date: date = Field(default_factory=date.today)
    appointment_time: time = Field(default_factory=datetime.now().time)
    duration: int = 45  # in minutes
    is_free_of_charge: bool = False
    notes: str = ""
    status: AppointmentStatus = AppointmentStatus.DONE

    class ConfigDict:
        """Pydantic configuration options."""

        from_attributes = True


class MonthlyInvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    WAIVED = "waived"


MONTHLY_INVOICE_STATUS_PT: dict[str, str] = {
    MonthlyInvoiceStatus.PENDING: "pendente",
    MonthlyInvoiceStatus.PAID: "pago",
    MonthlyInvoiceStatus.OVERDUE: "vencido",
    MonthlyInvoiceStatus.WAIVED: "cancelado",
}


class MonthlyInvoice(BaseModel):
    """
    Pydantic model for a patient's monthly invoice.
    """

    id: UUID = Field(default_factory=uuid4)
    patient_id: UUID
    invoice_month: int = Field(ge=1, le=12)
    invoice_year: int
    appointment_dates: list[date] = Field(default_factory=list)  # type: ignore
    session_price: int = Field(
        default=23000, ge=0, description="The session price in cents."
    )
    sessions_completed: int = Field(default=0, ge=0)
    sessions_to_recover: int = Field(default=0, ge=0)
    free_sessions: int = Field(default=0, ge=0)
    payment_status: MonthlyInvoiceStatus = MonthlyInvoiceStatus.PENDING
    nf_number: Optional[int] = None
    payment_date: Optional[date] = None
    total: int = Field(default=0, ge=0)

    class ConfigDict:
        """Pydantic configuration options."""

        from_attributes = True


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


class DocumentContent(BaseModel):
    content: str = Field(default="", description="The psychological document content.")


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="The document ID.")
    patient_id: UUID = Field(description="The patient ID.")
    category: DocumentCategory = Field(
        default=DocumentCategory.PRONTUARY, description="The document category."
    )
    file_name: str = Field(default="", description="The document name.")
    content: DocumentContent = Field(
        default=DocumentContent(content=""), description="The document content."
    )

    class ConfigDict:
        """Pydantic configuration options."""

        from_attributes = True


class PsychologistSettings(BaseModel):
    """
    Pydantic model for a psychologist's settings.
    """

    user_email: str = Field(description="The psychologist's Google email address.")
    psychologist_name: str = ""
    crp: Optional[str] = None
    default_session_price: int = Field(
        default=23000, ge=0, description="The default session price in cents."
    )
    default_evaluation_price: int = Field(
        default=350000, ge=0, description="The default evaluation price in cents."
    )
    default_session_duration: int = Field(
        default=45, ge=0, description="The default session duration in minutes."
    )
    logo_path: Optional[str] = Field(
        default=None, description="The path to the psychologist's logo."
    )

    @field_validator("user_email")
    def validate_user_email(cls, v: str) -> str:
        if not v.endswith("@gmail.com"):
            raise ValueError("User email must end with @gmail.com")
        return v

    class ConfigDict:
        """Pydantic configuration options."""

        from_attributes = True
