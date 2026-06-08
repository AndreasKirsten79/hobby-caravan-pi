# Hobby Caravan Pi

Raspberry Pi Setup für die Integration des **Hobby HobbyConnect**-Systems in Home Assistant.

Liest alle Daten der Wohnwagen-Steuerung (Lichter, Heizung, Batterie, Klimaanlage, Wasserstand, ...) per Bluetooth BLE aus und macht sie in Home Assistant steuerbar.

---

## Was ist das?

Die HobbyConnect-Box im Wohnwagen kommuniziert per Bluetooth BLE. Dieses Projekt verbindet einen Raspberry Pi per BLE mit der Box und leitet alle Daten als MQTT-Topics weiter. Home Assistant empfängt diese und stellt ~50 Sensoren, Schalter und Lichter bereit.

**Architektur:**

```
HobbyConnect Box
      │ BLE
      ▼
Raspberry Pi
 ├── ble_bridge.py  (systemd Service)
 │        │ MQTT
 │        ▼
 └── Docker Stack
      ├── Mosquitto   (MQTT Broker)   :1883
      ├── Home Assistant              :8123
      ├── InfluxDB    (Datenspeicher) :8086
      ├── Grafana     (Dashboards)    :3000
      ├── Nextcloud   (Dateiablage)   :8080
      ├── Tailscale   (VPN-Zugang)
      └── Uptime Kuma (Monitoring)    :3001
```

---

## Voraussetzungen

- Raspberry Pi 4 (empfohlen: 4 GB RAM)
- Debian 12/13 oder Raspberry Pi OS (64-bit)
- Hobby Wohnwagen mit HobbyConnect-System
- Tailscale-Account für Fernzugriff (kostenlos)

---

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/DEIN-USER/hobby-caravan-pi.git
cd hobby-caravan-pi
```

### 2. Konfiguration anpassen

```bash
cp .env.example .env
nano .env   # Tailscale-Key und Passwörter eintragen
```

**Pflichtfelder in `.env`:**
| Variable | Beschreibung |
|---|---|
| `TS_AUTHKEY` | Tailscale Auth-Key (tailscale.com → Settings → Keys) |
| `INFLUXDB_PASSWORD` | Beliebiges sicheres Passwort |
| `GRAFANA_PASSWORD` | Beliebiges sicheres Passwort |
| `MYSQL_ROOT_PASSWORD` | Beliebiges sicheres Passwort |
| `MYSQL_PASSWORD` | Beliebiges sicheres Passwort |

### 3. BLE MAC-Adresse ermitteln

```bash
sudo bluetoothctl
> scan on
# Warte bis "HobbyConnect" oder ähnliches Gerät erscheint
> scan off
> exit
```

MAC-Adresse in `hobbyconnect/ble_bridge.py` eintragen:
```python
BLE_MAC = "XX:XX:XX:XX:XX:XX"  # ← deine MAC hier (siehe Schritt 3)
```

### 4. Install-Script ausführen

```bash
chmod +x install.sh
./install.sh
```

### 5. Home Assistant einrichten

Nach dem ersten Start von HA unter `http://PI-IP:8123`:

**a) HA-Konto anlegen**
Beim ersten Aufruf führt HA durch die Ersteinrichtung. Standort und Zeitzone setzen — das wird für Wetterautomatisierungen benötigt.

**b) MQTT-Integration einrichten** ← Pflicht, sonst keine HobbyConnect-Daten
```
Einstellungen → Geräte & Dienste → Integration hinzufügen → MQTT
Host: localhost
Port: 1883
→ Speichern
```
Danach erscheinen alle HobbyConnect-Entitäten (Lichter, Sensoren, Schalter) automatisch.

**c) HA Companion App installieren** ← Pflicht für Push-Benachrichtigungen
Die Batterie-, Wetter- und Markise-Alarme nutzen `notify.mobile_app_...` — das funktioniert nur über die offizielle HA App:
- [iOS: Home Assistant im App Store](https://apps.apple.com/app/home-assistant/id1099568401)
- [Android: Home Assistant im Play Store](https://play.google.com/store/apps/details?id=io.homeassistant.companion.android)

Nach der Installation: App öffnen → mit deiner HA-Instanz verbinden → der Notify-Service wird automatisch angelegt. Den genauen Namen findest du unter:
```
Einstellungen → Geräte & Dienste → Companion App → dein Gerät → Entitäten
→ suche nach "notify" → das ist dein Service-Name
```
Diesen Namen dann in `packages/batterie_alarm.yaml` und `packages/wetter_alarm.yaml` eintragen.

**d) BTHome-Sensoren einrichten** (Bewegungsmelder, Türkontakte, Lux-Sensoren)
BTHome ist seit HA 2022.9 eingebaut — kein Plugin nötig. Die Sensoren werden automatisch per Bluetooth entdeckt sobald sie in Reichweite sind:
```
Einstellungen → Geräte & Dienste → BTHome → Geräte bestätigen
```
Die entity_ids der erkannten Sensoren dann in `homeassistant/automations.yaml` eintragen (ersetze die `bthome_sensor_XXXX_...` Platzhalter).

**e) HACS installieren** (optional, empfohlen)
HACS ist ein Community-Store für zusätzliche HA-Integrationen. Wird für dieses Projekt nicht zwingend benötigt, aber sinnvoll für zukünftige Erweiterungen:
```
https://hacs.xyz/docs/use/download/download/
```

**f) Automationen mit eigenen Geräte-IDs verknüpfen**
Die `automations.yaml` enthält Platzhalter (`DEINE_DEVICE_ID`, `DEINE_ENTITY_ID`). Am einfachsten über die HA UI neu anlegen:
```
Einstellungen → Automatisierungen → Automatisierung erstellen
```
Oder die IDs direkt aus dem HA Developer-Tool kopieren:
```
Entwicklerwerkzeuge → Zustände → Gerät suchen → Entity-ID kopieren
```

---

## Was muss jeder Nutzer anpassen?

| Datei | Was anpassen |
|---|---|
| `.env` | Alle Passwörter + Tailscale-Key |
| `hobbyconnect/ble_bridge.py` | `BLE_MAC` = MAC deiner HobbyConnect-Box |
| `hobbyconnect/hobbyconnect-bridge.service` | (wird auto. gesetzt durch install.sh) |
| `homeassistant/automations.yaml` | `device_id` / `entity_id` deiner BTHome-Sensoren |
| `homeassistant/packages/standort.yaml` | `device_tracker.DEIN_GERAET` → dein Gerät |
| `homeassistant/packages/batterie_alarm.yaml` | `notify.DEIN_NOTIFY_SERVICE` → dein Notify-Service |
| `homeassistant/packages/wetter_alarm.yaml` | `notify.DEIN_NOTIFY_SERVICE` → dein Notify-Service |
| `homeassistant/packages/landstrom.yaml` | `sensor.DEIN_SHELLY_ENERGIE_SENSOR` → dein Shelly |
| `homeassistant/configuration.yaml` | IP des Shelly für BLU-Scan |

---

## Enthaltene HA-Entitäten (hobbyconnect.yaml)

**Lichter (steuerbar):**
- Deckenlicht, Wandlicht, Küchenlicht, Außenlicht
- Ambientelicht 1-3, Bettlicht Links/Rechts
- Dusch- und Waschlicht

**Sensoren:**
- Innen-/Außentemperatur
- Batterie: Spannung, Strom, Ladezustand (%), Restlaufzeit
- Wasserstand (0/25/50/75/100%)
- Landstrom-Status, Heizung-Status
- GPS-Position (Breiten-/Längengrad)
- Klimaanlage (Dometic/Truma), Kühlschrank, Heizung

**Schalter:**
- Dometic Klimaanlage (Ein/Aus + Modus + Lüfter + Temperatur)
- Fußbodenheizung, Warmwassertherme

---

## Nützliche Befehle

```bash
# Bridge-Status
sudo systemctl status hobbyconnect-bridge

# Bridge-Logs live
sudo journalctl -u hobbyconnect-bridge -f

# Docker-Stack neu starten
cd ~/caravan-pi && docker compose restart

# MQTT-Topics live beobachten
docker exec -it mosquitto mosquitto_sub -h localhost -t "hobbyconnect/#" -v
```

---

## Verwandte Projekte

- [esp32-fendt-caravan-code](https://github.com/DEIN-USER/esp32-fendt-caravan-code) – ESP32 Integration für Fendt Wohnwagen

---

## Lizenz

MIT
