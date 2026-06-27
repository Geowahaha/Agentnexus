# Japanese Melon Greenhouse — Dataset Pack

Production-ready dataset from your smart-farm telemetry — for automation thresholds and harvest-cycle alignment.

## Deliverables

1. Schema-aligned export (JSON/CSV) from OBOLLA Smart Farm DB
2. Channel coverage report vs Japanese melon greenhouse schema
3. Download URL for latest dataset pack
4. Import notes for IoT / smart-farm systems

## Data sources

- HTTP ingest: `POST /api/v1/smart-farm/ingest`
- MQTT (TLS): `mqtts://43.128.75.149:8883` topic `obolla/farm/{farm_id}/telemetry`
- Manual CSV/JSON upload at /smart-farm

## Principles

- Credit upstream sensors and farm operator
- Do not fabricate readings — export from DB only
- OBOLLA orchestrates QA + export; you own the farm data