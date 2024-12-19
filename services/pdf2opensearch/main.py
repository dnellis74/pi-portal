from textract_detector import TextractDocumentTextDetector
from document_formatter import OpenSearchDocumentFormatter
from s3_manager import S3Manager  # Updated import
from utils import get_root_filename
import configparser


def main():
    # Load configuration
    config = configparser.ConfigParser()
    config.read('config.ini')

    BUCKET_NAME = config['aws']['input_bucket']
    FOLDER_PREFIX = config['aws']['folder_prefix']
    OUTPUT_BUCKET_NAME = config['aws']['output_bucket']
    REGION_NAME = config['aws']['region']

    # Initialize S3 manager and formatter
    s3_manager = S3Manager(region_name=REGION_NAME)
    formatter = OpenSearchDocumentFormatter()

    # List all objects in the folder
    object_keys = s3_manager.list_objects(BUCKET_NAME, FOLDER_PREFIX, exclude_extensions=['.json'])

    # Process each object
    for object_key in object_keys:
        print(f"Processing object: {object_key}")

        # Initialize Textract detector for each object
        detector = TextractDocumentTextDetector(
            bucket_name=BUCKET_NAME,
            document_key=object_key,
            region_name=REGION_NAME
        )

        try:
            # Extract text
            extracted_text_lines = detector.extract_text()

            # Format documents for OpenSearch
            opensearch_docs = formatter.format_document(
                lines=extracted_text_lines,
                bucket_name=BUCKET_NAME,
                document_key=object_key
            )

            # Upload each formatted document to the output bucket
            root_key = get_root_filename(object_key)
            for i, doc in enumerate(opensearch_docs):
                output_key = f"{root_key}_part_{i+1}.json"
                s3_manager.upload_document(
                    document=doc,
                    bucket_name=OUTPUT_BUCKET_NAME,
                    object_key=output_key
                )

        except RuntimeError as e:
            print(f"Failed to process {object_key}: {str(e)}")


if __name__ == "__main__":
    main()
