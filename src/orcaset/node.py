from copy import deepcopy
from typing import Any

from .decorators import NODE_CACHENAME


class Node[P]:
    _parent: P
    """
    Base class for nodes. Generic with respect to its parent type.
    """

    @property
    def parent(self) -> P:
        """Return the parent of the node."""
        try:
            return self._parent
        except AttributeError:
            raise AttributeError(
                f"Must set parent on {self.__class__.__name__} before accessing it."
            )

    @parent.setter
    def parent(self, parent: P):
        self._parent = parent

    @property
    def child_nodes(self) -> list["Node"]:
        """
        Immediate children of the node.

        Return a list of all attributes (excluding the `parent`) that are instances of `Node`.
        """
        children: list["Node"] = []
        for k, v in self.__dict__.items():
            if k != "_parent" and isinstance(v, Node):
                children.append(v)
        return children

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name != "_parent" and name != "parent" and isinstance(value, Node):
            value.parent = self

    def cache_clear(self) -> None:
        """Clear cache of the object and any children."""
        self._node_cache = {}

        for k, v in self.__dict__.items():
            try:
                if k != "_parent" and isinstance(v, Node):
                    v.cache_clear()
            except AttributeError:
                pass

    def __enter__(self):
        """Context manager returns a deep copy of the entire tree with a cleared cache."""
        # Cache is cleared (removed) for the entire tree since it is dropped in `__getstate__` which `deepcopy` uses.
        new_node = deepcopy(self)
        return new_node

    def __exit__(self, exc_type, exc_value, traceback):
        return False  # Propgate any errors

    def __getstate__(self):
        # Generator caching is not picklable since it may contain a generator,
        # so it is removed from state. This also removes the cache from `deepcopy`.
        state = super().__getstate__()
        # remove cache
        state_copy = {k: v for k, v in state.items() if k != NODE_CACHENAME}  # pyright: ignore[reportAttributeAccessIssue]
        return state_copy
