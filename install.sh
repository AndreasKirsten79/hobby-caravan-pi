#!/bin/bash
# ============================================================
# Hobby Caravan Pi - Installations-Script
# Getestet auf: Raspberry Pi 4, Debian 13 (trixie)
# ============================================================
set -e

INSTALL_USER=$(whoami)
DATA_DIR="/opt/caravan-data"
HOBBYCONNECT_DIR="/opt/hobbyconnect"
COMPOSE_DIR="$HOME/caravan-pi"

echo "========================================"
echo "  Hobby Caravan Pi – Setup"
echo "  User: $INSTALL_USER"
echo "========================================"

# --- Voraussetzungen prüfen ---
if [ "$EUID" -eq 0 ]; then
  echo "Bitte NICHT als root ausführen. Script nutzt sudo intern."
  exit 1
fi

# --- System-Pakete ---
echo "[1/7] System-Pakete installieren..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
  docker.io docker-compose-plugin \
  python3 python3-venv python3-pip \
  bluetooth bluez \
  git curl

# Docker-Gruppe
sudo usermod -aG docker "$INSTALL_USER"

# --- Datenverzeichnisse ---
echo "[2/7] Datenverzeichnisse anlegen..."
sudo mkdir -p \
  "$DATA_DIR/mosquitto/data" \
  "$DATA_DIR/mosquitto/log" \
  "$DATA_DIR/homeassistant" \
  "$DATA_DIR/backups/homeassistant" \
  "$DATA_DIR/influxdb/data" \
  "$DATA_DIR/influxdb/config" \
  "$DATA_DIR/grafana" \
  "$DATA_DIR/mariadb" \
  "$DATA_DIR/nextcloud" \
  "$DATA_DIR/uptime-kuma"
sudo chown -R "$INSTALL_USER:$INSTALL_USER" "$DATA_DIR"

# --- HobbyConnect Bridge ---
echo "[3/7] HobbyConnect Bridge installieren..."
sudo mkdir -p "$HOBBYCONNECT_DIR"
sudo chown "$INSTALL_USER:$INSTALL_USER" "$HOBBYCONNECT_DIR"
cp hobbyconnect/ble_bridge.py "$HOBBYCONNECT_DIR/"
python3 -m venv "$HOBBYCONNECT_DIR/venv"
"$HOBBYCONNECT_DIR/venv/bin/pip" install -q -r hobbyconnect/requirements.txt

# systemd Service
sudo cp hobbyconnect/hobbyconnect-bridge.service /etc/systemd/system/
sudo sed -i "s/YOUR_PI_USER/$INSTALL_USER/" /etc/systemd/system/hobbyconnect-bridge.service
sudo systemctl daemon-reload
sudo systemctl enable hobbyconnect-bridge

# --- Docker Compose vorbereiten ---
echo "[4/7] Docker Compose einrichten..."
mkdir -p "$COMPOSE_DIR"
cp docker-compose.yml "$COMPOSE_DIR/"
cp mosquitto.conf "$COMPOSE_DIR/"

if [ ! -f "$COMPOSE_DIR/.env" ]; then
  cp .env.example "$COMPOSE_DIR/.env"
  echo ""
  echo "  WICHTIG: Bitte jetzt $COMPOSE_DIR/.env bearbeiten!"
  echo "  Tailscale-Key und Passwörter eintragen, dann erneut ausführen."
  echo ""
  read -p "  Drücke Enter wenn du fertig bist..."
fi

# --- Home Assistant Config ---
echo "[5/7] Home Assistant Konfiguration kopieren..."
cp -r homeassistant/. "$DATA_DIR/homeassistant/"
echo "  HA-Config kopiert nach $DATA_DIR/homeassistant/"
echo "  WICHTIG: automations.yaml und packages/standort.yaml"
echo "  müssen noch mit deinen Geräte-IDs angepasst werden!"

# --- Docker Stack starten ---
echo "[6/7] Docker Stack starten..."
cd "$COMPOSE_DIR"
docker compose up -d

echo ""
echo "[7/7] HobbyConnect Bridge BLE-MAC konfigurieren..."
echo ""
echo "  Deine HobbyConnect-Box BLE MAC-Adresse ermitteln:"
echo "  sudo bluetoothctl"
echo "  > scan on"
echo "  > (suche nach 'HobbyConnect' oder ähnlichem Gerät)"
echo "  > scan off"
echo "  > exit"
echo ""
echo "  Dann eintragen in: $HOBBYCONNECT_DIR/ble_bridge.py"
echo "  Zeile:  BLE_MAC = \"XX:XX:XX:XX:XX:XX\"  ← deine MAC hier ersetzen"
echo ""
echo "  Danach: sudo systemctl start hobbyconnect-bridge"
echo ""

echo "========================================"
echo "  Setup abgeschlossen!"
echo ""
echo "  Dienste:"
echo "  Home Assistant:  http://$(hostname -I | awk '{print $1}'):8123"
echo "  Grafana:         http://$(hostname -I | awk '{print $1}'):3000"
echo "  InfluxDB:        http://$(hostname -I | awk '{print $1}'):8086"
echo "  Nextcloud:       http://$(hostname -I | awk '{print $1}'):8080"
echo "  Uptime Kuma:     http://$(hostname -I | awk '{print $1}'):3001"
echo ""
echo "  Bridge Status:   sudo systemctl status hobbyconnect-bridge"
echo "  Bridge Logs:     sudo journalctl -u hobbyconnect-bridge -f"
echo "========================================"
