import React, { useEffect, useState } from 'react';

const EXPECTED = [
  ['pv_power', 'Producción solar', 'W'],
  ['pv_voltage', 'Voltaje solar', 'V'],
  ['battery_voltage', 'Voltaje batería', 'V'],
  ['battery_soc', 'Carga batería', '%'],
  ['output_power', 'Consumo', 'W'],
  ['output_voltage', 'Voltaje salida', 'V'],
  ['inverter_temperature', 'Temperatura', '°C']
];

function presentation(measurement, apiOk) {
  if (!apiOk) return { text: 'OFFLINE', status: 'offline' };
  if (!measurement?.received || typeof measurement.value !== 'number' || !Number.isFinite(measurement.value)) {
    return { text: 'SCANNING...', status: 'scanning' };
  }
  const value = new Intl.NumberFormat('es-PR', { maximumFractionDigits: 2 }).format(measurement.value);
  return {
    text: `${value} ${measurement.unit}`,
    status: measurement.value === 0 ? 'zero' : 'active'
  };
}

export default function App() {
  const [payload, setPayload] = useState(null);
  const [apiOk, setApiOk] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    async function refresh() {
      try {
        const response = await fetch('/api/measurements', { cache: 'no-store', signal: controller.signal });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (active) {
          setPayload(data);
          setApiOk(true);
        }
      } catch (error) {
        if (active && error.name !== 'AbortError') setApiOk(false);
      }
    }
    refresh();
    const timer = setInterval(refresh, 3000);
    return () => { active = false; clearInterval(timer); controller.abort(); };
  }, []);

  const measurements = Object.fromEntries((payload?.measurements ?? []).map(item => [item.id, item]));
  return (
    <main className="container">
      <header className="header">
        <div><p className="eyebrow">MONITOREO LOCAL · SIN NUBE</p><h1>ANENJI Monitor</h1><p className="subtitle">SPI4865M150-300 · Panel de solo lectura</p></div>
        <span className={`connection ${apiOk ? 'local' : 'lost'}`}>{apiOk ? 'API LOCAL' : 'SIN CONEXIÓN'}</span>
      </header>

      <section className="notice">
        {apiOk ? 'La aplicación funciona. El protocolo serial del inversor aún no está implementado: las mediciones no se inventan.' : 'No se puede conectar al servidor Python. Comprueba que FastAPI esté encendido.'}
      </section>

      <section className="grid" aria-label="Mediciones">
        {EXPECTED.map(([id, label, unit]) => {
          const item = measurements[id];
          const display = presentation(item || { received: false, unit }, apiOk);
          return (
            <article className="metric" key={id}>
              <h2>{label}</h2>
              <div className={`reading ${display.status}`}>{display.text}</div>
              <p className="detail">{display.status === 'scanning' ? 'Esperando primera lectura válida' : display.status === 'offline' ? 'API no disponible' : display.status === 'zero' ? 'Cero confirmado por el equipo' : 'Medición recibida'}</p>
            </article>
          );
        })}
      </section>
      <footer>Datos reales únicamente cuando el lector USB y el protocolo del ANENJI estén verificados. Un cero real no indica por sí solo una falla.</footer>
    </main>
  );
}
