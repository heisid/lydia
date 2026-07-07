import os
from utilities import ToolResponse


def list_directory_content(path: str) -> ToolResponse:
    """Returns the contents of a directory"""
    """
    Args:
      path: Directory path (string), absolute or relative
    Returns:
      List the contents of a directory (list)
    """
    response = ToolResponse(
        status='success',
        message='',
        data=''
    )
    try:
        response.data = str(os.listdir(path))
        return response
    except Exception as e:
        response.status = 'error'
        response.message = repr(e)
        return response

def get_current_directory() -> ToolResponse:
    """Returns current directory"""
    """
    Args:
      No arguments
    Returns:
      Current directory (string)
    """
    return ToolResponse(
        status='success',
        message='',
        data=os.getcwd()
    )

def is_file(path: str) -> ToolResponse:
    """Check if a path is a file"""
    """
    Args:
      path. Path to the file (string)
    Returns:
      Current directory (string)
    """
    response = ToolResponse(
        status='success',
        message='',
        data=''
    )
    if not os.path.exists(path):
        response.status = 'error'
        response.message = 'Path not found'
    else:
        response.data = str(os.path.isfile(path))
    return response

def get_file_size(path: str) -> ToolResponse:
    """Get file size in bytes"""
    """
    Args:
      path. Path to the file (string)
    Returns:
      File size in bytes (integer) or error message
    """
    response = ToolResponse(
        status='success',
        message='',
        data=''
    )
    if not os.path.exists(path):
        response.status = 'error'
        response.message = 'Path not found'
    else:
        response.data = str(os.path.getsize(path))
    return response

def read_file(path: str) -> ToolResponse:
    """Read a file"""
    """
    Args:
      path. Path to the file (string)
    Returns:
      File content (string)
    """
    response = ToolResponse(
        status='success',
        message='',
        data=''
    )
    try:
        with open(path, 'r') as f:
            response.data = f.read()
        return response
    except Exception as e:
        response.status = 'error'
        response.message = repr(e)
        return response
    finally:
        f.close()

FILESYSTEM_TOOLS = {
    'list_directory_content': list_directory_content,
    'get_current_directory': get_current_directory,
    'is_file': is_file,
    'get_file_size': get_file_size,
    'read_file': read_file,
}