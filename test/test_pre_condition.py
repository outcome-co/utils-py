from unittest.mock import Mock

import pytest
from outcome.utils.pre_condition import UnmetPreconditionException, pre_condition


@pytest.fixture(params=[True, False])
def result(request):
    return request.param


def test_preco(result):
    def check():
        return result

    @pre_condition(check)
    def fn():
        ...

    if result:
        fn()
    else:
        with pytest.raises(UnmetPreconditionException):
            fn()


def test_preco_async_check(result):
    async def check():
        return result

    @pre_condition(check)
    def fn():
        ...

    if result:
        fn()
    else:
        with pytest.raises(UnmetPreconditionException):
            fn()


@pytest.mark.asyncio
async def test_preco_async_fn(result):
    def check():
        return result

    @pre_condition(check)
    async def fn():
        ...

    if result:
        await fn()
    else:
        with pytest.raises(UnmetPreconditionException):
            await fn()


@pytest.mark.asyncio
async def test_preco_async_both(result):
    async def check():
        return result

    @pre_condition(check)
    async def fn():
        ...

    if result:
        await fn()
    else:
        with pytest.raises(UnmetPreconditionException):
            await fn()


def test_pass_vars():
    t_args = (1, 2)
    t_kwargs = {
        'param': 'foo',
    }

    check = Mock()
    inner = Mock()

    @pre_condition(check)
    def fn(*args, **kwargs):
        inner(*args, **kwargs)

    fn(*t_args, **t_kwargs)

    check.assert_called_once_with(*t_args, **t_kwargs)
    inner.assert_called_once_with(*t_args, **t_kwargs)


def test_pass_exceptions():
    class MyCustomException(Exception):
        ...

    def check():
        raise MyCustomException

    @pre_condition(check)
    def fn():
        ...

    with pytest.raises(MyCustomException):
        fn()
