import pandas as pd

import requests
from bs4 import BeautifulSoup


def download_report(url_report):
    response = requests.get(url_report)
    if response.status_code != 200:
        raise Exception(f'Failed to retrieve the page. Status code: {response.status_code}.')
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        published_string = (
            soup.find('article', class_='m-meta-infos').find('span', string='Published').find_next_sibling('span').text
        )
    except AttributeError:
        published_string = None
    elements_with_event = soup.find_all('a', attrs={'data-track-event': 'ReportsDownload '})
    if len(elements_with_event) == 1:
        url_pdf = elements_with_event[0]['href']
        # Download the PDF file
        response = requests.get(url_pdf)
        if response.status_code != 200:
            raise Exception(f'Failed to retrieve the PDF file. Status code: {response.status_code}.')
        # Save the PDF file
        with open(f'data/docs/pdf/{url_report.split("/")[-1]}.pdf', 'wb') as f:
            f.write(response.content)
        print(f'\tDownloaded {url_report}.')
        return True, published_string
    elif len(elements_with_event):
        print(f'\tFound {len(elements_with_event)} download links for {url_report}.')
        return False, published_string
    else:
        print(f'\tFound no download link for {url_report}.')
        return False, published_string


def download_reports(scrape_all=False):
    try:
        reports = pd.read_csv('data/reports.csv', index_col='url')
    except FileNotFoundError:
        reports = pd.DataFrame(columns=['title', 'date_published', 'downloaded'])
        reports.index.name = 'url'

    page = 1
    while True:
        print(f'Processing page {page}...')
        # Define the URL of the IEA Analysis page
        url = f'https://www.iea.org/analysis?page={page}'

        # Send an HTTP GET request to the URL
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code != 200:
            if response.status_code == 500:
                print(f'Page {page} not found. Stopping the scraping process.')
                break
            raise Exception(f'Failed to retrieve the page. Status code: {response.status_code}.')

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the container that holds the report links
        report_container = soup.find('div', class_='o-layout__main').find('ul', class_='m-card-listing')

        # Find all report links within the container
        report_links = report_container.find_all('a')

        # Extract and print the report titles and URLs
        num_downloaded = reports['downloaded'].sum()
        for link in report_links:
            url = 'https://www.iea.org' + link['href']
            short_href = link['href'].replace('/reports/', '')

            if short_href in reports[reports['downloaded']].index:
                print(f'\tReport {short_href} already downloaded.')
                continue

            downloaded, published_string = download_report(url)
            reports.at[short_href, 'title'] = link.find('h2').text
            reports.at[short_href, 'date_published'] = published_string
            reports.at[short_href, 'downloaded'] = downloaded

        reports.to_csv('data/reports.csv', index_label='url')
        new_downloaded = reports['downloaded'].sum() - num_downloaded
        print(f'Page {page} processed. {new_downloaded} new reports downloaded.')
        if not scrape_all and new_downloaded == 0:
            break

        page += 1


if __name__ == '__main__':
    download_reports(scrape_all=False)
