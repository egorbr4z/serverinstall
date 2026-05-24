#!/bin/bash
set -euo pipefail

INSTALL_DIR="/opt/vpn-monitor"
SERVICE_NAME="vpn-monitor"
PORT="${APP_PORT:-8080}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

[ "$(id -u)" -eq 0 ] || error "Запустите от root: sudo ./install.sh"

info "Установка VPN Monitor..."

# ── Python и зависимости ──────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  info "Установка python3..."
  apt-get update -qq && apt-get install -y -qq python3 python3-pip python3-venv
fi

# Создаём venv чтобы не конфликтовать с системными пакетами
info "Создание виртуального окружения..."
python3 -m venv /opt/vpn-monitor-venv
/opt/vpn-monitor-venv/bin/pip install -q --upgrade pip
/opt/vpn-monitor-venv/bin/pip install -q -r "$(dirname "$0")/requirements.txt"
PYTHON="/opt/vpn-monitor-venv/bin/python"

# ── Копирование файлов ────────────────────────────────────────────────────────
info "Копирование файлов в ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}/static"
cp "$(dirname "$0")/main.py"        "${INSTALL_DIR}/"
cp "$(dirname "$0")/config.py"      "${INSTALL_DIR}/"
cp "$(dirname "$0")/static/index.html" "${INSTALL_DIR}/static/"

# ── systemd сервис ────────────────────────────────────────────────────────────
info "Создание systemd сервиса..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=VPN Monitor Web Interface
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${PYTHON} ${INSTALL_DIR}/main.py
Restart=always
RestartSec=5

# Настройки — переопределите нужные переменные
Environment=APP_HOST=0.0.0.0
Environment=APP_PORT=${PORT}
# Environment=VPN_AWG_CONTAINER=amnezia-awg
# Environment=VPN_XRAY_CONTAINER=amnezia-xray
# Environment=VPN_H2_SERVICE=hysteria-server
# Environment=VPN_H2_PORT=443
# Environment=VPN_H2_API_PORT=9090

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

# ── Итог ─────────────────────────────────────────────────────────────────────
IP=$(hostname -I | awk '{print $1}')
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}VPN Monitor установлен!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "  Адрес:    ${GREEN}http://${IP}:${PORT}${NC}"
echo ""
echo "  Управление сервисом:"
echo "    systemctl status  ${SERVICE_NAME}"
echo "    systemctl restart ${SERVICE_NAME}"
echo "    journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "  Настройка (имена контейнеров и т.д.):"
echo "    /etc/systemd/system/${SERVICE_NAME}.service"
echo "    → раскомментируйте и измените Environment= строки"
echo "    → затем: systemctl daemon-reload && systemctl restart ${SERVICE_NAME}"
echo ""
warn "Убедитесь, что порт ${PORT} открыт только для локальной сети (firewall)!"
echo ""
