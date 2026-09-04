"""
AI-generated math utility functions that were never referenced or tested.
Typical AI slop leftover from iterative prompting sessions.
"""

def square(x: float) -> float:
    return x * x

def cube(x: float) -> float:
    return x * x * x

def average(*numbers: float) -> float:
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)

def factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * factorial(n - 1)
