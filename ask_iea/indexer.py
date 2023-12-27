"""TODO DOCSTRING."""
import itertools

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from .utils.logger import Logger

# Define a logger
log = Logger(__name__)


class ReportIndexer:

    """TODO DOCSTRING."""

    def __init__(self, path_df: str = None) -> None:
        """TODO DOCSTRING."""
        if path_df is None:
            self.df = pd.DataFrame(columns=['url_report', 'title', 'abstract', 'date_published', 'url_pdf'])
            self.df.index.name = 'report_id'
        else:
            self.df = pd.read_csv(path_df, index_col='report_id')

    @staticmethod
    def scrape_report_information(url_report: str) -> dict:
        """TODO DOCSTRING."""
        response = requests.get(url_report)
        if response.status_code != 200:
            msg = f'Failed to load page. Status code: {response.status_code}. URL: {url_report}.'
            raise Exception(msg)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Title
        title = soup.find('h1').text
        # Abstract
        try:
            abstract = soup.find('div', class_='m-report-abstract').text
            abstract = abstract.replace('\n', ' ').strip()
        except AttributeError:
            abstract = None
        # Date published
        try:
            published_string = (
                soup.find('article', class_='m-meta-infos')
                .find('span', string='Published')
                .find_next_sibling('span')
                .text
            )
            date_published = pd.to_datetime(published_string).strftime('%Y-%m-%d')
        except AttributeError:
            date_published = None
        # URL to PDF file
        elements_with_event = soup.find_all('a', attrs={'data-track-event': 'ReportsDownload '})
        if len(elements_with_event) == 1:
            url_pdf = elements_with_event[0]['href']
        elif len(elements_with_event):
            msg = f'Found multiple download links. URL: {url_report}.'
            raise Exception(msg)
        else:
            url_pdf = None
        if url_pdf in ['#']:
            url_pdf = None

        return {
            'url_report': url_report,
            'title': title,
            'abstract': abstract,
            'date_published': date_published,
            'url_pdf': url_pdf,
        }

    def index_generator(
        self, already_scraped_urls: list = None, pages: [int] = None, break_after_n_pages: int = 1
    ) -> dict:
        """TODO DOCSTRING."""
        if already_scraped_urls is None:
            already_scraped_urls = []

        if not pages:
            pages = np.arange(1, 1000)

        num_known_pages = 0

        for page in pages:
            log.info(f'Indexing page {page}...')
            # Define the URL of the IEA Analysis page
            url = f'https://www.iea.org/analysis?page={page}'

            # Send an HTTP GET request to the URL
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code != 200:
                if response.status_code == 500:
                    log.info(f'Page {page} not found. Stop scraping process.')
                    break
                msg = f'Failed to retrieve the page. Status code: {response.status_code}.'
                raise Exception(msg)

            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the container that holds the report links
            report_container = soup.find('div', class_='o-layout__main').find('ul', class_='m-card-listing')
            # Find all report links within the container
            report_links = report_container.find_all('a')
            report_links = ['https://www.iea.org' + link['href'] for link in report_links]
            # Extract and print the report titles and URLs
            new_reports = [url_path for url_path in report_links if url_path not in already_scraped_urls]

            if len(new_reports) == 0:
                num_known_pages += 1
                log.info(f'\tNo new reports found on page {page}.')

            # Break if no new reports have been found on the page
            if num_known_pages == break_after_n_pages:
                break

            for url in new_reports:
                try:
                    report_data = self.scrape_report_information(url)
                except Exception as e:
                    raise e
                msg = f'\tIndexed new report: {url}.'
                if not report_data['url_pdf']:
                    msg += ' (No PDF found)'
                log.info(msg)

                yield report_data

    def add_new_reports(self, n_newest: int = 10, pages: [int] = None, break_after_n_pages: int = 1) -> None:
        """TODO DOCSTRING."""
        index_generator = self.index_generator(
            already_scraped_urls=self.df['url_report'].tolist(), pages=pages, break_after_n_pages=break_after_n_pages
        )
        if n_newest:
            index_generator = itertools.islice(index_generator, n_newest)

        for report in index_generator:
            report_id = report['url_report'].split('/')[-1]
            self.df.loc[report_id] = report

    def save_to_file(self, filename: str) -> None:
        """TODO DOCSTRING."""
        self.df.to_csv(filename, index_label='report_id')
