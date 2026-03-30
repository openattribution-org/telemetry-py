-- Add source_role and oa_telemetry_id columns to events table
-- Supports retrieval source identification and cross-observer deduplication (spec v0.1)

ALTER TABLE events
    ADD COLUMN source_role TEXT,
    ADD COLUMN oa_telemetry_id UUID;

-- source_role must be one of the standard roles
ALTER TABLE events
    ADD CONSTRAINT events_source_role_check CHECK (
        source_role IS NULL OR source_role IN ('origin', 'edge', 'index', 'agent')
    );

-- Index for deduplication: group by correlation ID + content URL
CREATE INDEX idx_events_telemetry_id ON events(oa_telemetry_id, content_url)
    WHERE oa_telemetry_id IS NOT NULL;

-- Index for filtering by source role (e.g., "show me all origin-reported retrievals")
CREATE INDEX idx_events_source_role ON events(source_role)
    WHERE source_role IS NOT NULL;
