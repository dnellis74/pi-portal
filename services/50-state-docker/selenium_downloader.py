import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class SeleniumDownloader():
    
    download_timeout = 10  # Set the timeout for downloading files (in seconds)
    
    def __init__(self, download_dir):
        # Ensure download_dir is an absolute path
        self.download_dir = os.path.abspath(download_dir)

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")  # Needed for headless Chrome on Windows
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Set Chrome preferences
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Initialize the Chrome driver using webdriver_manager
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Set download behavior using DevTools protocol
        self.driver.execute_cdp_cmd(
            "Page.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": self.download_dir}
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()
        
    def download_onbase_pdf(self, url):
        try:
            # Navigate to the URL
            self.driver.get(url)

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
            time.sleep(10)
        except TimeoutException as e:
            self.logger.error(f"Timeout while downloading from {url}: {e}")
        except NoSuchElementException as e:
            self.logger.error(f"Element not found while downloading from {url}: {e}")
        except Exception as e:
            self.logger.error(f"Error downloading from {url}: {e}")
            
    def download_google_url(self, url):
        try:
            # Navigate to the Google Drive sharing link
            self.driver.get(url)

            # Wait for the download button to be clickable and click it
            download_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@data-tooltip='Download']"))
            )
            download_button.click()
            time.sleep(10)
        except TimeoutException as e:
            self.logger.error(f"Timeout while downloading from {url}: {e}")
        except Exception as e:
            self.logger.error(f"Error downloading from {url}: {e}")
