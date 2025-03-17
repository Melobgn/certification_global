# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EpartenairesSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ProductItem(scrapy.Item):
    url = scrapy.Field()
    brand = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    image = scrapy.Field()
    model = scrapy.Field()
    generique = scrapy.Field()
