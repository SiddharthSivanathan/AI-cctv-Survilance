-- VisionOps AI — PostgreSQL initialization.
-- Runs once on first container start (docker-entrypoint-initdb.d).

-- TimescaleDB: time-series hypertables for detections/events/analytics.
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- UUID generation (uuid_generate_v4) and gen_random_uuid support.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Case-insensitive text (emails, usernames).
CREATE EXTENSION IF NOT EXISTS citext;
