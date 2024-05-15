import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def save_to_json(filename, new_data):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(new_data, file, ensure_ascii=False, indent=1)


class Scraper:
    def __init__(self):
        self.URL = 'https://quotes.toscrape.com/page/'
        self.page_number = 1
        self.authors_set = set()

    async def authors_scrape(self, link, session):
        url_base = 'http://quotes.toscrape.com'
        full_url = url_base + link
        print(f'Fetching    {full_url}')

        async with session.get(full_url) as response:
            response.raise_for_status()
            html = await response.text()

        soup = BeautifulSoup(html, 'lxml')
        full_name = soup.find('h3', class_='author-title').text
        born_date = soup.find('span', class_='author-born-date').text
        born_location = soup.find('span', class_='author-born-location').text
        description = soup.find('div', class_='author-description').text.strip()

        author_data = {
            'fullname': full_name,
            'born_date': born_date,
            'born_location': born_location,
            'description': description
        }
        return author_data

    async def quotes_scrape(self, session):
        data = []
        full_url = self.URL + str(self.page_number)
        print(f'Fetching    {full_url}')

        async with session.get(full_url) as response:
            response.raise_for_status()
            html = await response.text()

        soup = BeautifulSoup(html, 'lxml')
        quotes = soup.find_all('span', class_='text')
        authors = soup.find_all('small', class_='author')
        tags = soup.find_all('div', class_='tags')
        authors_urls = soup.find_all('a', string='(about)', href=True)
        [self.authors_set.add(a_url['href']) for a_url in authors_urls]

        for i in range(len(quotes)):
            quote = quotes[i].text
            author = authors[i].text
            tags_for_quote = tags[i].find_all('a', class_='tag')
            tags_list = [tag_f.text for tag_f in tags_for_quote]

            quote_data = {
                'tags': tags_list,
                'author': author,
                'quote': quote
            }
            data.append(quote_data)

        next_page = soup.find('li', class_='next')
        if next_page:
            self.page_number += 1
            data += await self.quotes_scrape(session)

        return data


async def main():
    scraper = Scraper()
    async with aiohttp.ClientSession() as session:
        print('Quotes scraping:')
        quotes_task = asyncio.create_task(scraper.quotes_scrape(session))
        quotes_data = await quotes_task
        await save_to_json('quotes.json', quotes_data)

        print('Authors scraping:')
        authors_tasks = [scraper.authors_scrape(link, session) for link in scraper.authors_set]
        authors_data = await asyncio.gather(*authors_tasks)
        await save_to_json('authors.json', authors_data)

if __name__ == "__main__":
    asyncio.run(main())