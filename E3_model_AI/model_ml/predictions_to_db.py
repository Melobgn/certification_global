
import argparse
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

def main(xgb_csv, yolo_csv, error_csv, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Créer les tables si elles n'existent pas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions_xgboost (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        description TEXT,
        title TEXT,
        product_id TEXT,
        is_weapon_pred BOOLEAN
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions_yolo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        title TEXT,
        description TEXT,
        image TEXT,
        confidence_score REAL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS errors_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        image TEXT
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS classification_history (
        classification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT UNIQUE,
        is_weapon BOOLEAN,
        confidence_score REAL,
        model_version TEXT,
        classification_date TEXT
    )''')

    # Charger les CSV
    xgb = pd.read_csv(xgb_csv)
    yolo = pd.read_csv(yolo_csv)
    errors = pd.read_csv(error_csv)

    # Nettoyage
    xgb.columns = xgb.columns.str.lower().str.strip()
    yolo.columns = yolo.columns.str.lower().str.strip()
    errors.columns = errors.columns.str.lower().str.strip()

    # Import dans DB
    xgb.to_sql("predictions_xgboost", conn, if_exists="replace", index=False)
    yolo.to_sql("predictions_yolo", conn, if_exists="replace", index=False)
    errors.to_sql("errors_images", conn, if_exists="replace", index=False)

    error_images_set = set(errors["image"].str.strip())
    classification_rows = []

    for _, row in yolo.iterrows():
        url = row["url"]
        product_id = url
        image_name = Path(row["image"]).name.strip()
        if Path(row["image"]).exists() or image_name in error_images_set:
            classification_rows.append((
                product_id,
                True,
                row["confidence_score"],
                "YOLO_v1",
                datetime.now().isoformat()
            ))

    urls_yolo = {row[0] for row in classification_rows}

    for _, row in xgb.iterrows():
        product_id = row["product_id"]
        if product_id not in urls_yolo:
            classification_rows.append((
                product_id,
                row["is_weapon_pred"],
                None,
                "XGBoost_v1",
                datetime.now().isoformat()
            ))

    for row in classification_rows:
        cursor.execute('''
            INSERT OR IGNORE INTO classification_history
            (product_id, is_weapon, confidence_score, model_version, classification_date)
            VALUES (?, ?, ?, ?, ?)
        ''', row)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importer les prédictions dans la base de données.")
    parser.add_argument("--xgb", required=True, help="Chemin vers predictions_xgboost.csv")
    parser.add_argument("--yolo", required=True, help="Chemin vers predictions_computer_vision.csv")
    parser.add_argument("--errors", required=True, help="Chemin vers error_images.csv")
    parser.add_argument("--db", required=True, help="Chemin vers la base SQLite")

    args = parser.parse_args()
    main(args.xgb, args.yolo, args.errors, args.db)