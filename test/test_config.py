from unittest.mock import patch

import pytest
from outcome.devkit.test_helpers import skip_for_integration
from outcome.utils import config


# We separate this into a non-fixture function
# to be able to use it in the @patch.dict
# decorator
def some_environ_raw():
    return {'env_key': 'env_value'}


@pytest.fixture(scope='module')
def some_config():
    return {'config_key': 'config_value'}


@pytest.fixture(scope='module')
def some_config_normalized(some_config):
    return {k.upper(): v for k, v in some_config.items()}


@skip_for_integration
class TestGet:
    @patch.dict('os.environ', some_environ_raw(), clear=True)
    def test_get_key_in_os_environ(self):
        conf = config.Config()
        assert conf.get('env_key') == 'env_value'

    @patch.dict('os.environ', {}, clear=True)
    def test_get_key_not_in_os_environ(self):
        conf = config.Config()
        with pytest.raises(KeyError):
            conf.get('env_key')

    @patch.dict('os.environ', {}, clear=True)
    def test_get_from_file(self, some_config):
        conf = config.Config('some_file')

        with patch.object(conf, 'get_config', autospec=True) as mocked_get_config:
            mocked_get_config.return_value = some_config
            assert conf.get('config_key') == some_config['config_key']

    @patch.dict('os.environ', {}, clear=True)
    def test_get_from_file_twice(self, some_config):
        conf = config.Config('some_file')

        with patch.object(conf, 'get_config', autospec=True) as mocked_get_config:
            mocked_get_config.return_value = some_config
            assert conf.get('config_key') == some_config['config_key']
            assert conf.get('config_key') == some_config['config_key']
            mocked_get_config.assert_called_once()


@skip_for_integration
class TestGetConfig:
    @patch('outcome.utils.config.toml', autospec=True)
    def test_get_without_aliases(self, mocked_toml, some_config, some_config_normalized):
        mocked_toml.load.return_value = some_config
        assert config.Config.get_config('some_file') == some_config_normalized

    @patch('outcome.utils.config.toml', autospec=True)
    def test_get_with_aliases(self, mocked_toml, some_config):
        mocked_toml.load.return_value = some_config

        aliases = {'config_key': 'my_config_key'}
        expected = {'MY_CONFIG_KEY': some_config['config_key']}

        assert config.Config.get_config('some_file', aliases) == expected


@pytest.fixture(scope='module')
def app_config():
    return {'app': {'port': 8000}, 'db': {'port': 5432, 'database': 'postgres'}}


@pytest.fixture(scope='module')
def loaded_config_file(app_config):
    tool_config = {'tool': {'poetry': {'name': 'NAME', 'version': 'VERSION'}}}
    return {**tool_config, **app_config}


@skip_for_integration
class TestFlattenKeys:
    def test_get_config_format(self, app_config):
        assert config.Config.flatten_keys(app_config) == {'APP_PORT': 8000, 'DB_PORT': 5432, 'DB_DATABASE': 'postgres'}

    def test_terminal_recursion_case(self):
        # The function should throw an error if a non-dict value is provided without a key
        with pytest.raises(Exception):
            config.Config.flatten_keys(value=1)
