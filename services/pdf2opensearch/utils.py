import os

def replace_file_extension(key: str, new_extension: str) -> str:
    # Split the key on the last dot to separate the filename and its extension
    parts = key.rsplit('.', 1)
    if len(parts) == 1:
        # If there's no extension, just add the new one
        return f"{key}.{new_extension.lstrip('.')}"
    else:
        # Replace the existing extension
        base = parts[0]
        return f"{base}.{new_extension.lstrip('.')}"
    
def get_root_filename(key: str) -> str:
    """
    Extracts the root part of a file name (removes the extension).

    :param key: The full key or file name.
    :return: The file name without the extension.
    """
    return os.path.splitext(key)[0]