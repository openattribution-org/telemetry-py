# Changelog

## 0.4.0

Breaking: rename correlation header and field to neutral name.

- HTTP header `OA-Telemetry-ID` → `Content-Telemetry-ID`
- Wire JSON field and Python attribute `oa_telemetry_id` → `content_telemetry_id`
- Server adds migration `004_rename_telemetry_id.sql` (renames the column on the `events` table and rebuilds the dedup index).

Migration: rename any `oa_telemetry_id` references in caller code to `content_telemetry_id`. Run `make migrate` against your database to apply `004_rename_telemetry_id.sql`.

## 0.3.1

MCPSessionTracker, default_source_role, version-sync check.

## 0.2.0

Pluralise session paths.

## 0.1.0

Initial release.
