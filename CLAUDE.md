# hass-startank

A Home Assistant custom integration (HACS) for the Safiery STAR-Tank BLE radar
tank sensor. Domain: `startank`. Code lives entirely under
`custom_components/startank/` as flat files — no subpackages. Keep it that way
unless a restructure is explicitly requested.

## Feedback loop — run this before you're done

```
script/check
```

This runs lint, type-check, and the full test suite, matching CI. Nothing here
needs real hardware — the BLE advertisement path is fully covered by synthetic
payloads in `tests/const.py`.

- `script/lint` — ruff format + autofix
- `script/lint-check` — ruff format/check without writing (CI-safe)
- `script/type-check` — `ty check`
- `script/test` — `pytest`, args pass through (`script/test -k parser`)

Pytest is strict (`filterwarnings = ["error"]`, `--strict-markers`); treat a
new warning as a signal, not noise to suppress.

Type checking uses [`ty`](https://github.com/astral-sh/ty); prefer a narrow
`# ty: ignore[rule] - reason` on the one offending line over a broader
suppression.

## How the integration works

The STAR-Tank broadcasts a 10-byte manufacturer-data payload under BLE company
id `0x0067` ('GN Hearing'), roughly every 60 s. There is no GATT, no pairing,
no connect — the integration subscribes to passive advertisements via
`homeassistant.components.bluetooth.async_register_callback`, decodes the
payload (see `parser.py` for the authoritative byte layout, cross-referenced
to Victron's `safiery.c`), and pushes the reading into a
`DataUpdateCoordinator`. Entities subclass `CoordinatorEntity` and read
`coordinator.data`.

Tank-geometry conversion (distance → level cm/%) lives in `sensor.py`'s
`_TankGeometryMixin` and reads config entry *options*, so updating tank
height/dead zone from the UI triggers a reload via `_async_options_updated` in
`__init__.py` without the user re-adding the device.

## File map

- `__init__.py` — entry setup/unload, options reload listener
- `manifest.json` — HA manifest, including `bluetooth` discovery matcher on
  manufacturer id 103 (`0x0067`), `connectable: false`
- `const.py` — domain, config/option keys, defaults
- `parser.py` — pure 10-byte advertisement decoder and NIC/MAC check. No I/O,
  no logger — safe to call from tests or anywhere
- `coordinator.py` — `StarTankCoordinator`: `DataUpdateCoordinator` driven by
  the BLE callback, holds the latest `StarTankReading` and last-seen RSSI
- `entity.py` — `StarTankEntity` base: device info + availability
- `config_flow.py` — Bluetooth discovery step + user-picks-from-advertised
  step, then a geometry step; also owns the options flow
- `sensor.py` — distance / level (cm) / level (%) / temperature / battery
  voltage / RSSI entities
- `binary_sensor.py` — low battery + sync button entities
- `strings.json` + `translations/en.json` — en is the source of truth; mirror
  structure when adding strings

## Conventions

- Never commit or push without being explicitly asked.
- Any change to the advertisement decoder MUST be accompanied by a cross-check
  against the Victron C reference driver linked at the top of `parser.py`.
  Victron has a known off-by-one on AccelZ (reads byte 10 of a 10-byte
  buffer); do not reintroduce it.
