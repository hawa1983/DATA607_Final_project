from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import csv
import pandas as pd

from selenium.webdriver.support.wait import WebDriverWait


def find_elements_safely_within_book(book, by, value):
    try:
        # Wait for the elements to be present and stable within the book context
        elements = WebDriverWait(book, 10).until(
            EC.presence_of_all_elements_located((by, value))
        )
        return elements
    except StaleElementReferenceException:
        # If the elements become stale, find them again within the book context
        return WebDriverWait(book, 10).until(
            EC.presence_of_all_elements_located((by, value))
        )


def find_element_safely_within_book(book, by, value):
    try:
        # Wait for the element to be present and stable within the book context
        return WebDriverWait(book, 10).until(
            EC.presence_of_element_located((by, value))
        )
    except StaleElementReferenceException:
        # If the element becomes stale, find it again within the book context
        return WebDriverWait(book, 10).until(
            EC.presence_of_element_located((by, value))
        )


class AudibleScraper:
    def __init__(self):
        # Specify the path to ChromeDriver
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option('detach', True)
        path = r'C:\Users\RemoteUser\Downloads\chromedriver-win64\chromedriver.exe'
        self.driver = webdriver.Chrome(options=chrome_options)
        self.url = "https://www.audible.com/search"

        # list to store basic book data
        self.data = []
        # list to store detailed book data including reviews
        self.detailed_data = []
        self.book_urls = []

    def scrape(self):
        self.driver.get(self.url)
        time.sleep(2)  # Wait for the page to load

        while True:
            books = self.driver.find_elements(By.CLASS_NAME, 'productListItem')
            for book in books:
                # Use CSS selectors or class names where possible
                try:
                    title_element = book.find_element(By.CSS_SELECTOR, 'h3.bc-heading a')
                    title = title_element.text if title_element else None
                except Exception as e:
                    print(f"An error occurred: {e}")

                try:
                    title_link_element = book.find_element(By.CSS_SELECTOR, 'h3.bc-heading a')
                    title_link = title_link_element.get_attribute('href') if title_link_element else None
                    self.book_urls.append(title_link)
                except Exception as e:
                    print(f"An error occurred: {e}")

                # Initialize default values
                try:
                    subtitle_element = book.find_element(By.CSS_SELECTOR, 'li.subtitle span')
                    subtitle = subtitle_element.text if subtitle_element else None
                except Exception as e:
                    print(f"Error occurred while fetching subtitle for book: {e}")

                # try:
                #     authors_elements = book.find_elements(By.CSS_SELECTOR, 'li.authorLabel span a')
                #     authors = [author.text for author in narrators_elements] if authors_elements else None
                # except Exception as e:
                #     print(f"An error occurred: {e}")

                try:
                    narrators_elements = book.find_elements(By.CSS_SELECTOR,
                                                                          'li.narratorLabel span a')
                    narrators = [narrator.text for narrator in narrators_elements] if narrators_elements else None
                except Exception as e:
                    print(f"An error occurred: {e}")

                try:
                    series_element = book.find_element(By.CSS_SELECTOR, 'li.seriesLabel span a')
                    series = series_element.text if series_element else None
                except NoSuchElementException:
                    regular_price = None  # Or handle as needed

                try:
                    length_element = book.find_element(By.CSS_SELECTOR, 'li.runtimeLabel span')
                    length = length_element.text if length_element else None
                except Exception as e:
                    print(f"An error occurred: {e}")

                try:
                    release_date_element = book.find_element(By.CSS_SELECTOR,
                                                                           'li.releaseDateLabel span')
                    release_date = release_date_element.text if release_date_element else None
                except Exception as e:
                    print(f"An error occurred: {e}")

                try:
                    language_element = book.find_element(By.CSS_SELECTOR, 'li.languageLabel span')
                    language = language_element.text if language_element else None
                except Exception as e:
                    print(f"An error occurred: {e}")

                try:
                    rating_element = book.find_element(By.CSS_SELECTOR,
                                                                     'li.ratingsLabel .bc-pub-offscreen')
                    rating = rating_element.text if rating_element else None
                except Exception as e:
                    print(f"An error occurred: {e}")

                try:
                    no_of_ratings_element = book.find_element(By.CSS_SELECTOR,
                                                                            'li.ratingsLabel .bc-size-small')
                    no_of_ratings = no_of_ratings_element.text if no_of_ratings_element else None
                except Exception as e:
                    print("An error occurred: {e}")

                try:
                    regular_price_element = book.find_element(By.CSS_SELECTOR,
                                                                            'p.buybox-regular-price span:nth-child(2)')
                    regular_price = regular_price_element.text if regular_price_element else None

                except NoSuchElementException:
                    regular_price = None  # Or handle as needed

                try:
                    sales_price_element = book.find_element(By.CSS_SELECTOR,
                                                                          'p.buybox-member-price span:nth-child(2)')
                    sales_price = sales_price_element.text if sales_price_element else None
                except NoSuchElementException:
                    regular_price = None  # Or handle as needed

                self.data.append({
                    'title': title,
                    'subtitle': subtitle,
                    # 'authors': authors,
                    'narrators': narrators,
                    # 'series': series,
                    'length': length,
                    'release_date': release_date,
                    'language': language,
                    'rating': rating,
                    'no_of_ratings': no_of_ratings,
                    'regular_price': regular_price,
                    'sales_price': sales_price,
                    'url': title_link
                })
                print(self.data)
            try:
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'nextButton'))
                )

                # Check if the next button is enabled (not disabled on the last page)
                if next_button.is_enabled():
                    next_button.click()
                    time.sleep(3)  # Wait for the next page to load
                else:
                    print("Reached the last page.")
                    break
            except TimeoutException:
                print("Next button not found within the given time frame.")
                break
            except NoSuchElementException:
                print("Next button not found on the page.")
                break

            # After collecting all data, save it in separate files
            # self.save_data(self.detailed_data, 'detailed_audible_data')

        # DataFrame to store data
        book_data = []

        # # Iterate through book detail pages
        # for book_url in self.book_urls:
        #     self.driver.get(book_url)
        #
        #     # Scrape reviews
        #     # Click the Amazon reviews button
        #     try:
        #         amazon_button = self.driver.find_element(By.CLASS_NAME, 'globalReviewsTabs')
        #         amazon_button.click()
        #         time.sleep(2)
        #     except Exception as e:
        #         print("There are no Amazon reviews:", e)
        #         break
        #
        #     reviews_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.reviewText span')
        #     reviews = "|".join([review.text for review in reviews_elements])
        #
        #     # Update book_data with additional details
        #     print(reviews)
        #     book_data['reviews'] = reviews
        #     self.detailed_data.append(book_data)

        #     # Store data
        #     for review, reviewer in zip(reviews, reviewers):
        #         details_data.append({"URL": book_url, "Reviewer": reviewer, "Review": review})
        #
        # # Convert to DataFrame
        # df = pd.DataFrame(details_data)
        #
        # # Save to CSV and JSON
        # df.to_csv('audible_reviews.csv', index=False)
        # df.to_json('audible_reviews.json', orient='records')

        def handle_pagination(self):
            try:
                # Replace with the correct CSS selector for the 'Next' button
                next_button_selector = 'ul.pagingElements > li > a.nextButton'

                # Wait until the next button is clickable or timeout after 10 seconds
                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, next_button_selector))
                )

                next_button = self.driver.find_element(By.CSS_SELECTOR, next_button_selector)

                if next_button:
                    next_button.click()
                    time.sleep(3)  # Wait for the next page to load
                    self.parse_main_page()  # Parse the next page
            except (NoSuchElementException, TimeoutException):
                print("Reached the last page or the 'Next' button is not available.")

        self.driver.quit()

    def save_data(self):
        # Save data to a CSV file
        keys = self.data[0].keys()
        with open('audible_data.csv', 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.data)

        # Save data to a JSON file
        with open('audible_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

        # # Save data to a CSV file
        # keys = self.detailed_data[0].keys()
        # with open('audible_view.csv', 'w', newline='', encoding='utf-8') as output_file:
        #     dict_writer = csv.DictWriter(output_file, keys)
        #     dict_writer.writeheader()
        #     dict_writer.writerows(self.detailed_data)
        #
        # # Save data to a JSON file
        # with open(f'audible_view.json', 'w', encoding='utf-8') as f:
        #     json.dump(self.detailed_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    scraper = AudibleScraper()
    scraper.scrape()
    scraper.save_data()
