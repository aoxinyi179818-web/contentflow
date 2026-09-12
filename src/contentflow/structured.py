"""Parse and validate JSON returned by structured ContentFlow nodes."""

from typing import TypeVar

from pydantic import BaseModel, ValidationError

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class StructuredOutputError(ValueError):
    """Raised when a model response is not valid for the expected contract."""


def parse_structured_output(content: str, schema: type[StructuredModel]) -> StructuredModel:
    """Validate one non-empty JSON response against a Pydantic model."""
    normalized_content = content.strip()
    if not normalized_content:
        raise StructuredOutputError("Structured model response must not be empty.")

    try:
        return schema.model_validate_json(normalized_content)
    except ValidationError as error:
        raise StructuredOutputError(f"Invalid {schema.__name__} JSON response: {error}") from error
