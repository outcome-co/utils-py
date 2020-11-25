from unittest.mock import Mock, patch

import pytest
import requests
from outcome.utils import env


@pytest.fixture(autouse=True)
def reset_is_google_state():
    env._is_google_cloud = None


class TestEnv:
    @patch.dict('os.environ', {'APP_ENV': 'env_for_unittest'})
    def test_env_in_os_environ(self):
        assert env.env() == 'env_for_unittest'

    @patch.dict('os.environ', {'APP_ENV': ' dev '})
    def test_env_with_white_space(self):
        assert env.env() == 'dev'
        assert env.is_dev()

    # We use clear=True to empty the dict
    @patch.dict('os.environ', {}, clear=True)
    def test_env_default_value(self):
        assert env.is_dev()
        assert not env.is_prod()
        assert not env.is_test()
        assert not env.is_integration()
        assert not env.is_e2e()

    @patch.dict('os.environ', {'APP_ENV': 'dev'})
    def test_is_dev(self):
        assert env.is_dev()
        assert not env.is_prod()
        assert not env.is_test()
        assert not env.is_integration()
        assert not env.is_e2e()

    @patch.dict('os.environ', {'APP_ENV': 'test'})
    def test_is_test(self):
        assert not env.is_dev()
        assert not env.is_prod()
        assert env.is_test()
        assert not env.is_integration()
        assert not env.is_e2e()

    @patch.dict('os.environ', {'APP_ENV': 'integration'})
    def test_is_integration(self):
        assert not env.is_dev()
        assert not env.is_prod()
        assert not env.is_test()
        assert env.is_integration()
        assert not env.is_e2e()

    @patch.dict('os.environ', {'APP_ENV': 'e2e'})
    def test_is_e2e(self):
        assert not env.is_dev()
        assert not env.is_prod()
        assert not env.is_test()
        assert not env.is_integration()
        assert env.is_e2e()

    @patch.dict('os.environ', {'APP_ENV': 'production'})
    def test_is_prod(self):
        assert not env.is_dev()
        assert env.is_prod()
        assert not env.is_test()
        assert not env.is_integration()
        assert not env.is_e2e()

    @patch('outcome.utils.env.requests.get', autospec=True)
    def test_is_google_cloud(self, mocked_requests_get):
        mocked_response = Mock()
        mocked_response.status_code = 200
        mocked_requests_get.return_value = mocked_response
        assert env.is_google_cloud()

    @patch('outcome.utils.env.requests.get', autospec=True)
    def test_is_google_cloud_cached(self, mocked_requests_get: Mock):
        mocked_response = Mock()
        mocked_response.status_code = 200
        mocked_requests_get.return_value = mocked_response

        assert env.is_google_cloud()
        assert env.is_google_cloud()
        mocked_requests_get.assert_called_once()

    @patch('outcome.utils.env.requests.get', autospec=True)
    def test_is_google_cloud_404(self, mocked_requests_get):  # noqa: WPS114
        mocked_response = Mock()
        mocked_response.status_code = 404
        mocked_requests_get.return_value = mocked_response
        assert not env.is_google_cloud()

    @patch('outcome.utils.env.requests.get', autospec=True)
    @pytest.mark.parametrize('exception', [requests.exceptions.Timeout, requests.exceptions.ConnectionError])
    def test_is_google_cloud_exception(self, mocked_requests_get, exception):
        mocked_requests_get.side_effect = exception
        assert not env.is_google_cloud()

    def test_is_pytest(self):
        assert env.is_pytest()

    @patch.dict('os.environ', {}, clear=True)
    def test_is_pytest_no_env(self):
        assert env.is_pytest()

    @patch.dict('os.environ', {}, clear=True)
    def test_is_not_ipython(self):
        assert not env.is_ipython()

    @patch.dict('os.environ', {}, clear=True)
    def test_is_ipython(self):
        # Mimic iPython
        __builtins__['get_ipython'] = lambda: True

        assert env.is_ipython()

        del __builtins__['get_ipython']

    @patch.dict('os.environ', {'__IPYTHON__': '1'}, clear=True)
    def test_is_ipython_env(self):
        assert env.is_ipython()
