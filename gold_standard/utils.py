#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""Generic utility functions."""

from collections.abc import Iterator
import itertools
from typing import TypeVar


T = TypeVar('T')
U = TypeVar('U')


def split_gen(it: Iterator[tuple[T, U]]) -> tuple[Iterator[T], Iterator[U]]:
    """
    Splits the iterator _it_ of tuples into two.

    From https://stackoverflow.com/questions/28030095/.
    """
    it_a, it_b = itertools.tee(it, 2)
    return (a for a, _ in it_a), (b for _, b in it_b)
