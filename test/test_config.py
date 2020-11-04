import base64
from typing import Tuple
from unittest.mock import Mock, patch

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


@pytest.fixture(scope='module')
def app_config():
    return {'app': {'port': 8000}, 'db': {'port': 5432, 'database': 'postgres'}}


@pytest.fixture(scope='module')
def loaded_config_file(app_config):
    tool_config = {'tool': {'poetry': {'name': 'NAME', 'version': 'VERSION'}}}
    return {**tool_config, **app_config}


@skip_for_integration
class TestEnvBackend:
    @patch.dict('os.environ', some_environ_raw(), clear=True)
    def test_get(self):
        env_backend = config.EnvBackend()
        assert env_backend.get('env_key') == 'env_value'
        assert 'env_key' in env_backend

    @patch.dict('os.environ', {'env_key': f'base64://{base64.b64encode(b"env_value").decode("utf-8")}'}, clear=True)
    def test_get_b64(self):
        env_backend = config.EnvBackend()
        assert env_backend.get('env_key') == 'env_value'
        assert 'env_key' in env_backend

    @patch.dict('os.environ', {}, clear=True)
    def test_get_error(self):
        env_backend = config.EnvBackend()
        assert 'env_key' not in env_backend
        with pytest.raises(KeyError):
            env_backend.get('env_key')


@skip_for_integration
class TestDefaultBackend:
    def test_get(self):
        default_backend = config.DefaultBackend(defaults={'env_key': 'env_value'})
        assert 'env_key' in default_backend
        assert default_backend.get('env_key') == 'env_value'

    def test_get_error(self):
        default_backend = config.DefaultBackend(defaults={})
        assert 'env_key' not in default_backend
        with pytest.raises(KeyError):
            default_backend.get('env_key')


@skip_for_integration
class TestTomlBackend:
    def test_get(self, some_config):
        toml_backend = config.TomlBackend('some_file')

        with patch.object(toml_backend, 'get_config', autospec=True) as mocked_get_config:
            mocked_get_config.return_value = some_config
            assert 'config_key' in toml_backend
            assert toml_backend.get('config_key') == some_config['config_key']

    def test_get_from_file_twice(self, some_config):
        toml_backend = config.TomlBackend('some_file')

        with patch.object(toml_backend, 'get_config', autospec=True) as mocked_get_config:
            mocked_get_config.return_value = some_config
            assert toml_backend.get('config_key') == some_config['config_key']
            assert toml_backend.get('config_key') == some_config['config_key']
            mocked_get_config.assert_called_once()

    def test_get_error(self):
        toml_backend = config.TomlBackend('some_file')
        with patch.object(toml_backend, 'get_config', autospec=True) as mocked_get_config:
            mocked_get_config.return_value = {}
            assert 'config_key' not in toml_backend
            with pytest.raises(KeyError):
                toml_backend.get('config_key')

    def test_contains_does_not_load_config_if_exists(self, some_config):
        toml_backend = config.TomlBackend('some_file')
        with patch.object(toml_backend, 'load_config', autospec=True) as mocked_load_config:
            toml_backend.config = some_config
            'config_key' in toml_backend
            mocked_load_config.assert_not_called()

    @patch('outcome.utils.config.toml', autospec=True)
    def test_get_without_aliases(self, mocked_toml, some_config, some_config_normalized):
        mocked_toml.load.return_value = some_config
        assert config.TomlBackend.get_config('some_file') == some_config_normalized

    @patch('outcome.utils.config.toml', autospec=True)
    def test_get_with_aliases(self, mocked_toml, some_config):
        mocked_toml.load.return_value = some_config

        aliases = {'config_key': 'my_config_key'}
        expected = {'MY_CONFIG_KEY': some_config['config_key']}

        assert config.TomlBackend.get_config('some_file', aliases) == expected

    def test_get_config_format(self, app_config):
        assert config.TomlBackend.flatten_keys(app_config) == {'APP_PORT': 8000, 'DB_PORT': 5432, 'DB_DATABASE': 'postgres'}

    def test_terminal_recursion_case(self):
        # The function should throw an error if a non-dict value is provided without a key
        with pytest.raises(Exception):
            config.TomlBackend.flatten_keys(value=1)


@skip_for_integration
class TestConfigGet:
    @patch.dict('os.environ', {'env_key': 'env_value'}, clear=True)
    def test_env_first(self):
        conf = config.Config('some_file', defaults={'env_key': 'default_value'})
        with patch.object(conf.backends[1], 'get', autospec=True) as mocked_get_from_file:
            with patch.object(conf.default_backend, 'get', autospec=True) as mocked_get_default:
                assert conf.get('env_key') == 'env_value'
                mocked_get_from_file.assert_not_called()
                mocked_get_default.assert_not_called()

    @patch.dict('os.environ', {}, clear=True)
    @patch('outcome.utils.config.DefaultBackend.get')
    @patch('outcome.utils.config.TomlBackend.get_config')
    def test_toml_second(self, mocked_get_config, mocked_get_default, some_config):
        mocked_get_config.return_value = some_config
        conf = config.Config('some_file', defaults={'env_key': 'default_value'})
        assert conf.get('config_key') == 'config_value'
        mocked_get_default.assert_not_called()

    @patch.dict('os.environ', {}, clear=True)
    @patch('outcome.utils.config.TomlBackend.__contains__', return_value=False)
    def test_default_last(self, mock_toml_contains):
        conf = config.Config('some_file', defaults={'other_key': 'default_value'})
        assert conf.get('other_key') == 'default_value'

    @patch.dict('os.environ', {}, clear=True)
    def test_get_default(self):
        conf = config.Config()

        assert conf.get('bad_key', 'default') == 'default'

    @patch.dict('os.environ', {}, clear=True)
    def test_get_default_none(self):
        conf = config.Config()

        assert conf.get('bad_key', None) is None

    def test_add_backend(self):
        conf = config.Config('some_file')

        class MyBackend(config.ConfigBackend):
            def get(self, key):
                return 'my_key'

            def __contains__(self, key):
                return True

        my_backend = MyBackend()

        assert len(conf.backends) == 2
        conf.add_backend(my_backend, 1)
        assert conf.backends[1] == my_backend
        assert len(conf.backends) == 3


@skip_for_integration
class TestAppConfig:
    @patch('outcome.utils.config.Config.get', autospec=True)
    @pytest.mark.parametrize('get_value', [('foo', 'foo'), ('foo-api-app', 'foo')])
    def test_config_get(self, mock_config_get: Mock, get_value: Tuple[str]):
        mock_config_get.return_value = get_value[0]
        conf = config.AppConfig()
        assert conf.get('APP_NAME') == get_value[1]
        assert conf.get('OTHER') == get_value[0]

    def test_config_get_with_default(self):
        conf = config.AppConfig()
        assert conf.get('APP_NAME', None) is None
        assert conf.get('APP_NAME', 'other-name') == 'other-name'
