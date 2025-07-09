from evidently import Report, Dataset, DataDefinition
from evidently.presets import DataDriftPreset, DataSummaryPreset
import pandas as pd

# === Charger les données ===
xgb_ref = pd.read_csv("/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/monitoring/evidently/xgboost_reference_sample.csv")
xgb_prod = pd.read_csv("/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/monitoring/evidently/xgboost_production_sample.csv")

# ✅ Renommer target en prédiction pour matcher avec prod
xgb_ref = xgb_ref.rename(columns={"is_weapon": "is_weapon_pred"})

# ✅ Nettoyer
xgb_ref = xgb_ref.dropna(subset=['title', 'description', 'is_weapon_pred'])
xgb_prod = xgb_prod.dropna(subset=['title', 'description', 'is_weapon_pred'])

# ✅ Définir les colonnes
definition = DataDefinition(
    categorical_columns=['is_weapon_pred'],
    text_columns=['title', 'description']
)

# ✅ Créer les datasets
reference_dataset = Dataset.from_pandas(xgb_ref, data_definition=definition)
production_dataset = Dataset.from_pandas(xgb_prod, data_definition=definition)

# ✅ Générer le rapport
report = Report(metrics=[
    DataDriftPreset(),
    DataSummaryPreset()
])
my_eval = report.run(reference_data=reference_dataset, current_data=production_dataset)
my_eval.save_html("xgboost_drift_report2.html")
print(my_eval.dict())

# report.save_html("xgboost_drift_summary_report.html")

# # === YOLO Monitoring PAS ASSEZ DE DONNEES IMAGES POUR LE MOMENT ===
# yolo_ref = pd.read_csv("/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/monitoring/evidently/yolo_reference_sample.csv")
# yolo_prod = pd.read_csv("/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/monitoring/evidently/yolo_production_sample.csv")

# print("\n🔍 Valeurs nulles dans yolo_reference_sample.csv :")
# print(yolo_ref.isnull().sum())

# print("\n🔍 Valeurs nulles dans yolo_production_sample.csv :")
# print(yolo_prod.isnull().sum())

# report = Report(metrics=[DataDriftPreset()])
# yolo_report = report.run(reference_data=yolo_ref, current_data=yolo_prod)
# yolo_report

# yolo_report.save_html("./yolo_drift_report.html")

# print("Rapports Evidently générés.")