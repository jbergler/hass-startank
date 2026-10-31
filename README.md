# hass-startank

Home Assistant custom integration for the **Safiery STAR-Tank** phased-coherent
radar tank sensor — the one that was previously only usable through Victron
Venus OS. No Cerbo GX, no Venus bridge, no pairing: the sensor broadcasts a
10-byte BLE advertisement roughly every 60 s and this integration decodes it
directly on your HA host.

## What you get

Per configured sensor, under one device:

| Entity                           | Notes                                                    |
| -------------------------------- | -------------------------------------------------------- |
| `sensor.<name>_distance`         | Raw radar distance from sensor face to the liquid (cm)   |
| `sensor.<name>_level`            | Liquid depth = tank height − distance (cm)               |
| `sensor.<name>_level`            | Same as a percentage (0–100 %)                           |
| `sensor.<name>_temperature`      | Sensor body temperature (°C)                             |
| `sensor.<name>_battery_voltage`  | CR2477 cell voltage (disabled by default)                |
| `sensor.<name>_signal_strength`  | Last-advert RSSI (disabled by default)                   |
| `binary_sensor.<name>_battery_low` | True below ~15 % of the CR2477 usable span            |
| `binary_sensor.<name>_sync_button` | Reflects the physical sync button (disabled by default) |

## Requirements

- Home Assistant with a working **Bluetooth** integration (HAOS on a Pi, an ESPHome
  Bluetooth proxy, or any supported adapter).
- A Safiery **STAR-Tank water** or compatible radar puck powered on and advertising.

## Install

### Via HACS (recommended)

1. HACS → Integrations → ⋮ → Custom repositories.
2. Add `https://github.com/jbergler/hass-startank` as an **Integration**.
3. Install **Safiery STAR-Tank**, restart HA.

### Manual

Copy `custom_components/startank/` into your HA `config/custom_components/`
directory and restart HA.

## Set up

When the sensor is in range, HA will show a **Discovered: STAR-Tank XXXXXX**
notification — accept it and enter your tank geometry:

| Option                 | Default   | Meaning                                                       |
| ---------------------- | --------- | ------------------------------------------------------------- |
| Tank height (cm)       | 100       | Internal top-to-bottom height.                                |
| Sensor dead zone (cm)  | 3         | Minimum distance the sensor can resolve (per Safiery spec).   |
| Full offset (cm)       | 0         | Distance from the sensor face down to the "100 % full" mark.  |

Nothing was discovered? Open **Settings → Devices & Services → Add integration
→ Safiery STAR-Tank** and pick the device by MAC address.

## How it works

The STAR-Tank uses Bluetooth 5.3 advertising-only mode under the GN Hearing
company id (`0x0067`), a 10-byte manufacturer-data payload containing hardware
id, battery voltage, temperature, raw distance (14 bits, 0.1 cm units), the
last three MAC octets for integrity, and X/Y accelerometer. The decoder in
`parser.py` mirrors the fields in Victron's upstream `dbus-ble-sensors`
reference. See the module docstring there for the full layout.

Each entry runs one `DataUpdateCoordinator` subscribed via
`bluetooth.async_register_callback` with a passive scanning filter — no
connection to the device is ever opened. Entities become `unavailable` only if
HA restarts without a cached advert; otherwise they hold the last reading.

## References

- Safiery product page: <https://safiery.com/product?id=star-tank-water>
- Victron C reference driver: <https://github.com/victronenergy/dbus-ble-sensors/blob/master/src/safiery.c>
- Venus OS Python port (ldenisey): <https://github.com/ldenisey/venus-os-dbus-ble-sensors-py>
