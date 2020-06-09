"""Environment information."""

import os
from typing import cast

# The name of the environment variable that determines the environment
_env_key = 'APP_ENV'

_dev_key = 'dev'
_test_key = 'test'
_integration_key = 'integration'
_prod_key = 'production'


def env() -> str:
    if _env_key in os.environ:
        return cast(str, os.environ.get(_env_key)).strip()
    return _dev_key


def is_dev() -> bool:
    return env() == _dev_key


def is_test() -> bool:
    return env() == _test_key


def is_integration() -> bool:
    return env() == _integration_key


def is_prod() -> bool:
    return env() == _prod_key
