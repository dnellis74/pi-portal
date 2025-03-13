#!/usr/bin/env python3

import boto3
import json
import csv
import os
import logging
from datetime import datetime
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Set base logging to WARNING
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Set AWS related loggers to WARNING level
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Explicitly set our logger to WARNING

def process_json_object(s3_client, bucket, key, csv_writer):
    """Process a single JSON object from S3 and write to CSV."""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = json.loads(response['Body'].read().decode('utf-8'))
        
        # Log the full content at debug level
        logger.debug(f"Content of {key}:\n{json.dumps(content, indent=2)}")
        
        # Extract required fields from Attributes object with default values if not present
        attributes = content.get('Attributes', {})
        row = {
            'jurisdiction': attributes.get('jurisdiction', 'N/A'),
            'document_title': attributes.get('_document_title', 'N/A'),
            'aq_type': attributes.get('aq_type', 'N/A'),
            'pi_url': attributes.get('pi_url', 'N/A')
        }
        
        csv_writer.writerow(row)
        logger.info(f"Successfully processed {key}")
        
    except ClientError as e:
        logger.error(f"Error processing {key} in bucket {bucket}: {str(e)}")
    except json.JSONDecodeError:
        logger.error(f"Error: {key} is not a valid JSON file")
    except Exception as e:
        logger.error(f"Unexpected error processing {key}: {str(e)}")

def traverse_bucket(s3_client, bucket_name, csv_writer):
    """Recursively traverse all objects in an S3 bucket."""
    logger.info(f"Processing bucket: {bucket_name}")
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' not in page:
                logger.warning(f"No contents found in bucket {bucket_name}")
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('.json'):
                    logger.debug(f"Found JSON file: {key}")
                    process_json_object(s3_client, bucket_name, key, csv_writer)
                    
    except ClientError as e:
        logger.error(f"Error accessing bucket {bucket_name}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error with bucket {bucket_name}: {str(e)}")

def main():
    logger.info("Starting document metadata extraction")
    
    # Initialize S3 client using default credentials
    s3_client = boto3.client('s3')
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'document_metadata_{timestamp}.csv')
    
    # List of buckets to process
    buckets = ['sbx-kendra-index', 'sbx-colorado-only']
    
    # CSV field names
    fieldnames = ['jurisdiction', 'document_title', 'aq_type', 'pi_url']
    
    logger.info(f"Writing results to: {output_file}")
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for bucket in buckets:
            traverse_bucket(s3_client, bucket, writer)
    
    logger.info("Process completed successfully")

if __name__ == "__main__":
    main() 