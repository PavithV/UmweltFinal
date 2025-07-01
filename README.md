# 🌍 Umweltmonitoring mit SenseBox und KI 🤖📈

WICHTIG: `.foo` Dateien aus `pg_logical/snapshots` und `pg_tblspc` löschen (sonst funktioniert das Projekt nicht!)

Ein containerisiertes Dashboard-System zur Überwachung von Umweltdaten wie Temperatur, Luftfeuchtigkeit und Luftdruck über eine SenseBox.  
Inklusive:

- 🚨 **Anomalie-Erkennung** für Temperaturdaten (IsolationForest)
- 🔮 **24-Stunden-Vorhersage** der Temperatur (Lineare Regression)
---
## Tools
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Plotly Dash](https://img.shields.io/badge/Plotly%20Dash-3F4F75?logo=plotly&logoColor=white)
![TimescaleDB](https://img.shields.io/badge/TimescaleDB-ffaa00?logo=postgresql&logoColor=white)

---

## 🔧 Features

- 📡 Automatisierte Datenaufnahme von einer SenseBox (über die SenseBox API)
- 💾 Speicherung der Sensordaten in einer TimescaleDB (PostgreSQL-Erweiterung)
- 📊 Plotly Dash Dashboard zur Visualisierung der Live-Daten, Anomalien und Vorhersagen
- 🧠 ML-Module zur:
  - Anomalie-Erkennung (Unregelmäßigkeiten in der Temperatur)
  - Temperatur-Vorhersage für die nächsten 24 Stunden
- 🐳 Komplette Containerisierung mit Docker & docker-compose

---


## 🚀 Projekt starten

Im Projektverzeichnis:
WICHTIG: `.foo` Dateien aus `pg_snapshots` und `pg_tblspc` löschen (sonst funktioniert das Projekt nicht!)
- `Docker Desktop` als Adminstrator starten
```bash
docker-compose up --build
```
- Menge an Daten welche gesammelt werden kann bei Bedarf in `data_collector.py` bearbeitet werden
- 🔗 Öffne im Browser: `http://localhost:8050`
  
---
