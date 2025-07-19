from functools import wraps
from itertools import tee
from types import GeneratorType
from typing import Any, Callable, Iterator, Type

# Cache generators (without kwargs)
NODE_CACHENAME = "_node_cache"


Tee: Type[Iterator] = tee([], 1)[0].__class__


def cached_generator(func):
    """Decorator to cache a generator function."""
    @wraps(func)
    def wrapper(self, *args):
        # try to get the cache from the object, or create if doesn't exist
        node_cache = getattr(self, NODE_CACHENAME, None)
        if node_cache is None:
            node_cache = {}
            setattr(self, NODE_CACHENAME, node_cache)
        cache = node_cache.get(func.__name__, None)
        if cache is None:
            cache = {}
            node_cache[func.__name__] = cache
        # return tee'd generator
        if args not in cache:
            cache[args] = func(self, *args)
        if isinstance(cache[args], (GeneratorType, Tee)):
            cache[args], r = tee(cache[args])
            return r
        return cache[args]

    return wrapper


class TypedProperty:
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        else:
            yield from self.func(obj)


def typed_property[T](func: Callable[[Any], T]) -> T:
    """
    Wraps the built-in `property` decorator with type hints equal to the return type.
    Allows subclasses to override attributes with computed properties and pass Pyright type checks.
    """
    return TypedProperty(func)  # type: ignore[return-value]
