# ANENJI Monitor

Aplicación web **local y de solo lectura** para investigar y, cuando se confirme el protocolo, monitorear el inversor **ANENJI SPI4865M150-300** desde Debian WSL2 mediante un adaptador USB serial CH340.

> **Estado actual:** la interfaz React y la API FastAPI funcionan de forma local. El módulo `backend/serial_reader.py` detecta el adaptador CH340 en `/dev/ttyUSB0` **sin abrir el puerto**, y FastAPI comunica su estado al dashboard mediante `/api/serial/status` y `/api/measurements`. La apertura real del puerto se verificó por separado con `serial_probe.py`. **Aún no obtenemos mediciones reales del inversor:** el protocolo del modelo no está confirmado.

## Estado del proyecto

| Parte | Estado |
| --- | --- |
| Interfaz React + Vite | ✅ Funciona localmente; panel actualizado con estados de conexión |
| API FastAPI | ✅ Funciona localmente; responde a las rutas existentes y al nuevo diagnóstico USB |
| Comunicación React ↔ FastAPI | ✅ Comprobada mediante el proxy de Vite (`HTTP 200`) |
| Indicadores `SCANNING...` | ✅ Siete tarjetas, sin mediciones inventadas |
| Estados visuales de API, USB y protocolo | ✅ `API LOCAL`, `CH340 DETECTADO` y `PROTOCOLO PENDIENTE` verificados en pantalla |
| `backend/serial_reader.py` | ✅ Detecta el dispositivo, comprueba VID:PID y permisos aparentes; no abre el USB |
| Estado USB desde FastAPI | ✅ `/api/serial/status` probado con CH340 conectado; `/api/measurements` incorpora el diagnóstico |
| Apertura de `/dev/ttyUSB0` mediante PySerial | ✅ Verificada por separado en el equipo de desarrollo |
| Escucha pasiva durante 15 s (9600, 8N1) | ✅ Ejecutada; no llegaron datos |
| Utilidades Modbus RTU: CRC, construcción y validación | ✅ Pruebas **offline**, con respuestas simuladas |
| Protocolo del SPI4865M150-300 | ⏳ Sin confirmar |
| Solicitudes reales de lectura, decodificación, historial y alertas | ⏳ Pendientes |

**Importante:** el código Modbus actual está probado con datos sintéticos, **no** contra el inversor. Que aparezca `CH340 DETECTADO` o `protocol_pending` significa que reconocimos el **adaptador USB**, no que el inversor esté comunicando datos. `port_accessible` comprueba permisos aparentes, pero no garantiza que el puerto pueda abrirse en ese instante.

El proyecto no debe presentar una lectura pendiente como `0`, ni enviar comandos de escritura o configuración. **`SCANNING...` significa ausencia de lectura válida**; un cero solo debe aparecer cuando una medición real sea recibida y validada.

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

> Nota: `setup.sh` es parte de la estructura del proyecto. Si utilizas una copia anterior del repositorio, asegúrate de que incluya ese archivo antes de ejecutarlo. Detén Vite antes de reinstalar paquetes, porque `npm ci` reconstruye `frontend/node_modules/`.

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

Comprueba desde Debian (con el entorno virtual del proyecto activado):

```bash
cd ~/anenji-monitor
source .venv/bin/activate
ls -l /dev/ttyUSB0
python -m serial.tools.list_ports -v
```

También puedes ejecutar `usbipd.exe list` y `usbipd.exe attach --wsl --busid 1-1` desde una terminal Debian WSL2 si `usbipd.exe` está disponible allí. Para `bind`, utiliza PowerShell como administrador cuando sea necesario.

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
- Diagnóstico del adaptador USB: <http://127.0.0.1:8000/api/serial/status>
- Mediciones y estado de conexión: <http://127.0.0.1:8000/api/measurements>
- Documentación de API: <http://127.0.0.1:8000/docs>

`/api/serial/status` identifica el CH340 sin abrir el puerto y devuelve, entre otros, `state`, `adapter_verified`, `port_accessible`, `protocol_verified` y `measurements_received`. Si el adaptador está disponible, se espera `state: "protocol_pending"`; si desaparece de Debian, `state: "usb_disconnected"`.

`/api/measurements` conserva los siete campos esperados por React y añade el objeto `serial` con el diagnóstico. **Las mediciones siguen pendientes** (`value: null`, `received: false`, `updated_at: null`): todavía no existe un decodificador serial verificado. El código inspecciona el estado del puerto cuando recibe solicitudes; no está transmitiendo datos al inversor.

### Terminal 2 — Frontend React

Abre **otra** ventana de Debian WSL2:

```bash
cd ~/anenji-monitor/frontend
nvm use 22  # solo si usas nvm y necesitas activar Node 22
npm run dev
```

Deja esta terminal abierta. Visita en tu navegador de Windows:

**<http://127.0.0.1:5173>**

La interfaz consulta `/api/measurements` a través del proxy local de Vite (hacia FastAPI en el puerto 8000). Presenta por separado:

- **`API LOCAL`**: el servidor Python responde.
- **`CH340 DETECTADO`**: el adaptador USB identificado está disponible para el sistema.
- **`PROTOCOLO PENDIENTE`**: aún no se confirmó la comunicación con el inversor.
- **`USB DESCONECTADO` / estado de error**: el adaptador no está disponible o no supera la comprobación correspondiente.
- **`SCANNING...`**: cada tarjeta espera una medición real y válida, no un cero simulado.

La interfaz mantiene los siete indicadores y se actualiza periódicamente. El código también distingue un cero confirmado de una lectura positiva y de una API desconectada; **esos valores reales todavía no están disponibles**.

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

**Consultar el diagnóstico pasivo del nuevo módulo (sin abrir el USB):**

```bash
python backend/serial_reader.py
```

**Ver el diagnóstico devuelto por FastAPI (requiere Terminal 1 encendida):**

```bash
curl -sS http://127.0.0.1:8000/api/serial/status | python -m json.tool
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:5173/api/measurements
```

Un `HTTP 200` indica que el frontend puede comunicarse con la API; **no** certifica mediciones reales.

**Escuchar 15 segundos sin enviar comandos de aplicación:**

```bash
python backend/serial_probe.py
```

La escucha configura y abre el puerto temporalmente; a diferencia de `serial_reader.py`, sí lo abre, aunque no transmite consultas.

**Probar la construcción y validación Modbus con datos simulados (sin USB):**

```bash
python backend/protocol.py
```

**Revisar cambios antes de versionarlos:**

```bash
git status --short
git diff
git diff --cached
git diff --cached --check
```

**Comprobar la compilación del frontend después de cambios:**

```bash
cd ~/anenji-monitor/frontend
npm run build
```

Regresa a la raíz del proyecto con `cd ~/anenji-monitor` cuando termines. La compilación no consulta el inversor.

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
│   ├── serial_reader.py        # Identificación y estado USB (sin abrir el puerto)
│   ├── serial_probe.py         # Escucha serial pasiva (abre temporalmente el puerto)
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

`.venv/`, `frontend/node_modules/`, las cachés de Python y las compilaciones generadas se excluyen de Git. El archivo local `comand.md` se mantiene fuera de los commits realizados hasta esta etapa.

## Arquitectura y privacidad

```text
ANENJI SPI4865M150-300
        │ Cable USB-B / adaptador CH340
        ▼
  /dev/ttyUSB0 (Debian WSL2)
        │
        ├──► serial_reader.py (inspección pasiva del adaptador)
        │             │
        │             ▼
        │        API FastAPI local ──► React (estado USB)
        │
        └──► Lector de mediciones futuro (protocolo por confirmar)
                      │
                      ▼
                 API FastAPI local ──► React (valores reales)
```

- API y frontend escuchan únicamente en `127.0.0.1`, no en `0.0.0.0`.
- **No** se publican mediciones reales ni se ofrece una API pública.
- `private/`, `data/`, `logs/`, `.venv/` y `node_modules/` están excluidos mediante `.gitignore`.
- `.gitignore` **no** detecta automáticamente secretos escritos dentro del código ni protege archivos ya rastreados. Revisa cada commit antes de subirlo.
- GitHub alberga el **código**, no la conexión USB, el historial energético del hogar ni las llaves SSH.
- `serial_reader.py` **no abre** el puerto USB; solo inspecciona los metadatos del adaptador y los permisos aparentes.
- Abrir el puerto con `serial_probe.py` puede configurar señales eléctricas de control del adaptador; el diagnóstico no transmite consultas de aplicación.
- No enviaremos comandos desconocidos, de escritura o de configuración a un equipo eléctrico en funcionamiento.
- La API HTTP y el dashboard no deben exponerse a la red pública sin una revisión de seguridad y controles adicionales.

## Solución de problemas habituales

| Síntoma | Qué significa | Qué revisar |
| --- | --- | --- |
| `usb_disconnected` en `/api/serial/status` | Debian no encuentra el puerto configurado | `usbipd list` / `usbipd.exe list`, conectar el CH340 a WSL2 y revisar `/dev/ttyUSB0` |
| CH340 figura como `Shared` | Compartido en Windows, pero no necesariamente conectado a WSL2 | Ejecutar `usbipd attach --wsl --busid <BUSID>` desde PowerShell; usar el BUSID real |
| `permission_denied` | El usuario no dispone de permisos aparentes para el dispositivo | Revisar permisos del dispositivo y pertenencia al grupo `dialout` |
| `protocol_pending` | El adaptador fue identificado; el protocolo del inversor sigue sin verificarse | Es el estado esperado durante esta fase, no una medición |
| `NO DATA RECEIVED` en `serial_probe.py` | No llegaron bytes espontáneos en la prueba de 15 s | Puede requerirse una consulta documentada; **no** enviar comandos al azar |
| `[Errno 98] address already in use` | Ya existe un proceso usando el puerto 8000 | Revisar la Terminal 1; detener el servidor anterior con `Ctrl+C` antes de reiniciarlo |
| Vite muestra `ECONNREFUSED 127.0.0.1:8000` | React intenta consultar FastAPI cuando no está disponible | Iniciar o reiniciar FastAPI en la Terminal 1; comprobar `/api/health` |
| `HTTP 200` pero tarjetas en `SCANNING...` | La API responde, pero aún no hay mediciones verificadas | Comportamiento correcto mientras no exista el protocolo confirmado |

## Próxima etapa

Identificar de forma **verificable** el protocolo serial del **SPI4865M150-300** (parámetros, solicitudes de **solo lectura**, estructura de respuesta y validación). El archivo `backend/serial_reader.py` **ya existe**, pero por ahora solo inspecciona el adaptador USB; falta implementar un lector de mediciones reales basado en consultas documentadas y compatibles.

Una vez identificada la comunicación, validar las respuestas del inversor, asociarlas correctamente con los siete campos de `/api/measurements` y comprobar la visualización en React. **Solo entonces** sustituiremos `SCANNING...` por valores medidos. El historial y las alertas seguirán siendo una etapa posterior...
