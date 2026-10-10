
"""
============================================================
ANENJI MONITOR - LOCAL BACKEND API
============================================================

Inverter: ANENJI SPI4865M150-300
Language: Python 3
Framework: FastAPI

PURPOSE:
    Provide a local API for displaying inverter measurements
    in the React dashboard.

SECURITY:
    - No cloud connection required.
    - No passwords or personal IP addresses stored.
    - No electrical configuration commands.
    - No simulated inverter measurements.
    - Intended to run on localhost only.

IMPORTANT:
    The serial protocol for this exact inverter model
    has not yet been verified.

    Therefore, actual inverter readings are NOT implemented.

    Until real measurements become available, values are
    returned as null with received=False.

============================================================
"""

# ------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------

# FastAPI provides the local HTTP API.
from fastapi import FastAPI

# JSONResponse allows us to return JSON with cache controls.
from fastapi.responses import JSONResponse


# ------------------------------------------------------------
# APPLICATION CONFIGURATION
# ------------------------------------------------------------

app = FastAPI(
    title="ANENJI Monitor - Local API",

    description=(
        "Local read-only monitoring API for the "
        "ANENJI SPI4865M150-300 solar inverter."
    ),

    version="0.1.0",

    # Enable Swagger documentation.
    docs_url="/docs",

    # Disable the alternative documentation interface.
    redoc_url=None,
)


# ------------------------------------------------------------
# INVERTER IDENTIFICATION
# ------------------------------------------------------------

# Public equipment model, not a personal serial number.
INVERTER_MODEL = "ANENJI SPI4865M150-300"


# ------------------------------------------------------------
# AVAILABLE MEASUREMENTS
# ------------------------------------------------------------

# Each entry contains:
#
# 1. Internal variable name
# 2. Display name
# 3. Measurement unit
#
# These definitions are not actual measurements.
# The hardware protocol must be verified before values
# can be received.

FIELDS = (
    ("pv_power", "Producción solar", "W"),
    ("pv_voltage", "Voltaje solar", "V"),
    ("battery_voltage", "Voltaje batería", "V"),
    ("battery_soc", "Carga batería", "%"),
    ("output_power", "Consumo", "W"),
    ("output_voltage", "Voltaje salida", "V"),
    ("inverter_temperature", "Temperatura", "°C"),
)


# ------------------------------------------------------------
# CURRENT COMMUNICATION STATE
# ------------------------------------------------------------

# This indicates whether real serial monitoring has been
# implemented and verified.
#
# It does NOT indicate whether the FastAPI server is running.

inverter_connection = "protocol_pending"


# ------------------------------------------------------------
# ROUTE 1 - API HOME
# ------------------------------------------------------------

@app.get("/")
def home():
    """
    Basic information about the local API.

    URL:
        http://127.0.0.1:8000/

    This route does not access the inverter.
    """

    return JSONResponse(
        content={
            "application": "ANENJI Monitor",
            "model": INVERTER_MODEL,
            "api_status": "online",
            "inverter_connection": inverter_connection,
            "documentation": "/docs",
            "measurements_endpoint": "/api/measurements",
        },
        headers={"Cache-Control": "no-store"},
    )


# ------------------------------------------------------------
# ROUTE 2 - API HEALTH CHECK
# ------------------------------------------------------------

@app.get("/api/health")
def health():
    """
    Verify that the Python API is running.

    URL:
        http://127.0.0.1:8000/api/health

    IMPORTANT:
        API online does not mean inverter connected.
    """

    return JSONResponse(
        content={
            "api": "online",
            "inverter": inverter_connection,
        },
        headers={"Cache-Control": "no-store"},
    )


# ------------------------------------------------------------
# ROUTE 3 - INVERTER MEASUREMENTS
# ------------------------------------------------------------

@app.get("/api/measurements")
def measurements():
    """
    Return the current measurement structure.

    URL:
        http://127.0.0.1:8000/api/measurements

    CURRENT BEHAVIOR:
        All readings are pending because the inverter
        serial protocol has not been implemented.

    VALUES:
        value = None
            No valid measurement has been received.

        received = False
            The field has not been measured successfully.

    FRONTEND:
        React uses these fields to display SCANNING...

    FUTURE:
        A verified serial reader will supply actual
        readings from /dev/ttyUSB0.
    """

    # Build the measurement list from the field definitions.
    measurement_list = []

    for field_id, label, unit in FIELDS:

        measurement_list.append(
            {
                "id": field_id,
                "label": label,
                "unit": unit,

                # No hardware measurement received yet.
                "value": None,

                # React will display SCANNING...
                "received": False,
            }
        )

    # Return the complete API response.
    return JSONResponse(
        content={
            "device": INVERTER_MODEL,

            # Connection status of the inverter protocol.
            "connection": inverter_connection,

            # No verified measurement timestamp exists.
            "updated_at": None,

            # Measurements expected by the React dashboard.
            "measurements": measurement_list,
        },

        # Prevent browsers from storing measurements in cache.
        headers={
            "Cache-Control": "no-store",
        },
    )


# ------------------------------------------------------------
# END OF FILE
# ------------------------------------------------------------

