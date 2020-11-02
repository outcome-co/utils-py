import os
import pickle  # noqa: S403
from unittest.mock import mock_open, patch

import pytest
from dogpile.cache.api import NO_VALUE
from outcome.utils import cache

test = 'test'
test_ttl = 5


class TestAsyncCache:
    region = cache.get_cache_region()
    cache.configure_cache_region(region, settings={}, prefix=test)

    @region.cache_on_arguments()
    async def non_cacheable_async_func(self):
        return test

    @region.cache_on_arguments()
    @cache.cache_async
    async def cacheable_async_func(self):
        return test

    @pytest.mark.asyncio
    async def test_cache_async_success(self):
        f = self.cacheable_async_func()
        assert await f == test
        assert await f == test

    @pytest.mark.asyncio
    async def test_cache_async_fail(self):
        f = self.non_cacheable_async_func()
        assert await f == test
        with pytest.raises(RuntimeError):
            assert await f == test


def dummy_cached_fn(**kwargs):
    return True


class DummyClass:
    def dummy_cached_fn(self):
        return True


module = __name__


def test_key_generator_no_namespace():
    prefix = f'{module}:{dummy_cached_fn.__name__}|'
    generator = cache.cache_key_generator(namespace=None, fn=dummy_cached_fn)
    key = generator()

    assert key.startswith(prefix)


def test_key_generator_namespace():
    prefix = f'{module}:{dummy_cached_fn.__name__}|ns|'
    generator = cache.cache_key_generator(namespace='ns', fn=dummy_cached_fn)
    key = generator()

    assert key.startswith(prefix)


def test_key_generator_with_kwargs():
    generator = cache.cache_key_generator(namespace=None, fn=dummy_cached_fn)

    with pytest.raises(ValueError):
        generator(foo='bar')


def test_key_generator_strip_self():

    inst_a = DummyClass()
    inst_b = DummyClass()

    generator_a = cache.cache_key_generator(namespace=None, fn=inst_a.dummy_cached_fn)
    generator_b = cache.cache_key_generator(namespace=None, fn=inst_b.dummy_cached_fn)

    # Since the methods are bound to the instances, the first argument
    # is `self`, which should be different - we want to ensure we've
    # detected and removed the `self` arg from the key calculation
    assert generator_a(1) == generator_b(1)


class Timer(object):
    """This object will replace the timer in cachetools for tests, to be able to mock key expiration."""

    def __init__(self, *args):
        self.time = 0

    def __call__(self):
        return self.time

    def __enter__(self):
        return self.time

    def __exit__(self, *exc):
        pass

    def tick(self, value: int = test_ttl):
        self.time += value + 1


key = 'key'
value = 'value'


args_raw = {'maxsize': 100, 'ttl': test_ttl}
test_cache_path_raw = 'test/.cache/cache.pkl'
persisted_args_raw = dict(cache_path=test_cache_path_raw, **args_raw)


@pytest.fixture
def args():
    return args_raw


@pytest.fixture
def args_persisted(args, test_cache_path):
    args_persisted = args.copy()
    args_persisted.update({'cache_path': test_cache_path})
    return args_persisted


@pytest.fixture
def test_cache_path():
    return test_cache_path_raw


def key_generator(*args, **kwargs):
    def gen(*args, **kwargs):
        return key

    return gen


class TestTTLBackend:
    region = cache.get_cache_region()
    cache.configure_cache_region(region, settings={'test.memory.cache_path': test_cache_path_raw}, prefix=test)

    @region.cache_on_arguments(function_key_generator=key_generator)
    @cache.cache_async
    async def sample_cacheable_function(self, value):
        return value

    @patch('cachetools.ttl._Timer', Timer)
    @pytest.mark.asyncio
    async def test_backend_coroutine(self, fs, test_cache_path):  # noqa: WPS218 - many `assert`
        fs.create_file(test_cache_path)
        backend = self.region.backend

        co_cache = self.sample_cacheable_function(value)
        assert co_cache.done is False
        # If the coroutine hasn't been awaited, the cache file is empty,
        # but when we `get` on the `backend`, we'll get the coroutine from `coroutine_cache`
        assert os.path.getsize(test_cache_path) == 0
        assert backend.get(key)[0] == co_cache

        new_co_cache = self.sample_cacheable_function(value)
        assert new_co_cache == co_cache
        awaited = await new_co_cache
        assert new_co_cache.done is True
        # If the coroutine has been awaited, the key is in the cache file and the backend returns the awaited values
        with open(test_cache_path, 'rb') as f:
            cached_tests = pickle.load(f)  # noqa: S301 - pickle usage
        assert cached_tests.get(key)[0].result == awaited
        assert backend.get(key)[0].result == awaited

    @pytest.mark.parametrize(('args'), [args_raw, persisted_args_raw])
    @patch('cachetools.ttl._Timer', Timer)
    def test_backend(self, args, fs):
        backend = cache.TTLBackend(args)

        backend.set(key, value)
        assert backend.get(key) == value
        backend.cache.timer.tick()
        assert backend.get(key) == NO_VALUE

        backend.set(key, value)
        assert backend.get(key) == value
        backend.delete(key)
        assert backend.get(key) == NO_VALUE

    @patch('cachetools.ttl._Timer', Timer)
    def test_backend_retrieve_existing_cache(self, fs):
        args_raw.update({'cache_path': test_cache_path_raw})
        backend = cache.TTLBackend(args_raw)
        backend.set(key, value)
        assert backend.get(key) == value

        # We update the `args_raw` each time we need it to avoid `cache_path`
        # being removed from the arguments in `TTLBackend.__init__`
        args_raw.update({'cache_path': test_cache_path_raw})
        new_backend = cache.TTLBackend(args_raw)
        assert new_backend.get(key) == value

    @patch('builtins.open', new_callable=mock_open)
    @patch('outcome.utils.cache.pickle', autospec=True)
    @patch('outcome.utils.cache.Path', autospec=True)
    @patch('outcome.utils.cache.TTLCache', autospec=True)
    def test_persisted_new_cache(self, mock_ttlcache, mock_path, mock_pickle, mock_read, test_cache_path, args_persisted):
        backend = cache.TTLBackend(args_persisted)
        mock_read.assert_called_with(test_cache_path, 'rb')
        mock_pickle.load.assert_called_with(mock_read())
        assert backend.cache == mock_ttlcache.return_value

    @pytest.mark.parametrize(('side_effect'), [FileNotFoundError, EOFError])
    @patch('outcome.utils.cache.Path', autospec=True)
    @patch('outcome.utils.cache.TTLCache', autospec=True)
    def test_persisted_error_opening_file(self, mock_ttlcache, mock_path, args_persisted, side_effect):
        with patch('builtins.open', side_effect=side_effect):
            backend = cache.TTLBackend(args_persisted)
            assert backend.cache == mock_ttlcache.return_value
