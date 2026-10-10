
"""
ANENJI MONITOR - SERIAL DIAGNOSTIC

Model: ANENJI SPI4865M150-300
Device: USB CH340
Port: /dev/ttyUSB0

Purpose:
    Listen for incoming serial data.

Security:
    - No application commands are sent.
    - No data is uploaded to the cloud.
    - No measurements are saved.
    - The serial port closes automatically.

The exact inverter protocol is not yet confirmed.
"""

import time
import serial


# Serial communication configuration
PORT = "/dev/ttyUSB0"
BAUDRATE = 9600
DURATION = 15


def main():
    print("=" * 50)
    print("ANENJI MONITOR - SERIAL DIAGNOSTIC")
    print("=" * 50)

    print(f"Port: {PORT}")
    print(f"Baud rate: {BAUDRATE}")
    print(f"Duration: {DURATION} seconds")
    print()

    connection = None

    try:
        # Prepare the serial connection.
        # Do not send any application commands.
        connection = serial.Serial(
            port=None,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
            exclusive=True,
        )

        # Request inactive control signals.
        connection.dtr = False
        connection.rts = False

        connection.port = PORT
        connection.open()

        print("SERIAL PORT OPEN")
        print("LISTENING FOR DATA...")
        print()

        total_bytes = 0
        deadline = time.monotonic() + DURATION

        # Passive listening only.
        while time.monotonic() < deadline:

            data = connection.read(
                connection.in_waiting or 1
            )

            if data:
                total_bytes += len(data)

                # Display incoming bytes in hexadecimal.
                print("RECEIVED:", data.hex(" "))

        print()
        print("=" * 50)

        if total_bytes == 0:
            print("NO DATA RECEIVED")
            print("The inverter may require a query.")
        else:
            print(f"TOTAL BYTES: {total_bytes}")

    except (serial.SerialException, OSError) as error:
        print(f"SERIAL ERROR: {error}")

    finally:
        if connection is not None and connection.is_open:
            connection.close()
            print("SERIAL PORT CLOSED")


if __name__ == "__main__":
    main()

