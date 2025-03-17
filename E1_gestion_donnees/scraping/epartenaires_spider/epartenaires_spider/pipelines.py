# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re
from html import unescape
import unicodedata


class EpartenairesSpiderPipeline:
    def clean_text(self, text):
        if not text:
            return ""
        
        # Décoder les entités HTML (comme &eacute; pour é)
        text = unescape(text)

        # Supprimer les balises HTML (expression régulière plus robuste)
        text = re.sub(r'<[^>]+>', ' ', text)  # Remplace les balises par des espaces
        text = re.sub(r'</?\w+\s*/?\s*>', ' ', text)  # Capture aussi les balises mal formées

        # Décoder les caractères Unicode mal encodés
        text = text.encode('utf-8', 'ignore').decode('utf-8')

        # Remplacer les tirets et underscores par des espaces
        text = re.sub(r'[-_]', ' ', text)

        # Supprimer les caractères spéciaux (garde les lettres, chiffres et espaces)
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

        # Normaliser les caractères Unicode (é → e, ç → c, etc.)
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')

        # Supprimer les espaces superflus
        text = re.sub(r'\s+', ' ', text).strip()

        return text


    def process_item(self, item, spider):
        """
        Nettoie les textes des champs avant de les stocker.
        """
        if 'title' in item:
            item['title'] = self.clean_text(item['title'])
        if 'description' in item:
            item['description'] = self.clean_text(item['description'])


        return item
