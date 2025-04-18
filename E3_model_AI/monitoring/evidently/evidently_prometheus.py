from prometheus_client import start_http_server, Gauge
import pandas as pd
import time
import os
import re
from evidently import Report, Dataset, DataDefinition
from evidently.presets import DataDriftPreset
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger le fichier .env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Détection de l'environnement
IS_DOCKER = os.path.exists("/app")
IS_CI = os.getenv("GITHUB_ACTIONS") == "true"

# Définir le chemin racine
if IS_DOCKER:
    BASE_DIR = Path("/app")
elif IS_CI:
    BASE_DIR = Path("E3_model_AI")
else:
    BASE_DIR = Path("/home/utilisateur/Documents/Certification/certification_global/E3_model_AI")


# === Chemins des fichiers
REF_XGB = BASE_DIR / "monitoring" / "evidently" / "xgboost_reference_sample.csv"
PROD_XGB = BASE_DIR / "monitoring" / "evidently" / "xgboost_production_sample.csv"

# === Stockage dynamique des métriques
prometheus_gauges = {}

def sanitize(name):
    return re.sub(r"[^a-zA-Z0-9_:]", "_", name).lower().strip("_")

def set_prometheus_metric(metric_name, value, labels=None):
    key = (metric_name, tuple(sorted((labels or {}).items())))
    if key not in prometheus_gauges:
        if labels:
            prometheus_gauges[key] = Gauge(metric_name, f"Metric: {metric_name}", list(labels.keys()))
        else:
            prometheus_gauges[key] = Gauge(metric_name, f"Metric: {metric_name}")
    if labels:
        prometheus_gauges[key].labels(**labels).set(value)
    else:
        prometheus_gauges[key].set(value)

def compute_and_expose_metrics():

    if not os.path.exists(REF_XGB) or not os.path.exists(PROD_XGB):
        print("❌ Fichier(s) manquant(s)")
        return

    xgb_ref = pd.read_csv(REF_XGB)
    xgb_prod = pd.read_csv(PROD_XGB)

    # Renommer target
    xgb_ref = xgb_ref.rename(columns={"is_weapon": "is_weapon_pred"})
    xgb_ref = xgb_ref.dropna(subset=["title", "description", "is_weapon_pred"])
    xgb_prod = xgb_prod.dropna(subset=["title", "description", "is_weapon_pred"])

    # Définir les types de colonnes
    definition = DataDefinition(
        categorical_columns=["is_weapon_pred"],
        text_columns=["title", "description"]
    )

    ref_dataset = Dataset.from_pandas(xgb_ref, data_definition=definition)
    prod_dataset = Dataset.from_pandas(xgb_prod, data_definition=definition)

    # === Structure Evidently
    report = Report(metrics=[DataDriftPreset()])
    my_eval = report.run(reference_data=ref_dataset, current_data=prod_dataset)
    result = my_eval.dict()

    print("✅ Résultat récupéré depuis report.dict()")
    print(result)

    # === Extraction et exposition Prometheus
    for metric in result.get("metrics", []):
        metric_id = sanitize(metric.get("metric_id", "unknown_metric"))
        metric_value = metric.get("value", {})
        print(f"🔍 Traitement metric_id={metric_id} | value={metric_value}")

        if isinstance(metric_value, (int, float)):
            metric_name = sanitize(f"evidently_{metric_id}")
            set_prometheus_metric(metric_name, metric_value)

        elif isinstance(metric_value, dict):
            for key, value in metric_value.items():
                if isinstance(value, (int, float)):
                    metric_name = sanitize(f"evidently_{metric_id}_{key}")
                    set_prometheus_metric(metric_name, value)

        # Cas spécifique : drift_by_columns → pas présent ici, mais si présent :
        if metric_id == "datadrift" and "drift_by_columns" in metric_value:
            for col, details in metric_value["drift_by_columns"].items():
                col_key = sanitize(col)
                drifted = 1 if details.get("drift_detected") else 0
                p_val = details.get("p_value", 0)

                set_prometheus_metric("xgb_column_drifted", drifted, labels={"column": col_key})
                set_prometheus_metric("xgb_column_p_value", p_val, labels={"column": col_key})

def main():
    print("📊 Serveur Prometheus lancé sur le port 8001...")
    start_http_server(8001)

    while True:
        try:
            compute_and_expose_metrics()
        except Exception as e:
            print(f"❌ Erreur Evidently → {e}")
        time.sleep(30)

if __name__ == "__main__":
    main()



# from prometheus_client import start_http_server, Gauge
# import time
# import pandas as pd
# import os
# from evidently import Report, Dataset, DataDefinition
# from evidently.presets import DataDriftPreset

# # === Chemins des fichiers
# REF_XGB = "xgboost_reference_sample.csv"
# PROD_XGB = "xgboost_production_sample.csv"
# REF_YOLO = "yolo_reference_sample.csv"
# PROD_YOLO = "yolo_production_sample.csv"

# # === Métriques globales Prometheus
# xgb_dataset_drift = Gauge("xgb_dataset_drift", "Drift global détecté pour XGBoost")
# xgb_drifted_features = Gauge("xgb_drifted_features", "Nombre de colonnes en drift XGBoost")
# xgb_total_features = Gauge("xgb_total_features", "Nombre total de colonnes XGBoost")
# xgb_share_drifted = Gauge("xgb_share_drifted_features", "Part des colonnes en drift XGBoost")

# yolo_dataset_drift = Gauge("yolo_dataset_drift", "Drift global détecté pour YOLO")
# yolo_drifted_features = Gauge("yolo_drifted_features", "Nombre de colonnes en drift YOLO")
# yolo_total_features = Gauge("yolo_total_features", "Nombre total de colonnes YOLO")
# yolo_share_drifted = Gauge("yolo_share_drifted_features", "Part des colonnes en drift YOLO")

# # === Métriques par colonne
# xgb_column_drift = {}
# xgb_column_p_value = {}
# yolo_column_drift = {}
# yolo_column_p_value = {}

# def compute_and_export_metrics(ref_file, prod_file, prefix, gauges_drift, gauges_by_column, columns_def):
#     if not os.path.exists(ref_file) or not os.path.exists(prod_file):
#         print(f"❌ Fichier manquant : {ref_file} ou {prod_file}")
#         return

#     ref = pd.read_csv(ref_file)
#     prod = pd.read_csv(prod_file)

#     # Spécifique à XGBoost : renommer la target
#     if "xgb" in prefix:
#         ref = ref.rename(columns={"is_weapon": "is_weapon_pred"})

#     # Nettoyage
#     ref = ref.dropna(subset=columns_def)
#     prod = prod.dropna(subset=columns_def)

#     # DataDefinition
#     definition = DataDefinition(
#         categorical_columns=["is_weapon_pred"],
#         text_columns=["title", "description"]
#     )

#     ref_dataset = Dataset.from_pandas(ref, data_definition=definition)
#     prod_dataset = Dataset.from_pandas(prod, data_definition=definition)

#     report = Report(metrics=[DataDriftPreset()])
#     report.run(reference_data=ref_dataset, current_data=prod_dataset)
#     result = report.as_dict()["metrics"][0]["result"]

#     # 🔢 Métriques globales
#     gauges_drift["dataset_drift"].set(1 if result["dataset_drift"] else 0)
#     gauges_drift["n_drifted"].set(result["n_drifted_features"])
#     gauges_drift["n_total"].set(result["n_features"])
#     gauges_drift["share_drifted"].set(result["share_drifted_features"])

#     # 📊 Par colonne
#     for col, details in result["drift_by_columns"].items():
#         col_key = col.lower().replace(" ", "_")

#         if col_key not in gauges_by_column["drift"]:
#             gauges_by_column["drift"][col_key] = Gauge(f"{prefix}_column_drifted", f"Colonne en drift - {col}", ['column'])
#             gauges_by_column["p_value"][col_key] = Gauge(f"{prefix}_column_p_value", f"P-value - {col}", ['column'])

#         drifted = 1 if details["drift_detected"] else 0
#         p_value = details.get("p_value", 0)

#         gauges_by_column["drift"][col_key].labels(column=col_key).set(drifted)
#         gauges_by_column["p_value"][col_key].labels(column=col_key).set(p_value)

# def main():
#     print("📊 Démarrage de Evidently Prometheus sur le port 8001...")
#     start_http_server(8001)

#     while True:
#         try:
#             compute_and_export_metrics(
#                 REF_XGB,
#                 PROD_XGB,
#                 prefix="xgb",
#                 gauges_drift={
#                     "dataset_drift": xgb_dataset_drift,
#                     "n_drifted": xgb_drifted_features,
#                     "n_total": xgb_total_features,
#                     "share_drifted": xgb_share_drifted
#                 },
#                 gauges_by_column={
#                     "drift": xgb_column_drift,
#                     "p_value": xgb_column_p_value
#                 },
#                 columns_def=["title", "description", "is_weapon_pred"]
#             )

#             compute_and_export_metrics(
#                 REF_YOLO,
#                 PROD_YOLO,
#                 prefix="yolo",
#                 gauges_drift={
#                     "dataset_drift": yolo_dataset_drift,
#                     "n_drifted": yolo_drifted_features,
#                     "n_total": yolo_total_features,
#                     "share_drifted": yolo_share_drifted
#                 },
#                 gauges_by_column={
#                     "drift": yolo_column_drift,
#                     "p_value": yolo_column_p_value
#                 },
#                 columns_def=["title", "description", "is_weapon_pred"]
#             )

#         except Exception as e:
#             print(f"❌ Erreur Evidently Monitoring : {e}")

#         time.sleep(30)

# if __name__ == "__main__":
#     main()
