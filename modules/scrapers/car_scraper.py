import os
import random
import time

import httpx
import pandas as pd
import requests
from bs4 import BeautifulSoup

from modules.scrapers.get_advertisement import AdvertisementFetcher
from utils.logger import console_logger
from utils.logger import file_logger


class CarScraper:
    """
        Scraps cars from otomoto.pl
        Args:
            model_file_path: path to file with models
            data_directory: path to directory where data will be saved
    """

    def __init__(self, model_file_path, data_directory):
        console_logger.info('Initializing Car scrapper')
        file_logger.info('Initializing Car scrapper')
        self.model_file_path = os.path.join(os.getcwd(), model_file_path)
        self.data_directory = os.path.join(os.getcwd(), data_directory)
        self.models = self._read_models()
        self.ad_fetcher = AdvertisementFetcher()

    def _read_models(self):
        with open(self.model_file_path, 'r', encoding='utf-8') as file:
            models = file.readlines()
        return models

    def get_cars_in_page(self, path, i):
        """
            Gets cars in page
            Args:
                path: path to page
                i: page number
            return:
                list of links
        """
        console_logger.info('Scrapping page: %s', i)
        file_logger.info('Scrapping page: %s', i)
        headers = [
            {
                'User-Agent':
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/117.0.0.0 Safari/537.36',
                'Accept':
                    'text/html,application/xhtml+xml,application'
                    '/xml;q=0.9,image/avif,image/webp,image/apng,*/*;'
                    'q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language':
                    'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer':
                    'https://www.google.com/',
            },
            {
                'User-Agent':
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; '
                    'rv:109.0) Gecko/20100101 Firefox/109.0',
                'Accept-Language': 'pl-PL,pl;q=0.9,en-US,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/'
                          'xml;q=0.9,image/avif,image/webp,'
                          'image/apng,*/*;q=0.8',
                'Referer':
                    'https://www.google.com/',
            },
            {
                'User-Agent':
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15;'
                    ' rv:109.0) Gecko/20100101 Firefox/117.0',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'Accept': 'text/html,application/xhtml+xml,'
                          'application/xml;q=0.9,image/avif,'
                          'image/webp,*/*;q=0.8',
                'Referer':
                    'https://www.google.com/',
            }
        ]
        header = random.choice(headers)
        res = httpx.get(f'{path}?page={i}', headers=header)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, features='lxml')
        links = []
        car_links_section = []
        try:
            car_links_section = soup.find(
                'main', attrs={'data-testid': 'search-results'})
            car_links_section = car_links_section.find_all('div')
        except Exception:
            try:
                header = random.choice(headers)
                res = httpx.get(f'{path}?page={i}', headers=header)
                res.raise_for_status()

                soup = BeautifulSoup(res.text, features='lxml')
                car_links_section = soup.find(
                    'div', attrs={'data-testid': 'search-results'})
                car_links_section = car_links_section.find_all(
                    'article',
                    attrs={
                        'data-media-size': True
                    }
                )
            except Exception:
                car_links_section = []
        for x in car_links_section:
            try:
                section = x.find('section')
                link = section.find('a', href=True)['href']
                links.append(link)
            except Exception:
                pass

        console_logger.info('Found %s links', len(links))
        file_logger.info('Found %s links', len(links))
        return links

    def scrap_model(self, model):
        """
            Scraps model
            Args:
                 model: model to scrap
        """
        model = model.strip()
        console_logger.info('Start scrapping model: %s', model)
        file_logger.info('Start scrapping model: %s', model)
        self.ad_fetcher.setup_fetcher()
        path = f'https://www.otomoto.pl/osobowe/{model}'
        try:
            res = requests.get(path)
            headers = {
                'User-Agent':
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/117.0.0.0 Safari/537.36',
                'Accept':
                    'text/html,application/xhtml+xml,application/xml;'
                    'q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
                    'application/signed-exchange;v=b3;q=0.7',
                'Accept-Language':
                    'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.google.com/',
            }
            res = httpx.get(path, headers=headers)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, features='lxml')
            last_page_num = int(soup.find_all(
                'li', attrs={'data-testid': 'pagination-list-item'})[-1].text)
        except Exception:
            last_page_num = 1
        last_page_num = min(last_page_num, 500)

        console_logger.info('Model has: %s subpages', last_page_num)
        file_logger.info('Model has: %s subpages', last_page_num)

        pages = range(1, last_page_num + 1)
        for page in pages:
            links = self.get_cars_in_page(path, page)
            self.ad_fetcher.fetch_ads(links)
            time.sleep(0.2)
        self.ad_fetcher.save_ads(model)

        console_logger.info('End Scrapping model: %s', model)
        file_logger.info('End Scrapping model: %s', model)

    def scrap_all_models(self):
        console_logger.info('Starting scrapping cars...')
        file_logger.info('Starting scrapping cars...')
        for model in self.models:
            try:
                self.scrap_model(model)
            except Exception as e:
                console_logger.error('Error while scrapping model: %s: %s', model, e)
                file_logger.error('Error while scrapping model: %s: %s', model, e)
                pass
        console_logger.info('End scrapping cars')
        file_logger.info('End scrapping cars')

    def combine_data(self):
        console_logger.info('Combining data...')
        file_logger.info('Combining data...')
        csv_filenames = [os.path.join(
            self.data_directory, f'{model.strip()}.csv')
            for model in self.models
        ]
        combined_data = []
        for filename in csv_filenames:
            try:
                combined_data.append(pd.read_csv(
                    filename, index_col=False, low_memory=False))
            except Exception as e:
                console_logger.error('Error while combining data: %s', e)
                file_logger.error('Error while combining data: %s', e)
                pass
        df_all = pd.concat(combined_data, ignore_index=True)
        df_all.to_csv('output/data/car.csv', index=False)
        console_logger.info('Combined data saved to car.csv')
        file_logger.info('Combined data saved to car.csv')
