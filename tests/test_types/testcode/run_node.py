from __future__ import annotations

from typing import Self

from orcaset.node import Node


# Node without dependencies
class UnsetNoneParent[P: None](Node[P]):
    pass


unp: None = (
    UnsetNoneParent().parent
)  # this will fail at runtime currently but should be typed to default `None`


# Two node vertical stack
class Parent[P: None](Node[P]):
    def __init__(self, item_child: "Child[Self]"):
        self.item_child = item_child


class Child[P: Parent](Node[P]):
    def __init__(self, value: int):
        self.value = value


p = Parent(item_child=Child[Parent](1))


# Incorrect parent type
class IncorrectParent[P: None](Node[P]):
    def __init__(self, item_b: Child[Self]):  # type: ignore[arg-type]
        self.item_b = item_b


class AnyNodeParent[P: None](Node[P]):
    def __init__(self, item_child: "Node[Self]"):
        self.item_child = item_child


AnyNodeParent[None](item_child=Child[AnyNodeParent](1))  # type: ignore[arg-type]

# Incorrect child type
p = Parent(item_child="not a child node")  # type: ignore[arg-type]


# Covariant parent type
class SubParent[P: None](Parent[P]):
    pass


sp = SubParent(item_child=Child[SubParent](1))


# Covariant child type
class SubChild[P: Parent](Child[P]):
    pass


p_subc = Parent(item_child=SubChild(1))


# Three node vertical stack
class A(Node):
    def __init__(self, item_b: "B[Self]"):
        self.item_b = item_b


class B[P: A](Node[P]):
    def __init__(self, item_c: "C[Self]"):
        self.item_c = item_c


class C[P: B](Node[P]):
    def __init__(self, value: int):
        self.value = value


a = A(item_b=B(item_c=C(1)))


# Test sibling nodes
class X[P](Node[P]):
    def __init__(self, item_y: "Y[Self]", item_z: "Z[Self]"):
        self.item_y = item_y
        self.item_z = item_z


class Y[P: X](Node[P]):
    def __init__(self, value: int):
        self.value = value


class Z[P: X](Node[P]):
    def get_y_value(self) -> int:
        return self.parent.item_y.value


x = X(item_y=Y(1), item_z=Z())
