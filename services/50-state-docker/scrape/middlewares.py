# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# myproject/middlewares.py

import os
import shutil
import time
import logging
import re
from urllib.parse import urlparse
from uuid import uuid4
from scrapy.http import HtmlResponse
from scrapy import signals
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from twisted.internet import threads

class SeleniumDownload:
    def __init__(self, download_dir):
        self.logger = logging.getLogger('scraper')
        logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.INFO)

        self.download_dir = download_dir

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True,  # To download PDFs instead of opening them
            "profile.default_content_setting_values.automatic_downloads": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=chrome_options)

    @classmethod
    def from_crawler(cls, crawler):
        # Get the download directory from settings or set a default one
        download_dir = crawler.settings.get('SELENIUM_DOWNLOAD_DIR', '/tmp')
        middleware = cls(download_dir)
        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)
        return middleware

    def process_request(self, request, spider):
        # Define the URL patterns that need Selenium for PDF downloads
        pdf_url_patterns = [
            r'google',
            r'hylandcloud',
        ]

        # Check if the request URL matches any of the patterns
        for pattern in pdf_url_patterns:
            if re.search(pattern, request.url):
                self.logger.info(f"Starting {request.url} with Selenium for file download")
                # return threads.deferToThread(self.selenium_download, request, pattern)
                return self.selenium_download(request, pattern)
        # If no pattern matches, let Scrapy handle the request
        return None
    
    def selenium_download(self, request, pattern):
        # Generate a unique download directory for each request
        unique_id = str(uuid4())
        unique_download_dir = os.path.join(self.download_dir, unique_id)
        os.makedirs(unique_download_dir, exist_ok=True)

        try:
            # Update browser preferences to use the unique directory
            self.driver.execute_cdp_cmd('Page.setDownloadBehavior', {
                'behavior': 'allow',
                'downloadPath': unique_download_dir
            })
            self.driver.get(request.url)
            
            # These methods wait for the right button to be active, and then start the download
            if pattern == r'google':
                self.google_click_button()
            elif pattern == r'hylandcloud':
                self.onbase_click_button()

            # Wait for the download to complete
            downloaded_file_path = self.wait_for_download(download_dir=unique_download_dir)
            # Read the data into an http response and return
            if downloaded_file_path:
                with open(downloaded_file_path, 'rb') as f:
                    file_data = f.read()
                response = HtmlResponse(
                    url=request.url,
                    body=file_data,
                    encoding='utf-8',
                    request=request
                )
                response.meta['download_slot'] = urlparse(request.url).netloc
                return response
            else:
                logging.error(f"Failed to download file from {request.url}")
                return HtmlResponse(
                    url=request.url,
                    status=500,
                    request=request
                )
        except Exception as e:
            logging.error(f"Error in Selenium middleware: {str(e)}")
            return HtmlResponse(
                    url=request.url,
                    status=500,
                    request=request
                )
        finally:
            # remove the file after processing
            shutil.rmtree(unique_download_dir)        
            self.logger.info(f"Completing {request.url} with Selenium for file download")
                    
    def google_click_button(self):
        download_button = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@data-tooltip='Download']"))
                    )
        download_button.click()
        
    def onbase_click_button(self):
        # Wait for the PDF to load and switch to proper frame
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "DocSelectPage"))
        )
        self.driver.switch_to.frame("DocSelectPage")
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "pdfViewerContainer"))
        )
        self.driver.switch_to.frame("pdfViewerContainer")
                
        # Find and click the download link
        mainContentElement = self.driver.find_element(By.ID, "main-content")
        target_anchor = mainContentElement.find_element(By.TAG_NAME, "a")
        target_anchor.click()

    def wait_for_download(self, download_dir, timeout=30):
        seconds = 0
        downloaded_file = None
        while seconds < timeout:
            files = os.listdir(download_dir)
            if files:
                for file_name in files:
                    if not file_name.endswith('.crdownload'):
                        downloaded_file = file_name
                        return os.path.join(download_dir, downloaded_file)
            time.sleep(1)
            seconds += 1
        return None

    def spider_closed(self):
        self.logger.info("Closing Selenium WebDriver")
        self.driver.quit()
