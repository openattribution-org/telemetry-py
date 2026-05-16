"""
OpenAttribution Telemetry Schema v0.1

This module defines the core data types for the OpenAttribution standard.
OpenAttribution is an open specification for tracking content attribution
in AI agent interactions.

The schema supports:
- Session-based event tracking
- Privacy-tiered conversation capture
- Content retrieval and citation tracking
- Commerce/conversion attribution
- Cross-session journey attribution
- AIMS manifest integration for licensing verification
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

EventType = Literal[
    # Content lifecycle events
    "content_retrieved",  # Content fetched from source
    "content_grounded",  # Content loaded into agent context
    "content_displayed",  # Content shown to user
    "content_engaged",  # User interacted with content
    "content_cited",  # Content referenced in response
    # Conversation events
    "turn_started",  # User initiated a conversation turn
    "turn_completed",  # Agent finished responding
    # Commerce events
    "product_viewed",  # Product page/details viewed
    "product_compared",  # Multiple products compared
    "cart_add",  # Item added to cart
    "cart_remove",  # Item removed from cart
    "checkout_started",  # Checkout flow initiated
    "checkout_completed",  # Purchase completed
    "checkout_abandoned",  # Checkout abandoned
]
"""
Supported event types for telemetry tracking.

Content events track the lifecycle of content through an agent interaction.
Conversation events capture the query/response flow with privacy controls.
Commerce events enable attribution for e-commerce conversions.
"""

OutcomeType = Literal["conversion", "abandonment", "browse"]
"""
Session outcome classifications.

- conversion: User completed a desired action (purchase, signup, etc.)
- abandonment: User started but did not complete an action
- browse: User browsed without specific conversion intent
"""

PrivacyLevel = Literal["full", "summary", "intent", "minimal"]
"""
Privacy levels for conversation data sharing.

- full: Complete query and response text included
- summary: LLM-generated summary of the conversation
- intent: Only classified intent/topic, no raw text
- minimal: Only metadata (token counts, content URLs)

The appropriate level depends on the trust agreement between
the signal emitter and consumer.
"""

IntentCategory = Literal[
    # Research intents
    "product_research",
    "comparison",
    "how_to",
    "troubleshooting",
    "general_question",
    # Commerce intents
    "purchase_intent",
    "price_check",
    "availability_check",
    "review_seeking",
    # Other
    "chitchat",
    "other",
]
"""
Standardized intent categories for conversation classification.

Used when privacy_level is "intent" to provide attribution signals
without exposing raw conversation text.
"""


# =============================================================================
# CORE MODELS
# =============================================================================

InitiatorType = Literal["user", "agent"]
"""
Actor type for the session initiator.

- user: A human end user (default)
- agent: An AI agent calling another agent
"""

SourceRole = Literal["origin", "edge", "index", "agent"]
"""
Who is reporting a retrieval event.

- origin: Content owner's web server detected an AI agent/bot request
- edge: CDN or edge network (Cloudflare, Fastly, Akamai, etc.) - reports even on cache MISS
- index: Search index or content repository that served the content
- agent: The AI agent itself, reporting content it fetched
"""

CitationType = Literal["direct_quote", "paraphrase", "reference", "contradiction"]
"""
How content was used in the response.

- direct_quote: Verbatim or near-verbatim excerpt
- paraphrase: Content restated in the agent's own words
- reference: Content referenced but not quoted or paraphrased
- contradiction: Content retrieved but explicitly disagreed with (negative attribution)
"""

CitationPosition = Literal["primary", "supporting", "mentioned"]
"""
Prominence of a citation in the agent's response.

- primary: Main source driving the response
- supporting: Corroborating or supplementary source
- mentioned: Briefly referenced without substantive use
"""

BotCategory = Literal["training", "inference", "search"]
"""
Edge platform's classification of the requesting bot.

- training: Crawling for model training
- inference: Fetching at query time (RAG) - most relevant for content attribution
- search: AI search indexing
"""

CacheStatus = Literal["hit", "miss", "bypass", "dynamic"]
"""
Edge cache result for a content retrieval.

- hit: Served from cache
- miss: Cache miss, fetched from origin
- bypass: Cache intentionally bypassed
- dynamic: Content generated dynamically (not cacheable)
"""


class Initiator(BaseModel):
    """
    Identity of the initiating agent.

    Used when initiator_type is "agent" to identify the calling agent.
    When the initiator is a human user, this is omitted and user_context
    describes the initiator instead.

    Attributes:
        agent_id: Calling agent's identifier.
        manifest_ref: Calling agent's AIMS manifest reference.
        operator_id: Organisation operating the calling agent.
    """

    agent_id: str | None = None
    manifest_ref: str | None = None
    operator_id: str | None = None


# =============================================================================
# DATA PROFILE MODELS (spec section 4)
# =============================================================================


class CitationData(BaseModel):
    """
    Recommended data profile for ``content_cited`` events.

    All fields are optional - they are recommended, not required.
    Place in the event's ``data`` dict or use this model for validation.

    Attributes:
        citation_type: How content was used in the response.
        excerpt_tokens: Token count of the excerpt used.
        position: Prominence of citation in the response.
        content_hash: SHA-256 of cited content for verification (``sha256:{hex}``).
    """

    citation_type: CitationType | None = None
    excerpt_tokens: int | None = None
    position: CitationPosition | None = None
    content_hash: str | None = None


class EdgeEnrichment(BaseModel):
    """
    Recommended data profile for ``content_retrieved`` events with ``source_role: edge``.

    CDN and edge network integrations SHOULD include these fields.
    All fields are optional.

    Attributes:
        user_agent: Request User-Agent header.
        bot_category: Edge platform's bot classification (training/inference/search).
        verified: Whether the bot identity was cryptographically verified.
        cache_status: Edge cache result (hit/miss/bypass/dynamic).
        response_status: HTTP response status code.
        response_bytes: Response body size in bytes.
        ja4: JA4 TLS client fingerprint.
        asn: Client AS number.
        asn_org: Client AS organisation name.
        country: ISO 3166-1 alpha-2 country code.
        ip_hash: SHA-256 of client IP (``sha256:{hex}``).
    """

    user_agent: str | None = None
    bot_category: BotCategory | None = None
    verified: bool | None = None
    cache_status: CacheStatus | None = None
    response_status: int | None = None
    response_bytes: int | None = None
    ja4: str | None = None
    asn: int | None = None
    asn_org: str | None = None
    country: str | None = None
    ip_hash: str | None = None


class OriginEnrichment(BaseModel):
    """
    Recommended data profile for ``content_retrieved`` events with ``source_role: origin``.

    All fields are optional.

    Attributes:
        user_agent: Request User-Agent header.
        ip_hash: SHA-256 of client IP (``sha256:{hex}``).
        response_status: HTTP response status code.
    """

    user_agent: str | None = None
    ip_hash: str | None = None
    response_status: int | None = None


class UserContext(BaseModel):
    """
    User context for personalization and segmentation.

    This information helps attribute content value across user segments
    without requiring personally identifiable information.

    Attributes:
        external_id: Optional opaque identifier from the emitter's system.
            Should NOT be PII - use a hashed or synthetic ID.
        segments: User segment labels (e.g., ["premium", "returning"]).
        attributes: Additional context attributes for analysis.
    """

    external_id: str | None = None
    segments: list[str] = Field(default_factory=list)
    attributes: dict = Field(default_factory=dict)


class ConversationTurn(BaseModel):
    """
    Captured conversation turn with privacy controls.

    Represents a single query/response exchange in an agent conversation.
    The privacy_level determines which fields are populated, allowing
    emitters to control data sharing based on their agreements.

    Attributes:
        privacy_level: Controls which fields are included.
        query_text: User's query (full/summary levels only).
        response_text: Agent's response (full/summary levels only).
        query_intent: Classified intent category (intent level and above).
        response_type: Classification of response type.
        content_urls_retrieved: Content fetched to answer the query.
        content_urls_cited: Content actually used/cited in response.
        query_tokens: Token count of the query.
        response_tokens: Token count of the response.
        model_id: Identifier of the model used (e.g., "claude-3-opus").
    """

    privacy_level: PrivacyLevel = "minimal"

    # Full/Summary level fields
    query_text: str | None = None
    response_text: str | None = None

    # Intent level fields
    query_intent: IntentCategory | None = None
    response_type: str | None = None  # "recommendation", "explanation", "comparison", etc.
    topics: list[str] = Field(default_factory=list)  # Detected topics/entities

    # Minimal level fields (always safe to include)
    content_urls_retrieved: list[str] = Field(default_factory=list)
    content_urls_cited: list[str] = Field(default_factory=list)
    query_tokens: int | None = None
    response_tokens: int | None = None
    model_id: str | None = None


class TelemetryEvent(BaseModel):
    """
    Single telemetry event within a session.

    Events are the atomic unit of tracking in OpenAttribution.
    Each event has a type, timestamp, and optional associations
    to content and products.

    Attributes:
        id: Unique identifier for this event.
        type: The event type (see EventType).
        timestamp: When the event occurred (UTC).
        content_url: Associated content URL, if applicable.
        product_id: Associated product, if applicable.
        turn: Conversation turn data for turn_started/turn_completed events.
        data: Additional event-specific metadata.

    Example:
        >>> event = TelemetryEvent(
        ...     id=uuid4(),
        ...     type="content_cited",
        ...     timestamp=datetime.now(UTC),
        ...     content_url="https://example.com/article",
        ...     data={"citation_type": "direct_quote"}
        ... )
    """

    id: UUID
    type: EventType
    timestamp: datetime
    source_role: SourceRole | None = None
    content_telemetry_id: UUID | None = None
    content_url: str | None = None
    product_id: UUID | None = None
    turn: ConversationTurn | None = None  # For turn_started/turn_completed events
    data: dict = Field(default_factory=dict)


class SessionOutcome(BaseModel):
    """
    Session outcome for attribution calculation.

    Captures the business result of a session, enabling attribution
    of content contribution to conversions.

    Attributes:
        type: Outcome classification (conversion/abandonment/browse).
        value_amount: Monetary value in minor currency units (e.g., cents for USD, yen for JPY).
        currency: ISO 4217 currency code (e.g., "USD", "EUR", "JPY").
        products: Product IDs involved in the outcome.
        metadata: Additional outcome details.

    Example:
        >>> outcome = SessionOutcome(
        ...     type="conversion",
        ...     value_amount=4999,  # $49.99 USD
        ...     currency="USD",
        ...     products=[product_uuid]
        ... )
    """

    type: OutcomeType
    value_amount: int = 0  # Minor currency units (cents, pence, yen, etc.)
    currency: str = "USD"  # ISO 4217
    products: list[UUID] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class TelemetrySession(BaseModel):
    """
    Complete telemetry session container.

    A session represents a bounded interaction between a user and an
    AI agent, from start to outcome. Sessions contain events and
    optionally conclude with an outcome for attribution.

    Attributes:
        schema_version: OpenAttribution schema version.
        session_id: Unique identifier for this session.
        initiator_type: Who started the session: "user" (default) or "agent".
        initiator: Identity of the calling agent when initiator_type is "agent".
        agent_id: Identifier for the responding AI agent (for multi-agent systems).
        content_scope: Opaque identifier for the content collection/permissions
            context. Implementers define the meaning (e.g., mix ID, manifest
            reference, API key scope). Used for attribution aggregation.
        manifest_ref: Optional reference to an AIMS manifest for licensing
            verification (e.g., "did:aims:abc123").
        prior_session_ids: Optional list of previous session IDs in the same
            user journey. Enables cross-session attribution for multi-day
            or multi-device customer journeys.
        started_at: Session start timestamp (UTC).
        ended_at: Session end timestamp (UTC), if concluded.
        user_context: User segmentation data.
        events: Ordered list of events in the session.
        outcome: Final session outcome, if concluded.

    Example:
        >>> session = TelemetrySession(
        ...     session_id=uuid4(),
        ...     content_scope="my-content-mix",
        ...     started_at=datetime.now(UTC),
        ...     user_context=UserContext(segments=["premium"])
        ... )
    """

    schema_version: str = "0.1"
    session_id: UUID

    # Actor types
    initiator_type: InitiatorType = "user"
    initiator: Initiator | None = None

    agent_id: str | None = None

    # Content scope and licensing
    content_scope: str | None = None
    manifest_ref: str | None = None

    # Cross-session attribution
    prior_session_ids: list[UUID] = Field(default_factory=list)

    # Session lifecycle
    started_at: datetime
    ended_at: datetime | None = None
    user_context: UserContext = Field(default_factory=UserContext)
    events: list[TelemetryEvent] = Field(default_factory=list)
    outcome: SessionOutcome | None = None
