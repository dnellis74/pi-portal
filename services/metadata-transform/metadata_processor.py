import boto3
import json
import traceback

class MetadataProcessor:
    def process(self, metadata):
        """
        Override this method to perform custom transformations on the metadata.
        """
        # By default, do nothing
        return metadata

def is_metadata_file(key):
    """
    Determines if the S3 object key corresponds to a metadata file.
    Modify the condition based on your metadata file naming conventions.
    """
    # Assuming metadata files end with '_metadata.json'
    return key.endswith('_metadata.json')

def get_metadata_from_s3(s3_client, bucket_name, key):
    """
    Retrieves and loads the metadata JSON from S3.
    """
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    content = response['Body'].read().decode('utf-8')
    metadata = json.loads(content)
    return metadata

def write_metadata_to_s3(s3_client, bucket_name, key, metadata):
    """
    Writes the modified metadata back to S3.
    """
    content = json.dumps(metadata)
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=content)

def main():
    s3 = boto3.client('s3')
    bucket_name = input("Enter the S3 bucket name: ")

    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name)

    # Use the custom processor
    processor = MetadataProcessor()
    total_files = 0
    altered_files = 0
    errors = []

    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if is_metadata_file(key):
                    total_files += 1
                    try:
                        metadata = get_metadata_from_s3(s3, bucket_name, key)
                        original_metadata = metadata.copy()
                        # Process the metadata
                        metadata = processor.process(metadata)
                        if metadata != original_metadata:
                            altered_files += 1
                            # Uncomment the following line to write back to S3
                            # write_metadata_to_s3(s3, bucket_name, key, metadata)
                    except Exception as e:
                        errors.append(f"Error processing {key}: {str(e)}")
                        traceback.print_exc()

    print(f"\nProcessing complete.")
    print(f"Total metadata files processed: {total_files}")
    print(f"Total metadata files altered: {altered_files}")
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(error)

if __name__ == "__main__":
    main()
a