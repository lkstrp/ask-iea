"""TODO DOCSTRING."""


def batch(iterable: list, n: int) -> list:
    """TODO DOCSTRING."""
    length = len(iterable)
    for ndx in range(0, length, n):
        yield iterable[ndx : min(ndx + n, length)]
