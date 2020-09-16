import os
from pathlib import Path
from unittest.mock import patch

import pytest
from outcome.utils.config import Config, FeatureException, FeatureSet, is_valid_feature_name

valid_feature_names_raw = [
    'feature',
    'my.feature',
    'my_feature',
]

invalid_feature_names_raw = [
    '_feature',
    'MY_FEATURE',
    '.fea',
    'feature_',
]


@pytest.fixture(params=valid_feature_names_raw)
def valid_feature_name(request):
    return request.param


@pytest.fixture(params=invalid_feature_names_raw)
def invalid_feature_name(request):
    return request.param


def test_valid_feature_names(valid_feature_name):
    assert is_valid_feature_name(valid_feature_name)


def test_invalid_feature_names(invalid_feature_name):
    assert not is_valid_feature_name(invalid_feature_name)


@pytest.fixture()
def feature_set():
    fs = FeatureSet()

    fs.register_feature('my_active_feature', default=True)
    fs.register_feature('my_inactive_feature', default=False)

    return fs


def test_invalid_registration():
    fs = FeatureSet()
    with pytest.raises(FeatureException):
        fs.register_feature('_invalid')


def test_duplicate_registration():
    fs = FeatureSet()
    fs.register_feature('feat')

    with pytest.raises(FeatureException):
        fs.register_feature('feat')


@patch.dict(os.environ, {}, clear=True)
class TestFeatureSetFromDefaults:
    def test_unknown_feature(self, feature_set: FeatureSet):
        with pytest.raises(FeatureException):
            feature_set.is_active('unknown_feature')

    def test_default_active_feature(self, feature_set: FeatureSet):
        assert feature_set.is_active('my_active_feature')

    def test_default_inactive_feature(self, feature_set: FeatureSet):
        assert not feature_set.is_active('my_inactive_feature')


@patch.dict(os.environ, {'WITH_FEAT_MY_ACTIVE_FEATURE': '0', 'WITH_FEAT_MY_INACTIVE_FEATURE': '1'}, clear=True)
class TestFeatureSetFromEnv:
    def test_unknown_feature(self, feature_set: FeatureSet):
        with pytest.raises(FeatureException):
            feature_set.is_active('unknown_feature')

    def test_deactivated_feature(self, feature_set: FeatureSet):
        assert not feature_set.is_active('my_active_feature')

    def test_activated_feature(self, feature_set: FeatureSet):
        assert feature_set.is_active('my_inactive_feature')


fixture_file = Path(Path(__file__).parent, 'fixtures', 'sample.toml')


@pytest.fixture()
def config():
    return Config(path=fixture_file)


@pytest.fixture()
def feature_set_with_config(config: Config):
    config.feature_set.register_feature('my_active_feature')
    config.feature_set.register_feature('my_inactive_feature')
    return config.feature_set


@patch.dict(os.environ, {}, clear=True)
class TestFeatureSetFromPyProject:
    def test_unknown_feature(self, feature_set_with_config: FeatureSet):
        with pytest.raises(FeatureException):
            feature_set_with_config.is_active('unknown_feature')

    def test_deactivated_feature(self, feature_set_with_config: FeatureSet):
        assert not feature_set_with_config.is_active('my_active_feature')

    def test_activated_feature(self, feature_set_with_config: FeatureSet):
        assert feature_set_with_config.is_active('my_inactive_feature')
