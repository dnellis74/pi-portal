
# Python Application for Amazon Textract and S3 Integration

## Requirements

I am building a Python application that integrates with Amazon Textract to process documents stored in S3. The application should have the following features and classes, each in a separate file:

### 1. **TextractDocumentTextDetector**
- This class handles asynchronous Textract job initiation and pagination.
- It should include a caching mechanism to avoid redundant API calls. Cache files should be named based on the document key and `NextToken` and stored in a structure that is safe for file systems.
- Only cache results when `JobStatus` is `"SUCCEEDED"`. Do not cache partial or incomplete results when the status is `"IN_PROGRESS"`.
- The `_poll_for_completion` method should process paginated responses and use cache files if they exist.
- Use proper error handling for AWS API calls and log failures.

### 2. **OpenSearchDocumentFormatter**
- This class takes extracted text lines from Textract and formats them into a list of JSON objects, ensuring that each object is no larger than 1 MB.
- Each JSON object should include metadata such as the source bucket, document key, and a timestamp.
- Provide a unique `document_id` for the entire document.

### 3. **S3Uploader**
- This class uploads JSON documents to an S3 bucket.
- Include robust error handling for AWS API calls and logging of successes and failures.

### 4. **Utility Functions**
- **`replace_file_extension`**: Replace the file extension of an S3 object key with a new extension.
- **`get_root_filename`**: Extract the "root" part of an S3 object key (i.e., remove the file extension).

### 5. **Main Script**
- Use `configparser` to load AWS and S3 configuration values from a `config.ini` file.
- Orchestrate the workflow:
  - Detect text in an input document using `TextractDocumentTextDetector`.
  - Format the detected text into JSON objects using `OpenSearchDocumentFormatter`.
  - Upload the formatted JSON objects to an S3 bucket using `S3Uploader`.
  - Name the uploaded files using the root name of the input document key, appending `_part_<number>.json` for multi-part documents.

---

## Implementation Details
- Include detailed logging in all classes and methods for debugging and operational visibility.
- Use Python best practices for error handling and code organization.
