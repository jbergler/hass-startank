# hass-startank

A Home Assistant integration decoding Safiery STAR-Tank BLE radar advertisements
into HA entities.

## Language

**Advertisement**:
One 10-byte manufacturer-data broadcast from the STAR-Tank under BLE company id
`0x0067`. Every reading HA exposes is derived from the most recent one. The
sensor transmits roughly every 60 s and there is no connected/GATT path.
_Avoid_: packet, message, telegram.

**Reading**:
The parsed, immutable snapshot of one advertisement, exposed as the
`StarTankReading` dataclass. All entity values are pure functions of the
coordinator's current reading plus the entry's tank geometry options.

**Tank geometry**:
The three user-supplied dimensions — tank height, sensor dead zone, full-mark
offset — that turn raw distance (sensor face → liquid surface) into a liquid
level. Stored on the config entry's `options`, so changes trigger a reload.

**NIC check**:
Integrity match between the three bytes the sensor embeds in its advertisement
(bytes 5–7) and the last three octets of the device's BT MAC. The coordinator
drops any advertisement that fails this check.
