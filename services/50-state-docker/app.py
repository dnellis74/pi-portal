from datetime import datetime
import boto3
import logging
from gspread_array_map import GsheetArrayMap
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrape.spiders.legis_50_state import LegisSpider
import json

def lambda_handler(event, context):
    # Set up basic configuration
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info("Starting the application...")

    try:
        now = datetime.now()
        job_folder = f'scrape/{now.year}-{now.month}-{now.day}_{now.hour}-{now.minute}-{now.second}'
        filename = '50_state_legis.json'
        ## Get urls from sheet and write them to file
        extract_fields = True
        urls_json = f'{job_folder}/{filename}'
        if (extract_fields is True):
            gsheet_to_file(urls_json)
            logger.info(f'Data written to {urls_json}')
                
        ## Crawl and write 
        # Initialize a Scrapy CrawlerProcess with your project's settings
        settings = get_project_settings()
        process = CrawlerProcess(settings)    
        # Schedule the spider to run
        process.crawl(LegisSpider, legis_file=filename, job_folder=job_folder)
        # Start the crawling process (it will block here until the spider is done)
        process.start()

    except Exception as e:
        logger.exception(f'Error: {e}')
        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'message': 'An unexpected error occurred.'
            }
        }
        
    return {
        'statusCode': 200,
        'body': 'success'
    }
def gsheet_to_file(filename):
        # Path to your service account credentials JSON file
        creds_file = './sbx-kendra-8e724bd9a0ce.json'
        # URL of the Google Sheet
        sheet_id = '1pvqmNPP_22wvKdiCYFqcj1z55Z3lgZOX0nDDHhmmIZg'
        sheet_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0'
        worksheet_name = 'Individual doc links'
        wanted_fields = ['State', 'Regulation Name', 'Link']
        # Field to use as the key in the returned dictionary
        # Instantiate the GspreadArrayMap class
        gspread_map = GsheetArrayMap(creds_file)
        # Retrieve data from the sheet
        docs = gspread_map.get_fields(sheet_url, wanted_fields, worksheet_name)
        worksheet_name = 'CARB Current Air District Rule Data'
        wanted_fields = ['Air District Name', 'Rules', 'Regulatory Text']
        docs = docs + gspread_map.get_fields(sheet_url, wanted_fields, worksheet_name) 

        # Write the dictionary to the file in JSON format
        # Convert the list to JSON
        json_data = json.dumps(docs)
        write_data_to_s3('sbx-piai-docs', filename, json_data)    

def write_data_to_s3(bucket_name, object_name, data):
    # Set logging level for boto3 and botocore
    logging.getLogger('boto3').setLevel(logging.INFO)
    logging.getLogger('botocore').setLevel(logging.INFO)
    # Optional: Set logging level for specific AWS service-related modules (like s3transfer)
    logging.getLogger('s3transfer').setLevel(logging.INFO)
    # Initialize the S3 client
    s3_client = boto3.client('s3')
    
    # Upload the data
    s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=data)
    logging.info(f"Data uploaded to '{bucket_name}/{object_name}' successfully.")


if __name__ == '__main__':
    lambda_handler(None, None)