from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Patient(BaseModel):
    """
    Pydantic model for a patient.
    Provides data validation for patient records.
    """

    # Allow id to be None when creating a new patient, but it will be set by the DB.
    # The default_factory ensures a new UUID is generated if no id is provided.
    id: UUID = Field(default_factory=uuid4)

    name: str
    address: str
    birthdate: date
    is_child: bool

    cpf_cnpj: Optional[str] = None

    school: Optional[str] = None
    tutor_cpf_cnpj: Optional[str] = None

    class ConfigDict:
        """
        Pydantic configuration options.
        'from_attributes = True' allows the model to be created from ORM objects.
        """

        from_attributes = True
