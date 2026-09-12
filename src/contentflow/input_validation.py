"""Shared validation for user-provided workflow topics."""

MAX_TOPIC_LENGTH = 500


class TopicInputError(ValueError):
    """Raised when a topic cannot be submitted to the content workflow."""


def validate_topic(topic: str) -> str:
    """Return one normalized topic, rejecting empty and oversized input early."""
    if not isinstance(topic, str):
        raise TopicInputError("topic must be a string")

    normalized_topic = topic.strip()
    if not normalized_topic:
        raise TopicInputError("topic must not be empty")
    if len(normalized_topic) > MAX_TOPIC_LENGTH:
        raise TopicInputError(f"topic must not exceed {MAX_TOPIC_LENGTH} characters")
    return normalized_topic
