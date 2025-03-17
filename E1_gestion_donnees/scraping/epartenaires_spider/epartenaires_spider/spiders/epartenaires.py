import scrapy
# from scrapy.spiders import XMLFeedSpider
# from urllib.parse import urlparse
from ..items import ProductItem
import pandas as pd 
import re
import csv
import time
import logging
import os
from scrapy.utils.log import configure_logging


class EpartenairesSpider(scrapy.Spider):
    name = "epartenaires"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Charger les marques depuis les feuilles Excel
        self.generique_weapon_df = pd.read_excel('/home/utilisateur/Documents/Certification/certif_gestions_donnees/referentiel_armes_feu.xlsx', sheet_name='generique')
        self.weapon_brands_df = pd.read_excel('/home/utilisateur/Documents/Certification/certif_gestions_donnees/referentiel_armes_feu.xlsx', sheet_name='marques')
        
        # Créer des listes pour les armes et marques
        self.generique_weapon = self.generique_weapon_df['weapon'].dropna().str.strip().str.lower().tolist()
        self.weapon_brands = self.weapon_brands_df['brand'].dropna().str.strip().str.lower().tolist()
    
        
        # Fonction pour nettoyer les chaînes en supprimant les caractères spéciaux
        def clean_text(text):
            # Remplacer les caractères non alphanumériques par un espace
            return re.sub(r'[^a-zA-Z0-9\s]', '', text).strip().lower()


        # Charger les données du fichier Excel
        brand_model_df = pd.read_excel('/home/utilisateur/Documents/Certification/certif_gestions_donnees/referentiel_armes_feu.xlsx', sheet_name='marques_modeles')


        # Assurez-vous que les colonnes brand et model sont bien nettoyées
        brand_model_df['brand'] = brand_model_df['brand'].dropna().str.strip().str.lower().apply(clean_text)
        brand_model_df['model'] = brand_model_df['model'].dropna().astype(str).str.strip().apply(clean_text)


        # Créer un dictionnaire avec brand en clé et set des modèles comme valeurs
        self.brand_model_dict = {}
        for _, row in brand_model_df.iterrows():
            brand = row.get('brand')
            model = row.get('model')


            # Vérifier si la marque et le modèle existent et ne sont pas NaN
            if pd.notna(brand) and pd.notna(model):
                if brand not in self.brand_model_dict:
                    self.brand_model_dict[brand] = set()
                self.brand_model_dict[brand].add(model)


        # Créer la regex pour les marques et modèles
        brand_model_regex_parts = []


        # Ajoutez les combinaisons brand + model
        for brand, models in self.brand_model_dict.items():
            for model in models:
                brand_model_regex_parts.append(
                    rf'\b(?:{re.escape(brand)}\s*{re.escape(model)}|{re.escape(model)}\s*{re.escape(brand)})\b'
                )


        # Compiler la regex pour marques et modèles
        self.brand_model_regex = re.compile('|'.join(brand_model_regex_parts), re.IGNORECASE)


        # Créer la regex pour les termes génériques
        generic_regex_parts = [r'\b(?:' + '|'.join(map(re.escape, self.generique_weapon)) + r')\b']


        # Compiler la regex pour termes génériques
        self.generique_regex = re.compile('|'.join(generic_regex_parts), re.IGNORECASE)


        
    def start_requests(self):
        # Sitemaps des sites partenaires à scraper
        sitemap_url = 'https://www.bricodepot.fr/productSitemap3.xml'
        yield scrapy.Request(url=sitemap_url, callback=self.parse_sitemap, dont_filter=True)
            


    def parse_sitemap(self, response):
        # print(f"Content-Type: {response.headers.get('Content-Type')}")
        # print(f"Body (first 500 chars): {response.body[:500]}")
        # Extraire toutes les URLs contenant "http"
        all_urls = response.xpath('//*[contains(text(), "http")]/text()').getall()

        
        # Filtrer pour exclure les URLs d'images (.jpg, .png, etc.)
        filtered_urls = [
            url for url in all_urls
            if not url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.pdf', '.zip', '.css', '.js'))
        ]


        if not filtered_urls:
            self.logger.warning(f"No valid URLs found in sitemap: {response.url}")
        
        
        for url in filtered_urls:
            if 'sitemap' in url:
                # self.logger.info(f"Found sub-sitemap: {url}")
                yield scrapy.Request(url=url, callback=self.parse_sitemap, dont_filter=True)
            else:
                # Activer Playwright pour les pages de produit
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_product,
                )


    
    def parse_product(self, response):
        found_brand = None
        found_model = None
        found_generique = None


        title = (
            response.xpath(
                '//head/title/text() | '  # Titre dans la balise <title>
                '//meta[@property="og:title"]/@content | '  # Open Graph title
                '//meta[@name="twitter:title"]/@content | '  # Twitter card title
                '//h1/text() | '  # Premier <h1> sur la page
                '//meta[@itemprop="name"]/@content | '  # Microdata: itemprop="name"
                '//meta[@itemprop="headline"]/@content | '  # Microdata: itemprop="headline"
                '//div[contains(@class, "product-title")]//text() | '  # Titre dans un div avec une classe spécifique
                '//span[contains(@class, "title")]//text() | '  # Titre dans un span
                '//div[contains(@id, "title")]//text() | '  # Titre dans un div avec un ID spécifique
                '//meta[@property="dc:title"]/@content'  # Dublin Core title
            ).get()
            or "Titre non trouvé"
        )
        
        description = (
            response.xpath(
                '//meta[@name="description"]/@content | '  # Description dans meta
                '//meta[@property="og:description"]/@content | '  # Open Graph description
                '//meta[@name="twitter:description"]/@content | '  # Twitter card description
                '//meta[@itemprop="description"]/@content | '  # Microdata: itemprop="description"
                '//p[contains(@class, "description")]//text() | '  # Paragraphe avec une classe spécifique
                '//div[contains(@class, "description")]//text() | '  # Div avec une classe contenant description
                '//span[contains(@class, "description")]//text() | '  # Span avec une classe contenant description
                '//div[contains(@id, "description")]//text() | '  # Div avec un ID spécifique
                '//section[contains(@class, "description")]//text() | '  # Section dédiée à la description
                '//h2[contains(@class, "description")]//text() | '  # <h2> avec une classe description
                '//h2[contains(text(), "Description")]//text() | '  # <h2> contenant le mot "Description"
                '//h2/following-sibling::p[1]//text() | '  # Premier paragraphe après un <h2>
                '//h2/text() | '  # Parfois, la description est dans un <h2>
                '//h2/following-sibling::div[1]//text()'  # Premier div après un <h2>
            ).get()
            or "Description non trouvée"
        )

        # Extraction des images avec Playwright
        image = response.xpath(
            '//meta[@property="og:image"]/@content | '
            '//meta[@itemprop="image"]/@content | '
            '//img[@class="product-image"]/@src | '  # Images chargées par JS
            '//img[contains(@class, "product-image")]/@src | '
            '//img[contains(@src, "product")]/@src | '
            '//picture/source[@srcset]/@srcset | '
            '//div[@class="main-image"]//img/@src | '
            '//img[contains(@alt, "product")]/@src | '
            '//img[@class="main-product-image"]/@src | '
            '//img[@id="primaryImage"]/@src | '
            '//img[@data-src]/@data-src | '
            '//img[@srcset]/@srcset | '
            '//div[@id="image-block"]//img/@src | '
            '//figure[@class="product-image"]//img/@src | '
            '//a[@class="lightbox"]//img/@src | '
            '//span[@class="image-wrapper"]//img/@src | '
            '//img[@data-ng-src]/@src'  # Nouveau sélecteur
        ).getall()


        # Filtrage des images pour exclure les images non pertinentes
        filtered_images = [
            img for img in image
            if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) and
            not any(keyword in img.lower() for keyword in ["logo", "favicon", "icon", "placeholder"])
        ]


        # Convertir toutes les URLs relatives en absolues
        filtered_images = [response.urljoin(img) for img in filtered_images]
            
        # Vérifier la marque et le modèle dans le titre, la description, ou l'image avec regex
        if not found_brand and not found_model and title:
            for brand, models in self.brand_model_dict.items():
                for model in models:
                    if brand in title.lower() and model in title.lower():
                        found_brand = brand
                        found_model = model
                        break
            if not found_brand and self.brand_model_regex.search(title):
                found_brand = self.brand_model_regex.search(title).group()


        if not found_brand and not found_model and description:
            for brand, models in self.brand_model_dict.items():
                for model in models:
                    if brand in description.lower() and model in description.lower():
                        found_brand = brand
                        found_model = model
                        break
            if not found_brand and self.brand_model_regex.search(description):
                found_brand = self.brand_model_regex.search(description).group()
                


        # Vérifier les termes génériques, même si une marque/modèle est trouvée
        if title and self.generique_regex.search(title):
            found_generique = self.generique_regex.search(title).group()
        elif description and self.generique_regex.search(description):
            found_generique = self.generique_regex.search(description).group()


        # Vérification finale : Si on a une marque et un modèle MAIS aucun titre ou description, on ignore
        if (found_brand and found_model) and not (title and description):
            self.logger.warning(f"Produit ignoré : Marque & Modèle trouvés mais pas de titre/description ({response.url})")
            return
        
        if found_brand and found_model or found_generique:
            product_item = ProductItem()
            product_item['url'] = response.url
            product_item['brand'] = found_brand if found_brand else ''
            product_item['model'] = found_model if found_model else ''
            product_item['generique'] = found_generique if found_generique else ''
            product_item['title'] = title if title else ''
            product_item['description'] = description if description else ''
            product_item['image'] = filtered_images if filtered_images else []


            # Logs pour débogage avant écriture
            self.logger.info(f"Extracted Product Data: {product_item}")
            print("Final Item:", product_item)


            yield product_item
        else:
            self.logger.info(f"No relevant data found in product: {response.url}")
