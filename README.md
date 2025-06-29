# 🌍 Umweltmonitoring mit SenseBox und KI 🤖📈

Ein containerisiertes Dashboard-System zur Überwachung von Umweltdaten wie Temperatur, Luftfeuchtigkeit und Luftdruck über eine SenseBox.  
Inklusive:

- 🚨 **Anomalie-Erkennung** für Temperaturdaten (IsolationForest)
- 🔮 **24-Stunden-Vorhersage** der Temperatur (Lineare Regression)

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

- `Docker Desktop` als Adminstrator starten
```bash
docker-compose up --build
```
- Menge an Daten welche gesammelt werden kann bei Bedarf in `data_collector.py` bearbeitet werden
- 🔗 Öffne im Browser: `http://localhost:8050`
  
---
