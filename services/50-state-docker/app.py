from dataclasses import dataclass
from datetime import datetime
import boto3
import logging
from gspread_array_map import GsheetArrayMap
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrape.spiders.legis_50_state import LegisSpider
import json

# Set up basic configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Starting the application...")

    # Set logging level for boto3 and botocore
logging.getLogger('boto3').setLevel(logging.INFO)
logging.getLogger('botocore').setLevel(logging.INFO)
# Optional: Set logging level for specific AWS service-related modules (like s3transfer)
logging.getLogger('s3transfer').setLevel(logging.INFO)
# Initialize the S3 client
s3_client = boto3.client('s3')
bucket_name = 'sbx-piai-docs'
legis_file = '50_state_legis.json'
log_file='scrape.log'

def lambda_handler(event, context):
    try:
        now = datetime.now()
        job_folder = f'scrape/{now.year}-{now.month}-{now.day}_{now.hour}-{now.minute}-{now.second}'
        ## Get urls from sheet and write them to file
        input_s3_key = f'{job_folder}/{legis_file}'
        
        json_data = gsheet_to_json()
        s3_client.put_object(Bucket=bucket_name, Key=input_s3_key, Body=json_data)
        logging.info(f"Data uploaded to '{bucket_name}/{input_s3_key}' successfully.")
                
        ## Crawl and write 
        # Initialize a Scrapy CrawlerProcess with your project's settings
        settings = get_project_settings()
        process = CrawlerProcess(settings)    
        # Schedule the spider to run
        process.crawl(LegisSpider, legis_file=legis_file, job_folder=job_folder, log_file=log_file)
        # Start the crawling process (it will block here until the spider is done)
        process.start()

        #upload log to s3 for posterity
        s3_client.upload_file(log_file, bucket_name, f'{job_folder}/{log_file}')
    except Exception as e:
        logger.exception(f'Error: {e}')
        return 1
        
    return 0

def gsheet_to_json():
        # Path to your service account credentials JSON file
        creds_file = './sbx-kendra-8e724bd9a0ce.json'

        # Field to use as the key in the returned dictionary
        # Instantiate the GspreadArrayMap class
        gspread_map = GsheetArrayMap(creds_file)
        # Retrieve data
        transformed_result = []
        
        # Colorado guidance
        logger.info("Reading Colorado guidance")        
        sheet_url = get_sheet_url('1Iey3LEPm9rZYMZ0dSkPnL9IN7vYCbnwkBLlogJarKBs')
        worksheet_name = 'support_docs'
        wanted_fields = ['page_title', 'link_title', 'pdf_link']
        docs = gspread_map.get_fields(sheet_url, wanted_fields, worksheet_name)
        for doc in docs:
            transformed_result.append((transform_row(wanted_fields, doc)))
                
        # 50 states
        logger.info("Reading 50 state")
        sheet_url = get_sheet_url('1pvqmNPP_22wvKdiCYFqcj1z55Z3lgZOX0nDDHhmmIZg')
        worksheet_name = 'Individual doc links'
        wanted_fields = ['State', 'Regulation Name', 'Link']
        docs = gspread_map.get_fields(sheet_url, wanted_fields, worksheet_name)
        for doc in docs:
            transformed_result.append((transform_row(wanted_fields, doc)))
        
        # CARB
        logger.info("Reading CARB")
        worksheet_name = 'CARB Current Air District Rule Data'
        wanted_fields = ['Air District Name', 'Rules', 'Regulatory Text']
        docs = gspread_map.get_fields(sheet_url, wanted_fields, worksheet_name) 
        for doc in docs:
            transformed_result.append((transform_row(wanted_fields, doc)))
                
        # Convert the list to JSON
        return json.dumps(transformed_result, indent=4)

def transform_row(wanted_fields, doc):
    return {'jurisdiction': doc[wanted_fields[0]], 'name': doc[wanted_fields[1]], 'url': doc[wanted_fields[2]]}
    
def get_sheet_url(sheet_id):
    return f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0'

if __name__ == '__main__':
    lambda_handler(None, None)
