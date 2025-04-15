from prometheus_client import start_http_server, Gauge
import time
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset
import os

# === Métriques Prometheus
xgb_drift = Gauge("xgboost_data_drift", "Dérive de données XGBoost")
yolo_drift = Gauge("yolo_data_drift", "Dérive de données YOLO")

# === Chemins relatifs
REF_XGB = "xgboost_reference_sample.csv"
PROD_XGB = "xgboost_production_sample.csv"
REF_YOLO = "yolo_reference_sample.csv"
PROD_YOLO = "yolo_production_sample.csv"

def compute_drift(ref_file, prod_file):
    if os.path.exists(ref_file) and os.path.exists(prod_file):
        ref = pd.read_csv(ref_file)
        prod = pd.read_csv(prod_file)

        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=ref, current_data=prod)
        result = report.as_dict()
        return result["metrics"][0]["result"]["dataset_drift"]
    else:
        return None

def main():
    print("📊 Démarrage de Evidently Prometheus sur le port 8001...")
    start_http_server(8001)

    while True:
        try:
            xgb_score = compute_drift(REF_XGB, PROD_XGB)
            if xgb_score is not None:
                xgb_drift.set(xgb_score)

            yolo_score = compute_drift(REF_YOLO, PROD_YOLO)
            if yolo_score is not None:
                yolo_drift.set(yolo_score)

        except Exception as e:
            print(f"❌ Erreur dans le monitoring Evidently → {e}")

        time.sleep(30)  # Rafraîchir toutes les 30 secondes

if __name__ == "__main__":
    main()
