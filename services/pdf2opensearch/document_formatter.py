from datetime import datetime
import json
import logging
from typing import List, Dict, Optional
import uuid


class OpenSearchDocumentFormatter:
    """
    Formats extracted Textract text into a list of JSON-compatible dictionaries,
    ensuring that each document does not exceed a maximum size of 1 MB.
    """

    MAX_JSON_SIZE = 1024 * 1024  # 1 MB in bytes

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the OpenSearchDocumentFormatter.

        :param logger: Optional logger instance. If None, a default logger is used.
        """
        self.logger = logger or logging.getLogger(__name__)

    def format_document(self, 
                        lines: List[str], 
                        bucket_name: str, 
                        document_key: str) -> List[Dict[str, object]]:
        """
        Convert extracted text lines and metadata into a list of JSON-like structures,
        each limited to a maximum size of 1 MB.

        :param lines: The lines of text extracted by Textract.
        :param bucket_name: The S3 bucket name where the original document is stored.
        :param document_key: The S3 object key of the original document.
        :return: A list of dictionaries representing the formatted JSON documents.
        """
        if not lines:
            self.logger.warning("No lines to format into JSON documents.")

        document_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Prepare the metadata
        metadata = {
            "source_bucket": bucket_name,
            "source_document_key": document_key,
            "indexed_at": timestamp
        }

        # Initialize the list of JSON objects and current working object
        json_objects = []
        current_object = {
            "document_id": document_id,
            "metadata": metadata,
            "lines": []
        }
        current_size = len(json.dumps(current_object).encode('utf-8'))  # Calculate initial size

        # Add lines while respecting the 1 MB size limit
        for line in lines:
            line_size = len(json.dumps(line).encode('utf-8'))  # Size of the line in bytes
            if current_size + line_size > self.MAX_JSON_SIZE:
                # Finalize the current JSON object and start a new one
                json_objects.append(current_object)
                current_object = {
                    "document_id": document_id,
                    "metadata": metadata,
                    "lines": []
                }
                current_size = len(json.dumps(current_object).encode('utf-8'))

            # Add the line to the current JSON object
            current_object["lines"].append(line)
            current_size += line_size

        # Append the last JSON object if it has any lines
        if current_object["lines"]:
            json_objects.append(current_object)

        self.logger.info(f"Formatted document into {len(json_objects)} JSON objects, each <= 1 MB.")
        return json_objects
