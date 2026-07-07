from functools import reduce

from utilities import ToolResponse


def get_sum(number_array: list[int|float]) -> ToolResponse:
    """Sum list of numbers"""
    """
    Args:
      number_array (list[int|float])
    Returns:
      The sum of numbers in the array
    """
    result = sum(number_array)
    return ToolResponse(
        status='success',
        message='',
        data=str(result)
    )

def multiply(number_array: list[int|float]) -> ToolResponse:
    """Multiply list of numbers"""
    """
    Args:
      number_array (list[int|float])
    Returns:
      The product of numbers in the array
    """
    result = reduce(lambda x, y: x * y, number_array)
    return ToolResponse(
        status='success',
        message='',
        data=str(result)
    )

def divide(x: float, y: float) -> ToolResponse:
    """Divide two numbers"""
    """
    Args:
      x: The first number (float)
      y: The second number (float)

    Returns:
      The result (float) of the division x / y
    """
    response = ToolResponse(
        status='success',
        message='',
        data=''
    )
    if y == 0:
        response.status = 'error'
        response.message = 'Division by zero'
    else:
        response.data = str(x / y)
    return response

CALCULATOR_TOOLS = {
    'get_sum': get_sum,
    'multiply': multiply,
    'divide': divide,
}