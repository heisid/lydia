import os

def list_directory_content(path: str) -> list|str:
    """Returns the contents of a directory"""
    """
    Args:
      path: Directory path (string), absolute or relative
    Returns:
      List the contents of a directory (list) or error message
    """
    try:
        return os.listdir(path)
    except Exception as e:
        return repr(e)

def get_current_directory() -> str:
    """Returns current directory"""
    """
    Args:
      No arguments
    Returns:
      Current directory (string)
    """
    return os.getcwd()

def is_file(path: str) -> bool|str:
    """Check if a path is a file"""
    """
    Args:
      path. Path to the file (string)
    Returns:
      Current directory (string) or error message
    """
    if not os.path.exists(path):
        return 'Path not found'
    return os.path.isfile(path)

def get_file_size(path: str) -> int|str:
    """Get file size in bytes"""
    """
    Args:
      path. Path to the file (string)
    Returns:
      File size in bytes (integer) or error message
    """
    if not os.path.exists(path):
        return 'Path not found'
    return os.path.getsize(path)

def read_file(path: str) -> str|None:
    """Read a file"""
    """
    Args:
      path. Path to the file (string)
    Returns:
      File content (string) or None if file not found
    """
    try:
        with open(path, 'r') as f:
            return f.read()
    finally:
        f.close()