from dataclasses import dataclass
from typing import ClassVar, Self, Type

import pytest

from orcaset import Node, cached_generator
from orcaset.node import NODE_CACHENAME


def test_single_node():
    class A(Node):
        def __init__(self, value: int):
            self.value = value

    a = A(value=1)
    assert a.value == 1
    with pytest.raises(AttributeError):
        a.parent


def test_setattr():
    node = Node()
    node.string = "animal"  # Can't set a property on a string, so this would raise an attribute error if `Node` tries to set `_struct_parent` on it.
    node.other = Node()
    assert node.other.parent is node  # type: ignore


def test_child_node_set():
    class A[P](Node[P]):
        def __init__(self, value: int):
            self.value = value

    class B(Node):
        def __init__(self, a: "A[Self]"):
            self.a = a

    b = B(A(value=1))
    assert b.a.value == 1
    assert b.a.parent is b
    with pytest.raises(AttributeError):
        b.parent


def test_cache_clear():
    class A(Node):
        @cached_generator
        def numbers(self):
            yield from (1,)

    a = A()
    _ = list(a.numbers())
    assert len(a._node_cache) > 0
    a.cache_clear()
    assert len(a._node_cache) == 0


def test_node_context_manager():
    @dataclass
    class A[P: A](Node[P]):
        value: str
        child: Node[Self]

        @cached_generator
        def values(self):
            yield from [self.value]

    @dataclass
    class B[P: A](Node[P]):
        parent_type: ClassVar[Type[A]] = A
        value: str

        @cached_generator
        def values(self):
            yield from [self.value]

    # A > A > B
    top = A(value="top", child=A[A](value="mid", child=B[A](value="bottom")))
    mid: A = top.child  # pyright: ignore[reportAssignmentType]
    bot: B = mid.child  # pyright: ignore[reportAssignmentType]
    # populate caches
    _ = list(top.values())
    _ = list(mid.values())
    _ = list(bot.values())
    assert len(top._node_cache) > 0
    assert len(mid._node_cache) > 0
    assert len(bot._node_cache) > 0

    with mid as mid_copy:
        assert mid_copy.parent == top
        assert mid_copy == mid
        assert mid_copy.child == bot
        # Cache is cleared (actually removed) in the deep copy process
        assert getattr(mid_copy.parent, NODE_CACHENAME, None) is None
        assert getattr(mid_copy, NODE_CACHENAME, None) is None
        assert getattr(mid_copy.child, NODE_CACHENAME, None) is None

    # Confirm any errors are propagated out of the context manager
    with pytest.raises(ZeroDivisionError):
        with mid as _:
            _ = 1 / 0


def test_get_state():
    @dataclass
    class A[P: A](Node[P]):
        value: str
        child: Node[Self]

        @cached_generator
        def values(self):
            yield from [self.value]

    @dataclass
    class B[P: A](Node[P]):
        parent_type: ClassVar[Type[A]] = A
        value: str

        @cached_generator
        def values(self):
            yield from [self.value]

    # A > A > B
    top = A(value="top", child=A[A](value="mid", child=B[A](value="bottom")))
    mid: A = top.child  # pyright: ignore[reportAssignmentType]
    bot: B = mid.child  # pyright: ignore[reportAssignmentType]
    # populate caches
    _ = list(top.values())
    _ = list(mid.values())
    _ = list(bot.values())

    assert top.__getstate__() == {"value": "top", "child": mid}
    assert mid.__getstate__() == {
        "value": "mid",
        "child": bot,
        "__orig_class__": A[A],
        "_parent": top,
    }
    assert bot.__getstate__() == {
        "value": "bottom",
        "__orig_class__": B[A],
        "_parent": mid,
    }


def test_child_nodes():
    @dataclass
    class A[P: A](Node[P]):
        value: str
        child: Node[Self]

        @cached_generator
        def values(self):
            yield from [self.value]

    @dataclass
    class B[P: A](Node[P]):
        parent_type: ClassVar[Type[A]] = A
        value: str

        @cached_generator
        def values(self):
            yield from [self.value]
    

    assert B[A](value="any").child_nodes == []  # Node without children
    a = A(value="top", child=A[A](value="mid", child=B[A](value="bottom")))
    assert a.child_nodes == [a.child]
    assert a.child_nodes[0].child_nodes == [a.child.child]  # type: ignore
    