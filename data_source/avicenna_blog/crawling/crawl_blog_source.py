import time
import os
import json
import re
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from core.log_config import logging

logger = logging.getLogger()

def sanitize_filename(url):
    # Remove protocol and domain
    path = url.replace("https://avicennaresearch.com/blog/", "")
    # Replace invalid filename characters
    path = re.sub(r'[<>:"/\\|?*]', "_", path)
    # If path is empty, use 'index'
    if not path:
        path = "index"
    return path + ".html"

def extract_article_content(url):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        
        # Wait for main content to load
        main_content = wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        # Get the HTML content of the main tag
        html_content = main_content.get_attribute('outerHTML')
        
        # Create filename from URL
        filename = sanitize_filename(url)
        
        # Ensure blog directory exists
        os.makedirs("blog", exist_ok=True)
        
        # Save to file
        filepath = os.path.join("blog", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"Successfully processed: {url} -> {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing {url}: {str(e)}")
        return False
        
    finally:
        driver.quit()

def crawl_blog():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get("https://avicennaresearch.com/blog/")
        wait = WebDriverWait(driver, 10)
        
        while True:
            try:
                load_more = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.button.button-secondary.gh-loadmore"))
                )
                driver.execute_script("arguments[0].click();", load_more)
                time.sleep(2)
                logger.info("Clicked 'Load more' button")
            except Exception as e:
                logger.info("No more 'Load more' button found - reached end of content")
                break
        
        feed = driver.find_element(By.CSS_SELECTOR, "div.post-feed.gh-feed.gh-canvas")
        articles = feed.find_elements(By.TAG_NAME, "article")
        
        article_urls = []
        for article in articles:
            try:
                link = article.find_element(By.TAG_NAME, "a").get_attribute("href")
                title = article.find_element(By.TAG_NAME, "h2").text
                article_urls.append(link)
                logger.info(f"Found article: {title} - {link}")
            except Exception as e:
                logger.warning(f"Failed to extract article details: {str(e)}")
                continue
                
        logger.info(f"Total articles found: {len(article_urls)}")
        
        # Process articles in parallel
        num_cores = multiprocessing.cpu_count()
        logger.info(f"Using {num_cores} CPU cores for parallel processing")
        
        with ProcessPoolExecutor(max_workers=num_cores) as executor:
            results = list(executor.map(extract_article_content, article_urls))
        
        successful = sum(1 for r in results if r)
        logger.info(f"Successfully processed {successful} out of {len(article_urls)} articles")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    crawl_blog()
