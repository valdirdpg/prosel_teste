import itertools

import math


def grouper(iterable, n):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def grouper_cycle(iterable, itens, n):
    it = itertools.cycle(iterable)
    for index in range(itens):
        yield tuple(itertools.islice(it, n))


def take(iterable, n):
    total = len(iterable)
    it = iter(iterable)
    chunk_size = math.ceil(total / n)
    for i in range(n):
        yield itertools.islice(it, chunk_size)
