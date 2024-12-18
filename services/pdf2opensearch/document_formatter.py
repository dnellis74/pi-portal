from datetime import datetime
import logging
from typing import Dict, List, Optional
import uuid

class OpenSearchDocumentFormatter:
    """
    Formats extracted Textract text into a JSON-compatible dictionary suitable for
    indexing into OpenSearch.
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the OpenSearchDocumentFormatter.

        :param logger: Optional logger instance. If None, a default logger is used.
        """
        self.logger = logger or self._get_logger()

    def _get_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def format_document(self, 
                        lines: List[str], 
                        bucket_name: str, 
                        document_key: str) -> Dict[str, object]:
        """
        Convert extracted text lines and metadata into a JSON-like structure
        suitable for indexing into OpenSearch.

        :param lines: The lines of text extracted by Textract.
        :param bucket_name: The S3 bucket name where the original document is stored.
        :param document_key: The S3 object key of the original document.
        :return: A dictionary representing the OpenSearch document.
        """
        if not lines:
            self.logger.warning("No lines to format into an OpenSearch document.")

        document_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        doc = {
            "document_id": document_id,
            "extracted_text": "\n".join(lines),
            "lines": lines,
            "metadata": {
                "source_bucket": bucket_name,
                "source_document_key": document_key,
                "indexed_at": timestamp
            }
        }

        self.logger.info(f"Formatted document with ID {document_id} for OpenSearch indexing.")
        return doc
    