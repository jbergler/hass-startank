"""Decode Safiery STAR-Tank BLE advertisements.

The STAR-Tank is a phased-coherent radar tank sensor that broadcasts a
10-byte manufacturer-data blob (company id 0x0067, 'GN Hearing') roughly every
60 s. There is no GATT, no pairing — this is pure advertising.

Payload layout (little-endian bit packing to match Victron's reference):

| byte  | field          | notes                                        |
| ----- | -------------- | -------------------------------------------- |
| 0     | HardwareID     | bits 0..6                                    |
| 1     | BatteryVoltage | bits 0..6, scale 1/32 V                      |
| 2     | Temperature    | bits 0..6, bias -40 °C                       |
| 2 b7  | SyncButton     | 1 while sync button is held                  |
| 3-4   | RawValue (U14) | distance sensor->liquid in 0.1 cm units      |
| 5-7   | NIC            | last three MAC octets, for integrity match   |
| 8     | AccelX (S8)    | scale 1/1024 g                               |
| 9     | AccelY (S8)    | scale 1/1024 g                               |

AccelZ in the Victron reference reads byte 10, which is out of bounds for the
documented 10-byte payload (known Victron off-by-one); omitted here.

References:
    https://github.com/victronenergy/dbus-ble-sensors/blob/master/src/safiery.c
    https://github.com/ldenisey/venus-os-dbus-ble-sensors-py
"""

from __future__ import annotations

from dataclasses import dataclass

PAYLOAD_LEN = 10


@dataclass(frozen=True, slots=True)
class StarTankReading:
    """One decoded STAR-Tank advertisement."""

    hardware_id: int
    battery_voltage: float
    temperature_c: int
    sync_button: bool
    distance_cm: float
    nic_last3: tuple[int, int, int]
    accel_x_g: float
    accel_y_g: float

    @property
    def low_battery(self) -> bool:
        """True if the CR2477 cell is below ~15% of its usable span.

        Mirrors Venus OS's threshold: percent = (V - 2.2) / 0.65 * 100.
        """
        pct = max(0.0, min(100.0, (self.battery_voltage - 2.2) / 0.65 * 100.0))
        return pct < 15.0


def decode(payload: bytes) -> StarTankReading | None:
    """Return a reading, or None if the payload is not a STAR-Tank advert."""
    if len(payload) != PAYLOAD_LEN:
        return None
    raw_u16 = payload[3] | (payload[4] << 8)
    return StarTankReading(
        hardware_id=payload[0] & 0x7F,
        battery_voltage=(payload[1] & 0x7F) / 32.0,
        temperature_c=(payload[2] & 0x7F) - 40,
        sync_button=bool(payload[2] & 0x80),
        distance_cm=(raw_u16 & 0x3FFF) / 10.0,
        nic_last3=(payload[5], payload[6], payload[7]),
        accel_x_g=_s8(payload[8]) / 1024.0,
        accel_y_g=_s8(payload[9]) / 1024.0,
    )


def nic_matches_address(reading: StarTankReading, address: str) -> bool:
    """Check the advert's NIC against the last 3 octets of a BT address."""
    try:
        parts = [int(p, 16) for p in address.split(":")]
    except ValueError:
        return False
    if len(parts) != 6:
        return False
    return tuple(parts[3:]) == reading.nic_last3


def _s8(b: int) -> int:
    return b - 256 if b >= 128 else b
