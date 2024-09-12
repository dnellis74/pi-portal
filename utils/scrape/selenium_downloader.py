from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class SeleniumDownloader():
    def __init__(self, download_dir):
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })

        # Initialize the Chrome driver
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get("https://www.google.com")
        self.driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        self.driver.execute("send_command", params)

        

    def __enter__(self):
        return self
    
    def download_onbase_pdf(self, url):
        # Navigate to the URL
        self.driver.get(url)

        # Wait for the PDF to load and switch to proper frame
        WebDriverWait(self.driver, 8).until(
            EC.presence_of_element_located((By.ID, "DocSelectPage"))
        )
        self.driver.switch_to.frame("DocSelectPage")
        WebDriverWait(self.driver, 8).until(
            EC.presence_of_element_located((By.ID, "pdfViewerContainer"))
        )
        self.driver.switch_to.frame("pdfViewerContainer")
                
        # Find and click the download link
        mainContentElement = self.driver.find_element(By.ID, "main-content")
        target_anchor = mainContentElement.find_element(By.TAG_NAME, "a")
        target_anchor.click()

        # Wait for the download to complete
        time.sleep(5)  # Adjust this time based on your network speed and file size
        
    def download_google_url(self, url):
        # Navigate to the Google Drive sharing link
        self.driver.get(url)

        # Wait for the download button to be clickable and click it
        download_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@data-tooltip='Download']"))
        )
        download_button.click()

        # Wait for the file to be downloaded (adjust the time as needed)
        time.sleep(5)