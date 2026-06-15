-- Add content_grounded to events_type_check constraint
-- content_grounded was added to the OpenAttribution standard after 001_telemetry_schema.sql
-- was written; it is defined as a core EventType in src/openattribution/telemetry/schema.py.
-- Without this migration, inserting a content_grounded event fails with a CheckViolation.

ALTER TABLE events DROP CONSTRAINT IF EXISTS events_type_check;

ALTER TABLE events
    ADD CONSTRAINT events_type_check CHECK (
        event_type IN (
            -- Content lifecycle events
            'content_retrieved', 'content_grounded', 'content_displayed', 'content_engaged', 'content_cited',
            -- Conversation events
            'turn_started', 'turn_completed',
            -- Commerce events
            'product_viewed', 'product_compared', 'cart_add', 'cart_remove',
            'checkout_started', 'checkout_completed', 'checkout_abandoned'
        )
    );
