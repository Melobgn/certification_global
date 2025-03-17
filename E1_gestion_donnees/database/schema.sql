CREATE TABLE IF NOT EXISTS site (
    site_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS product (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    brand TEXT,
    title TEXT,
    description TEXT,
    model TEXT,
    generic_name TEXT,
    FOREIGN KEY (site_id) REFERENCES site(site_id)
);

CREATE TABLE IF NOT EXISTS product_image (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);

CREATE TABLE IF NOT EXISTS classification_history (
    classification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    is_weapon BOOLEAN NOT NULL,
    confidence_score FLOAT NOT NULL,
    model_version TEXT NOT NULL,
    classification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);

CREATE TABLE IF NOT EXISTS data_processing_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_type TEXT NOT NULL,
    status TEXT NOT NULL,
    details TEXT,
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les recherches
CREATE INDEX idx_product_site ON product(site_id);
CREATE INDEX idx_classification_product ON classification_history(product_id); 