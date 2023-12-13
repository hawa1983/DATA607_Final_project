from pip._internal.utils import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, \
    ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import csv
import pandas as pd
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging

# Create an empty DataFrame to store the scraped data
reviews_data_df = pd.DataFrame()


# Function to save data to a CSV file
def save_to_file(data_frame, file_path):
    data_frame.to_csv(file_path, index=False)


def extract_book_info(book):
    book_data = {}
    try:
        book_data['title'] = book.find_element(By.CSS_SELECTOR, 'h3.bc-heading a').text
    except NoSuchElementException:
        book_data['title'] = None

    try:
        book_data['subtitle'] = book.find_element(By.CSS_SELECTOR, 'li.subtitle span').text
    except NoSuchElementException:
        book_data['subtitle'] = None

    try:
        book_data['authors'] = [author.text for author in
                                book.find_elements(By.CSS_SELECTOR, 'li.authorLabel span a')]
    except NoSuchElementException:
        book_data['authors'] = []

    try:
        book_data['narrators'] = [narrator.text for narrator in
                                  book.find_elements(By.CSS_SELECTOR, 'li.narratorLabel span a')]
    except NoSuchElementException:
        book_data['narrators'] = []

    try:
        book_data['series'] = book.find_element(By.CSS_SELECTOR, 'li.seriesLabel span a').text
    except NoSuchElementException:
        book_data['series'] = None

    try:
        book_data['length'] = book.find_element(By.CSS_SELECTOR, 'li.runtimeLabel span').text
    except NoSuchElementException:
        book_data['length'] = None

    try:
        book_data['release_date'] = book.find_element(By.CSS_SELECTOR, 'li.releaseDateLabel span').text
    except NoSuchElementException:
        book_data['release_date'] = None

    try:
        book_data['language'] = book.find_element(By.CSS_SELECTOR, 'li.languageLabel span').text
    except NoSuchElementException:
        book_data['language'] = None

    try:
        book_data['rating'] = book.find_element(By.CSS_SELECTOR, 'li.ratingsLabel .bc-pub-offscreen').text
    except NoSuchElementException:
        book_data['rating'] = None

    try:
        book_data['no_of_ratings'] = book.find_element(By.CSS_SELECTOR, 'li.ratingsLabel .bc-size-small').text
    except NoSuchElementException:
        book_data['no_of_ratings'] = None

    try:
        book_data['regular_price'] = book.find_element(By.CSS_SELECTOR,
                                                       'p.buybox-regular-price span:nth-child(2)').text
    except NoSuchElementException:
        book_data['regular_price'] = None

    try:
        book_data['sales_price'] = book.find_element(By.CSS_SELECTOR,
                                                     'p.buybox-member-price span:nth-child(2)').text
    except NoSuchElementException:
        book_data['sales_price'] = None

    try:
        book_data['category'] = book.find_element(By.CSS_SELECTOR, 'li.categoriesLabel a').text
    except NoSuchElementException:
        book_data['category'] = None

    try:
        genre_elements = book.find_elements(By.CSS_SELECTOR, 'div.bc-section span.bc-chip-text')
        book_data['genres'] = [genre.text for genre in genre_elements]
    except NoSuchElementException:
        book_data['genres'] = []

    try:
        book_data['url'] = book.find_element(By.CSS_SELECTOR, 'h3.bc-heading a').get_attribute('href')
    except NoSuchElementException:
        book_data['url'] = None

    return book_data


def extract_review_info(review_elements, reviewer_id_elements):
    review_data = []
    for review_element, reviewer_id_element in zip(review_elements, reviewer_id_elements):
        review_data.append({
            'reviewer_id': reviewer_id_element.text,
            'review': review_element.text
        })
    return review_data


def save_data(data, csv_filename, json_filename):
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    # Save data to CSV
    df.to_csv(csv_filename, index=False)
    # Save data to JSON
    df.to_json(json_filename, orient='records', lines=True)


class AudibleScraper:
    def __init__(self):
        # Add this line to log chromedriver version
        chrome_options = Options()
        # chrome_options.add_experimental_option('detach', True)

        # Specify the path to the ChromeDriver executable
        chrome_driver_path = r'C:\Users\RemoteUser\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe'

        # Initialize Chrome WebDriver with the specified service
        chrome_service = ChromeService(executable_path=chrome_driver_path)

        # Add this line to log chromedriver version
        desired_capabilities = DesiredCapabilities.CHROME.copy()
        desired_capabilities['loggingPrefs'] = {'browser': 'ALL'}

        self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

        # Maximize the browser window
        self.driver.maximize_window()

        self.url = "https://www.audible.com/search?feature_six_browse-bin=18685580011&feature_twelve_browse-bin=18685552011&pageSize=50&sort=review-rank&ref_pageloadid=lLpatCZ3I2jVcbaV&ref=a_search_l1_feature_twelve_browse-bin_0&pf_rd_p=daf0f1c8-2865-4989-87fb-15115ba5a6d2&pf_rd_r=EZ1D5488G5TQE1V4G8BF&pageLoadId=lKeM4jw2D71tFz7T&ref_plink=not_applicable&creativeId=9648f6bf-4f29-4fb4-9489-33163c0bb63e"
        self.data = []

    def wait_for_element(self, by, value, timeout=10):
        try:
            element_present = EC.presence_of_element_located((by, value))
            WebDriverWait(self.driver, timeout).until(element_present)
        except TimeoutException:
            print(f"Timed out waiting for page to load element {value}")

    def scrape_reviews(self, book_url):
        self.driver.get(book_url)
        print(book_url)
        # First, extract the book information including the category
        book_info = extract_book_info(self.driver)

        def wait_for_overlay_disappearance():
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element((By.CSS_SELECTOR, "div.att_lightbox_background"))
                )
            except TimeoutException:
                print('Overlay did not disappear within the timeout')
                pass

        # def close_overlay_if_present():
        #     try:
        #         close_button = self.driver.find_element(By.CSS_SELECTOR, "span#att_lightbox_close_x")
        #         close_button.click()
        #         wait_for_overlay_disappearance()
        #     except NoSuchElementException:
        #         # No close button, overlay not present
        #         pass
        #
        # def click_with_retry(self, element, retries=3):
        #     attempt = 0
        #     while attempt < retries:
        #         try:
        #             # Scroll the element into view before attempting to click
        #             self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
        #                                        element)
        #             time.sleep(1)  # Add a short delay to ensure the page has settled
        #             WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(element))
        #             element.click()
        #             return  # Click successful, exit the function
        #         except ElementClickInterceptedException:
        #             self.close_overlay_if_present()
        #             attempt += 1
        #         except ElementNotInteractableException:
        #             time.sleep(1)
        #             attempt += 1
        #         if attempt == retries:
        #             raise Exception(f"Failed to click element after {retries} attempts.")

        # Initial wait for the overlay to disappear
        wait_for_overlay_disappearance()

        reviews_data = []

        # Find all review tabs and iterate over them if they exist
        review_tabs = self.driver.find_elements(By.XPATH,
                                                '//div[contains(@class, "bc-tab-set")]/a[contains(@class, "bc-tab-heading")]')
        if not review_tabs:
            print("No review tabs available on this page.")
            return pd.DataFrame(reviews_data)

        for tab in review_tabs:
            try:
                # Extract the label of the reviews tab
                tab_label = tab.text.strip()

                logging.info(f"Reviews Tab: {tab_label}")

                # Scroll back to the reviews tab before clicking it
                self.driver.execute_script("arguments[0].scrollIntoView(true);", tab)
                time.sleep(5)  # Allow time for the page to settle after scrolling

                # Now use click_with_retry to handle the click
                self.click_with_retry(tab)

                if not tab_label == "Amazon reviews":
                    self.expand_reviews_on_current_page()
                else:
                    self.expand_reviews_to_amazon_page()

                # After clicking the tab, call scrape_reviews_on_current_page
                self.scrape_reviews_on_current_page(reviews_data, book_info['category'], book_info['genres'])

                while self.go_to_next_reviews_page():
                    # After each pagination, call scrape_reviews_on_current_page
                    self.scrape_reviews_on_current_page(reviews_data, book_info['category'], book_info['genres'])
            except TimeoutException:
                logging.error("Timeout occurred while waiting for a review tab to become clickable.")
            except Exception as e:
                logging.error(f"Failed to click on a review tab due to an exception: {e}")

            # # Save the final data to a file after processing all tabs
            # print(reviews_data)
            # reviews_data_df = pd.DataFrame(reviews_data)
            # save_to_file(reviews_data_df, "scraped_reviews.csv")
            #
            # # Save and print the tab's label
            # print(f"Reviews Tab: {tab_label}")

        return pd.DataFrame(reviews_data)

    # //div[contains(@class, 'USreviews')]
    # //div[contains(@class, 'AUreviews')]
    def scrape_reviews_on_current_page(self, reviews_data, book_category, book_genres):
        try:
            # Wait for the reviews to load on this page
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.reviewText span'))
            )

            # Log a message indicating that reviews are present
            logging.info("Reviews are present on this page.")

            # Log the HTML content to inspect the structure
            logging.debug("HTML Content:")
            logging.debug(self.driver.page_source)

            review_elements = self.driver.find_elements(By.XPATH, '//div[contains(@class, "USreviews")]/h3[contains(@class, "bc-heading")]/following-sibling::p[contains(@class, "bc-size-body")]')
            for review_element in review_elements:
                reviews_data.append({
                    'review': review_element.text,
                    'category': book_category,  # Add the category to each review's data
                    'genres': ', '.join(book_genres)  # Convert list of genres to a string
                })
                # Print each review
                # print(
                # f"Review: {review_element.text}, Reviewer: {reviewer_id_element.text}, Category: {book_category}, Genres: {', '.join(book_genres)}")

            print("End of Reviews on Current Page")
        except Exception as e:
            # Log the exception information for debugging
            logging.error(f"An exception occurred: {e}")

    def go_to_next_reviews_page(self):
        try:
            # Locate the pagination button
            next_button = self.driver.find_element(By.CSS_SELECTOR, 'ul.a-pagination li.a-last a')
            if next_button and next_button.is_displayed():
                # Scroll the pagination button into the center of the view before clicking
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                           next_button)
                time.sleep(2)  # Wait for the scrolling to complete and the page to settle
                next_button.click()
                # Wait for the next page of reviews to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.reviewText span'))
                )
                return True
        except NoSuchElementException:
            # Log a message indicating no more pages
            logging.info("No more pages of reviews.")
            return False
        except ElementClickInterceptedException:
            # Log a message indicating the click is intercepted
            logging.warning("Click intercepted by another element.")
            self.close_overlay_if_present()
            return False
        except TimeoutException:
            # Log a message indicating a timeout
            logging.error("Timed out waiting for next page of reviews to load.")
            return False

    def expand_reviews_on_current_page(self):
        while True:
            try:
                # Wait for the "Show More Reviews" button to be clickable
                show_more_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Show More Reviews']"))
                )
                # Scroll to the "Show More Reviews" button and click it
                self.driver.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
                show_more_button.click()

                # Wait for the button to become invisible after clicking, indicating it has processed
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element(show_more_button)
                )

                # Short delay to allow any page updates to occur
                time.sleep(2)

            except TimeoutException:
                # If the button doesn't become invisible within the timeout, assume no more reviews and break the loop
                break
            except NoSuchElementException:
                # If the button isn't found at all, also assume no more reviews and break the loop
                break

        return False

    def expand_reviews_to_amazon_page(self):
        try:
            # Wait for the container that should contain the 'See all reviews' link to load
            container = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "adbl-amzn-portlet-reviews-in-iframe"))
            )

            # If the container is actually an iframe, you would need to switch to it:
            # self.driver.switch_to.frame("adbl-amzn-portlet-reviews-in-iframe")

            # Scroll within the container to the bottom
            self.driver.execute_script(
                "var container = arguments[0];"
                "container.scrollTop = container.scrollHeight;",
                container
            )

            # Wait for the 'See all reviews' link to become visible after scrolling
            see_all_reviews_link = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, "//a[contains(text(), 'See all reviews')]"))
            )

            # Click the 'See all reviews' link
            see_all_reviews_link.click()

            # Wait for some condition that indicates the next action can be taken
            # For example, wait for navigation to complete
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )

        except TimeoutException:
            print("Timed out waiting for the reviews container or 'See all reviews' link.")
            self.driver.save_screenshot('debug_timeout.png')
            return False
        except NoSuchElementException:
            print("Could not find the reviews container or 'See all reviews' link.")
            self.driver.save_screenshot('debug_no_element.png')
            return False

        # If the container is an iframe, switch back to the main document
        # self.driver.switch_to.default_content()

        return True

    # ...

    # ...
    def close_overlay_if_present(self):
        try:
            close_button = self.driver.find_element(By.CSS_SELECTOR, "span#att_lightbox_close_x")
            close_button.click()
            # Wait until the overlay is gone before proceeding
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element((By.CSS_SELECTOR, "div.att_lightbox_background"))
            )
        except NoSuchElementException:
            # If the close button doesn't exist, ignore it
            pass
        except TimeoutException:
            # If the overlay didn't disappear in time, handle the timeout
            print("The overlay did not disappear in time.")

    #
    # def click_with_retry(element, retries=3):
    #     attempt = 0
    #     while attempt < retries:
    #         try:
    #             element.click()
    #             return  # Click successful, exit the function
    #         except ElementClickInterceptedException:
    #             close_overlay_if_present()
    #             attempt += 1
    #             if attempt == retries:
    #                 raise  # Re-raise the exception if max retries reached

    def click_with_retry(self, element, retries=3):
        attempt = 0
        while attempt < retries:
            try:
                # Scroll the element into view before attempting to click
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                           element)
                time.sleep(5)  # Add a short delay to ensure the page has settled
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(element))
                element.click()
                return  # Click successful, exit the function
            except ElementClickInterceptedException:
                self.close_overlay_if_present()
                attempt += 1
            except ElementNotInteractableException:
                time.sleep(1)
                attempt += 1
            if attempt == retries:
                raise Exception(f"Failed to click element after {retries} attempts.")

    def go_to_next_page(self):
        try:
            # Updated to use the new method
            next_button = self.driver.find_element(By.XPATH,
                                                   "//span[contains(@class, 'nextButton') and not(contains(@class, 'bc-button-disabled'))]/a")

            next_page_url = next_button.get_attribute('href')
            if next_page_url:
                self.driver.get(next_page_url)
                # Scroll to the bottom of the page to ensure all lazy-loaded elements are loaded
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Wait a bit for the page to load after scrolling
                time.sleep(5)
                return True
            else:
                print("Reached the last page or no 'Next' button found. Stopping the spider.")
                return False
        except NoSuchElementException:
            print("Reached the last page or no 'Next' button found. Stopping the spider.")
            return False

    def scrape(self):

        self.driver.get(self.url)

        # Create a DataFrame to store all book data
        all_book_data = []
        all_reviews_data = []

        while True:
            books = self.driver.find_elements(By.CLASS_NAME, 'productListItem')
            for book in books:
                book_data = extract_book_info(book)
                print(book_data)
                all_book_data.append(book_data)
            if not self.go_to_next_page():
                break

        # Save the book and review data
        save_data(all_book_data, 'audible_books.csv', 'audible_books.json')

        # Scrape reviews for each book
        for book_data in all_book_data:
            if book_data['url']:
                # print(book_data['url'])
                book_reviews_df = self.scrape_reviews(book_data['url'])
                # print(book_reviews_df)
                all_reviews_data.append(book_reviews_df)
                # print(all_reviews_data)
        save_data(all_reviews_data, 'audible_reviews.csv', 'audible_reviews.json')

        # Close the driver
        self.driver.quit()


if __name__ == "__main__":
    scraper = AudibleScraper()
    scraper.scrape()
    # scraper.save_data()
