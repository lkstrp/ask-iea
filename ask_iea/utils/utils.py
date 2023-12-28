"""Some utility functions."""


def batch(iterable: list, n: int) -> list:
    """Batch an iterable into chunks of size n.

    Args:
    ----
        iterable (list): List to be batched.
        n (int): Size of each batch.

    Returns:
    -------
        list: List of batches.
    """
    length = len(iterable)
    for ndx in range(0, length, n):
        yield iterable[ndx : min(ndx + n, length)]
