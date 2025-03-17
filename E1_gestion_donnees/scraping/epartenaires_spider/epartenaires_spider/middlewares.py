# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html


from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from urllib.parse import urlencode
import requests 
from twisted.internet.error import TimeoutError as TwistedTimeoutError
from twisted.internet.error import TCPTimedOutError
# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
import csv
import logging
import random


# class IgnoreTimeoutMiddleware:
#     def process_exception(self, request, exception, spider):
#         if isinstance(exception, (TimeoutError, TCPTimedOutError, TwistedTimeoutError)):
#             spider.logger.info(f"Ignoring timeout for {request.url}")
            
#             # Enregistrer l'URL avec timeout dans un fichier CSV
#             with open('slow_sites.csv', 'a', newline='') as file:
#                 writer = csv.writer(file)
#                 writer.writerow([request.url])
            
#             return None  # Continue le scraping en passant à l'URL suivante
#         else:
#             spider.logger.warning(f"Other exception encountered: {exception} for {request.url}")


class EpartenairesSpiderSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.


    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s


    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.


        # Should return None or raise an exception.
        return None


    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.


        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i


    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.


        # Should return either None or an iterable of Request or item objects.
        pass


    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.


        # Must return only requests (not items).
        for r in start_requests:
            yield r


    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class LogIgnoringResponseMiddleware:
    def __init__(self):
        # Ouvrir le fichier CSV pour écrire les URLs ignorées
        self.file = open("ignored_responses.csv", "w", newline="")
        self.csv_writer = csv.writer(self.file)
        self.csv_writer.writerow(["url"])


    def process_response(self, request, response, spider):
        # Vérifier le statut de la réponse ignorée
        if response.status in (403, 404):
            # Enregistrer l'URL et le statut dans le fichier CSV
            self.csv_writer.writerow([response.url, response.status])
            spider.logger.info(f"Ignored response URL saved: {response.url} with status {response.status}")
            raise IgnoreRequest(f"Ignoring response with status {response.status} for {response.url}")
            
        return response


    def close_spider(self, spider):
        # Fermer le fichier CSV à la fin
        self.file.close()


class EpartenairesSpiderDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.


    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s


    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.


        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None


    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.


        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response


    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.


        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass


    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
        


class FakeUserAgentMiddleware:
    def __init__(self, settings):
        self.user_agents = settings.get('USER_AGENT')


    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)


    def make_header(self):
        # Choose a random user agent
        user_agent = random.choice(self.user_agents)
        header = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'identity',
            'DNT': '1',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        return header
    
    def process_request(self, request, spider):
        # Generate and set the header for the request
        header = self.make_header()
        request.headers.update(header)
        print(request.headers['User-Agent'])  # Print the User-Agent being used
