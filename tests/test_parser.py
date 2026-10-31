"""Unit tests for the BLE advertisement decoder."""

from __future__ import annotations

import pytest

from custom_components.startank.parser import (
    PAYLOAD_LEN,
    decode,
    nic_matches_address,
)

from tests.const import SAMPLE_PAYLOAD, TEST_ADDRESS


def test_decode_known_payload() -> None:
    reading = decode(SAMPLE_PAYLOAD)
    assert reading is not None
    assert reading.hardware_id == 5
    assert reading.battery_voltage == pytest.approx(2.84375)
    assert reading.temperature_c == 23
    assert reading.sync_button is True
    assert reading.distance_cm == pytest.approx(75.3)
    assert reading.nic_last3 == (0x11, 0x22, 0x33)
    assert reading.accel_x_g == pytest.approx(10 / 1024)
    assert reading.accel_y_g == pytest.approx(-5 / 1024)


def test_decode_rejects_wrong_length() -> None:
    assert decode(b"\x00" * (PAYLOAD_LEN - 1)) is None
    assert decode(b"\x00" * (PAYLOAD_LEN + 1)) is None


def test_distance_masks_high_bits_not_overflow() -> None:
    # Set high two bits of byte 4 (which must be ignored): decoded distance
    # should still come from the lower 14 bits.
    payload = bytearray(SAMPLE_PAYLOAD)
    payload[4] |= 0b1100_0000
    reading = decode(bytes(payload))
    assert reading is not None
    assert reading.distance_cm == pytest.approx(75.3)


def test_low_battery_threshold() -> None:
    reading = decode(SAMPLE_PAYLOAD)
    assert reading is not None
    assert reading.low_battery is False

    # Battery byte 71 => 71/32 = 2.218 V => percent ≈ 2.8 % => low.
    low = bytearray(SAMPLE_PAYLOAD)
    low[1] = 71
    low_reading = decode(bytes(low))
    assert low_reading is not None
    assert low_reading.low_battery is True


def test_nic_matches_address() -> None:
    reading = decode(SAMPLE_PAYLOAD)
    assert reading is not None
    assert nic_matches_address(reading, TEST_ADDRESS)
    assert not nic_matches_address(reading, "AA:BB:CC:00:00:00")
    assert not nic_matches_address(reading, "garbage")
