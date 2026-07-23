"""
Prompt domain models.

Provider-agnostic, immutable value objects that represent a structured
prompt payload ready for serialization into any LLM format.

No Gemini / OpenAI / Anthropic-specific keys or types are used here.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class PromptRole(Enum):
    """
    The role assigned to a prompt message in a conversational context.

    Maps to the standard roles accepted by virtually every LLM API
    without being tied to any specific provider.
    """
    SYSTEM    = "system"
    USER      = "user"
    ASSISTANT = "assistant"


class PromptSectionType(Enum):
    """
    Semantic category of a prompt section.

    Allows downstream adapters to reorder, filter, or format specific
    sections without parsing raw text.
    """
    INSTRUCTION        = "instruction"       # Task framing / persona
    BIRTH_CHART        = "birth_chart"       # Raw planetary positions
    DASHA              = "dasha"             # Active Dasha periods
    YOGA_SUMMARY       = "yoga_summary"      # Detected yoga list + scores
    INTERPRETATION     = "interpretation"    # Per-category interpretation text
    USER_QUERY         = "user_query"        # Optional free-text question


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PromptSection:
    """
    A single labelled block of structured text within a prompt.

    Attributes
    ----------
    section_type:
        Semantic tag that identifies what this section contains.
    heading:
        Short, human-readable heading rendered before the body.
    body:
        Pre-formatted text content for this section.
    """
    section_type: PromptSectionType
    heading: str
    body: str


@dataclass(frozen=True)
class PromptMessage:
    """
    A single conversational turn, equivalent to one chat message.

    Attributes
    ----------
    role:
        Who is speaking (system / user / assistant).
    content:
        The full text of the message.
    """
    role: PromptRole
    content: str


# ---------------------------------------------------------------------------
# Core domain model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StructuredPrompt:
    """
    Provider-agnostic, immutable prompt payload.

    Contains both a structured representation (sections) for programmatic
    inspection and a pre-rendered message sequence (messages) for direct
    submission to any chat-completion API.

    Attributes
    ----------
    sections:
        Ordered tuple of PromptSection objects.  Consumers (e.g., provider
        adapters) may iterate these to build provider-specific request bodies.
    messages:
        Ordered tuple of PromptMessage objects representing a chat thread.
        Ready for direct serialization into {"role": ..., "content": ...}
        dicts that every major LLM API accepts.
    metadata:
        Immutable key-value store for arbitrary bookkeeping data such as
        ascendant sign, language, or request identifiers.
        Values are strings to remain serialization-agnostic.
    """
    sections: Tuple[PromptSection, ...]
    messages: Tuple[PromptMessage, ...]
    metadata: Tuple[Tuple[str, str], ...]  # ((key, value), ...)

    # ------------------------------------------------------------------
    # Read-only helpers
    # ------------------------------------------------------------------

    def sections_by_type(
        self, section_type: PromptSectionType
    ) -> Tuple[PromptSection, ...]:
        """Return all sections matching the given type."""
        return tuple(s for s in self.sections if s.section_type is section_type)

    def messages_by_role(self, role: PromptRole) -> Tuple[PromptMessage, ...]:
        """Return all messages with the given role."""
        return tuple(m for m in self.messages if m.role is role)

    def get_metadata(self, key: str) -> str | None:
        """Return the value for a metadata key, or None if absent."""
        for k, v in self.metadata:
            if k == key:
                return v
        return None

    def to_chat_dicts(self) -> Tuple[dict, ...]:
        """
        Render messages as plain dicts compatible with any chat-completion API.

        Example output element:
            {"role": "user", "content": "..."}
        """
        return tuple(
            {"role": m.role.value, "content": m.content} for m in self.messages
        )
