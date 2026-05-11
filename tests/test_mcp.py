"""Tests for the MCP session tracker and Client.default_source_role."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
import pytest

from openattribution.telemetry import Client, MCPSessionTracker


def _response(json_data: dict, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json=json_data,
        request=httpx.Request("POST", "https://telemetry.example.com"),
    )


@pytest.fixture
def client() -> Client:
    return Client(
        endpoint="https://telemetry.example.com",
        api_key="test-key",
        fail_silently=False,
        max_retries=0,
    )


class TestMCPSessionTracker:
    @pytest.mark.asyncio
    async def test_reuses_session_for_same_external_id(self, client):
        session_id = uuid4()
        with patch.object(
            client.client, "request", new_callable=AsyncMock
        ) as request:
            request.return_value = _response({"session_id": str(session_id)})
            tracker = MCPSessionTracker(client, content_scope="forage-shopping")

            first = await tracker.get_or_create_session("conv-1")
            second = await tracker.get_or_create_session("conv-1")

        assert first == session_id == second
        # Only one /sessions/start call — the second resolved from the registry.
        start_calls = [c for c in request.call_args_list if c.args[1].endswith("/sessions/start")]
        assert len(start_calls) == 1
        assert tracker.session_count == 1

    @pytest.mark.asyncio
    async def test_track_retrieved_stamps_agent_source_role(self, client):
        session_id = uuid4()
        with patch.object(
            client.client, "request", new_callable=AsyncMock
        ) as request:
            request.return_value = _response({"session_id": str(session_id)})
            tracker = MCPSessionTracker(client, content_scope="forage-shopping")
            await tracker.track_retrieved(
                "conv-1", ["https://forageshopping.com/guides/headphones"]
            )

        events_call = next(c for c in request.call_args_list if c.args[1].endswith("/events"))
        payload = events_call.kwargs["json"]
        assert payload["session_id"] == str(session_id)
        assert len(payload["events"]) == 1
        event = payload["events"][0]
        assert event["type"] == "content_retrieved"
        assert event["source_role"] == "agent"
        assert event["content_url"] == "https://forageshopping.com/guides/headphones"

    @pytest.mark.asyncio
    async def test_track_checkout_completed_ends_session(self, client):
        session_id = uuid4()
        with patch.object(
            client.client, "request", new_callable=AsyncMock
        ) as request:
            request.return_value = _response({"session_id": str(session_id)})
            tracker = MCPSessionTracker(client, content_scope="forage-shopping")
            await tracker.get_or_create_session("conv-1")
            await tracker.track_checkout(
                "conv-1", type="completed", value_amount=4999, currency="USD"
            )

        paths = [c.args[1] for c in request.call_args_list]
        assert any(p.endswith("/events") for p in paths)
        assert any(p.endswith("/sessions/end") for p in paths)
        assert tracker.session_count == 0

    @pytest.mark.asyncio
    async def test_record_event_no_ops_without_existing_session(self, client):
        with patch.object(
            client.client, "request", new_callable=AsyncMock
        ) as request:
            tracker = MCPSessionTracker(client)
            await tracker.record_event(
                "conv-never-started", "checkout_started", data={"checkout_id": "x"}
            )
        request.assert_not_called()

    @pytest.mark.asyncio
    async def test_record_event_attaches_to_existing_session(self, client):
        session_id = uuid4()
        with patch.object(
            client.client, "request", new_callable=AsyncMock
        ) as request:
            request.return_value = _response({"session_id": str(session_id)})
            tracker = MCPSessionTracker(client, content_scope="forage-shopping")
            await tracker.get_or_create_session("conv-1")
            assert tracker.get_session("conv-1") == session_id
            await tracker.record_event(
                "conv-1", "checkout_started", data={"checkout_id": "abc"}
            )
        events_call = next(c for c in request.call_args_list if c.args[1].endswith("/events"))
        event = events_call.kwargs["json"]["events"][0]
        assert event["type"] == "checkout_started"
        assert event["source_role"] == "agent"
        assert event["data"] == {"checkout_id": "abc"}

    @pytest.mark.asyncio
    async def test_empty_urls_no_op(self, client):
        with patch.object(
            client.client, "request", new_callable=AsyncMock
        ) as request:
            tracker = MCPSessionTracker(client)
            await tracker.track_retrieved("conv-1", [])
            await tracker.track_cited("conv-1", [])
            await tracker.track_engaged("conv-1", [])
        request.assert_not_called()


class TestDefaultSourceRole:
    @pytest.mark.asyncio
    async def test_stamped_when_not_set(self, mock_event):
        client = Client(
            endpoint="https://telemetry.example.com",
            api_key="k",
            fail_silently=False,
            max_retries=0,
            default_source_role="agent",
        )
        with patch.object(
            client.client, "request", new_callable=AsyncMock, return_value=_response({})
        ) as request:
            await client.record_events(uuid4(), [mock_event(source_role=None)])
        payload = request.call_args.kwargs["json"]
        assert payload["events"][0]["source_role"] == "agent"

    @pytest.mark.asyncio
    async def test_per_event_role_wins(self, mock_event):
        client = Client(
            endpoint="https://telemetry.example.com",
            api_key="k",
            fail_silently=False,
            max_retries=0,
            default_source_role="agent",
        )
        with patch.object(
            client.client, "request", new_callable=AsyncMock, return_value=_response({})
        ) as request:
            await client.record_events(uuid4(), [mock_event(source_role="edge")])
        payload = request.call_args.kwargs["json"]
        assert payload["events"][0]["source_role"] == "edge"


@pytest.fixture
def mock_event():
    from datetime import UTC, datetime

    from openattribution.telemetry import TelemetryEvent

    def _make(source_role=None):
        return TelemetryEvent(
            id=uuid4(),
            type="content_retrieved",
            timestamp=datetime.now(UTC),
            source_role=source_role,
            content_url="https://example.com/x",
        )

    return _make
