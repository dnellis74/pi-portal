from document_formatter import OpenSearchDocumentFormatter
from text_detector import TextractDocumentTextDetector
import configparser

from uploader import S3Uploader

if __name__ == "__main__":
    
    config = configparser.ConfigParser()
    config.read('config.ini')

    BUCKET_NAME = config['aws']['input_bucket']
    DOCUMENT_KEY = config['aws']['input_object_key']
    OUTPUT_BUCKET_NAME = config['aws']['output_bucket']
    REGION_NAME = config['aws']['region']

    detector = TextractDocumentTextDetector(
        bucket_name=BUCKET_NAME,
        document_key=DOCUMENT_KEY,
        region_name=REGION_NAME,  # specify the region as needed
        max_retries=60,
        delay=5
    )

    formatter = OpenSearchDocumentFormatter()
    try:
        extracted_text_lines = detector.extract_text()
        opensearch_doc = formatter.format_document(
            lines=extracted_text_lines,
            bucket_name=BUCKET_NAME,
            document_key=DOCUMENT_KEY
        )
        
        # Upload the formatted document to S3
        uploader = S3Uploader(region_name=REGION_NAME)
        uploader.upload_doc(
            document=opensearch_doc,
            bucket_name=OUTPUT_BUCKET_NAME,
            object_key=DOCUMENT_KEY
        )

    except RuntimeError:
        detector.logger.error("An error occurred during the text extraction or formatting process.", exc_info=True)
