# HobbyConnect BLE Protokoll — Dokumentation

Stand: 2026-06-19 | Panel V011902 | Software V012000

Quellen:
- Eigene Live-Tests (RPi4 + bleak/paho-mqtt)
- paveltresnak/hobby-caravan-esphome-ble (Hobby De Luxe 495 UL, SW V011100)
- esphome/esphome PR #13327 (rawsludge / tomasslivka)

## BLE-Verbindung

| Parameter          | Wert                                         |
|--------------------|----------------------------------------------|
| BLE-Name           | `HobbyConnect Data`                          |
| Service UUID       | `C7841029-FE7C-4894-8532-F97908EF1AE4`      |
| Characteristic     | `00000001-0000-1000-8000-00805f9b34fb` (NOTIFY + WRITE) |
| Handshake          | `net-BT_ID-<pi_bt_mac>` + `net-BT_VARS`     |
| Chunk-Groesse      | 17 Byte, Trennzeichen `@`                   |

## WRITE-Befehle (verifiziert)

### Toggle (Ein/Aus) — FUNKTIONIERT
```
cmd-tgl:<KEY>
```
Kippt den Zustand. Kein "set" moeglich! `cmd-set:KEY=1` wird von der Box ignoriert.

Beispiel: `cmd-tgl:LIGHT_WAND` → Wandlicht toggelt.

### Wert setzen (Dimmer, Lednice, Klima) — TEILWEISE
```
net-<KEY>-<WERT>
```
Setzt einen Wert direkt.

**Bei Pavel (SW V011100) verifiziert:**
- `net-LIGHT_DIM2-8` → Wohnraum-Dimmer auf ~50% (N=0..15)
- `net-FRIDGE_SOURCE-N` → Kuehlschrank-Quelle (0=Auto/1=Gas/2=12V/3=230V)
- `net-FRIDGE_TEMP-N` → Kuehlschrank-Temperatur (1-5, 5=max)

**Bei uns (SW V012000) NICHT funktionierend:**
- `net-LIGHT_DIM1/2/3-N` → BLE WRITE geht durch, aber keine Helligkeitsaenderung
- Grund: Unser Panel meldet keine LIGHT_DIM Keys im BT_START-Dump (siehe unten)

### Nicht verwenden
```
cmd-set:<KEY>=<WERT>     ← wird von der Box ignoriert
cmd-dim-start/stop       ← nicht noetig, net-KEY-N setzt direkt
```

## Licht-Keys (unser Modell, SW V012000)

Alle Lichter sind rein on/off (0/1) ueber BLE. Physisches Dimmen am Panel
hat 15 Stufen, wird aber NICHT ueber BLE exponiert.

| Key             | Physisches Licht           | Dimmbar am Panel | Dimmbar per BLE |
|-----------------|----------------------------|------------------|-----------------|
| LIGHT_DECKE     | 3 LED-Strahler (Decke)     | Ja (15 Stufen)   | NEIN            |
| LIGHT_WAND      | Wandlicht vorn             | Ja (15 Stufen)   | NEIN            |
| LIGHT_BETTL     | Bettlicht links            | Ja (15 Stufen)   | NEIN            |
| LIGHT_BETTR     | Bettlicht rechts           | Ja (15 Stufen)   | NEIN            |
| LIGHT_KUECHE    | Kuechenlicht               | ?                | NEIN            |
| LIGHT_AUSSEN    | Aussenlicht                | Nein             | NEIN            |
| LIGHT_AMB1      | Ambientelicht Betten       | Nein             | NEIN            |
| LIGHT_AMB2      | Ambientelicht Sitzgruppe   | Nein             | NEIN            |
| LIGHT_AMB3      | LED Ring Decke             | Nein             | NEIN            |
| LIGHT_DUSCHE    | Duschlicht (ACHTUNG: Key heisst LIGHT_WASCH!) | ? | NEIN |
| LIGHT_WASCH     | Waschlicht (ACHTUNG: Key heisst LIGHT_DUSCHE!)| ? | NEIN |
| LIGHT_FUSSB     | Fussbodenbeleuchtung       | ?                | NEIN            |
| LIGHT_THERME    | Therme-Licht               | ?                | NEIN            |
| LIGHT_ZUSATZL/M/R | Zusatzlichter L/M/R      | ?                | NEIN            |

### Vergleich mit Pavel (495 UL, SW V011100)

Pavel hat WENIGER on/off-Keys (kein WAND, DECKE, BETTL, BETTR), dafuer
LIGHT_DIM0-4 als eigene dimmbare Kanaele. Die DIM-Keys existieren in
unserem Firmware-Stand (V012000) nicht.

| Pavels Modell          | Unser Modell           |
|------------------------|------------------------|
| LIGHT_DIM2 (Wohnraum)  | LIGHT_WAND (on/off)   |
| LIGHT_DIM3 (Ambient)   | LIGHT_DECKE (on/off)  |
| LIGHT_DIM1 (unbekannt) | LIGHT_BETTL/R (on/off)|
| kein LIGHT_WAND        | kein LIGHT_DIM*        |

## Sensor-Keys (READ, BT_START-Dump)

### Temperaturen & System
| Key                | Bedeutung              | Beispiel     |
|--------------------|------------------------|--------------|
| TEMP_IN            | Innentemperatur        | 24,0°C       |
| TEMP_OUT           | Aussentemperatur       | 23,0°C       |
| LINE_EN            | 230V angeschlossen     | 0/1          |
| HS_EN              | Heizungssystem enabled | 0/1          |
| AC_EN              | Klimaanlage enabled    | 0/1          |
| SOFTWARE_VERSION   | Firmware-Version       | V012000      |
| PANEL_VERSION      | Panel-Version          | V011902      |
| VEHICLE_TYPE       | Fahrzeugtyp            | 10           |
| GSM_SIGNAL         | GSM-Signalstaerke      | 17           |
| LATITUDE           | GPS Breitengrad        | (leer wenn kein GPS) |
| LONGITUDE          | GPS Laengengrad        | (leer wenn kein GPS) |

### Batterie (IBS0_ — Intelligent Battery Sensor)
| Key                    | Bedeutung           | Beispiel   |
|------------------------|---------------------|------------|
| IBS0_UBAT              | Batteriespannung    | 13,9 V     |
| IBS0_IBAT              | Strom (+/-)         | 0,0 A      |
| IBS0_SOC2              | Ladezustand         | 100%       |
| IBS0_REMAINING_TIME    | Restlaufzeit        | 77,5 h     |
| IBS0_AVAILABLE         | Sensor verfuegbar   | 0/1        |

### Wasser
| Key                | Bedeutung           | Werte               |
|--------------------|---------------------|----------------------|
| WATER_LEVEL        | Frischwasser-Stand  | 0-4 (Stufen: 0/25/50/75/100%) |

ACHTUNG: Wert kommt teils als "37:37" (Doppelpunkt-Format). Bridge parst
mit `value.split(':')[0]`. Tank = 47 Liter.

### Heizung & Warmwasser
| Key                | Bedeutung              |
|--------------------|------------------------|
| HEATER_AVAILABLE   | Heizung verfuegbar     |
| HEATER_ONOFF       | Heizung ein/aus        |
| HEATER_TEMP        | Heizungstemperatur     |
| HEATER_WATER       | Warmwasser ein/aus     |
| HEATER_WATER_TEMP  | Warmwasser-Temperatur  |
| HEATER_EL          | Elektro-Heizung        |
| HEATER_GAS         | Gas-Heizung            |
| TH_A_EN / TH_W_EN  | Truma Luft/Wasser     |
| TH_A_T / TH_W_T    | Truma Zieltemperatur  |

### Kuehlschrank
| Key                | Bedeutung              | Steuerbar? |
|--------------------|------------------------|------------|
| FRIDGE_AVAILABLE   | Kuehlschrank vorhanden | read-only  |
| FRIDGE_ON_OFF      | Ein/Aus                | cmd-tgl:FRIDGE_ON_OFF |
| FRIDGE_SOURCE      | Quelle (0=Auto/1=Gas/2=12V/3=230V) | net-FRIDGE_SOURCE-N |
| FRIDGE_TEMP        | Stufe (1-5, 5=max)     | net-FRIDGE_TEMP-N |
| FRIDGE_MODE        | Modus                  | read-only? |
| FRIDGE_TYPE        | Typ                    | read-only  |

### Klimaanlage (Dometic FreshJet)
| Key                    | Bedeutung           | Beispiel   | Steuerbar? |
|------------------------|---------------------|------------|------------|
| AC_DOM_FJ_AVAILABLE    | FreshJet vorhanden  | 1          | read-only  |
| AC_DOM_FJ_ENABLE       | FreshJet ein/aus    | Off        | cmd-tgl?   |
| AC_DOM_FJ_MODE         | Modus               | Auto       | net-AC_DOM_FJ_MODE-N? |
| AC_DOM_FJ_FAN_SPEED    | Luefterstufe        | Auto       | net-AC_DOM_FJ_FAN_SPEED-N? |
| AC_DOM_FJ_TARGETTEMP   | Zieltemperatur      | 20         | net-AC_DOM_FJ_TARGETTEMP-N? |
| AC_TRUMA_*             | Truma Klima         | —          | Nein (AVAILABLE=0) |
| AC_TRUMA_LIGHT_DIMMER  | Truma Beleuchtung   | 80         | read-only  |

### Elektro-Zusatzheizung (Ultraheat)
| Key                    | Bedeutung           | Beispiel   | Steuerbar? |
|------------------------|---------------------|------------|------------|
| ULTRAHEAT_AVAILABLE    | Ultraheat vorhanden | 0          | read-only  |
| ULTRAHEAT_ONOFF        | Ein/Aus             | Off        | cmd-tgl?   |
| ULTRAHEAT_POWER        | Leistung            | 2000 W     | read-only? |
| ULTRAHEAT_TEMP         | Temperatur          | 5          | net-?      |

## Bekannte Bugs & Fallstricke

1. **LIGHT_DUSCHE / LIGHT_WASCH sind vertauscht** in hobbyconnect.yaml
   (LIGHT_WASCH = physisch Duschlicht, LIGHT_DUSCHE = physisch Waschlicht)

2. **WATER_LEVEL Doppelpunkt-Format**: Box sendet teils "37:37" statt "37".
   Fix: `value.split(':')[0]`

3. **cmd-set funktioniert NICHT** fuer bool-Kanaele. Immer `cmd-tgl` verwenden.

4. **Zustandsbewusstes Toggle noetig**: HA sendet "on"/"off", aber die Box
   kann nur togglen. Bridge muss letzten State tracken und Toggle unterdruecken
   wenn Soll == Ist (sonst Desync bei schnellem Klicken).

5. **BLE Chunk-Grenze**: Befehle >17 Byte werden mit `@` gesplittet.
   Bridge muss Fragmente zusammensetzen.

6. **DIM-Sensor unit_of_measurement**: Verursacht non-fatal Errors in HA
   wenn im Light-Block definiert (hobbyconnect.yaml).

## Offene Fragen (an Pavel / Community)

- Warum hat SW V012000 keine LIGHT_DIM Keys, obwohl das Panel physisch 15 Dimm-Stufen hat?
- Gibt es einen versteckten Befehl um DIM-Feedback in neuerer Firmware zu aktivieren?
- Sind die DIM-Keys bei V012000 nur umbenannt, oder wurde Remote-Dimmen entfernt?

## Referenzen

- GitHub Issue: https://github.com/AndreasKirsten79/hobby-caravan-pi/issues/1
- Pavels Repo: https://github.com/paveltresnak/hobby-caravan-esphome-ble
- ESPHome PR: https://github.com/esphome/esphome/pull/13327
- Pavels Protokoll-Doku: docs/ble-protocol.md + docs/protocol-keys-full.md
