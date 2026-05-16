-- Rename oa_telemetry_id → content_telemetry_id to match the neutral
-- Content-Telemetry-ID header introduced in spec v0.4.

ALTER TABLE events
    RENAME COLUMN oa_telemetry_id TO content_telemetry_id;

DROP INDEX IF EXISTS idx_events_telemetry_id;

CREATE INDEX idx_events_telemetry_id ON events(content_telemetry_id, content_url)
    WHERE content_telemetry_id IS NOT NULL;
