import React, { useEffect, useState } from 'react';

// Los siete indicadores que ya utiliza nuestro dashboard.
// Son definiciones de pantalla, no mediciones inventadas.
const EXPECTED = [
  ['pv_power', 'Producción solar', 'W'],
  ['pv_voltage', 'Voltaje solar', 'V'],
  ['battery_voltage', 'Voltaje batería', 'V'],
  ['battery_soc', 'Carga batería', '%'],
  ['output_power', 'Consumo', 'W'],
  ['output_voltage', 'Voltaje salida', 'V'],
  ['inverter_temperature', 'Temperatura', '°C'],
];

const POLL_INTERVAL_MS = 3000;
const REQUEST_TIMEOUT_MS = 7000;
const numberFormat = new Intl.NumberFormat('es-PR', {
  maximumFractionDigits: 2,
});

const USB_ERRORS = new Set([
  'usb_disconnected',
  'permission_denied',
  'adapter_unverified',
  'invalid_device',
  'invalid_port',
  'inspection_error',
  'usb_error',
]);

/** Estado de la API; no equivale al estado del inversor. */
function apiBadge(apiState) {
  if (apiState === 'online') return { label: 'API LOCAL', tone: 'local' };
  if (apiState === 'offline') return { label: 'API OFFLINE', tone: 'lost' };
  return { label: 'COMPROBANDO API', tone: 'pending' };
}

/** Disponibilidad del adaptador CH340 (no confirma comunicación con el inversor). */
function usbBadge(apiState, serial) {
  if (apiState !== 'online') {
    return { label: 'USB SIN VERIFICAR', tone: 'unknown' };
  }

  switch (serial?.state) {
    case 'usb_disconnected':
      return { label: 'USB DESCONECTADO', tone: 'lost' };
    case 'permission_denied':
      return { label: 'USB SIN PERMISOS', tone: 'lost' };
    case 'adapter_unverified':
      return { label: 'ADAPTADOR NO VERIFICADO', tone: 'pending' };
    case 'invalid_device':
    case 'invalid_port':
    case 'inspection_error':
    case 'usb_error':
      return { label: 'ERROR DE USB', tone: 'lost' };
    default:
      if (serial?.adapter_verified === true && serial?.port_accessible === true) {
        return { label: 'CH340 DETECTADO', tone: 'local' };
      }
      return { label: 'USB SIN VERIFICAR', tone: 'unknown' };
  }
}

/** La verificación del protocolo es independiente de detectar el CH340. */
function protocolBadge(apiState, serial) {
  if (apiState !== 'online') {
    return { label: 'PROTOCOLO SIN VERIFICAR', tone: 'unknown' };
  }
  if (serial?.protocol_verified === true) {
    return { label: 'PROTOCOLO VERIFICADO', tone: 'local' };
  }
  return { label: 'PROTOCOLO PENDIENTE', tone: 'pending' };
}

/** Mensaje explicativo sin confundir el adaptador USB con el inversor. */
function noticeContent(apiState, serial) {
  if (apiState === 'checking') {
    return {
      tone: 'neutral',
      text: 'Comprobando la conexión con la API local de ANENJI Monitor...',
    };
  }
  if (apiState === 'offline') {
    return {
      tone: 'error',
      text: 'No se puede conectar con FastAPI. Comprueba que la Terminal 1 siga ejecutando el backend en el puerto 8000.',
    };
  }
  if (serial?.state === 'usb_disconnected') {
    return {
      tone: 'error',
      text: 'La API funciona, pero Debian no detecta el CH340. Comprueba la conexión USB con WSL2.',
    };
  }
  if (serial?.state === 'permission_denied') {
    return {
      tone: 'error',
      text: 'El CH340 está detectado, pero el proceso no tiene permisos suficientes sobre el puerto serial.',
    };
  }
  if (serial && USB_ERRORS.has(serial.state)) {
    return {
      tone: 'warning',
      text: 'La API funciona, pero no se ha podido verificar el adaptador USB. Revisa el diagnóstico del puerto.',
    };
  }
  if (serial?.adapter_verified !== true || serial?.port_accessible !== true) {
    return {
      tone: 'warning',
      text: 'La API responde, pero todavía no contamos con una verificación válida del adaptador USB.',
    };
  }
  if (serial.protocol_verified !== true) {
    return {
      tone: 'neutral',
      text: 'CH340 detectado. El protocolo del inversor SPI4865M150-300 sigue pendiente de verificar. No se muestran valores simulados.',
    };
  }
  if (serial.measurements_received !== true) {
    return {
      tone: 'neutral',
      text: 'Protocolo verificado; esperando la primera lectura válida del inversor.',
    };
  }
  return {
    tone: 'success',
    text: 'El backend indica comunicación verificada. Solo se muestran mediciones marcadas como recibidas y numéricamente válidas.',
  };
}

/** El número solo aparece con lectura y protocolo verificados por el backend. */
function presentation(measurement, unit, apiState, serial) {
  if (apiState === 'offline') {
    return { text: 'OFFLINE', status: 'offline', detail: 'API no disponible' };
  }
  if (apiState === 'checking') {
    return { text: 'SCANNING...', status: 'scanning', detail: 'Conectando con la API' };
  }
  if (serial && USB_ERRORS.has(serial.state)) {
    return { text: 'OFFLINE', status: 'offline', detail: 'Puerto USB no disponible o no verificado' };
  }
  if (serial?.adapter_verified !== true || serial?.port_accessible !== true) {
    return { text: 'SCANNING...', status: 'scanning', detail: 'Esperando verificación del CH340' };
  }
  if (serial.protocol_verified !== true || serial.measurements_received !== true) {
    return { text: 'SCANNING...', status: 'scanning', detail: 'Esperando primera lectura verificada' };
  }
  if (
    measurement?.received !== true ||
    typeof measurement.value !== 'number' ||
    !Number.isFinite(measurement.value)
  ) {
    return { text: 'SCANNING...', status: 'scanning', detail: 'Lectura aún no disponible' };
  }

  const text = `${numberFormat.format(measurement.value)} ${unit}`;
  return measurement.value === 0
    ? { text, status: 'zero', detail: 'Cero confirmado por el equipo' }
    : { text, status: 'active', detail: 'Medición recibida' };
}

export default function App() {
  const [payload, setPayload] = useState(null);
  const [apiState, setApiState] = useState('checking');

  useEffect(() => {
    let active = true;
    let pollTimer;
    let currentRequest;

    // Un nuevo ciclo empieza solo al terminar el anterior: evita solapamientos.
    async function refresh() {
      const controller = new AbortController();
      currentRequest = controller;
      const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

      try {
        const response = await fetch('/api/measurements', {
          cache: 'no-store',
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        if (!data || !Array.isArray(data.measurements)) {
          throw new Error('Respuesta de API inválida');
        }

        if (active) {
          setPayload(data);
          setApiState('online');
        }
      } catch {
        if (active) {
          // Eliminar las lecturas anteriores al perder la conexión con la API.
          setPayload(null);
          setApiState('offline');
        }
      } finally {
        clearTimeout(timeout);
        if (currentRequest === controller) currentRequest = null;
        if (active) pollTimer = setTimeout(refresh, POLL_INTERVAL_MS);
      }
    }

    refresh();
    return () => {
      active = false;
      clearTimeout(pollTimer);
      currentRequest?.abort();
    };
  }, []);

  const serial = payload?.serial ?? null;
  const measurements = Object.fromEntries(
    (payload?.measurements ?? [])
      .filter((item) => item && typeof item.id === 'string')
      .map((item) => [item.id, item]),
  );
  const api = apiBadge(apiState);
  const usb = usbBadge(apiState, serial);
  const protocol = protocolBadge(apiState, serial);
  const notice = noticeContent(apiState, serial);

  return (
    <main className="container">
      <header className="header">
        <div className="heading">
          <p className="eyebrow">MONITOREO LOCAL · SIN NUBE</p>
          <h1>ANENJI Monitor</h1>
          <p className="subtitle">SPI4865M150-300 · Panel de solo lectura</p>
        </div>
        <div className="status-group" aria-label="Estado de conexión">
          <span className={`connection ${api.tone}`}>{api.label}</span>
          <span className={`connection ${usb.tone}`}>{usb.label}</span>
          <span className={`connection ${protocol.tone}`}>{protocol.label}</span>
        </div>
      </header>

      <section className={`notice notice--${notice.tone}`} aria-live="polite">
        {notice.text}
      </section>

      <section className="grid" aria-label="Mediciones">
        {EXPECTED.map(([id, label, unit]) => {
          const display = presentation(measurements[id], unit, apiState, serial);
          return (
            <article className="metric" key={id}>
              <h2>{label}</h2>
              <div className={`reading ${display.status}`}>{display.text}</div>
              <p className="detail">{display.detail}</p>
            </article>
          );
        })}
      </section>

      <footer>
        Detectar el adaptador CH340 no confirma comunicación con el inversor.
        Los valores se muestran únicamente después de verificar el protocolo y
        recibir mediciones válidas. Un cero real no indica por sí solo una falla.
      </footer>
    </main>
  );
}
