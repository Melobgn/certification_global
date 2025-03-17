import sqlite3
import pandas as pd
import glob
import os

def create_database():
    """Crée la base de données et les tables"""
    conn = sqlite3.connect('database/weapon_detection.db')
    
    # Lire et exécuter le script schema.sql
    with open('database/schema.sql', 'r') as schema_file:
        conn.executescript(schema_file.read())
    
    conn.close()

def get_site_name_from_file(filename):
    """Détermine le nom du site et l'URL de son sitemap à partir du nom du fichier CSV"""
    if 'mda' in filename.lower():
        return 'mda', 'https://www.mda-electromenager.com/sitemap.xml'
    elif 'bricodepot' in filename.lower():
        return 'bricodepot', 'https://www.bricodepot.fr/productSitemap2.xml'
    elif 'joueclub' in filename.lower():
        return 'joueclub', 'https://www.joueclub.fr/Assets/Rbs/Seo/100185/fr_FR/Rbs_Catalog_Product.1.xml'
    elif 'armurerie_lavaux' in filename.lower():
        return 'armurerie_lavaux', 'https://www.armurerie-lavaux.com/sitemap.xml'
    elif 'boutiquedesartsmartiaux' in filename.lower():
        return 'boutiquedesartsmartiaux', 'https://boutiquedesartsmartiaux.com/sitemap.xml'
    else:
        return 'unknown', 'unknown'

def import_products():
    """Importe les données des fichiers CSV dans la base"""
    conn = sqlite3.connect('database/weapon_detection.db')
    cursor = conn.cursor()

    # Récupérer tous les fichiers CSV à la racine
    csv_files = glob.glob('*.csv')
    
    for csv_file in csv_files:
        print(f"Importing {csv_file}...")
        
        # Déterminer le site à partir du nom du fichier
        site_name, site_url = get_site_name_from_file(csv_file)
        
        if site_name == 'unknown':
            print(f"Skipping unknown site file: {csv_file}")
            continue
            
        # Insérer le site s'il n'existe pas déjà
        cursor.execute("""
            INSERT OR IGNORE INTO site (name, url)
            VALUES (?, ?)
        """, (site_name, site_url))
        
        # Récupérer le site_id
        cursor.execute("SELECT site_id FROM site WHERE name = ?", (site_name,))
        site_id = cursor.fetchone()[0]
        
        # Lire le fichier CSV
        try:
            df = pd.read_csv(csv_file)
            
            # Pour chaque ligne du CSV
            for _, row in df.iterrows():
                try:
                    # Insérer le produit sans les images
                    cursor.execute("""
                        INSERT INTO product (
                            site_id, url, brand, title, description, 
                            model, generic_name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        site_id,
                        row.get('url', ''),
                        row.get('brand', ''),
                        row.get('title', ''),
                        row.get('description', ''),
                        row.get('model', ''),
                        row.get('generique', '')
                    ))
                    
                    product_id = cursor.lastrowid

                    # Gérer les images
                    if not pd.isna(row['image']):
                        if isinstance(row['image'], str):
                            try:
                                images = eval(row['image'])
                            except:
                                images = [row['image']]
                        else:
                            images = [row['image']]

                        # Insérer chaque URL d'image
                        for image_url in images:
                            if image_url and not pd.isna(image_url):
                                cursor.execute("""
                                    INSERT INTO product_image (product_id, image_url)
                                    VALUES (?, ?)
                                """, (product_id, image_url))
                    
                    # Log l'import
                    cursor.execute("""
                        INSERT INTO data_processing_log (
                            process_type, status, details
                        ) VALUES (?, ?, ?)
                    """, (
                        'import',
                        'success',
                        f"Imported product from {site_name}: {row.get('title', 'No title')}"
                    ))
                    
                except Exception as e:
                    print(f"Error importing row from {csv_file}: {str(e)}")
                    cursor.execute("""
                        INSERT INTO data_processing_log (
                            process_type, status, details
                        ) VALUES (?, ?, ?)
                    """, (
                        'import',
                        'error',
                        f"Error importing row from {csv_file}: {str(e)}"
                    ))
                    continue
            
            conn.commit()
            
        except Exception as e:
            print(f"Error processing file {csv_file}: {str(e)}")
            cursor.execute("""
                INSERT INTO data_processing_log (
                    process_type, status, details
                ) VALUES (?, ?, ?)
            """, (
                'import',
                'error',
                f"Error processing file {csv_file}: {str(e)}"
            ))
            continue
    
    conn.close()

if __name__ == "__main__":
    # Créer la base de données
    create_database()
    
    # Importer les données
    import_products()
    print("Import completed successfully!") 