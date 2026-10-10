#!/usr/bin/env bash
# ANENJI Monitor — instalador de dependencias para Debian/WSL2.
# Ejecutar desde el repositorio: ./setup.sh
# No instala componentes de Windows, no abre el USB y no envía datos del inversor.

set -Eeuo pipefail

error() {
  printf '\n[ERROR] %s\n' "$*" >&2
  exit 1
}

info() {
  printf '\n[ANENJI] %s\n' "$*"
}

trap 'printf "\n[ERROR] La instalación se interrumpió en la línea %s.\n" "$LINENO" >&2' ERR

# Trabajar siempre desde la raíz del proyecto, aunque se ejecute desde otra carpeta.
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

info "Instalador local de ANENJI Monitor"

[[ -f backend/requirements.txt ]] || error "Falta backend/requirements.txt."
[[ -f frontend/package.json ]] || error "Falta frontend/package.json."
[[ -f frontend/package-lock.json ]] || error "Falta frontend/package-lock.json (necesario para npm ci)."

# Se requiere una instalación funcional de Python, venv y pip.
command -v python3 >/dev/null 2>&1 || error "No se encontró python3. Instala Python 3 con venv en Debian."
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || error "Se requiere Python 3.10 o superior."

# Cuando nvm ya está instalado, intentamos usar Node 22 para Vite 7.
# No se instala nvm silenciosamente ni se descargan scripts desconocidos.
if [[ -s "$HOME/.nvm/nvm.sh" ]]; then
  info "Se encontró nvm; seleccionando Node.js 22..."
  set +u
  # shellcheck source=/dev/null
  source "$HOME/.nvm/nvm.sh"
  set -u
  if ! nvm use 22 >/dev/null 2>&1; then
    info "Node 22 no está instalado; nvm intentará instalarlo (requiere internet)."
    nvm install 22 || error "No se pudo instalar Node.js 22 mediante nvm."
    nvm use 22 || error "No se pudo activar Node.js 22."
  fi
fi

command -v node >/dev/null 2>&1 || error "No se encontró Node.js. Instala Node 22 (por ejemplo con nvm)."
command -v npm >/dev/null 2>&1 || error "No se encontró npm. Instala Node.js con npm."

# Versiones de Node.js compatibles con los requisitos de Vite 7 conocidos.
node -e 'const [major,minor]=process.versions.node.split(".").map(Number); if (!((major===20&&minor>=19)||(major===22&&minor>=12)||(major>=24))) process.exit(1)' \
  || error "Node.js incompatible con Vite 7. Recomendado: Node 22.12 o superior de la rama 22."

info "Python: $(python3 --version 2>&1)"
info "Node: $(node --version) | npm: $(npm --version)"

if [[ ! -f .venv/bin/python ]]; then
  info "Creando entorno virtual .venv/ ..."
  python3 -m venv .venv || error "No se pudo crear .venv; verifica que python3-venv esté instalado."
else
  info "Reutilizando el entorno virtual .venv/ existente."
fi

info "Instalando dependencias de Python y PySerial..."
# PySerial se instala explícitamente porque todavía puede faltar en requirements.txt.
"$PROJECT_ROOT/.venv/bin/python" -m pip install \
  -r "$PROJECT_ROOT/backend/requirements.txt" \
  'pyserial>=3.5,<4'

info "Instalando dependencias del frontend con npm ci..."
(
  cd "$PROJECT_ROOT/frontend"
  npm ci --no-audit --no-fund
)

info "Instalación finalizada."
printf '\nInicia el backend en la Terminal 1:\n'
printf '  cd ~/anenji-monitor\n  source .venv/bin/activate\n  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000\n'
printf '\nInicia el frontend en la Terminal 2:\n'
printf '  cd ~/anenji-monitor/frontend\n  nvm use 22  # si utilizas nvm\n  npm run dev\n'
printf '\nAbre en tu navegador: http://127.0.0.1:5173\n'
printf 'NOTA: No se conectó el USB ni se enviaron comandos al inversor.\n'
