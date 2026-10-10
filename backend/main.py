"""API local de ANENJI Monitor (SPI4865M150-300).

- Conserva las rutas y los campos consumidos por React.
- Consulta el estado del adaptador USB CH340 en cada petición.
- No abre el puerto serial, no transmite comandos y no simula lecturas.
- El protocolo específico del inversor aún no está verificado.

Ejecutar desde la raíz del proyecto:
    python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
"""

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Se ejecuta Uvicorn desde ~/anenji-monitor, como backend.main:app.
from backend.serial_reader import inspect_serial_port


LOGGER = logging.getLogger(__name__)
INVERTER_MODEL = "ANENJI SPI4865M150-300"

# ID, nombre visible y unidad. Son metadatos, NO mediciones.
FIELDS = (
    ("pv_power", "Producción solar", "W"),
    ("pv_voltage", "Voltaje solar", "V"),
    ("battery_voltage", "Voltaje batería", "V"),
    ("battery_soc", "Carga batería", "%"),
    ("output_power", "Consumo", "W"),
    ("output_voltage", "Voltaje salida", "V"),
    ("inverter_temperature", "Temperatura", "°C"),
)

app = FastAPI(
    title="ANENJI Monitor - Local API",
    description=(
        "API local de monitoreo, sin control eléctrico, para el "
        "ANENJI SPI4865M150-300."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url=None,
)


def _json(payload: dict[str, Any]) -> JSONResponse:
    """Desactiva el almacenamiento en caché de los estados y las lecturas."""
    return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})


def _serial_status() -> dict[str, Any]:
    """Consulta SOLO metadatos del puerto; nunca abre el USB.

    La inspección ocurre en cada petición: así se ven desconexiones y
    reconexiones sin reiniciar la API. Un adaptador reconocido NO es una
    comunicación verificada con el inversor.
    """
    try:
        return inspect_serial_port().to_dict()
    except Exception:
        # Fallar de forma conservadora: nunca afirmar que el equipo está conectado.
        LOGGER.exception("Error inesperado al inspeccionar el dispositivo USB")
        return {
            "port": None,
            "state": "inspection_error",
            "device_present": False,
            "usb_detected": False,
            "adapter_verified": False,
            "port_accessible": False,
            "protocol_verified": False,
            "measurements_received": False,
            "message": "No se pudo determinar el estado del puerto serial.",
        }


def _empty_measurements() -> list[dict[str, Any]]:
    """Devuelve únicamente campos pendientes; cero nunca significa 'sin datos'."""
    return [
        {
            "id": field_id,
            "label": label,
            "unit": unit,
            "value": None,
            "received": False,
        }
        for field_id, label, unit in FIELDS
    ]


@app.get("/")
def home() -> JSONResponse:
    """Información básica de la API y estado actual del USB."""
    status = _serial_status()
    return _json(
        {
            "application": "ANENJI Monitor",
            "model": INVERTER_MODEL,
            "api_status": "online",
            "inverter_connection": status["state"],
            "documentation": "/docs",
            "measurements_endpoint": "/api/measurements",
            "serial_status_endpoint": "/api/serial/status",
        }
    )


@app.get("/api/health")
def health() -> JSONResponse:
    """Distingue la salud de FastAPI de la disponibilidad del adaptador."""
    status = _serial_status()
    return _json(
        {
            "api": "online",
            "inverter": status["state"],
            "usb": {
                "device_present": status["device_present"],
                "adapter_verified": status["adapter_verified"],
                "port_accessible": status["port_accessible"],
            },
        }
    )


@app.get("/api/serial/status")
def serial_status() -> JSONResponse:
    """Diagnóstico local del CH340; no representa una lectura del inversor."""
    return _json(_serial_status())


@app.get("/api/measurements")
def measurements() -> JSONResponse:
    """Mantiene la estructura que espera React, sin lecturas simuladas."""
    status = _serial_status()
    return _json(
        {
            "device": INVERTER_MODEL,
            "connection": status["state"],
            "updated_at": None,
            "measurements": _empty_measurements(),
            # Campo adicional: React puede usarlo en una siguiente versión.
            "serial": status,
        }
    )
