import scrapy
import pandas as pd
from scrapy import signals
from scrapy.signalmanager import dispatcher
import sqlite3

class AudibleSpider(scrapy.Spider):
    name = "audible"
    allowed_domains = ["www.audible.com"]

    start_urls = ["https://www.audible.com/search"]

    custom_settings = {
        'FEEDS': {
            'audible.csv': {
                'format': 'csv',
                'overwrite': True
            },
            'audible.json': {
                'format': 'json',
                'overwrite': True,
                'indent': 4
            },
        }
    }

    # Initialize a list to store the review data
    def __init__(self):
        self.reviews_data = []
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46'
                }
            )

    def parse(self, response):
        books = response.xpath(
            '(//div[@class="adbl-impression-container "])/div//li[contains(@class,"productListItem")]')
        for book in books:
            title = book.xpath('.//h3[contains(@class, "bc-heading")]/a/text()').get()
            title_link = book.xpath('.//h3[contains(@class, "bc-heading")]/a/@href').get()
            subtitle = book.xpath('.//li[contains(@class, "subtitle")]/span/text()').get()
            authors = book.xpath('.//li[contains(@class, "authorLabel")]/span/a/text()').getall()
            narrators = book.xpath('.//li[contains(@class, "narratorLabel")]/span/a/text()').getall()
            series = book.xpath('.//li[contains(@class, "seriesLabel")]/span/a/text()').get()
            length = book.xpath('.//li[contains(@class, "runtimeLabel")]/span/text()').get()
            release_date = book.xpath('.//li[contains(@class, "releaseDateLabel")]/span/text()').get()
            language = book.xpath('.//li[contains(@class, "languageLabel")]/span/text()').get()
            rating = book.xpath(
                './/li[contains(@class, "ratingsLabel")]/span[contains(@class, "bc-pub-offscreen")]/text()').get()
            no_of_ratings = book.xpath(
                './/li[contains(@class, "ratingsLabel")]/span[contains(@class, "bc-size-small")]/text()').get()
            regular_price = book.xpath('.//p[contains(@id, "buybox-regular-price")]/span[2]/text()').get()
            sales_price = book.xpath('.//p[contains(@id, "buybox-member-price")]/span[2]/text()').get()

            if length:
                length = length.split(':')[1].strip()
            if release_date:
                release_date = release_date.split('\n')[1].strip()
            if language:
                language = language.split('\n')[1].strip()
            if regular_price:
                regular_price = regular_price.split('\n')[1].strip()

            item = {
                'title': title,
                'subtitle': subtitle,
                'authors': authors,
                'narrators': narrators,
                'series': series,
                'length': length,
                'release_date': release_date,
                'language': language,
                'rating': rating,
                'no_of_ratings': no_of_ratings,
                'regular_price': regular_price,
                'sales_price': sales_price,
                'title_link': title_link
            }

            # To handle genres, yield a request to the book detail page if a title link is available
            if title_link:
                yield response.follow(
                    url=title_link,
                    callback=self.parse_title,
                    meta={'item': item}  # Pass the current book item
                )
            else:
                yield item  # If there's no title link, yield the item as it is

        pagination = response.xpath('//ul[contains(@class, "pagingElements")]')
        next_button = pagination.xpath(
            './/span[contains(@class, "nextButton") and not(contains(@class, "bc-button-disabled"))]/a/@href')

        next_page_url = next_button.get()

        if next_page_url:
            yield response.follow(
                next_page_url,
                callback=self.parse,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46'
                }
            )
        else:
            self.logger.info("Reached the last page or no 'Next' button found. Stopping the spider.")

    def parse_title(self, response):
        reviews_data = []
        # Extract genres as before
        genres = response.xpath('//div[contains(@class, "bc-expander")]//span[@class="bc-chip-text"]/text()').getall()
        categories = response.xpath('//li[contains(@class, "categoriesLabel")]/a/text()').getall()
        reviews_tabs = response.xpath('//div[contains(@class, "bc-tab-set")]')

        # Function to add reviews to the list if they exist
        def add_reviews(review_list):
            if review_list:  # Checks if the review list is not empty
                reviews_data.extend([review.strip() for review in review_list])

        # US reviews
        usreviews = response.xpath(
            '//div[contains(@class, "USreviews")]/h3[contains(@class, "bc-heading")]/following-sibling::p[contains(@class, "bc-size-body")]/text()').getall()
        add_reviews(usreviews)

        # UK reviews
        ukreviews = response.xpath(
            '//div[contains(@class, "UKreviews")]/h3[contains(@class, "bc-heading")]/following-sibling::p[contains(@class, "bc-size-body")]/text()').getall()
        add_reviews(ukreviews)

        # AU reviews
        aureviews = response.xpath(
            '//div[contains(@class, "AUreviews")]/h3[contains(@class, "bc-heading")]/following-sibling::p[contains(@class, "bc-size-body")]/text()').getall()
        add_reviews(aureviews)

        # Amazon reviews
        amazonreviews = response.xpath(
            '//div[contains(@class, "review-text-content")]/span/text()').getall()
        add_reviews(amazonreviews)

        # If there are no reviews at all, you might want to add a placeholder or leave as an empty list
        if not reviews_data:
            reviews_data = ["no reviews"]  # Placeholder for no reviews

        item = response.meta['item']
        item['genres'] = [genre.strip() for genre in genres]  # Clean the genres
        item['categories'] = [category.strip() for category in categories]  # Clean the categories
        item['reviews'] = reviews_data  # Add the cleaned and consolidated reviews

        # Extract the Amazon URL from the book details page
        amazon_url = response.xpath('//a[@data-hook="see-all-reviews-link-foot"]/@href').get()

        # Check if an Amazon URL was found
        if amazon_url:
            # If found, follow the Amazon URL to scrape reviews
            print(amazon_url)
            yield response.follow(
                url=amazon_url,
                callback=self.parse_amazon_reviews,
                meta={'item': item},  # Pass along the existing item
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46'
                }
            )
        else:
            # If there's no Amazon URL, yield the item with the details scraped so far
            yield item

    def parse_amazon_reviews(self, response):
        # Retrieve the item passed via meta
        item = response.meta['item']

        # Scrape the review texts
        reviews = response.xpath(
            '//div[contains(@class, "review-data")]/span[contains(@class, "review-text-content")]/span')
        for review in reviews:
            review_text = review.xpath('.//text()').get().strip()
            print(f"Scraped review: {review_text}")  # Debugging line
            review_item = {
                'title_link': item['title_link'],
                'review_text': review_text
            }
            self.reviews_data.append(review_item)
            yield review_item

            # Check for a 'Next' page link and follow if found
            next_page_link = response.xpath('//ul[@class="a-pagination"]/li[@class="a-last"]/a/@href')
            if next_page_link:
                next_page_url = next_page_link.get()
                yield response.follow(
                    url=next_page_url,
                    callback=self.parse_amazon_reviews,
                    meta={'item': response.meta['item']},  # Pass along the meta information
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46'
                    }
                )

    # Method to be called when the spider is closed
    def spider_closed(self, spider):
        # Convert the list of reviews to a DataFrame
        reviews_df = pd.DataFrame(self.reviews_data)

        # Save to CSV
        reviews_df.to_csv('amazon_reviews.csv', index=False)

        # Save to JSON
        reviews_df.to_json('amazon_reviews.json', orient='records', lines=True, indent=4)
