from datetime import date
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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


class AppointmentData(BaseModel):
    """
    Nested model for appointment-derived data that can be recomputed from appointments table.
    """

    sessions_completed: int = Field(default=0, ge=0)
    sessions_to_recover: int = Field(default=0, ge=0)
    free_sessions: int = Field(default=0, ge=0)
    appointment_dates: list[date] = Field(default_factory=list)  # type: ignore

    class ConfigDict:
        from_attributes = True


class MonthlyInvoice(BaseModel):
    """
    Pydantic model for a patient's monthly invoice.
    """

    id: UUID = Field(default_factory=uuid4)
    patient_id: UUID
    invoice_month: int = Field(ge=1, le=12)
    invoice_year: int
    appointment_data: AppointmentData = Field(default_factory=AppointmentData)
    session_price: int = Field(
        default=23000, ge=0, description="The session price in cents."
    )
    partaking: int = Field(
        default=0, ge=0, description="The partaking amount in cents."
    )
    payment_status: MonthlyInvoiceStatus = MonthlyInvoiceStatus.PENDING
    nf_number: Optional[int] = None
    payment_date: Optional[date] = None
    total: int = Field(default=0, ge=0)

    class ConfigDict:
        from_attributes = True

    @property
    def sessions_completed(self) -> int:
        return self.appointment_data.sessions_completed

    @property
    def sessions_to_recover(self) -> int:
        return self.appointment_data.sessions_to_recover

    @property
    def free_sessions(self) -> int:
        return self.appointment_data.free_sessions

    @property
    def appointment_dates(self) -> list[date]:
        return self.appointment_data.appointment_dates
