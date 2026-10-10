"""ANENJI Monitor: diagnóstico del puerto serial USB (sin transmitir datos).

Modelo de referencia: ANENJI SPI4865M150-300.

Este módulo SOLO inspecciona el dispositivo de Linux y los identificadores USB.
No abre el puerto, no consulta al inversor y no interpreta mediciones.
Su protocolo serial específico continúa sin verificarse.
"""

import argparse
import json
import os
import stat
from dataclasses import asdict, dataclass

import serial
from serial.tools import list_ports


DEFAULT_PORT = "/dev/ttyUSB0"
EXPECTED_VID = 0x1A86
EXPECTED_PID = 0x7523


@dataclass(frozen=True)
class SerialStatus:
    """Estado preliminar de hardware, apto para serializarse como JSON."""

    port: str
    state: str
    device_present: bool
    usb_detected: bool
    adapter_verified: bool
    port_accessible: bool
    protocol_verified: bool
    measurements_received: bool
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


def _status(
    port: str,
    state: str,
    message: str,
    *,
    device_present: bool = False,
    usb_detected: bool = False,
    adapter_verified: bool = False,
    port_accessible: bool = False,
) -> SerialStatus:
    """Construye estados consistentes sin atribuir mediciones al inversor."""
    return SerialStatus(
        port=port,
        state=state,
        device_present=device_present,
        usb_detected=usb_detected,
        adapter_verified=adapter_verified,
        port_accessible=port_accessible,
        protocol_verified=False,
        measurements_received=False,
        message=message,
    )


def inspect_serial_port(port: str | None = None) -> SerialStatus:
    """Detecta el CH340 y revisa permisos, sin abrir el puerto.

    ``port_accessible`` solo indica permisos aparentes de lectura/escritura.
    NO demuestra que el puerto pueda abrirse ni que el inversor responda.
    """
    selected_port = port if port is not None else os.getenv(
        "ANENJI_SERIAL_PORT", DEFAULT_PORT
    )

    if not selected_port:
        return _status("", "invalid_port", "No se especificó un puerto serial.")

    try:
        device_info = os.stat(selected_port)
    except FileNotFoundError:
        return _status(
            selected_port, "usb_disconnected", "El puerto serial no existe en Debian."
        )
    except OSError:
        return _status(
            selected_port, "inspection_error", "No se pudo inspeccionar el puerto serial."
        )

    if not stat.S_ISCHR(device_info.st_mode):
        return _status(
            selected_port, "invalid_device", "La ruta no es un dispositivo de caracteres."
        )

    try:
        available_ports = list_ports.comports(include_links=True)
    except (OSError, serial.SerialException):
        return _status(
            selected_port,
            "inspection_error",
            "No se pudo obtener la lista de puertos seriales.",
            device_present=True,
        )

    resolved_port = os.path.realpath(selected_port)
    port_info = next(
        (
            item for item in available_ports
            if os.path.realpath(item.device) == resolved_port
        ),
        None,
    )

    if port_info is None:
        return _status(
            selected_port,
            "adapter_unverified",
            "El dispositivo existe, pero PySerial no pudo identificar su adaptador USB.",
            device_present=True,
        )

    usb_detected = port_info.vid is not None and port_info.pid is not None
    adapter_verified = (
        port_info.vid == EXPECTED_VID and port_info.pid == EXPECTED_PID
    )

    if not adapter_verified:
        return _status(
            selected_port,
            "adapter_unverified",
            "El puerto no coincide con el CH340 esperado (VID:PID 1A86:7523).",
            device_present=True,
            usb_detected=usb_detected,
        )

    # La presencia de permisos no garantiza acceso exclusivo ni respuesta USB.
    accessible = os.access(selected_port, os.R_OK | os.W_OK)
    if not accessible:
        return _status(
            selected_port,
            "permission_denied",
            "CH340 detectado; faltan permisos de lectura o escritura.",
            device_present=True,
            usb_detected=True,
            adapter_verified=True,
        )

    return _status(
        selected_port,
        "protocol_pending",
        "CH340 identificado; permisos aparentes correctos. Protocolo sin confirmar.",
        device_present=True,
        usb_detected=True,
        adapter_verified=True,
        port_accessible=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnóstico USB pasivo del ANENJI Monitor")
    parser.add_argument("--port", help="Puerto Linux, por ejemplo /dev/ttyUSB0")
    args = parser.parse_args()

    result = inspect_serial_port(args.port)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    print("\nUSB ABIERTO: NO | COMANDOS ENVIADOS: NO | MEDICIONES: PENDIENTES")


if __name__ == "__main__":
    main()
