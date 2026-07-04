# GPS Filter

A Home Assistant custom integration that filters noisy GPS updates from a source `device_tracker` entity and exposes a cleaner filtered tracker.

## Features

- Config flow for selecting a source entity and tuning filter thresholds
- Live GPS filtering with a coordinator-based architecture
- Rejects points that are:
  - too inaccurate
  - duplicated
  - moving too fast based on calculated speed
- Exposes the last received point, last accepted point, last filter result, and engine statistics through the coordinator state
- Logs accepted and rejected updates with distance, speed, and accuracy details

## How it works

1. The integration listens to a configured source `device_tracker` entity.
2. Each update is converted into a GPS point and passed through the filter engine.
3. The filter engine keeps the last accepted point and only forwards updates that pass the checks.
4. A Home Assistant device tracker entity exposes the filtered location.

## Configuration

1. Install the integration into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration from Settings → Devices & Services → Add Integration.
4. Choose the source `device_tracker` entity and set:
   - maximum speed (km/h)
   - maximum GPS accuracy

## Filter behavior

The engine currently accepts the first point, then rejects updates when:

- GPS accuracy exceeds the configured threshold
- the incoming point is an exact duplicate of the previous point
- the calculated movement speed exceeds the configured maximum

## Development

The project includes unit tests for the filter engine and coordinator flow.
