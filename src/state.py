
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InverterState:
    # Solar
    pv_voltage: float = 0.0
    pv_current: float = 0.0
    pv_power: float = 0.0

    # Battery
    battery_voltage: float = 0.0
    battery_current: float = 0.0
    battery_soc: float = 0.0

    # Inverter output
    output_voltage: float = 0.0
    output_current: float = 0.0
    output_power: float = 0.0
    output_frequency: float = 0.0

    # Inverter
    inverter_temperature: float = 0.0

    # Communication status
    connected: bool = False
    data_valid: bool = False
    last_update: datetime | None = None
    updated_fields: set[str] = field(default_factory=set)

    def update_measurements(self, measurements: dict):
        allowed = {
            "pv_voltage",
            "pv_current",
            "pv_power",
            "battery_voltage",
            "battery_current",
            "battery_soc",
            "output_voltage",
            "output_current",
            "output_power",
            "output_frequency",
            "inverter_temperature",
        }

        updated = False

        for name, value in measurements.items():
            if name in allowed and isinstance(value, (int, float)):
                setattr(self, name, float(value))
                self.updated_fields.add(name)
                updated = True

        if updated:
            self.data_valid = True
            self.last_update = datetime.now()

