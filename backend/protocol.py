
"""
ANENJI Monitor - Protocol utilities.

Generic Modbus RTU functions for investigating
possible inverter communication.

IMPORTANT:
- Compatibility with SPI4865M150-300 is unverified.
- This file does NOT open the serial port.
- This file does NOT send commands.
- Tests use simulated responses only.
"""


def crc16_modbus(data: bytes) -> int:
    """Calculate standard Modbus RTU CRC-16."""
    crc = 0xFFFF

    for byte in data:
        crc ^= byte

        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1

    return crc


def add_crc(data: bytes) -> bytes:
    """Append CRC, least-significant byte first."""
    crc = crc16_modbus(data)
    return data + crc.to_bytes(2, "little")


def build_read_request(
    slave: int,
    register: int,
    count: int = 1,
) -> bytes:
    """
    Build a Modbus function 0x03 read request.

    Only creates the bytes in memory.
    It does not transmit anything.
    """
    if not 1 <= slave <= 247:
        raise ValueError("Invalid slave address")

    if not 0 <= register <= 65535:
        raise ValueError("Invalid register address")

    if not 1 <= count <= 32:
        raise ValueError("Invalid register count")

    if register + count > 65536:
        raise ValueError("Register range exceeds limit")

    payload = (
        bytes([slave, 0x03])
        + register.to_bytes(2, "big")
        + count.to_bytes(2, "big")
    )

    return add_crc(payload)


def parse_read_response(
    frame: bytes,
    slave: int,
    count: int,
) -> list[int]:
    """Validate and decode a Modbus 0x03 response."""

    if len(frame) < 5:
        raise ValueError("Incomplete response")

    expected_crc = crc16_modbus(frame[:-2])
    received_crc = int.from_bytes(frame[-2:], "little")

    if received_crc != expected_crc:
        raise ValueError("Invalid CRC")

    if frame[0] != slave:
        raise ValueError("Unexpected slave address")

    if frame[1] == 0x83:
        raise ValueError(
            f"Modbus exception: {frame[2]}"
        )

    if frame[1] != 0x03:
        raise ValueError("Unexpected function code")

    if frame[2] != count * 2:
        raise ValueError("Unexpected data length")

    if len(frame) != 3 + count * 2 + 2:
        raise ValueError("Invalid frame size")

    values = []

    for offset in range(3, 3 + count * 2, 2):
        values.append(
            int.from_bytes(
                frame[offset:offset + 2],
                "big",
            )
        )

    return values


def main():
    """Run offline protocol tests without USB."""

    print("ANENJI MONITOR - PROTOCOL TEST")
    print("--------------------------------")
    print("MODE: OFFLINE")
    print("USB: NOT ACCESSED")
    print()

    # Known Modbus framing example.
    request = build_read_request(
        slave=1,
        register=0,
        count=1,
    )

    assert request == bytes.fromhex(
        "01 03 00 00 00 01 84 0A"
    )

    print("REQUEST TEST: PASSED")
    print("Example request:", request.hex(" "))

    # Construct a simulated response.
    fake_response = add_crc(
        bytes.fromhex("01 03 02 12 34")
    )

    decoded = parse_read_response(
        fake_response,
        slave=1,
        count=1,
    )

    assert decoded == [4660]

    print("CRC TEST: PASSED")
    print("RESPONSE TEST: PASSED")
    print("Simulated value:", decoded[0])

    # Verify that corrupted data is rejected.
    corrupted = bytearray(fake_response)
    corrupted[3] ^= 0x01

    try:
        parse_read_response(bytes(corrupted), 1, 1)
    except ValueError:
        print("CORRUPTION TEST: PASSED")
    else:
        raise AssertionError(
            "Corrupted response was accepted"
        )

    print()
    print("ALL OFFLINE TESTS PASSED")
    print("No commands were sent to the inverter.")


if __name__ == "__main__":
    main()

