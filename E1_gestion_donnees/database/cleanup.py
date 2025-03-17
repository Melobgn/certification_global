import sqlite3
from datetime import datetime
import logging
import os

# Configuration du logging
logging.basicConfig(
    filename='database/cleanup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def connect_db():
    """Établit la connexion à la base de données"""
    try:
        return sqlite3.connect('database/weapon_detection.db')
    except sqlite3.Error as e:
        logging.error(f"Erreur de connexion à la base de données: {e}")
        raise

def cleanup_old_data():
    """Supprime les données plus anciennes que 12 mois"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Compter les enregistrements avant nettoyage
        cursor.execute("SELECT COUNT(*) FROM product")
        count_before = cursor.fetchone()[0]
        
        # Supprimer les produits anciens
        cursor.execute("""
            DELETE FROM product 
            WHERE created_at < date('now', '-12 months')
        """)
        
        # Compter les enregistrements après nettoyage
        cursor.execute("SELECT COUNT(*) FROM product")
        count_after = cursor.fetchone()[0]
        
        deleted_count = count_before - count_after
        
        # Nettoyer les images orphelines
        cursor.execute("""
            DELETE FROM product_image 
            WHERE product_id NOT IN (SELECT product_id FROM product)
        """)
        
        # Nettoyer les vieux logs
        cursor.execute("""
            DELETE FROM data_processing_log 
            WHERE created_at < date('now', '-6 months')
        """)
        
        # Enregistrer l'opération de nettoyage
        cursor.execute("""
            INSERT INTO data_processing_log (
                process_type, status, details
            ) VALUES (?, ?, ?)
        """, (
            'cleanup',
            'success',
            f"Nettoyage effectué: {deleted_count} produits supprimés"
        ))
        
        conn.commit()
        logging.info(f"Nettoyage réussi: {deleted_count} produits supprimés")
        
    except sqlite3.Error as e:
        conn.rollback()
        logging.error(f"Erreur lors du nettoyage: {e}")
        cursor.execute("""
            INSERT INTO data_processing_log (
                process_type, status, details
            ) VALUES (?, ?, ?)
        """, (
            'cleanup',
            'error',
            f"Erreur lors du nettoyage: {str(e)}"
        ))
        conn.commit()
        
    finally:
        conn.close()

def optimize_database():
    """Optimise la base de données"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("VACUUM")
        cursor.execute("ANALYZE")
        logging.info("Optimisation de la base de données effectuée")
        
    except sqlite3.Error as e:
        logging.error(f"Erreur lors de l'optimisation: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        logging.info("Début du processus de nettoyage")
        cleanup_old_data()
        optimize_database()
        logging.info("Fin du processus de nettoyage")
        
    except Exception as e:
        logging.error(f"Erreur critique lors du nettoyage: {e}") 