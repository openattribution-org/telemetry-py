"""
OpenAttribution Telemetry - SDK for AI content attribution.

OpenAttribution enables fair compensation for content creators when their
content is used by AI agents to generate valuable responses.

Example:
    >>> from openattribution.telemetry import Client, ConversationTurn
    >>> async with Client(endpoint, api_key) as client:
    ...     session_id = await client.start_session(content_scope="my-content-mix")
    ...     await client.record_event(
    ...         session_id=session_id,
    ...         event_type="turn_completed",
    ...         turn=ConversationTurn(privacy_level="intent", query_intent="comparison")
    ...     )
"""

from openattribution.telemetry.acp import session_to_content_attribution
from openattribution.telemetry.client import Client
from openattribution.telemetry.extract import (
    extract_citation_urls,
    extract_indexed_citations,
    extract_result_urls,
)
from openattribution.telemetry.schema import (
    ConversationTurn,
    EventType,
    Initiator,
    InitiatorType,
    IntentCategory,
    OutcomeType,
    PrivacyLevel,
    SessionOutcome,
    SourceRole,
    TelemetryEvent,
    TelemetrySession,
    UserContext,
)
from openattribution.telemetry.ucp import session_to_attribution

__all__ = [
    # Client
    "Client",
    # Extraction
    "extract_citation_urls",
    "extract_indexed_citations",
    "extract_result_urls",
    # UCP bridge
    "session_to_attribution",
    # ACP bridge
    "session_to_content_attribution",
    # Type aliases
    "EventType",
    "InitiatorType",
    "SourceRole",
    "OutcomeType",
    "PrivacyLevel",
    "IntentCategory",
    # Models
    "Initiator",
    "UserContext",
    "ConversationTurn",
    "TelemetryEvent",
    "SessionOutcome",
    "TelemetrySession",
]

__version__ = "0.2.0"
