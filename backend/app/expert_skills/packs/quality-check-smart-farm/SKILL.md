# Quality Check Flow — Smart Farm

OBOLLA loads **live sensor readings from your Smart Farm DB** — buyers do not paste CSV manually.

## Pipeline

Checklist → Run → Review → Verdict

## Sensor channels (Japanese melon greenhouse default)

- temp_day_c, temp_night_c, humidity_pct, uv_index, light_lux, co2_ppm
- ec_ms, ph, soil_moisture_pct, brix

## QA rules

1. Compare readings against crop schema ranges and growth stage
2. Flag missing channels, stale timestamps, impossible values
3. Verdict: **READY** or **NEEDS_CORRECTION** with P0/P1 list
4. Never invent sensor values — use telemetry block only

## Buyer input

Optional notes in task text. Link farm via `farm_id: <uuid>` or use your default farm from /smart-farm.