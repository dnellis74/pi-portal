import boto3

def find_largest_object(bucket_name):
    s3_client = boto3.client('s3')

    paginator = s3_client.get_paginator('list_objects_v2')
    largest_object = None
    largest_size = 0

    for page in paginator.paginate(Bucket=bucket_name):
        if 'Contents' in page:
            for obj in page['Contents']:
                if obj['Size'] > largest_size:
                    largest_size = obj['Size']
                    largest_object = obj

    if largest_object:
        print(f"Largest object: {largest_object['Key']}")
        print(f"Size: {largest_size} bytes")
    else:
        print("No objects found in the bucket.")

# Replace 'your-bucket-name' with the name of your S3 bucket
bucket_name = 'sbx-kendra-index'
find_largest_object(bucket_name)
