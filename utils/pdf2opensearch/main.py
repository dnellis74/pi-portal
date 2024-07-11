import os
import sys
import argparse
import PyPDF2

from opensearchpy import OpenSearch, helpers

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def transform_to_opensearch_docs(pdf_path, index_name):
    text = extract_text_from_pdf(pdf_path)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

    actions = [
        {
            '_index': index_name,
            '_id': pdf_name,
            'text': text
        }
    ]

    return actions

def main():
    parser = argparse.ArgumentParser(description='Transform a PDF into OpenSearch documents')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('index_name', help='Name of the OpenSearch index')
    parser.add_argument('--host', default='localhost', help='OpenSearch host URL')
    parser.add_argument('--port', default=9200, type=int, help='OpenSearch port number')
    args = parser.parse_args()

    pdf_path = args.pdf_path
    index_name = args.index_name
    host = args.host
    port = args.port

    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} does not exist.")
        sys.exit(1)

    actions = transform_to_opensearch_docs(pdf_path, index_name)

    #index(pdf_path, host, port, actions)

def index(pdf_path, host, port, actions):
    client = OpenSearch(hosts=[{'host': host, 'port': port}])

    try:
        helpers.bulk(client, actions)
        print(f"PDF '{os.path.basename(pdf_path)}' transformed and indexed in OpenSearch.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()