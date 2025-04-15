from evidently import Report
from evidently.presets import DataDriftPreset
import pandas as pd
import os

# === XGBoost Monitoring ===
xgb_ref = pd.read_csv("/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/monitoring/evidently/xgboost_reference_sample.csv")
xgb_prod = pd.read_csv("/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/monitoring/evidently/xgboost_production_sample.csv")

# ✅ Renommer la colonne d'annotation (label) pour matcher celle de prod
xgb_ref = xgb_ref.rename(columns={'is_weapon': 'is_weapon_pred'})

xgb_ref = xgb_ref.dropna(subset=['is_weapon_pred'])
xgb_prod = xgb_prod.dropna(subset=['is_weapon_pred'])

# Afficher les valeurs nulles
print("🔍 Valeurs nulles dans xgboost_reference_sample.csv :")
print(xgb_ref.isnull().sum())

print("\n🔍 Valeurs nulles dans xgboost_production_sample.csv :")
print(xgb_prod.isnull().sum())



report = Report(metrics=[DataDriftPreset()])
xgb_report = report.run(reference_data=xgb_ref, current_data=xgb_prod)
xgb_report
xgb_report.save_html("xgboost_drift_report.html")

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
