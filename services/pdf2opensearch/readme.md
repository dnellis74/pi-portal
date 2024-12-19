# **Prompt**

I am building a Python application that integrates with Amazon Textract and OpenSearch to process documents stored in S3. The application should have the following structure and functionality:

---

## **1. S3Manager Class**

- This class manages all S3 operations, including:
  - **Listing Objects (`list_objects`)**:
    - Recursively list objects under a given S3 folder (prefix).
    - Allow excluding certain file extensions, such as `.json`, to avoid processing metadata files.
    - Include proper logging to track the number of objects listed and their details.
  - **Uploading Documents (`upload_document`)**:
    - Upload JSON documents to an S3 bucket.
    - Handle errors gracefully and log successes.
    - Ensure the uploaded files are named correctly.

---

## **2. TextractDocumentTextDetector Class**

- This class handles text detection using Amazon Textract.
- **Key Features**:
  - **Textract Job Management**:
    - Start a Textract asynchronous job (`_start_document_text_detection`).
    - Poll for job completion (`_poll_for_completion`), including handling paginated responses using `NextToken`.
  - **Caching**:
    - Cache responses locally in a folder named `cache`.
    - Use a sub-folder based on the S3 object key, replacing slashes (`/`) with underscores (`_`).
    - Name cache files sequentially as `page_1.json`, `page_2.json`, etc.
    - Ensure only successful Textract responses are cached. Skip caching incomplete or failed results.
    - If cached results exist, reuse them instead of making live Textract API calls.
  - **Error Handling**:
    - Gracefully handle Textract API errors and retry appropriately.

---

## **3. OpenSearchDocumentFormatter Class**

- This class formats text lines extracted by Textract into OpenSearch-compatible JSON documents.
- **Key Features**:
  - Split the document into multiple JSON objects if the size exceeds 1 MB.
  - Each JSON document should include:
    - A unique `_id` for OpenSearch.
    - Metadata fields like `source_bucket`, `source_document_key`, and `indexed_at`.
    - A `lines` field containing the text content.
  - Include robust logging for debugging and transparency.

---

## **4. Utilities**

- **`replace_file_extension`**:
  - Replace the file extension of an S3 object key with a new extension.
- **`get_root_filename`**:
  - Extract the "root" part of an S3 object key (i.e., remove the file extension).

---

## **5. Main Script**

- Use `configparser` to load AWS and S3 configuration values from a `config.ini` file.
- Workflow:
  1. Read the input S3 bucket and folder prefix from the configuration file.
  2. Use the `S3Manager` to list all objects under the folder, excluding metadata files (e.g., `.json`).
  3. For each document:
     - Use `TextractDocumentTextDetector` to extract text.
     - Format the extracted text into OpenSearch-compatible JSON documents using `OpenSearchDocumentFormatter`.
     - Upload the formatted documents to the specified S3 bucket using `S3Manager`.
  4. Skip processing of metadata or unsupported file types.

---

## **Configuration File (`config.ini`)**

- Example structure:
```ini
[aws]
input_bucket = my-bucket
folder_prefix = input-folder/
output_bucket = my-output-bucket
region = us-east-1
```

---

## **Code Requirements**

- Use Python best practices for error handling, logging, and modular design.
- Ensure all classes are in separate files (`s3_manager.py`, `textract_detector.py`, `document_formatter.py`).
- Include a `main.py` script that orchestrates the workflow.
- Optimize the code for efficiency and maintainability.
