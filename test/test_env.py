from unittest.mock import patch

from outcome.utils import env


class TestEnv:
    @patch.dict('os.environ', {'APP_ENV': 'env_for_unittest'})
    def test_env_in_os_environ(self):
        assert env.env() == 'env_for_unittest'

    # We use clear=True to empty the dict
    @patch.dict('os.environ', {}, clear=True)
    def test_env_default_value(self):
        assert env.is_dev()
        assert not env.is_prod()
        assert not env.is_test()
        assert not env.is_integration()

    @patch.dict('os.environ', {'APP_ENV': 'dev'})
    def test_is_dev(self):
        assert env.is_dev()
        assert not env.is_prod()
        assert not env.is_test()
        assert not env.is_integration()

    @patch.dict('os.environ', {'APP_ENV': 'test'})
    def test_is_test(self):
        assert not env.is_dev()
        assert not env.is_prod()
        assert env.is_test()
        assert not env.is_integration()

    @patch.dict('os.environ', {'APP_ENV': 'integration'})
    def test_is_integration(self):
        assert not env.is_dev()
        assert not env.is_prod()
        assert not env.is_test()
        assert env.is_integration()

    @patch.dict('os.environ', {'APP_ENV': 'production'})
    def test_is_prod(self):
        assert not env.is_dev()
        assert env.is_prod()
        assert not env.is_test()
        assert not env.is_integration()
