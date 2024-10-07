from dataclasses import dataclass
from dataclasses_json import dataclass_json

import dataclasses
import json
import os
import sys
import argparse
import PyPDF2

@dataclass_json
@dataclass
class Fields:
    pdf_name: str
    text: str

@dataclass_json
@dataclass
class CloudSearchDocument:
    type: str
    id: str
    fields: Fields

def extract_text_from_pdf(file_name):
    with open(file_name, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def transform_to_cloudsearch_doc(pdf_name, text) -> CloudSearchDocument:
    fields = Fields(pdf_name, text)
    return CloudSearchDocument("add", pdf_name, fields)
    
def get_file_names(path):
    file_names = []
    # Walk through the directory tree
    for root, dirs, files in os.walk(path):
        for file in files:
            # Get the full path of the file
            file_path = os.path.join(root, file)
            # Add the file path to the array
            file_names.append(file_path)
    return file_names

def write_file(pdf_name, content: str):
    json_filename = os.path.join("download", pdf_name)
    json_filename = json_filename + "_batch.json"
    try:
        json_data = json.dumps(content, indent=2, default=lambda o: o.to_dict())
        with open(json_filename, 'w') as file:
            file.write(json_data)
        print(f"Successfully wrote content to {json_filename}")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")

def main():
    parser = argparse.ArgumentParser(description='Transform a PDF into OpenSearch documents')
    parser.add_argument('pdf_path', help='Path to the PDF directory')
    parser.add_argument('--host', default='localhost', help='OpenSearch host URL')
    parser.add_argument('--port', default=9200, type=int, help='OpenSearch port number')
    args = parser.parse_args()

    pdf_path = args.pdf_path
    host = args.host
    port = args.port

    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} does not exist.")
        sys.exit(1)

    os.makedirs("download", exist_ok=True)
    for dirpath, dirnames, filenames in os.walk(pdf_path):
        for dir in dirnames:
            print("Processing directory: ", dir)
            file_names = get_file_names(os.path.join(pdf_path,dir))
            cloudsearch_batch = []
            for file_name in file_names:
                file_ext = os.path.splitext(os.path.basename(file_name))
                if file_ext[1] == '.pdf':
                    print("Processing PDF: ", file_ext[0])
                    try:
                        text = extract_text_from_pdf(file_name)
                        cloudsearchdoc: str = transform_to_cloudsearch_doc(file_ext[0], text)
                        cloudsearch_batch.append(cloudsearchdoc)
                    except RuntimeError as e:
                        print("Error extracting: ", e)
            if len(cloudsearch_batch) > 0:
                write_file(dir, cloudsearch_batch)

if __name__ == '__main__':
    main()