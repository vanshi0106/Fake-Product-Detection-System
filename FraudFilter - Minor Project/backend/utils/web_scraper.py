import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from urllib.parse import urlparse

# Ensure 'scraped_files' folder exists
SCRAPED_FILES_FOLDER = "scraped_files"
os.makedirs(SCRAPED_FILES_FOLDER, exist_ok=True)

def extract_product_info(url):
    """Extracts product ID and product name from the URL."""
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')

    prod_id = path_parts[-1] if len(path_parts) > 1 else "UnknownID"
    prod_name = path_parts[-3].replace("-", " ").upper() if len(path_parts) > 2 else "Unknown Product"

    return prod_id, prod_name


def scrape_reviews(url, max_pages=1):
    """
    Scrapes reviews & ratings from product URL.
    Always returns a DataFrame (never string).
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        driver.get(url)
        time.sleep(5)

        reviews, ratings = [], []
        prod_id, prod_name = extract_product_info(url)
        page_count = 0

        while page_count < max_pages:
            page_count += 1

            # Scrape ratings
            rating_elements = driver.find_elements(By.CSS_SELECTOR, "div.MKiFS6.ojKpP6") #change this html tags according to you target rating.
            for rating in rating_elements:
                txt = rating.text.strip()
                if txt.replace(".", "", 1).isdigit():  # allow floats
                    ratings.append(float(txt))

            # Scrape reviews
            review_elements = driver.find_elements(By.CSS_SELECTOR, "p.qW2QI1")   #change this html tags according to you target review
            reviews.extend([r.text.strip() for r in review_elements])

            # Click next page
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "a._9QVEpD")
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(5)
            except:
                break

        # If no reviews, return empty DataFrame (NOT string)
        if len(reviews) == 0:
            return prod_id, prod_name, None, pd.DataFrame()

        # Match review/rating lengths
        if len(reviews) > len(ratings):
            ratings.extend([0] * (len(reviews) - len(ratings)))

        df = pd.DataFrame({
            "prod_id": [prod_id] * len(reviews),
            "prod_name": [prod_name] * len(reviews),
            "customer_review": reviews,
            "customer_rating": ratings
        })

        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prod_name.replace(' ', '_')}_{timestamp}.csv"
        file_path = os.path.join(SCRAPED_FILES_FOLDER, filename)
        df.to_csv(file_path, index=False)

        return prod_id, prod_name, file_path, df

    except Exception:
        # Return empty DataFrame on ANY error
        return None, None, None, pd.DataFrame()

    finally:
        driver.quit()

