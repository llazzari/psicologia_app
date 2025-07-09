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

    @field_validator("contact", "cpf_cnpj", "tutor_cpf_cnpj")
    @classmethod
    def check_contact_value(cls, v: Optional[str]) -> Optional[str]:
        """Ensures contact has a valid value."""
        if v is not None and len(v) != 11:
            raise ValueError("Contact must be 11 digits")
        return v

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


class MonthlyInvoice(BaseModel):
    """
    Pydantic model for a patient's monthly invoice.
    """

    id: UUID = Field(default_factory=uuid4)
    patient_id: UUID
    invoice_month: int = Field(ge=1, le=12)
    invoice_year: int
    appointment_dates: list[date] = Field(default_factory=list)  # type: ignore
    session_price: int = Field(default=23000, ge=0)  # in cents
    sessions_completed: int = Field(default=0, ge=0)
    sessions_to_recover: int = Field(default=0, ge=0)
    free_sessions: int = Field(default=0, ge=0)
    payment_status: str = "pending"  # one of 'pending', 'paid', 'overdue', 'waived'
    nf_number: Optional[int] = None
    payment_date: Optional[date] = None

    @field_validator("payment_status")
    @classmethod
    def check_payment_status(cls, v: str) -> str:
        """Ensures payment_status has a valid value."""
        allowed_statuses: set[str] = {"pending", "paid", "overdue", "waived"}
        if v not in allowed_statuses:
            raise ValueError(f"Payment status must be one of {allowed_statuses}")
        return v

    class ConfigDict:
        """Pydantic configuration options."""

        from_attributes = True
