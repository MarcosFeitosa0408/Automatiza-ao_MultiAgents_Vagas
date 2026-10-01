from pydantic import Field, field_validator

from core.schemas.job import StrictModel


class OpportunitySearchRequest(StrictModel):
    query: str = Field(min_length=1, max_length=200)
    country: str = Field(default="br", pattern=r"^[a-zA-Z]{2}$")
    location: str = Field(default="", max_length=200)

    @field_validator("query", "country", "location", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        return value.lower()