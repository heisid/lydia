from functools import reduce

def get_sum(number_array: list[int|float]):
    """Sum list of numbers"""
    """
    Args:
      number_array (list[int|float])
    Returns:
      The sum of numbers in the array
    """
    return sum(number_array)

def multiply(number_array: list[int|float]) -> int|float:
    """Multiply list of numbers"""
    """
    Args:
      number_array (list[int|float])
    Returns:
      The product of numbers in the array
    """
    if len(number_array) < 1:
        return 0
    return reduce(lambda x, y: x * y, number_array)

def divide(x: float, y: float) -> float:
    """Divide two numbers"""
    """
    Args:
      x: The first number (float)
      y: The second number (float)

    Returns:
      The result (float) of the division x / y
    """
    return x / y