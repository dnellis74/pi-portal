import os

def get_root_filename(key: str) -> str:
    """
    Extracts the root part of a file name (removes the extension).

    :param key: The full key or file name.
    :return: The file name without the extension.
    """
    return os.path.splitext(key)[0]
