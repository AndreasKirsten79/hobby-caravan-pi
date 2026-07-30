# Backup-Strategie

Dieses Repository ist die öffentliche, sanitisierte Quelle dieses Projekts (Platzhalter statt echter BLE-MAC/API-Keys/Zugangsdaten, siehe `README.md`).

**Zusätzlich** existiert außerhalb von GitHub ein privates Backup der vollständigen lokalen Arbeitskopie (inkl. echter Konfigurationswerte und Git-Historie):

- **Live-Mirror**: 1:1-Spiegel der lokalen Arbeitskopie, taeglich aktualisiert
- **Tages-Archive**: rollierende ZIP-Snapshots, 31 Tage Aufbewahrung, danach automatische Löschung der ältesten Archive
- Läuft automatisiert über einen geplanten Task auf dem Rechner der Arbeitskopie, taeglich um 18:00 Uhr
- Beide Backup-Wege wurden per Restore-Test verifiziert (Git-Historie + Dateien vollständig wiederherstellbar)

Dieses Backup liegt **bewusst nicht** in diesem öffentlichen Repo, da es reale Zugangsdaten enthält (SSH-Passwort, BLE-MAC, Tailscale-IP, API-Keys). Details zu Speicherort und Wiederherstellung stehen in der privaten Projektnotiz beim Maintainer.

Der Pi selbst (`/opt/hobbyconnect/`, `/opt/caravan-data/`) ist **kein** Backup-Ziel — Deploys laufen ausschließlich von der privaten Arbeitskopie zum Pi, nie umgekehrt.
