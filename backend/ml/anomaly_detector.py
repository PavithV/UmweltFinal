import os
import time
import joblib
import pandas as pd
import psycopg2
import numpy as np
from datetime import timedelta
from sklearn.linear_model import LinearRegression
from database import get_conn
from sklearn.ensemble import IsolationForest

MODEL_PATH = os.getenv("MODEL_PATH", "/app/model/anomaly_iforest.joblib")
FORECAST_MODEL_PATH = os.getenv("FORECAST_MODEL_PATH", "/app/model/temp_forecast_lr.joblib")
SENSOR_ID = os.getenv("ML_SENSOR_ID")  # fokussierter Sensor
TRAIN_LIMIT = int(os.getenv("TRAIN_LIMIT", "10000"))
MSE = 0


def wait_for_db(max_retries=10, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            conn = get_conn()
            conn.close()
            print("DB-Verbindung erfolgreich")
            return
        except psycopg2.OperationalError as e:
            print(f"Warte auf DB (Versuch {retries+1}/{max_retries}): {e}")
            time.sleep(delay)
            retries += 1
    raise RuntimeError("Konnte nach mehreren Versuchen keine Verbindung zur Datenbank aufbauen.")


def load_data():
    query = """
        SELECT time, value
        FROM measurements
        WHERE sensor_id = %s
        ORDER BY time ASC
        LIMIT %s;
    """
    with get_conn() as conn:
        df = pd.read_sql(query, conn, params=[SENSOR_ID, TRAIN_LIMIT])
    df["time"] = pd.to_datetime(df["time"])
    df = df.dropna()
    return df


print("Lade Daten für Temperatur-Vorhersage...")


def train_forecast_model():
    df = load_data()

    if df.empty:
        print("Keine Daten für Temperatur-Vorhersage vorhanden.")
        return

    df = df.copy()
    df["t"] = range(len(df))
    df["hour"] = df["time"].dt.hour
    df["weekday"] = df["time"].dt.weekday

    # Zyklische Features für Stunde und Wochentag
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["weekday_sin"] = np.sin(2 * np.pi * df["weekday"] / 7)
    df["weekday_cos"] = np.cos(2 * np.pi * df["weekday"] / 7)

    X = df[["t", "hour_sin", "hour_cos", "weekday_sin", "weekday_cos"]]
    y = df["value"]

    model = LinearRegression()
    model.fit(X, y)

    model_dir = os.path.dirname(FORECAST_MODEL_PATH)
    if model_dir and not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)

    joblib.dump(model, FORECAST_MODEL_PATH)
    print("Forecast-Modell trainiert & gespeichert →", FORECAST_MODEL_PATH)
    from sklearn.metrics import mean_squared_error

    y_pred = model.predict(X)
    mse = mean_squared_error(y, y_pred)
    print(f"Trainings-MSE: {mse:.2f}", flush=True)


def predict_future(hours=24):
    df = load_data()
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["t"] = range(len(df))
    last_time = df["time"].iloc[-1]
    start_t = df["t"].iloc[-1] + 1

    future_times = [last_time + timedelta(hours=i + 1) for i in range(hours)]
    t_values = list(range(start_t, start_t + hours))
    hour_values = [t.hour for t in future_times]
    weekday_values = [t.weekday() for t in future_times]

    future_df = pd.DataFrame({
        "t": t_values,
        "hour": hour_values,
        "weekday": weekday_values
    })

    # Zyklische Features auch hier berechnen
    future_df["hour_sin"] = np.sin(2 * np.pi * future_df["hour"] / 24)
    future_df["hour_cos"] = np.cos(2 * np.pi * future_df["hour"] / 24)
    future_df["weekday_sin"] = np.sin(2 * np.pi * future_df["weekday"] / 7)
    future_df["weekday_cos"] = np.cos(2 * np.pi * future_df["weekday"] / 7)

    future_df = future_df[["t", "hour_sin", "hour_cos", "weekday_sin", "weekday_cos"]]

    if not os.path.exists(FORECAST_MODEL_PATH):
        raise FileNotFoundError("Forecast-Modell nicht gefunden. Bitte zuerst trainieren.")

    model = joblib.load(FORECAST_MODEL_PATH)
    preds = model.predict(future_df)

    return pd.DataFrame({"time": future_times, "predicted": preds})


def load_data_for_anomaly():
    query = """
        SELECT EXTRACT(EPOCH FROM time) AS t, value
        FROM measurements
        WHERE sensor_id = %s
        ORDER BY time DESC
        LIMIT %s;
    """
    with get_conn() as conn:
        df = pd.read_sql(query, conn, params=[SENSOR_ID, TRAIN_LIMIT])
    return df.sort_values("t")


def train_anomaly_model():
    df = load_data_for_anomaly()
    if df.empty:
        print("Keine Daten für Anomalie-Training gefunden.", flush=True)
        return
    model = IsolationForest(contamination=0.01, random_state=0)
    model.fit(df[["value"]])
    model_dir = os.path.dirname(MODEL_PATH)
    if model_dir and not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print("Anomalie-Modell gespeichert →", MODEL_PATH, flush=True)
    try:
        preds = model.predict(df[["value"]])
        n_anom = int((preds == -1).sum())
        print(f"Anomalien im Trainingsset: {n_anom} von {len(df)}", flush=True)
    except Exception:
        pass


def predict(values: pd.Series):
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Modelldatei nicht gefunden unter {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    arr = values.to_numpy().reshape(-1, 1)
    return model.predict(arr)


def detect_latest():
    query = """
        SELECT EXTRACT(EPOCH FROM time) AS t, value
        FROM measurements
        WHERE sensor_id = %s
        ORDER BY time DESC
        LIMIT 1;
    """
    with get_conn() as conn:
        df = pd.read_sql(query, conn, params=[SENSOR_ID])
    if df.empty:
        print("Keine aktuelle Messung gefunden.")
        return
    latest_value = df["value"].iloc[0]
    result = predict(pd.Series([latest_value]))
    if result[0] == -1:
        print(f"🚨 Anomalie erkannt: {latest_value}", flush=True)
    else:
        print(f"✅ Normalwert: {latest_value}")


if __name__ == "__main__":
    print("ML_SENSOR_ID =", SENSOR_ID)
    if not SENSOR_ID:
        print("Setze ML_SENSOR_ID-Umgebungsvariable, um Modell zu trainieren.")
    else:
        try:
            wait_for_db(max_retries=12, delay=5)
            print("DB-Verbindung steht, starte Training...")
        except RuntimeError as e:
            print("Fehler: ", e)
            exit(1)
        train_anomaly_model()
        train_forecast_model()

        print("Starte Anomalie-Erkennung alle 10 Sekunden...", flush=True)
        while True:
            detect_latest()
            time.sleep(10)
