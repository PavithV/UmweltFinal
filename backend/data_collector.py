import os
import time
import requests
import pandas as pd
import sys
from datetime import datetime, timezone, timedelta
from database import insert_measurements, get_conn
import psycopg2
#Variablen
BASE_URL = "https://api.opensensemap.org"
BOX_ID = os.getenv("SENSEBOX_ID") or "5e7e9b94946d0c001b6e64b4"
POLL_SEC = int(os.getenv("POLL_SECONDS", 30))
RUN_HISTORIC = os.getenv("RUN_HISTORIC", "false").lower() == "true"


# Funktion zum Warten auf die Datenbankverbindung
# max_retries: Maximale Anzahl an Versuchen, die Datenbank zu erreichen
# delay: Wartezeit zwischen den Versuchen in Sekunden
# Gibt bei Erfolg zurück oder beendet das Programm bei Misserfolg
def wait_for_db(max_retries=12, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            conn = get_conn()
            conn.close()
            print("DB-Verbindung erfolgreich", flush=True)
            return
        except psycopg2.OperationalError as e:
            print(f"Warte auf DB (Versuch {retries+1}/{max_retries}): {e}", flush=True)
            time.sleep(delay)
            retries += 1
    print("Konnte keine Verbindung zur DB aufbauen, beende Collector.", flush=True)
    sys.exit(1)

# Funktion zum Abrufen der neuesten Messwerte von der SenseBox API
# Gibt eine Liste von Tupeln zurück: (timestamp, sensor_id, sensor_name, unit, value)
# timestamp: Zeitstempel der Messung (UTC)
def fetch_latest_measurements():
    url = f"{BASE_URL}/boxes/{BOX_ID}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    sensors = r.json().get("sensors", [])
    rows = []
    for s in sensors:
        val = s.get("lastMeasurement")
        if not val:
            continue
        ts = datetime.fromisoformat(val["createdAt"].replace("Z", "+00:00")).astimezone(timezone.utc)
        rows.append((ts, s["_id"], s.get("title"), s.get("unit"), float(val["value"])))
    return rows

# Funktion zum Abrufen historischer Messwerte
# Speichert die Daten in der Datenbank
# Gibt keine Rückgabewerte zurück, sondern speichert direkt in der DB
def fetch_historical_measurements(days=14):
    print(f"Lade historische Daten der letzten {days} Tage...", flush=True)

    # Beispielhafte feste Zeiten - hier kannst du days verwenden, um dynamisch zu rechnen
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=days)

    from_date_str = from_date.isoformat().replace("+00:00", "Z")
    to_date_str = to_date.isoformat().replace("+00:00", "Z")

    # Hole Box-Info (um Sensor-IDs zu bekommen)
    r = requests.get(f"{BASE_URL}/boxes/{BOX_ID}", timeout=10)
    r.raise_for_status()
    box = r.json()
    sensors = box.get("sensors", [])

    all_rows = []
    for sensor in sensors:
        sensor_id = sensor["_id"]
        url = f"{BASE_URL}/boxes/{BOX_ID}/data/{sensor_id}?from-date={from_date_str}&to-date={to_date_str}&download=false"
        print(f"-> Sensor {sensor['title']} ({sensor_id})", flush=True)
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            data = r.json()
            for entry in data:
                ts = datetime.fromisoformat(entry["createdAt"].replace("Z", "+00:00")).astimezone(timezone.utc)
                value = float(entry["value"])
                all_rows.append((ts, sensor_id, sensor["title"], sensor["unit"], value))
        except Exception as e:
            print(f"Fehler beim Laden von {sensor_id}: {e}", flush=True)

    print(f"{len(all_rows)} historische Messwerte geladen.", flush=True)
    if all_rows:
        insert_measurements(all_rows)


def main():
    wait_for_db()
    print("Collector gestartet", flush=True)

    # Einmaliger Import historischer Daten
    fetch_historical_measurements(days=14)

    # Dann normaler Live-Modus
    while True:
        try:
            print(f"Abruf für SenseBox {BOX_ID} ...", flush=True)
            rows = fetch_latest_measurements()
            print(f"{len(rows)} Live-Messwerte gefunden", flush=True)
            if rows:
                insert_measurements(rows)
        except Exception as e:
            print("Collector error:", e, flush=True)
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
