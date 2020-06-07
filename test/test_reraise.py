from unittest.mock import Mock

import pytest
from outcome.utils import reraise


@pytest.fixture(scope='module')
def target_exception_class():
    class MyTargetException(Exception):
        pass

    return MyTargetException


@pytest.fixture(scope='module')
def second_target_exception_class():
    class MySecondTargetException(Exception):
        pass

    return MySecondTargetException


@pytest.fixture(scope='module')
def source_exception_class():
    class MySourceException(Exception):
        pass

    return MySourceException


@pytest.fixture(scope='module')
def second_source_exception_class():
    class MySecoundSourceException(Exception):
        pass

    return MySecoundSourceException


@pytest.fixture(scope='module')
def source_exception(source_exception_class):
    return source_exception_class()


@pytest.fixture(scope='module')
def source_thrower(source_exception):
    def thrower():
        raise source_exception

    return thrower


@pytest.fixture(scope='module')
def key_thrower():
    def thrower():
        raise KeyError

    return thrower


class TestDefaultMapper:
    def test_default_mapper(self, target_exception_class):
        ex = Exception()
        mapped = reraise.default_mapper(ex, target_exception_class)

        assert isinstance(mapped, target_exception_class)


class TestRemapException:
    def test_with_default_mapper(self, target_exception_class, source_exception_class, source_thrower):
        with pytest.raises(target_exception_class):
            with reraise.remap_exception(
                source_exception_class, target_exception_class, reraise.default_mapper,
            ):
                source_thrower()

    def test_passthrough_source_exception(self, target_exception_class, source_exception_class, key_thrower):
        with pytest.raises(KeyError):
            with reraise.remap_exception(
                source_exception_class, target_exception_class, reraise.default_mapper,
            ):
                key_thrower()

    def test_with_custom_mapper(
        self, target_exception_class, source_exception_class, source_exception, source_thrower,
    ):
        my_mapper = Mock()
        my_mapper.return_value = target_exception_class()

        with pytest.raises(target_exception_class):
            with reraise.remap_exception(source_exception_class, target_exception_class, my_mapper):
                source_thrower()

        my_mapper.assert_called_once_with(source_exception, target_exception_class)


class TestReraiseAs:
    def test_reraise_sync(self, source_exception_class, target_exception_class, source_thrower):
        @reraise.reraise_as(source_exception_class, target_exception_class)
        def decorated():
            source_thrower()

        with pytest.raises(source_exception_class):
            source_thrower()

        with pytest.raises(target_exception_class):
            decorated()

    def test_double_reraise(
        self, source_exception_class, second_source_exception_class, target_exception_class, second_target_exception_class,
    ):
        @reraise.reraise_as(second_source_exception_class, second_target_exception_class)
        @reraise.reraise_as(source_exception_class, target_exception_class)
        def decorated(exc):
            raise exc

        with pytest.raises(KeyError):
            decorated(KeyError)

        with pytest.raises(target_exception_class):
            decorated(source_exception_class)

        with pytest.raises(second_target_exception_class):
            decorated(second_source_exception_class)

    @pytest.mark.asyncio
    async def test_reraise_async(self, source_exception_class, target_exception_class, source_thrower):
        @reraise.reraise_as(source_exception_class, target_exception_class)
        async def decorated():
            source_thrower()

        with pytest.raises(source_exception_class):
            source_thrower()

        with pytest.raises(target_exception_class):
            await decorated()
