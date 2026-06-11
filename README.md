# OpenAttribution telemetry SDK for Python

[![PyPI version](https://badge.fury.io/py/openattribution-telemetry.svg)](https://badge.fury.io/py/openattribution-telemetry)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Python SDK for the [Content Telemetry](https://github.com/SPUR-Coalition/telemetry) standard - the neutral open standard for reporting how AI agents use content. Track what content influenced AI agent responses.

Part of the [OpenAttribution](https://openattribution.org) project.

## Installation

```bash
pip install openattribution-telemetry
# or: uv add openattribution-telemetry
```

For the reference server:

```bash
pip install openattribution-telemetry[server]
```

## Quick start

```python
import asyncio
from uuid import uuid4

from openattribution.telemetry import (
    Client,
    ConversationTurn,
    SessionOutcome,
    UserContext,
)

async def main():
    async with Client(
        endpoint="https://api.example.com/telemetry",
        api_key="your-api-key"
    ) as client:

        # Start a session
        session_id = await client.start_session(
            content_scope="my-content-mix",
            user_context=UserContext(segments=["premium"])
        )

        # Record content retrieval
        content_url = "https://www.wirecutter.com/reviews/best-wireless-headphones"
        await client.record_event(
            session_id=session_id,
            event_type="content_retrieved",
            content_url=content_url,
        )

        # Record a conversation turn with privacy controls
        await client.record_event(
            session_id=session_id,
            event_type="turn_completed",
            turn=ConversationTurn(
                privacy_level="intent",
                query_intent="product_research",
                response_type="recommendation",
                topics=["headphones", "wireless"],
                content_urls_cited=[content_url],
                response_tokens=150,
            )
        )

        # End session with outcome
        await client.end_session(
            session_id=session_id,
            outcome=SessionOutcome(
                type="conversion",
                value_amount=9999,  # $99.99 in cents
                currency="USD",
            )
        )

asyncio.run(main())
```

## Bulk upload

If your agent collects telemetry locally and uploads after the session ends, use `upload_session` to send everything in one request:

```python
from datetime import UTC, datetime
from uuid import uuid4

from openattribution.telemetry import (
    Client,
    SessionOutcome,
    TelemetryEvent,
    TelemetrySession,
)

session = TelemetrySession(
    session_id=uuid4(),
    initiator_type="agent",
    agent_id="my-agent",
    content_scope="my-content-mix",
    started_at=datetime.now(UTC),
    events=[
        TelemetryEvent(
            id=uuid4(),
            type="content_retrieved",
            timestamp=datetime.now(UTC),
            content_url="https://www.rtings.com/headphones/reviews/best-noise-cancelling",
        ),
    ],
    outcome=SessionOutcome(type="conversion", value_amount=9999),
)

async with Client(endpoint="https://api.example.com/telemetry", api_key="key") as client:
    server_session_id = await client.upload_session(session)
```

## Extraction utilities

Helpers for extracting content URLs from AI-generated text:

```python
from openattribution.telemetry import (
    extract_citation_urls,
    extract_indexed_citations,
    extract_result_urls,
)

# Extract URLs from Markdown links and bare URLs in AI responses
urls = extract_citation_urls("See [Wirecutter](https://example.com/review) for details")
# ["https://example.com/review"]

# Resolve [n] citation markers to URLs using a numbered source list
sources = ["https://guardian.com/article-1", "https://guardian.com/article-2"]
cited = extract_indexed_citations("The policy was announced [1].", sources)
# ["https://guardian.com/article-1"]

# Extract URLs from search result objects (works with most search APIs)
results = [{"url": "https://a.com"}, {"url": "https://b.com"}]
urls = extract_result_urls(results)
# ["https://a.com", "https://b.com"]
```

## Commerce protocol bridges

### UCP integration

```python
from openattribution.telemetry import session_to_attribution

attribution = session_to_attribution(telemetry_session)
# Embed in UCP checkout payload
```

### ACP integration

```python
from openattribution.telemetry import session_to_content_attribution

content_attribution = session_to_content_attribution(telemetry_session)
# Include in ACP checkout request
```

## Reference server

A working FastAPI server implementation is included:

```bash
pip install openattribution-telemetry[server]
uvicorn openattribution.telemetry_server.main:app --host 0.0.0.0 --port 8007
```

See [`server/README.md`](./server/README.md) for setup, endpoints, and deployment.

## Specification

The Content Telemetry standard is stewarded by the SPUR Coalition: [SPUR-Coalition/telemetry](https://github.com/SPUR-Coalition/telemetry). Schemas resolve at [contenttelemetry.org](https://contenttelemetry.org).

This SDK implements the standard and vendors a copy of `schema.json` for validation.

## Licence

Apache 2.0 - see [LICENSE](./LICENSE) for details.
