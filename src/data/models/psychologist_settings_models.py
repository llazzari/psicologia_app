from typing import Optional

from pydantic import BaseModel, Field, field_validator


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
        from_attributes = True
