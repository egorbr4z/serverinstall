import os

# Docker container names (Amnezia self-hosted)
AWG_CONTAINER  = os.environ.get("VPN_AWG_CONTAINER",  "amnezia-awg")
XRAY_CONTAINER = os.environ.get("VPN_XRAY_CONTAINER", "amnezia-xray")

# WireGuard/AmneziaWG interface inside the container
AWG_INTERFACE  = os.environ.get("VPN_AWG_IFACE", "awg0")

# Hysteria2 systemd service name and ports
HYSTERIA2_SERVICE  = os.environ.get("VPN_H2_SERVICE",  "hysteria-server")
HYSTERIA2_PORT     = int(os.environ.get("VPN_H2_PORT",     "443"))
HYSTERIA2_API_PORT = int(os.environ.get("VPN_H2_API_PORT", "9090"))

# xray config paths to try (in order)
XRAY_CONFIG_PATHS = [
    "/opt/amnezia/xray/config.json",
    "/etc/xray/config.json",
    "/usr/local/etc/xray/config.json",
]

# Web server
APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
APP_PORT = int(os.environ.get("APP_PORT", "8080"))
