"""Shared configuration for the API schemas."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_title(value: object) -> object:
    """Trim surrounding whitespace from a title value."""
    if isinstance(value, str):
        return value.strip()
    return value


class Schema(BaseModel):
    """Base schema able to read data from domain entities."""

    model_config = ConfigDict(from_attributes=True)


class TitledSchema(Schema):
    """Schema with a required, validated title."""

    title: str = Field(min_length=5, max_length=120)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        """Trim surrounding whitespace before length validation."""
        return _strip_title(value)


class OptionalTitledSchema(Schema):
    """Schema with an optional, validated title for partial updates."""

    title: str | None = Field(default=None, min_length=5, max_length=120)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        """Trim surrounding whitespace before length validation."""
        return _strip_title(value)
