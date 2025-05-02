import os
import time
from urllib.parse import urljoin
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from core.log_config import logging
from core.config import (
    AVICENNA_LEARN_URL,
    AVICENNA_LEARN_CRAWL_STORING_DIRECTORY,
)

logger = logging.getLogger()



def sanitize_filename(url):
    path = url.replace("https://", "").replace("/", "_")
    if path[-1] in ["/", "_"]:
        path = path[:-1]
    return path + ".html"


def crawl_page(url):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        content = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.theme-doc-markdown.markdown"))
        )

        html_content = content.get_attribute("outerHTML")

        filename = sanitize_filename(url)
        filepath = os.path.join(AVICENNA_LEARN_CRAWL_STORING_DIRECTORY, filename)

        os.makedirs("learn", exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Successfully crawled: {url}")

    except Exception as e:
        logger.error(f"Error crawling {url}: {str(e)}")

    finally:
        driver.quit()


def fetch_all_sources():
    def expand_all_collapsed():
        max_attempts = 10
        attempts = 0
        while attempts < max_attempts:
            collapsed_elements = driver.find_elements(By.CSS_SELECTOR, '[aria-expanded="false"]')
            if not collapsed_elements:
                break
            for element in collapsed_elements:
                try:
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Failed to expand element: {str(e)}")
                    continue
            attempts += 1

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    base_url = AVICENNA_LEARN_URL

    try:
        driver.get(base_url)

        wait = WebDriverWait(driver, 10)
        try:
            sidebar_menu = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.theme-doc-sidebar-menu.menu__list"))
            )
        except Exception as e:
            logger.error(f"Could not find sidebar menu: {str(e)}")
            return

        expand_all_collapsed()

        final_html = driver.execute_script("""
            return document.querySelector("ul.theme-doc-sidebar-menu.menu__list").innerHTML;
        """)

        soup = BeautifulSoup(final_html, "html.parser")

        links = soup.find_all("a")

        unique_urls = set()
        url_text_map = {}

        for link in links:
            href = link.get("href")
            text = link.get_text(strip=True)
            if href and text:
                full_url = urljoin(base_url, href)
                unique_urls.add(full_url)
                url_text_map[full_url] = text

        logger.info(f"\nFound {len(unique_urls)} unique links to crawl")

        os.makedirs("learn", exist_ok=True)

        num_cores = multiprocessing.cpu_count()
        logger.info(f"Using {num_cores} CPU cores for parallel crawling")

        with ProcessPoolExecutor(max_workers=num_cores) as executor:
            executor.map(crawl_page, unique_urls)

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

    finally:
        driver.quit()


if __name__ == "__main__":
    fetch_all_sources()
