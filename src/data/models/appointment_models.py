from datetime import date, datetime, time
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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
    appointment_date: date = Field(default_factory=date.today)
    appointment_time: time = Field(default_factory=datetime.now().time)
    duration: int = 45  # in minutes
    is_free_of_charge: bool = False
    notes: str = ""
    status: AppointmentStatus = AppointmentStatus.DONE

    class ConfigDict:
        from_attributes = True
