import heapq
import inspect
from collections.abc import Generator, Iterable
from dataclasses import dataclass, field
from datetime import date
from itertools import dropwhile
from typing import Callable, Generic, TypeVar, get_origin, get_type_hints, overload

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


@overload
def date_series(start: date, freq: relativedelta, end: date | None = None) -> Generator[date, None, None]: ...
@overload
def date_series(start: date, freq: relativedelta, end: relativedelta | None = None) -> Generator[date, None, None]: ...
def date_series(
    start: date, freq: relativedelta, end: date | relativedelta | None = None
) -> Generator[date, None, None]:
    """
    Returns a generator of dates starting from `start` and incrementing by `freq`.
    If `end` is provided, the series will end at the specified date or `start + end` if `end` is a `relativedelta`.
    Returns an infinite generator of dates if `end` is not provided.

    Increments dates by adding `i * freq` to `start` for `i` in `0...n`.
    """
    if end is None:
        end = date.max
    elif isinstance(end, relativedelta):
        end = start + end

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
    node: type[Node]
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

    def __repr__(self) -> str:
        return self.dump().__repr__()

    def pretty(self, indent: int = 2) -> str:
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
            descriptor: "NodeDescriptor" = cls(
                node, cls_name=node.__name__, attr_name=attr_name, code=inspect.getsource(node)
            )
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

    def filter(self, predicate: Callable[["NodeDescriptor"], bool]) -> list["NodeDescriptor"]:
        """
        Filter the node and its children based on a predicate.
        Returns a list of NodeDescriptors that match the predicate.
        """
        result = []
        if predicate(self):
            result.append(self)
        for child in self.children:
            result.extend(child.filter(predicate))
        return result


def get_nodes(node: Node, ignore: Callable[[Node], bool] | None = None) -> list[Node]:
    """
    Depth-first search for a node and all descendant nodes of a given node, recursively.

    Skips nodes for which the `ignore` function returns True. Continues to search children of ignored nodes.

    Args:
        node (Node): The root node to start the search from.
        ignore (Callable[[Node], bool] | None): A function that determines whether to skip a node.

    Returns:
        list[Node]: A list of all descendant nodes in depth-first order.
    """
    nodes = []
    for child in node.child_nodes:
        nodes.extend(get_nodes(child, ignore=ignore))
    if ignore is None or not ignore(node):
        nodes.append(node)
    return nodes
