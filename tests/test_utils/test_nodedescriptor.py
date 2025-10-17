from __future__ import annotations

from orcaset import Node
from orcaset.utils import NodeDescriptor


class Leaf(Node["Composite"]):
    pass


class Composite(Node["Root"]):
    left: Leaf
    right: Leaf


class Root(Node[None]):
    main: Composite


def build_descriptor() -> NodeDescriptor:
    return NodeDescriptor.describe(Root)


def test_describe_builds_descriptor_tree():
    descriptor = build_descriptor()

    assert descriptor.cls_name == "Root"
    assert descriptor.attr_name is None
    assert len(descriptor.children) == 1

    [main_descriptor] = descriptor.children
    assert main_descriptor.attr_name == "main"
    assert main_descriptor.cls_name == "Composite"
    assert [c.attr_name for c in main_descriptor.children] == ["left", "right"]
    assert all(c.cls_name == "Leaf" for c in main_descriptor.children)


def test_flatten_returns_depth_first_post_order():
    descriptor = build_descriptor()

    flattened = [(depth, node.attr_name, node.cls_name) for depth, node in descriptor.flatten()]
    assert flattened == [
        (2, "left", "Leaf"),
        (2, "right", "Leaf"),
        (1, "main", "Composite"),
        (0, None, "Root"),
    ]


def test_dump_serializes_tree_structure():
    descriptor = build_descriptor()

    dump_result = descriptor.dump()
    assert dump_result["cls_name"] == "Root"
    assert dump_result["attr_name"] is None
    assert "class Root" in (dump_result["code"] or "")

    [main_dump] = dump_result["children"]
    assert main_dump["attr_name"] == "main"
    assert main_dump["cls_name"] == "Composite"
    assert [child["attr_name"] for child in main_dump["children"]] == ["left", "right"]


def test_pretty_print_includes_all_nodes():
    descriptor = build_descriptor()

    expected = "      left (Leaf)\n      right (Leaf)\n    main (Composite)\n  None (Root)\n"
    assert descriptor.pretty() == expected


def test_filter_returns_matching_descriptors():
    descriptor = build_descriptor()

    matching = descriptor.filter(lambda node: node.cls_name == "Leaf")
    assert sorted(node.attr_name for node in matching) == ["left", "right"]  # type: ignore
