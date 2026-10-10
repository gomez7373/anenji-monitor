# ANENJI Monitor

Interfaz web **local** para el inversor ANENJI SPI4865M150-300 conectado a Debian WSL2 mediante USB CH340 (`/dev/ttyUSB0`).

## Estado del proyecto

- ✅ Interfaz React y CSS funcional
- ✅ API local FastAPI funcional
- ✅ Indicadores `SCANNING...` sin valores simulados
- ⏳ Protocolo serial de este modelo pendiente de confirmar
- ⏳ Lecturas reales, historial y alertas todavía no implementados

**Importante:** La interfaz no controla el inversor ni envía comandos al puerto serial. Un cero real y una lectura pendiente deben tratarse como situaciones distintas.

## Uso local (Debian WSL2)

Requiere Python 3 con `venv`, Node.js compatible con Vite 7 (Node 20.19+ o 22.12+) y npm.

**Terminal A:**

```bash
cd ~/anenji-monitor
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

**Terminal B:**

```bash
cd ~/anenji-monitor/frontend
npm install
npm run dev
```

Visita `http://127.0.0.1:5173` desde el navegador del mismo equipo. Si el reenvío de localhost de WSL2 no funciona, revisa la configuración de WSL antes de exponer ningún puerto a la red.

## Seguridad

- API y servidor web enlazados a `127.0.0.1`, no `0.0.0.0`.
- Ninguna medición real se publica en GitHub ni en GitHub Pages.
- Las carpetas `private/`, `data/`, `logs/` y los secretos se excluyen de Git.
- `.gitignore` no protege archivos ya rastreados ni secretos embebidos en código; inspecciona siempre `git diff --cached` antes de cada commit.
- No publiques capturas, IP, números de serie ni tokens reales.
- No es un proyecto que controle parámetros eléctricos o de carga del inversor.

## Arquitectura

`ANENJI → CH340 → lector serial futuro → API FastAPI local → React`.

Aún no se ha verificado el protocolo serial específico del equipo. La API devuelve lecturas **pendientes** hasta que exista un decodificador probado. No se enviarán comandos arbitrarios a un sistema eléctrico en funcionamiento.
