from time import strftime, localtime

from utilities import ToolResponse


def get_current_time() -> ToolResponse:
    """Get current date and time"""
    """
    Args:
      no arguments
    Returns:
      Current date and time in the format "%Y-%m-%d %H:%M:%S"
    """
    return ToolResponse(
        status='success',
        message='',
        data=strftime("%Y-%m-%d %H:%M:%S", localtime())
    )

EXTRA_TOOLS = {
    'get_current_time': get_current_time,
}