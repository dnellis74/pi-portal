from dataclasses import dataclass
from datetime import datetime
import boto3
import logging
from gspread_array_map import GsheetArrayMap
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from scrape.spiders.legis_50_state import LegisSpider
import json

def scraper():
    # Set logging level for boto3 and botocore
    logging.getLogger('boto3').setLevel(logging.INFO)
    logging.getLogger('botocore').setLevel(logging.INFO)
    
    # Optional: Set logging level for specific AWS service-related modules (like s3transfer)
    logging.getLogger('s3transfer').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    
    # Create the logger
    logger_name = 'scraper'
    log_file = 'scraper.log'
    
    # Truncate the log file at startup
    with open(log_file, "w"):
        pass  # Open the file in write mode to clear its contents
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    ## Everything breaks in "w" mode.  For now, a only
    file_handler = logging.FileHandler(log_file, mode='a')  # Change to 'a' if you want to append
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Disable propagation to prevent the root logger from logging again
    logger.propagate = False

    # Test logging
    logger.info("This is an info message")
    logger.error("This is an error message")
    
    # Disable Scrapy's default logging configuration
    configure_logging(install_root_handler=False)

    # Use the custom logger for Scrapy and direct all logs to both handlers
    scrapy_settings = get_project_settings()
    scrapy_settings.LOGGING = None  # Disable Scrapy's internal logging config
    scrapy_settings.LOG_ENABLED = True
    scrapy_settings.LOG_LEVEL = "INFO"
    scrapy_settings.LOG_STDOUT = True
    
    # Initialize the S3 client
    s3_client = boto3.client('s3')
    bucket_name = 'sbx-piai-docs'
    legis_file = '50_state_legis.json'
    
    try:
        job_folder = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        ## Get urls from sheet and write them to file
        s3_object_key = f'{job_folder}/{legis_file}'
        
        json_data = gsheet_to_json()
        s3_client.put_object(Bucket=bucket_name, Key=s3_object_key, Body=json_data)
        logger.info(f"Data uploaded to '{bucket_name}/{s3_object_key}' successfully.")
                
        ## Crawl and write 
        # Initialize a Scrapy CrawlerProcess with your project's settings
       
        # Configure settings for concurrency
        scrapy_settings.set('JOB_FOLDER', job_folder)
        scrapy_settings.set('BUCKET_NAME', bucket_name)
        process = CrawlerProcess(scrapy_settings)    
        # Schedule the spider to run
        process.crawl(LegisSpider, legis_file=legis_file, job_folder=job_folder)
        # Start the crawling process (it will block here until the spider is done)
        process.start()
        
        # upload log to s3 for posterity
        s3_client.upload_file(log_file, bucket_name, f'{job_folder}/{log_file}')
    except Exception as e:
        logger.exception(f'Error: {e}')
        return 1        
    return 0

def gsheet_to_json():
        logger = logging.getLogger('scraper')

        # Path to your service account credentials JSON file
        creds_file = './sbx-kendra-8e724bd9a0ce.json'

        # Field to use as the key in the returned dictionary
        # Instantiate the GspreadArrayMap class
        gspread_map = GsheetArrayMap(creds_file)
        # Retrieve data
        normalized_result = []
        
        # Colorado guidance
        guidance = False
        if (guidance):
            logger.info("Reading Colorado guidance")        
            sheet_url = get_sheet_url('1Iey3LEPm9rZYMZ0dSkPnL9IN7vYCbnwkBLlogJarKBs')
            worksheet_name = 'support_docs'
            wanted_fields = ['jurisdiction', 'page_title', 'link_title', 'pdf_link', 'doc_type', 'tombstone', 'language']        
            docs = gspread_map.get_fields(sheet_url, wanted_fields, worksheet_name)
            current_doc = 2
            start_doc = 690 # set to start doc in guidance sheet
            end_doc = 690
            for doc in docs:       
                if (current_doc >= start_doc):
                    if (end_doc != -1 and current_doc > end_doc):
                        break
                    title:str = doc[wanted_fields[1]]
                    # hack
                    doc[wanted_fields[1]] = title.replace("| Colorado Department of Public Health and Environment", "").strip()
                    normalized_result.append((normalize(wanted_fields, doc)))
                current_doc += 1
                
        # 50 states
        FiddyState = False
        if FiddyState:
            logger.info("Reading 50 state")
            sheet_url = get_sheet_url('1pvqmNPP_22wvKdiCYFqcj1z55Z3lgZOX0nDDHhmmIZg')
            worksheet_name = 'Individual doc links'
            wanted_fields = ['State', 'Regulation Name', 'Description', 'Link', 'doc_type', 'tombstone', 'language']
            docs = gspread_map.get_fields(sheet_url, wanted_fields, worksheet_name)
            current_doc = 2
            start_doc = 6079 # set to start doc in guidance sheet
            end_doc = 6128 # -1 for to the end
            for doc in docs:
                if (current_doc >= start_doc):
                    if (end_doc != -1 and current_doc > end_doc):
                        break
                    normalized_result.append((normalize(wanted_fields, doc)))
                current_doc += 1

        # CARB            
        carb = True
        if carb:
            logger.info("Reading CARB")
            sheet_url = get_sheet_url('1pvqmNPP_22wvKdiCYFqcj1z55Z3lgZOX0nDDHhmmIZg')
            worksheet_name = 'CARB Current Air District Rule Data'
            wanted_fields = ['Air District Name', 'Regulation', 'Rules', 'Regulatory Text', 'doc_type', 'tombstone', 'language']
            docs = gspread_map.get_fields(sheet_url, wanted_fields, worksheet_name) 
            for doc in docs:
                normalized_result.append((normalize(wanted_fields, doc)))
                
        # Convert the list to JSON
        return json.dumps(normalized_result, indent=4)

def normalize(wanted_fields, doc):
    return {
        'jurisdiction': doc[wanted_fields[0]],
        'title': doc[wanted_fields[1]],
        'description': doc[wanted_fields[2]],
        'url': doc[wanted_fields[3]],
        'doc_type': doc[wanted_fields[4]],
        'tombstone': doc[wanted_fields[5]],
        'language': doc[wanted_fields[6]]
    }
    
def get_sheet_url(sheet_id):
    return f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0'

def jurisdiction_filter(jurisdiction):
    if jurisdiction != 'California (SCAQMD)':
        return False
    return True
if __name__ == '__main__':
    scraper()
