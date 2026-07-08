from utilities import ToolResponse
import requests


HEADERS = {
    'User-Agent': 'MeongOrenBot/1.0 (+https://kucing-oren.com/)'
}

def web_search(search_term: str) -> ToolResponse:
    """Search on the internet (search.kucing-oren.com)"""
    """
    Args:
       search_term: The search term (string)
    Returns:
      Search result (json)
    """
    response = ToolResponse(
        status='success',
        message='',
        data=''
    )
    try:
        r = requests.get(f'https://search.kucing-oren.com/api/v1/web?s={search_term}')
        response.data = r.text
        return response
    except Exception as e:
        response.status = 'error'
        response.message = str(e)
        return response

def goto_url(url: str) -> ToolResponse:
    """Visit any URL"""
    """
    Args:
       url: URL to visit (string)
    Returns:
      raw HTTP GET response from url (string)
    """
    response = ToolResponse(
        status='success',
        message='',
        data=''
    )
    try:
        r = requests.get(url, headers=HEADERS)
        response.data = r.text
        return response
    except Exception as e:
        response.status = 'error'
        response.message = str(e)
        return response

WEB_TOOLS = {
    'web_search': web_search,
    'goto_url': goto_url,
}