from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class SeleniumOnBasePdf():
    def __init__(self, download_dir):
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })

        # Initialize the Chrome driver
        self.driver = webdriver.Chrome(options=chrome_options)
        

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()
    
    def download_pdf(self, url):
        try:
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

            print(f"PDF downloaded successfully {url}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            # Close the browser
            return 0

    # Usage example
    # url = "https://oitco.hylandcloud.com/POP/DocPop/DocPop.aspx?docid=4556851"  # Replace with your actual URL
    # download_dir = os.path.join(os.path.expanduser("~"), "Downloads")  # Set your desired download directory
    # download_dir = "."
    # download_pdf(url, download_dir)

