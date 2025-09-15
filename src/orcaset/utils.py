import heapq
import inspect
from collections.abc import Generator, Iterable
from dataclasses import dataclass, field
from datetime import date
from itertools import dropwhile
from typing import Callable, Generic, TypeVar, get_origin, get_type_hints

from dateutil.relativedelta import relativedelta

from .node import Node


def merge_distinct(*iterables: Iterable):
    """
    Merges iterable results into a single sorted sequence without duplicates.

    Input iterables must be sorted. Input iterables are lazily evaluated and
    may be infinite generators.

    >>> merged = merge_distinct((i for i in [1, 3]), (i for i in range(5)))
    >>> list(merged)
    [0, 1, 2, 3, 4]
    """
    min_heap = heapq.merge(*iterables)
    last_yielded = None

    for next_value in min_heap:
        if next_value != last_yielded:
            yield next_value
            last_yielded = next_value


def date_series(
    start: date, freq: relativedelta, end_offset: relativedelta | None = None
) -> Generator[date, None, None]:
    """
    Returns a generator of dates starting from `start` and incrementing by `freq`.
    If `end_offset` is provided, the series will end at `start + end_offset`.

    Increments dates by adding `i * freq` to `start` for `i` in `0...n`.
    """
    if end_offset is not None:
        end = start + end_offset
    else:
        end = date.max

    i = 0
    current_date = start
    while current_date < end:
        yield current_date
        i += 1
        current_date = min(start + i * freq, end)


def yield_and_return[T](i: Iterable[T]) -> Generator[T, None, T]:
    """
    Yields elements from an iterable and returns the last element.

    This function is useful for yielding from historical data and continuing from the last element.
    Raises ValueError if the iterable is empty.

    Example:
    >>> def continuation(gen):
    ...     last = yield from yield_and_return(gen)
    ...     yield from (last + 1, last + 2)
    >>> list(continuation(range(3)))
    [0, 1, 2, 3, 4]
    """
    element = None
    for element in i:
        yield element

    if element is None:
        raise ValueError("Iterable must not be empty")

    return element


_T = TypeVar("_T")


class take_first_range(Generic[_T]):
    """
    Take the first range of consecutive items for which the predicate returns true.

    Example:
    >>> list(take_first_range(lambda c: c.isupper(), 'abCDefGHi'))
    ['C', 'D']
    """

    def __init__(
        self,
        iterable: Iterable[_T],
        predicate: Callable[[_T], bool],
    ):
        self.predicate = predicate
        self.iterable = dropwhile(lambda i: not self.predicate(i), iter(iterable))

    def __iter__(self):
        return self

    def __next__(self) -> _T:
        next_item = next(self.iterable)
        if self.predicate(next_item):
            return next_item
        else:
            raise StopIteration


@dataclass
class NodeDescriptor:
    cls_name: str
    attr_name: str | None = None
    children: list["NodeDescriptor"] = field(default_factory=list)
    code: str | None = None

    def flatten(self) -> list[tuple[int, "NodeDescriptor"]]:
        """Flattened structure of the node and its children."""

        def _flatten_recursive(node: NodeDescriptor, depth: int = 0) -> list[tuple[int, NodeDescriptor]]:
            result = []
            for c in node.children:
                result.extend(_flatten_recursive(c, depth + 1))
            result.append((depth, node))
            return result

        return _flatten_recursive(self)

    def dump(self):
        """Dump the structure to JSON format"""
        return {
            "cls_name": self.cls_name,
            "attr_name": self.attr_name,
            "children": [c.dump() for c in self.children],
            "code": self.code,
        }
    
    def pretty(self, indent: int = 0) -> str:
        """Pretty print the structure of the node."""
        indent_str = " " * indent
        result = ""
        for child in self.children:
            result += child.pretty(indent + 2)
        result = result + f"{indent_str}{self.attr_name} ({self.cls_name})\n"
        return result

    @classmethod
    def describe(cls, node: type[Node]):
        """
        Describe the structure of a Node and its children.
        """

        def _get_structure_recursive(node, attr_name: str | None = None):
            """
            Get the structure of a Node and its children.
            """
            descriptor: "NodeDescriptor" = cls(cls_name=node.__name__, attr_name=attr_name, code=inspect.getsource(node))
            hints = get_type_hints(node)

            for name, hint in hints.items():
                if name.startswith("_"):
                    continue
                if hasattr(hint, "__origin__"):
                    hint = get_origin(hint)

                try:
                    if issubclass(hint, Node):
                        child = _get_structure_recursive(hint, attr_name=name)
                        descriptor.children.append(child)
                except TypeError:
                    pass

            return descriptor

        return _get_structure_recursive(node)


def get_nodes(node: Node) -> list[Node]:
    """
    Get a node and all descendant nodes of a given node, recursively.

    Args:
        node (Node): The root node to start the search from.

    Returns:
        list[Node]: A list of all descendant nodes in depth-first order.
    """
    nodes = []
    for child in node.child_nodes:
        nodes.extend(get_nodes(child))
    nodes.append(node)
    return nodes