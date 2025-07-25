from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field


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


class ClassTime(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"


class Child(BaseModel):
    school: Optional[str] = Field(default=None, description="The child's school name.")
    grade: Optional[str] = Field(default=None, description="The child's grade.")
    class_time: Optional[ClassTime] = Field(
        default=None, description="The child's class time."
    )
    tutor_name: Optional[str] = Field(
        default=None, description="The child's tutor name."
    )
    tutor_cpf_cnpj: Optional[str] = Field(
        default=None, description="The child's tutor CPF/CNPJ."
    )


class PatientGender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class PatientInfo(BaseModel):
    name: str
    birthdate: Optional[date] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    gender: Optional[PatientGender] = None
    cpf_cnpj: Optional[str] = None

    @computed_field
    @property
    def age(self) -> Optional[str]:
        if self.birthdate:
            age_in_days: int = (datetime.now().date() - self.birthdate).days
            years: int = age_in_days // 365
            formatted_years: str = f"{years} anos" if years > 1 else "1 ano"
            months: int = (age_in_days % 365) // 30
            if months == 0:
                return formatted_years
            formatted_months: str = f"e {months} meses" if months > 1 else "e 1 mês"
            return f"{formatted_years} {formatted_months}"
        return None


class Patient(BaseModel):
    """
    Pydantic model for a patient.
    Provides data validation for patient records.
    """

    id: UUID = Field(default_factory=uuid4)
    info: PatientInfo
    status: PatientStatus = PatientStatus.ACTIVE
    diagnosis: Optional[str] = None
    contract: Optional[str] = None
    child: Optional[Child] = None

    class ConfigDict:
        from_attributes = True
