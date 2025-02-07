import re

def sanitize_s3_key(key: str) -> str:
    """
    Sanitizes an S3 object key by removing or replacing invalid characters.
    Allowed characters are mostly printable ASCII characters.
    """
    # Replace invalid characters with underscores
    sanitized_key = re.sub(r'[^a-zA-Z0-9!_.*\'()/\-]', '_', key)
    
    # Optional: If you want to limit key length (S3 supports up to 1024 bytes for keys)
    max_key_length = 1024
    return sanitized_key[:max_key_length]

def sanitize_metadata(metadata: dict) -> dict:
    """
    Sanitizes S3 metadata by removing or replacing invalid characters in metadata keys.
    S3 metadata keys must be ASCII characters and can't include `@`, `=`, etc.
    """
    sanitized_metadata = {}
    for key, value in metadata.items():
        # Remove any invalid characters from the metadata key
        sanitized_key = re.sub(r'[^\x00-\x7F]+', '', key)  # Keep only ASCII characters
        
        # Ensure the metadata key length does not exceed 128 bytes
        max_meta_key_length = 128
        sanitized_key = sanitized_key[:max_meta_key_length]

        # Optional: Ensure the metadata value is also a string
        if not isinstance(value, str):
            value = str(value)
        safe_value = re.sub(r'[^\x00-\x7F]+', '', value)  # Keep only ASCII characters

        sanitized_metadata[sanitized_key] = safe_value

    return sanitized_metadata

# Example usage
s3_key = "invalid/key@with spaces&special#characters.txt"
metadata = {
    "author@name": "John Doe",
    "invalid#key=value": "Metadata with invalid characters",
    "another-invalid/key": 12345
}

clean_key = sanitize_s3_key(s3_key)
clean_metadata = sanitize_metadata(metadata)

print("Sanitized S3 Key:", clean_key)
print("Sanitized Metadata:", clean_metadata)
