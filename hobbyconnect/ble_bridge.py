#!/usr/bin/env python3
import asyncio
import logging
import signal
import sys
import queue
from datetime import datetime
import paho.mqtt.client as mqtt
from bleak import BleakClient

# ============================================================
# ANPASSEN: BLE MAC-Adresse deiner HobbyConnect-Box
# Ermitteln mit: sudo bluetoothctl → scan on → suche "HobbyConnect"
# ============================================================
BLE_MAC         = "DE:00:05:10:60:23"  # <-- DEINE MAC HIER EINTRAGEN
BLE_CHAR        = "00000001-0000-1000-8000-00805f9b34fb"
BLE_TIMEOUT     = 15.0
SESSION_TIME    = 300
RECONNECT_DELAY = 5

MQTT_HOST   = "localhost"
MQTT_PORT   = 1883
TOPIC_STATE = "hobbyconnect/state/{key}"
TOPIC_CMD   = "hobbyconnect/cmd/#"
TOPIC_AVAIL = "hobbyconnect/availability"

SAFE_WRITE_KEYS = {
    "LIGHT_WAND","LIGHT_DECKE","LIGHT_KUECHE","LIGHT_AUSSEN",
    "LIGHT_AMB1","LIGHT_AMB2","LIGHT_AMB3","LIGHT_BETTL","LIGHT_BETTR",
    "LIGHT_DUSCHE","LIGHT_WASCH","LIGHT_FUSSB","LIGHT_THERME",
    "LIGHT_ZUSATZL","LIGHT_ZUSATZM","LIGHT_ZUSATZR",
    "AC_DOM_FJ_ENABLE","AC_DOM_FJ_MODE","AC_DOM_FJ_FAN_SPEED","AC_DOM_FJ_TARGETTEMP",
}

TOGGLE_KEYS = {
    "AC_DOM_FJ_ENABLE",
}

NET_KEYS = {
    "AC_DOM_FJ_FAN_SPEED",
    "AC_DOM_FJ_MODE",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("hobbyconnect")

_running     = True
_fragment    = ""
_cmd_queue   = queue.Queue()
_mqtt_client = None


async def ble_write_chunked(client, cmd: str, response: bool = True):
    if len(cmd) <= 17:
        await client.write_gatt_char(BLE_CHAR, cmd.encode("utf-8"), response=response)
    else:
        chunk1 = cmd[:17] + "@"
        chunk2 = cmd[17:]
        await client.write_gatt_char(BLE_CHAR, chunk1.encode("utf-8"), response=response)
        await asyncio.sleep(0.1)
        await client.write_gatt_char(BLE_CHAR, chunk2.encode("utf-8"), response=response)
    log.info("BLE WRITE ✓ %s", cmd)


def mqtt_setup():
    client = mqtt.Client(client_id="hobbyconnect_bridge")
    client.will_set(TOPIC_AVAIL, "offline", qos=1, retain=True)
    client.on_connect = _on_connect
    client.on_message = _on_message
    client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client


def _on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        log.info("MQTT connected")
        client.publish(TOPIC_AVAIL, "online", qos=1, retain=True)
        client.subscribe(TOPIC_CMD, qos=1)
    else:
        log.error("MQTT failed rc=%d", rc)


def _on_message(client, userdata, msg):
    key     = msg.topic.split("/")[-1].upper()
    payload = msg.payload.decode("utf-8", errors="ignore").strip()
    if not payload:
        return
    if key not in SAFE_WRITE_KEYS:
        log.warning("Write blocked: %s", key)
        return
    if key.startswith("LIGHT_") or key in TOGGLE_KEYS:
        command = f"cmd-tgl:{key}"
    elif key in NET_KEYS:
        command = f"net-{key}-{payload}"
    else:
        command = f"cmd-set:{key}={payload}"
    _cmd_queue.put(command)
    log.info("CMD queued: %s", command)


def mqtt_pub(key, value):
    _mqtt_client.publish(TOPIC_STATE.format(key=key), value, qos=0, retain=True)


def handle_notification(_, data):
    global _fragment
    raw = data.decode("utf-8", errors="ignore")
    if raw.endswith("@"):
        if _fragment and ":" in _fragment:
            logging.getLogger("hobbyconnect").debug("Stale fragment discarded: %r", _fragment)
            _fragment = ""
        _fragment += raw[:-1]
        return
    full = (_fragment + raw).strip()
    _fragment = ""
    if not full or ":" not in full or full == "BT_START:":
        return
    key, _, value = full.partition(":")
    key   = key.strip()
    value = value.strip().replace("^C", "°C")
    if not key or not all(c.isalnum() or c == "_" for c in key):
        log.debug("Discarding invalid key: %r", key)
        return
    if len(key) > 30:
        log.debug("Discarding too-long key: %r", key)
        return
    mqtt_pub(key, value)
    log.info("PUB %s = %s", key, value)


async def ble_session():
    log.info("BLE connecting → %s", BLE_MAC)
    try:
        async with BleakClient(BLE_MAC, timeout=BLE_TIMEOUT) as client:
            log.info("BLE connected ✓")
            await client.start_notify(BLE_CHAR, handle_notification)
            await asyncio.sleep(0.5)
            # Bluetooth-MAC des Pi (klein, Doppelpunkte) als BT_ID senden
            import subprocess
            bt_mac = subprocess.check_output(
                "hciconfig hci0 | grep 'BD Address' | awk '{print $3}'",
                shell=True
            ).decode().strip().lower()
            await ble_write_chunked(client, f"net-BT_ID-{bt_mac}", response=True)
            await asyncio.sleep(0.2)
            await ble_write_chunked(client, "net-BT_VARS", response=True)
            log.info("Init handshake sent ✓")
            loop = asyncio.get_event_loop()
            deadline = loop.time() + SESSION_TIME
            while loop.time() < deadline and _running:
                try:
                    while not _cmd_queue.empty():
                        cmd = _cmd_queue.get_nowait()
                        await ble_write_chunked(client, cmd)
                        await asyncio.sleep(0.1)
                except Exception as e:
                    log.error("Write error: %s", e)
                await asyncio.sleep(0.5)
            await client.stop_notify(BLE_CHAR)
    except Exception as e:
        log.warning("BLE session error: %s", e)


async def main():
    global _mqtt_client, _running
    log.info("HobbyConnect BLE Bridge starting – %s", datetime.now().isoformat())
    _mqtt_client = mqtt_setup()
    await asyncio.sleep(3)
    while _running:
        await ble_session()
        if _running:
            log.info("Waiting %ds before next session...", RECONNECT_DELAY)
            await asyncio.sleep(RECONNECT_DELAY)
    _mqtt_client.publish(TOPIC_AVAIL, "offline", qos=1, retain=True)
    _mqtt_client.loop_stop()
    _mqtt_client.disconnect()
    log.info("Bridge stopped.")


def _stop(*_):
    global _running
    _running = False


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    asyncio.run(main())
