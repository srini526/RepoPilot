def add(a: float, b: float) -> float:
    return a + b


def divide(a: float, b: float) -> float:
    # Intentional bug: this should divide, not multiply.
    return a * b
