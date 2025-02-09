# Mayan Upload Service

Service to sync documents from S3 to Mayan EDMS based on metadata.

## Features
- Monitors S3 folder for documents
- Creates document types in Mayan if they don't exist
- Uploads documents to Colorado cabinet with correct document type 

## Development Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
- Windows: `venv\Scripts\activate`
- Unix/MacOS: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (see .env.example)

5. Run the script:
```bash
python s3_to_mayan.py
```

## Environment Variables

- `MAYAN_API_URL`: URL of the Mayan EDMS instance (default: 'http://localhost:80')
- `MAYAN_API_TOKEN`: API token for authentication with Mayan EDMS (default: 'default_token')
- `S3_BUCKET_NAME`: Name of the S3 bucket containing the documents (default: 'sbx-colorado-only')
- `S3_FOLDER_PATH`: Path to the folder in the S3 bucket (default: '/')
- `MAYAN_COLORADO_CABINET_ID`: ID of the Colorado cabinet in Mayan EDMS (default: '1')

Note: AWS credentials are read from ~/.aws/credentials. Make sure you have configured your AWS credentials using `aws configure` or by manually creating the credentials file.

## AWS Configuration

1. Install AWS CLI:
```bash
pip install awscli
```

2. Configure AWS credentials:
```bash
aws configure
```

Or manually create `~/.aws/credentials` with:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

You can also specify a different profile when running the script:
```bash
python s3_to_mayan.py --profile another-profile
```

## Docker Setup

The Docker setup remains unchanged since it doesn't need the virtual environment, but developers can now easily work on the code locally using venv. 