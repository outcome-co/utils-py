"""Pre-condition check decorator."""

from asyncio import iscoroutinefunction
from typing import Callable

from asgiref.sync import async_to_sync
from makefun import wraps


def pre_condition(pre_condition_fn: Callable[..., bool]):  # noqa: WPS231,WPS212
    """Executes a pre-condition function over the provided arguments before calling the decorated function.

    Automatically handles async pre-condition functions and wrapped functions.

    Exceptions raised in the pre-condition will pass through the decorator.
    If the pre-condition returns False, an UnmetPreconditionException will be raised.

    Args:
        pre_condition_fn (Callable[..., bool]): The pre-condition function.

    Raises:
        UnmetPreconditionException: If the pre-condition fails.

    Returns:
        Callable: The wrapped function
    """

    def pre_condition_decorator(fn: Callable):  # noqa: WPS231
        if iscoroutinefunction(fn) and iscoroutinefunction(pre_condition_fn):

            @wraps(fn)
            async def with_precondition(*args, **kwargs):
                if not await pre_condition_fn(*args, **kwargs):
                    raise UnmetPreconditionException
                return await fn(*args, **kwargs)

        elif iscoroutinefunction(fn):

            @wraps(fn)
            async def with_precondition(*args, **kwargs):  # noqa: WPS440
                if not pre_condition_fn(*args, **kwargs):
                    raise UnmetPreconditionException
                return await fn(*args, **kwargs)

        elif iscoroutinefunction(pre_condition_fn):

            @wraps(fn)
            def with_precondition(*args, **kwargs):  # noqa: WPS440
                # Use async_to_sync to call an async from a sync: https://www.aeracode.org/2018/02/19/python-async-simplified/
                if not async_to_sync(pre_condition_fn)(*args, **kwargs):
                    raise UnmetPreconditionException
                return fn(*args, **kwargs)

        else:

            @wraps(fn)
            def with_precondition(*args, **kwargs):  # noqa: WPS440
                if not pre_condition_fn(*args, **kwargs):
                    raise UnmetPreconditionException
                return fn(*args, **kwargs)

        return with_precondition

    return pre_condition_decorator


class UnmetPreconditionException(Exception):
    ...
