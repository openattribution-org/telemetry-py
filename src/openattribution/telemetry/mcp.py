"""OpenAttribution Telemetry — MCP session tracker.

Provides session continuity across stateless MCP tool calls. The calling
agent passes a stable ``external_session_id`` string; this module maps it to
an OA session UUID and reuses it across tool calls within the same server
process.

Usage in an MCP tool::

    from openattribution.telemetry import Client, MCPSessionTracker

    client = Client(endpoint="https://telemetry.openattribution.org", api_key="...")
    tracker = MCPSessionTracker(client, content_scope="my-shopping-agent")

    # In your MCP tool handler:
    async def search_products(query: str, session_id: str | None = None):
        results = await do_search(query)
        await tracker.track_retrieved(session_id, [r.url for r in results])
        return format_results(results)

The in-process registry works correctly for single-process MCP servers. For
multi-process or distributed deployments, session continuity must be handled
upstream — for example, include the OA session ID in your tool response and
pass it back as ``external_session_id`` on subsequent calls.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid4

from openattribution.telemetry.schema import EventType, SessionOutcome, TelemetryEvent

if TYPE_CHECKING:
    from openattribution.telemetry.client import Client

# Events emitted by an agent SDK always carry source_role="agent".
_AGENT: Literal["agent"] = "agent"


class MCPSessionTracker:
    """Session tracker for MCP agents.

    Maintains an in-process mapping of external session IDs to OA session
    UUIDs. Sessions are created on first use and reused across subsequent
    tool calls. All events emitted through this tracker are stamped with
    ``source_role="agent"``.
    """

    def __init__(self, client: Client, content_scope: str = "mcp-agent") -> None:
        """Initialise the tracker.

        Args:
            client: A configured :class:`~openattribution.telemetry.Client`.
            content_scope: Stable identifier for this agent's content scope
                (e.g. mix ID, manifest reference, or descriptive slug like
                ``"my-shopping-agent"``).
        """
        self._client = client
        self._content_scope = content_scope
        self._registry: dict[str, UUID | None] = {}

    @property
    def client(self) -> Client:
        """The underlying :class:`~openattribution.telemetry.Client`.

        Use for advanced cases not covered by the convenience methods (e.g.
        emitting an event type with custom ``data`` on an existing session via
        :meth:`record_event`).
        """
        return self._client

    def get_session(self, external_session_id: str | None) -> UUID | None:
        """Return the OA session UUID for an external ID *without* creating one.

        Returns None if no session has been started for this external ID yet.
        Use this for events that should only attach to an existing session
        (e.g. a checkout that follows earlier search activity).
        """
        if external_session_id is None:
            return None
        return self._registry.get(external_session_id)

    async def get_or_create_session(
        self,
        external_session_id: str | None,
    ) -> UUID | None:
        """Get or create an OA session for the given external session ID.

        If ``external_session_id`` is None, a new anonymous session is created
        on every call (no continuity across tool calls).

        Returns:
            OA session UUID, or None on silent failure.
        """
        if external_session_id is not None and external_session_id in self._registry:
            return self._registry[external_session_id]

        session_id = await self._client.start_session(
            content_scope=self._content_scope,
            external_session_id=external_session_id,
        )

        if external_session_id is not None:
            self._registry[external_session_id] = session_id

        return session_id

    async def record_event(
        self,
        external_session_id: str | None,
        event_type: EventType,
        *,
        content_url: str | None = None,
        data: dict | None = None,
    ) -> None:
        """Emit a single event on an *existing* session.

        Looks the session up via :meth:`get_session` (no creation) and stamps
        ``source_role="agent"``. No-ops if no session exists for this ID — useful
        for follow-on events like ``checkout_started`` that only make sense once
        a conversation has produced retrievals.
        """
        session_id = self.get_session(external_session_id)
        if session_id is None:
            return
        await self._client.record_event(
            session_id,
            event_type,
            content_url=content_url,
            source_role=_AGENT,
            data=data,
        )

    async def track_retrieved(
        self,
        external_session_id: str | None,
        urls: list[str],
    ) -> None:
        """Emit ``content_retrieved`` events for a list of URLs.

        Call this after fetching products, search results, or any content
        that influenced the agent's response.
        """
        if not urls:
            return
        session_id = await self.get_or_create_session(external_session_id)
        if session_id is None:
            return

        now = datetime.now(UTC)
        events = [
            TelemetryEvent(
                id=uuid4(),
                type="content_retrieved",
                timestamp=now,
                source_role=_AGENT,
                content_url=url,
            )
            for url in urls
        ]
        await self._client.record_events(session_id, events)

    async def track_grounded(
        self,
        external_session_id: str | None,
        urls: list[str],
    ) -> None:
        """Emit ``content_grounded`` events for content loaded into context.

        Call this for the subset of retrieved content the agent actually
        loaded into its working context (after reranking / filtering).
        """
        if not urls:
            return
        session_id = await self.get_or_create_session(external_session_id)
        if session_id is None:
            return

        now = datetime.now(UTC)
        events = [
            TelemetryEvent(
                id=uuid4(),
                type="content_grounded",
                timestamp=now,
                source_role=_AGENT,
                content_url=url,
            )
            for url in urls
        ]
        await self._client.record_events(session_id, events)

    async def track_cited(
        self,
        external_session_id: str | None,
        urls: list[str],
        *,
        citation_type: Literal["direct_quote", "paraphrase", "reference", "contradiction"]
        | None = None,
        position: Literal["primary", "supporting", "mentioned"] | None = None,
    ) -> None:
        """Emit ``content_cited`` events for content referenced in a response."""
        if not urls:
            return
        session_id = await self.get_or_create_session(external_session_id)
        if session_id is None:
            return

        data: dict = {}
        if citation_type is not None:
            data["citation_type"] = citation_type
        if position is not None:
            data["position"] = position

        now = datetime.now(UTC)
        events = [
            TelemetryEvent(
                id=uuid4(),
                type="content_cited",
                timestamp=now,
                source_role=_AGENT,
                content_url=url,
                data=dict(data),
            )
            for url in urls
        ]
        await self._client.record_events(session_id, events)

    async def track_engaged(
        self,
        external_session_id: str | None,
        urls: list[str],
        *,
        interaction_type: Literal["click", "view", "expand", "share"] | None = None,
    ) -> None:
        """Emit ``content_engaged`` events when a user interacts with content.

        This is the strongest attribution signal before a purchase event.
        """
        if not urls:
            return
        session_id = await self.get_or_create_session(external_session_id)
        if session_id is None:
            return

        data: dict = {}
        if interaction_type is not None:
            data["interaction_type"] = interaction_type

        now = datetime.now(UTC)
        events = [
            TelemetryEvent(
                id=uuid4(),
                type="content_engaged",
                timestamp=now,
                source_role=_AGENT,
                content_url=url,
                data=dict(data),
            )
            for url in urls
        ]
        await self._client.record_events(session_id, events)

    async def track_checkout(
        self,
        external_session_id: str | None,
        *,
        type: Literal["completed", "abandoned", "started"],  # noqa: A002
        value_amount: int | None = None,
        currency: str | None = None,
        products: list[str] | None = None,
    ) -> None:
        """Record a checkout outcome and end the session.

        Emits ``checkout_completed`` / ``checkout_abandoned`` / ``checkout_started``
        then, for completed/abandoned, ends the session with the matching
        outcome type and drops the session from the registry.
        """
        session_id = (
            self._registry.get(external_session_id)
            if external_session_id is not None
            else None
        )
        if session_id is None:
            return

        event_type: Literal["checkout_completed", "checkout_abandoned", "checkout_started"] = (
            "checkout_completed"
            if type == "completed"
            else "checkout_abandoned"
            if type == "abandoned"
            else "checkout_started"
        )
        await self._client.record_event(
            session_id, event_type, source_role=_AGENT
        )

        if type in ("completed", "abandoned"):
            outcome_type: Literal["conversion", "abandonment"] = (
                "conversion" if type == "completed" else "abandonment"
            )
            await self._client.end_session(
                session_id,
                SessionOutcome(
                    type=outcome_type,
                    value_amount=value_amount or 0,
                    currency=currency or "USD",
                    products=products or [],
                ),
            )
            if external_session_id is not None:
                self._registry.pop(external_session_id, None)

    async def end_session(
        self,
        external_session_id: str | None,
        *,
        type: Literal["conversion", "abandonment", "browse"],  # noqa: A002
        value_amount: int | None = None,
        currency: str | None = None,
    ) -> None:
        """End a session with an explicit outcome.

        Use :meth:`track_checkout` for commerce outcomes. Use this for
        non-commerce session endings (browse sessions, timeouts, explicit
        abandonment).
        """
        session_id = (
            self._registry.get(external_session_id)
            if external_session_id is not None
            else None
        )
        if session_id is None:
            return

        await self._client.end_session(
            session_id,
            SessionOutcome(
                type=type,
                value_amount=value_amount or 0,
                currency=currency or "USD",
            ),
        )
        if external_session_id is not None:
            self._registry.pop(external_session_id, None)

    @property
    def session_count(self) -> int:
        """Number of active sessions in the registry."""
        return len(self._registry)
