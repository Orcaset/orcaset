from orcaset import Node
from orcaset.utils import get_nodes


class TestGetNodes:
    def test_single_node_no_children(self):
        """Test get_nodes on a node with no children."""
        node = Node()
        result = get_nodes(node)
        assert result == [node]

    def test_single_child(self):
        """Test get_nodes on a node with one child."""
        class ChildNode(Node):
            pass

        parent = Node()
        child = ChildNode()
        parent.child = child

        result = get_nodes(parent)
        assert result == [child, parent]

    def test_multiple_children(self):
        """Test get_nodes on a node with multiple children."""
        class ChildNode(Node):
            pass

        parent = Node()
        child1 = ChildNode()
        child2 = ChildNode()
        parent.child1 = child1
        parent.child2 = child2

        result = get_nodes(parent)
        assert result == [child1, child2, parent]

    def test_nested_children(self):
        """Test get_nodes on a node with nested children."""
        class ChildNode(Node):
            pass

        class GrandChildNode(Node):
            pass

        root = Node()
        child = ChildNode()
        grandchild = GrandChildNode()
        root.child = child
        child.grandchild = grandchild

        result = get_nodes(root)
        assert result == [grandchild, child, root]

    def test_deeply_nested_children(self):
        """Test get_nodes on a deeply nested tree."""
        class Level1Node(Node):
            pass

        class Level2Node(Node):
            pass

        class Level3Node(Node):
            pass

        root = Node()
        level1 = Level1Node()
        level2 = Level2Node()
        level3 = Level3Node()

        root.level1 = level1
        level1.level2 = level2
        level2.level3 = level3

        result = get_nodes(root)
        assert result == [level3, level2, level1, root]

    def test_multiple_branches(self):
        """Test get_nodes on a node with multiple branches."""
        class BranchNode(Node):
            pass

        root = Node()
        branch1 = BranchNode()
        branch2 = BranchNode()
        leaf1 = BranchNode()
        leaf2 = BranchNode()

        root.branch1 = branch1
        root.branch2 = branch2
        branch1.leaf1 = leaf1
        branch2.leaf2 = leaf2

        result = get_nodes(root)
        print(result)
        assert result == [leaf1, branch1, leaf2, branch2, root]

    def test_empty_tree(self):
        """Test get_nodes on an empty tree (just root)."""
        root = Node()
        result = get_nodes(root)
        assert result == [root]

    def test_node_with_non_node_attributes(self):
        """Test get_nodes ignores non-Node attributes."""
        class ChildNode(Node):
            pass

        root = Node()
        child = ChildNode()
        root.child = child
        root.value = 42  # Non-Node attribute
        root.name = "test"  # Non-Node attribute

        result = get_nodes(root)
        assert result == [child, root]
