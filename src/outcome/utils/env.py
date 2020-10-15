"""Environment information."""

import os
import traceback
from typing import cast

import requests

# The name of the environment variable that determines the environment
_env_key = 'APP_ENV'

_dev_key = 'dev'
_test_key = 'test'
_integration_key = 'integration'
_e2e_key = 'e2e'
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


def is_e2e() -> bool:
    return env() == _e2e_key


def is_prod() -> bool:
    return env() == _prod_key


_is_google_cloud = None


def is_google_cloud() -> bool:
    """GCP machines have access to an internal metadata server - if the server is not available, you're not on GCP.

    https://cloud.google.com/compute/docs/storing-retrieving-metadata#querying

    Returns:
        bool: True if running on GCP.
    """
    global _is_google_cloud

    if _is_google_cloud is not None:
        return _is_google_cloud

    # There are a LOT of linting exceptions in this function, as WPS **really** doesn't like
    # global variables, but the `_is_google_cloud` variable, by definition, contains
    # global immutable state (the module is either running on GCP or it isn't, that's not going
    # to change), we just don't know the state until we check the first time.

    try:
        response = requests.get(
            'http://metadata.google.internal/', timeout=1.5, headers={'Metadata-Flavor': 'Google'},  # noqa: WPS432
        )
        _is_google_cloud = response.status_code == 200  # noqa: WPS432,WPS122,WPS442
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        _is_google_cloud = False  # noqa: WPS432,WPS121,WPS122,WPS442

    return _is_google_cloud  # noqa: WPS432,WPS121,WPS122,WPS442,R504


# We don't try to test this
def is_ipython() -> bool:  # pragma: no cover
    try:
        __IPYTHON__
        return True
    except NameError:
        return False


# This isn't an exact science, but we can try!
def is_pytest() -> bool:
    # Shortcut that only works when you're actually in a test
    if 'PYTEST_CURRENT_TEST' in os.environ:
        return True

    for frame in traceback.extract_stack():  # pragma: no cover
        # The pytest can appear as `site-packages/_pytest` or `site-packages/pytest`
        if 'site-packages' in frame.filename and 'pytest' in frame.filename:
            return True

    return False  # pragma: no cover
