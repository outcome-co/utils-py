"""Caching functions for the Github Auth module."""

import asyncio
import hashlib
import pickle  # noqa: S403
import warnings
from pathlib import Path
from typing import Any, Dict

from cachetools import TTLCache
from dogpile.cache import CacheRegion, make_region, register_backend
from dogpile.cache.api import NO_VALUE, CacheBackend
from dogpile.cache.util import compat
from makefun import wraps


class CoroutineCache:
    # `CoroutineCache` allows to cache `async`functions.
    # As a coroutine can't be called twice, we need this to check when it's done or not.

    def __init__(self, co=None, result=None):
        self.co = co
        self.done = False
        self.result = result
        self.lock = asyncio.Lock()
        self.await_hooks = []

    def __await__(self):  # noqa: WPS611 - `yield` magic method usage
        # We catch the warnings here because this is a sync function
        # and we can't use `async with self.lock`
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=DeprecationWarning)
            with (yield from self.lock):
                if self.done:
                    return self.result
                self.result = yield from self.co.__await__()  # noqa: WPS609 - direct magic attribute usage
                self.done = True
                self.co = None
                # These hooks allow to apply functions that will run only when the coroutine is awaited
                for hook in self.await_hooks:
                    hook(self)
                return self.result

    def __reduce__(self):  # noqa: WPS603
        # This method is used by `pickle` to know how to serialize this object
        # Note this only works in the case the coroutine is already done
        # We need to return `(class_object, (tuple_of_arguments_to_pass_to_class_constructor))`
        return (self.__class__, (None, self.result))


def cache_async(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        r = f(*args, **kwargs)
        return CoroutineCache(r)

    return wrapped


def get_cache_region():
    return make_region(function_key_generator=cache_key_generator)


# This is a copy of the default key generator from dogpile, but
# with additional hashing to avoid using sensitive values as cache keys
def cache_key_generator(namespace, fn, to_str=str):
    if namespace is None:
        namespace = f'{fn.__module__}:{fn.__name__}'  # noqa: WPS609 - direct magic attribute usage
    else:
        namespace = f'{fn.__module__}:{fn.__name__}|{namespace}'  # noqa: WPS609 - direct magic attribute usage

    # Remove the `self` argument, since it'll always change
    fn_args = compat.inspect_getargspec(fn)
    has_self = fn_args[0] and fn_args[0][0] in {'self', 'cls'}

    def generate_key(*args, **kw):
        if kw:
            raise ValueError('The dogpile.cache default key creation function does not accept keyword arguments.')
        if has_self:
            args = args[1:]

        # Encode the args since they may be sensitive
        arg_key = hashlib.sha224(''.join(map(to_str, args)).encode('utf-8')).hexdigest()
        return f'{namespace}|{arg_key}'

    return generate_key


_default_cache_backend = 'memory'
# Expiration is dogpile's expiration TTL
_default_expiration = 300

_default_cache_size = 100

# The Cache TTL is the underlying backend TTL, which should
# be greater than dogpile's
# https://dogpilecache.sqlalchemy.org/en/latest/api.html#memcached-backends
_default_cache_ttl = _default_expiration * 1.5  # noqa: WPS432

# This gives us shortcuts to the actual modules
_backend_map = {
    _default_cache_backend: _default_cache_backend,
    'memcache': 'dogpile.cache.memcached',
}

# Default settings
_default_backend_args = {
    'memory': {'maxsize': _default_cache_size, 'ttl': _default_cache_ttl},
    'memcache': {'url': '127.0.0.1', 'distributed_lock': True},
}


def configure_cache_region(cache_region: CacheRegion, settings: Dict[str, Any], prefix: str):
    backend_key = f'{prefix}.backend'
    expiration_key = f'{prefix}.expiration'

    # Determine the backend
    backend = settings.get(backend_key, _default_cache_backend)
    expiration = int(settings.get(expiration_key, _default_expiration))

    # Find all the args that make sense for the backend
    backend_arg_prefix = f'{prefix}.{backend}.'
    backend_args = {
        k[len(backend_arg_prefix) :]: v for k, v in settings.items() if k.startswith(backend_arg_prefix)  # noqa: E203
    }

    resolved_args = {**_default_backend_args[backend], **backend_args}

    # Configure the cache region
    cache_region.configure(
        _backend_map[backend], expiration_time=expiration, arguments=resolved_args, replace_existing_backend=True,
    )


class TTLBackend(CacheBackend):
    _cache_path = 'cache_path'

    def __init__(self, arguments):

        self.persisted_cache_path = arguments.pop(self._cache_path, None)
        # This `coroutine_cache` will keep in memory all coroutines that have not already been awaited
        self.coroutine_cache = TTLCache(**arguments)
        # A potentially persisted cache for all items to keep in cache
        self.cache = TTLCache(**arguments)

        if self.persisted_cache_path:
            Path(self.persisted_cache_path).parent.mkdir(parents=True, exist_ok=True)

            try:
                # If we find a cache file and no argument was modified, then we retrieve the cache in file
                with open(self.persisted_cache_path, 'rb') as f:
                    pickled_cache = pickle.load(f)  # noqa: S301 - pickle usage
                    if all(getattr(self.cache, arg_key) == getattr(pickled_cache, arg_key) for arg_key in arguments.keys()):
                        self.cache = pickled_cache  # noqa: WPS220 - deep nesting

            except (FileNotFoundError, EOFError):
                pass

    def get(self, key):
        coroutine = self.coroutine_cache.get(key, None)
        if coroutine:
            return coroutine

        return self.cache.get(key, NO_VALUE)

    def coroutine_awaited(self, key, co):
        # This function will be called with when the coroutine is awaited.
        # It transfers the coroutine from the in memory coroutine cache to the potentially persisted general cache.
        self.set(key, self.coroutine_cache.pop(key, co))

    def set(self, key, value):  # noqa: WPS125, A003
        # In the case when the coroutine have not been awaited, we add it to the in memory coroutine cache
        if isinstance(value[0], CoroutineCache) and not value[0].done:
            value[0].await_hooks.append(lambda co: self.coroutine_awaited(key, co))
            self.coroutine_cache[key] = value
            return

        self.cache[key] = value
        if self.persisted_cache_path:
            self.persist_cache()

    def delete(self, key):
        self.coroutine_cache.pop(key, None)

        sentinel = object()
        if self.cache.pop(key, sentinel) is not sentinel and self.persisted_cache_path:
            self.persist_cache()

    def persist_cache(self):
        with open(self.persisted_cache_path, 'wb') as f:
            pickle.dump(self.cache, f)


register_backend(_default_cache_backend, __name__, TTLBackend.__name__)
