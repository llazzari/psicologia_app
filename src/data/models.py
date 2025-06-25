from datetime import date, time
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


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
    birthdate: Optional[date] = None
    is_child: bool = True

    cpf_cnpj: Optional[str] = None

    school: Optional[str] = None
    tutor_cpf_cnpj: Optional[str] = None
    status: str = "active"

    @field_validator("status")
    @classmethod
    def check_status_value(cls, v: str) -> str:
        """Ensures status has a valid value."""
        allowed_statuses: set[str] = {"active", "inactive", "in testing", "lead"}
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of {allowed_statuses}")
        return v

    class ConfigDict:
        """
        Pydantic configuration options.
        'from_attributes = True' allows the model to be created from ORM objects.
        """

        from_attributes = True


class Appointment(BaseModel):
    """
    Pydantic model for an individual appointment/session.
    """

    id: UUID = Field(default_factory=uuid4)
    patient_id: UUID
    patient_name: str
    appointment_date: date
    appointment_time: time
    duration: int = 45  # in minutes
    is_free_of_charge: bool = False
    notes: str = ""

    class ConfigDict:
        """Pydantic configuration options."""

        from_attributes = True


class MonthlyInvoice(BaseModel):
    """
    Pydantic model for a patient's monthly invoice.
    """

    id: UUID = Field(default_factory=uuid4)
    patient_id: UUID
    invoice_month: str  # Format MMM, e.g. "Jan", "Feb", etc.
    session_price: int  # in cents
    sessions_completed: int
    payment_status: str  # Validated to be 'pending', 'paid', 'overdue', 'waived'
    payment_date: Optional[date] = None

    @field_validator("payment_status")
    @classmethod
    def check_payment_status(cls, v: str) -> str:
        """Ensures payment_status has a valid value."""
        allowed_statuses = {"pending", "paid", "overdue", "waived"}
        if v not in allowed_statuses:
            raise ValueError(f"Payment status must be one of {allowed_statuses}")
        return v

    class ConfigDict:
        """Pydantic configuration options."""

        from_attributes = True
