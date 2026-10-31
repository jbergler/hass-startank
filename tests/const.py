"""Deterministic STAR-Tank payloads shared across tests."""

from __future__ import annotations

TEST_ADDRESS = "AA:BB:CC:11:22:33"

# hw_id=5, battery=2.84 V (91/32), temp=23 °C (63-40), sync=1,
# distance=75.3 cm (753 / 10), NIC=11:22:33 (matches TEST_ADDRESS),
# accelX = 10/1024 g, accelY = -5/1024 g
SAMPLE_PAYLOAD = bytes(
    [
        5,
        91,
        (1 << 7) | 63,
        753 & 0xFF,
        (753 >> 8) & 0x3F,
        0x11,
        0x22,
        0x33,
        10,
        (-5) & 0xFF,
    ]
)
