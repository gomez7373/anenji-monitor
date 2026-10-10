# ANENJI Monitor

Aplicación web **local y de solo lectura** para investigar y, cuando se confirme el protocolo, monitorear el inversor **ANENJI SPI4865M150-300** desde Debian WSL2 mediante un adaptador USB serial CH340.

> **Estado actual:** la interfaz y la API funcionan; Linux detecta el CH340 como `/dev/ttyUSB0` y Python puede abrir el puerto. **Aún no obtenemos mediciones reales del inversor.** No se ha confirmado su protocolo serial.

## Estado del proyecto

| Parte | Estado |
| --- | --- |
| Interfaz React + Vite | ✅ Funciona localmente |
| API FastAPI | ✅ Funciona localmente |
| Indicadores `SCANNING...` | ✅ Sin mediciones inventadas |
| Detección del CH340 por PySerial | ✅ Verificada en el equipo de desarrollo |
| Apertura de `/dev/ttyUSB0` | ✅ Verificada en el equipo de desarrollo |
| Escucha pasiva durante 15 s (9600, 8N1) | ✅ Ejecutada; no llegaron datos |
| Utilidades Modbus RTU: CRC, construcción y validación | ✅ Pruebas **offline**, con respuestas simuladas |
| Protocolo del SPI4865M150-300 | ⏳ Sin confirmar |
| Consultas reales, historial y alertas | ⏳ Pendientes |

**Importante:** el código Modbus actual está probado con datos sintéticos, **no** contra el inversor. El proyecto no debe presentar una lectura pendiente como `0`, ni enviar comandos de escritura o configuración.

## Requisitos

- Computadora Windows con **WSL2 + Debian**.
- **Python 3.10+** con soporte para `venv` y `pip`.
- **Node.js 22** y `npm` (recomendado mediante [nvm](https://github.com/nvm-sh/nvm)); Vite 7 también admite versiones concretas más recientes según su documentación.
- **usbipd-win** instalado en Windows para compartir el adaptador USB con WSL2: [usbipd-win](https://github.com/dorssel/usbipd-win).
- Cable USB-B y adaptador CH340 detectado por Windows (en el equipo de desarrollo aparece como `USB-SERIAL CH340`).

`setup.sh` instala las **dependencias del proyecto** en Debian, pero **no instala automáticamente** Windows, WSL2, Debian, usbipd-win ni Python del sistema. Tampoco instala software del fabricante. Si esos requisitos faltan, configúralos primero.

## Primera instalación

Si empiezas desde cero, consigue primero acceso al repositorio privado de GitHub y clónalo desde **Debian WSL2**:

```bash
cd ~
git clone git@github.com:gomez7373/anenji-monitor.git
cd anenji-monitor
```

Si ya tienes la carpeta `~/anenji-monitor`, **no vuelvas a clonarla**. En ambos casos, desde la raíz del proyecto ejecuta:

```bash
cd ~/anenji-monitor
chmod +x setup.sh
./setup.sh
```

> Nota: el script `setup.sh` estará disponible en GitHub cuando se incluya en un nuevo commit y se publique con `git push`.

El instalador:

1. Comprueba Python, Node y npm (si ya tienes `nvm`, intenta activar Node 22; puede instalarlo mediante nvm si falta).
2. Crea `.venv/` si es necesario.
3. Instala las dependencias de `backend/requirements.txt` y **PySerial** en `.venv/`.
4. Ejecuta `npm ci` dentro de `frontend/` usando `package-lock.json`.

Requiere internet para descargar dependencias de Python y npm cuando no están instaladas. **No envía datos del inversor a ningún servidor.** No usa `sudo`, no ejecuta `apt update` ni altera la configuración eléctrica del equipo.

> Si no tienes Python con `venv`, Node/npm o usbipd-win, primero debes instalarlos en el sistema operativo correspondiente. En esta computadora usamos Node 22 con nvm.

## Los cuatro terminales: ¿cuál hace qué?

**Solo los terminales 1 y 2 deben permanecer ejecutándose para ver la interfaz.** Los terminales 3 y 4 se utilizan cuando necesitas conectar el USB o realizar diagnósticos; no son servidores permanentes.

| Terminal | Dónde | Función | ¿Queda abierta? |
| --- | --- | --- | --- |
| **1 — Backend** | Debian WSL2 | Ejecuta FastAPI en `127.0.0.1:8000` | **Sí**, mientras uses el monitor |
| **2 — Frontend** | Debian WSL2 | Ejecuta React/Vite en `127.0.0.1:5173` | **Sí**, mientras uses el monitor |
| **3 — USB** | Windows PowerShell | Comparte o reconecta el CH340 con WSL2 | **No**, después de conectar |
| **4 — Desarrollo** | Debian WSL2 | Diagnósticos seriales, pruebas y Git | **No**, solo cuando lo necesites |

### Terminal 3 — Conectar USB a WSL2 (cuando haga falta)

En **Windows PowerShell**:

```powershell
usbipd list
```

Localiza la línea **USB-SERIAL CH340** y toma su `BUSID` real; por ejemplo `1-1` en nuestra computadora. Ese identificador puede cambiar.

Si aparece `Not shared`, realiza **una sola vez** el siguiente comando en PowerShell **como administrador**:

```powershell
usbipd bind --busid 1-1
```

Para conectarlo a WSL2 (habitualmente no requiere PowerShell de administrador):

```powershell
usbipd attach --wsl --busid 1-1
```

Si ya figura como `Shared`, basta el comando `attach`. Si WSL2 se reinicia o desconectas el cable, puede ser necesario repetirlo. **No selecciones la cámara, el Bluetooth ni otros dispositivos por error.**

Comprueba desde Debian:

```bash
ls -l /dev/ttyUSB0
python -m serial.tools.list_ports -v
```

> La ruta `/dev/ttyUSB0` se verificó en el equipo de desarrollo, pero puede variar entre computadoras. La presencia del puerto solo demuestra detección del adaptador, no lecturas del inversor.

### Terminal 1 — Backend FastAPI

Abre una ventana de **Debian WSL2**:

```bash
cd ~/anenji-monitor
source .venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Deja esta terminal abierta. En el navegador puedes consultar:

- API: <http://127.0.0.1:8000/>
- Estado de la API: <http://127.0.0.1:8000/api/health>
- Documentación de API: <http://127.0.0.1:8000/docs>

La API todavía devuelve **mediciones pendientes**: no está conectada al decodificador serial.

### Terminal 2 — Frontend React

Abre **otra** ventana de Debian WSL2:

```bash
cd ~/anenji-monitor/frontend
nvm use 22  # solo si usas nvm y necesitas activar Node 22
npm run dev
```

Deja esta terminal abierta. Visita en tu navegador de Windows:

**<http://127.0.0.1:5173>**

La interfaz consulta `/api/measurements` a través del proxy local de Vite. Hasta que existan respuestas verificadas del inversor, es correcto que muestre `SCANNING...`.

### Terminal 4 — Diagnósticos y Git

Abre una tercera ventana de Debian WSL2 (además de las del backend y frontend):

```bash
cd ~/anenji-monitor
source .venv/bin/activate
```

**Verificar el adaptador y el puerto:**

```bash
ls -l /dev/ttyUSB0
python -m serial.tools.list_ports -v
```

**Escuchar 15 segundos sin enviar comandos de aplicación:**

```bash
python backend/serial_probe.py
```

**Probar la construcción y validación Modbus con datos simulados (sin USB):**

```bash
python backend/protocol.py
```

**Revisar cambios antes de versionarlos:**

```bash
git status --short
git diff
git diff --cached
```

Esta terminal puede cerrarse cuando hayas terminado. No hace falta ejecutar `serial_probe.py` para utilizar la interfaz web.

## Estructura principal

```text
anenji-monitor/
├── .gitignore
├── README.md
├── setup.sh                    # Instalación de dependencias del proyecto
├── backend/
│   ├── main.py                 # API local FastAPI
│   ├── protocol.py             # Utilidades Modbus y pruebas offline
│   ├── serial_probe.py         # Escucha serial pasiva (diagnóstico)
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       └── styles.css
└── src/
    └── state.py
```

`.venv/` y `frontend/node_modules/` se generan durante la instalación y están excluidos de Git. El archivo local `comand.md` **no forma parte del primer commit**.

## Arquitectura y privacidad

```text
ANENJI SPI4865M150-300
        │ USB-B / CH340
        ▼
  /dev/ttyUSB0 (Debian WSL2)
        │
        ▼
  Lector serial futuro (solo lectura, pendiente de protocolo)
        │
        ▼
  API FastAPI local ──► Frontend React local
```

- API y frontend escuchan únicamente en `127.0.0.1`, no en `0.0.0.0`.
- **No** se publican mediciones reales ni se ofrece una API pública.
- `private/`, `data/`, `logs/`, `.venv/` y `node_modules/` están excluidos mediante `.gitignore`.
- `.gitignore` **no** detecta automáticamente secretos escritos dentro del código ni protege archivos ya rastreados. Revisa cada commit antes de subirlo.
- GitHub alberga el **código**, no la conexión USB, el historial energético del hogar ni las llaves SSH.
- Abrir el puerto serial puede configurar señales eléctricas de control del adaptador; el diagnóstico no transmite consultas de aplicación.
- No enviaremos comandos desconocidos, de escritura o de configuración a un equipo eléctrico en funcionamiento.

## Próxima etapa

Identificar de forma verificable el protocolo del **SPI4865M150-300**, crear `backend/serial_reader.py`, validar las respuestas reales y conectarlas a `/api/measurements`. Solo entonces sustituiremos `SCANNING...` por valores medidos.
