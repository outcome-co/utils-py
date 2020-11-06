import os
import warnings
from pathlib import Path
from unittest.mock import patch

import pytest
from outcome.utils import feature_set
from outcome.utils.config import Config

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

expected_feature_keys = [
    ('feat', 'WITH_FEAT_FEAT'),
    ('my.feat', 'WITH_FEAT_MY_FEAT'),
    ('my.nested.feat', 'WITH_FEAT_MY_NESTED_FEAT'),
]


@pytest.mark.parametrize('feature,key', expected_feature_keys)
def test_feature_env_keys(feature, key):
    assert feature_set._feature_to_config_key(feature) == key


@pytest.fixture(params=valid_feature_names_raw)
def valid_feature_name(request):
    return request.param


@pytest.fixture(params=invalid_feature_names_raw)
def invalid_feature_name(request):
    return request.param


def test_valid_feature_names(valid_feature_name):
    assert feature_set._is_valid_feature_name(valid_feature_name)


def test_invalid_feature_names(invalid_feature_name):
    assert not feature_set._is_valid_feature_name(invalid_feature_name)


boolean_true_values_raw = [
    't',
    'y',
    '1',
    'true',
    'yes',
    'YES',
    'TRUE',
    1,
    True,
]


boolean_false_values_raw = [
    'f',
    'n',
    '0',
    'false',
    'no',
    'NO',
    False,
    0,
]


@pytest.fixture(autouse=True)
def reset_features():
    feature_set.reset()


@pytest.fixture(params=boolean_true_values_raw)
def truth_value(request):
    return request.param


@pytest.fixture(params=boolean_false_values_raw)
def false_value(request):
    return request.param


def test_coerce_truth_values(truth_value):
    assert feature_set._coerce_boolean(truth_value)


def test_coerce_false_values(false_value):
    assert not feature_set._coerce_boolean(false_value)


def test_invalid_registration():
    with pytest.raises(feature_set.FeatureException):
        feature_set.register_feature('_invalid')


default_feature = 'default_feature'
inactive_feature = 'inactive_feature'
active_feature = 'active_feature'
unknown_feature = 'unknown'

feature_toml = Path(Path(__file__).parent, 'fixtures', 'sample.toml')
feature_config = Config(feature_toml)

expected_feature_states = [
    (default_feature, False),
    (inactive_feature, False),
    (active_feature, True),
]


@pytest.fixture()
def register_feature():
    feature_set.register_feature(default_feature)
    feature_set.register_feature(inactive_feature, default=False)
    feature_set.register_feature(active_feature, default=True)


@pytest.mark.usefixtures('register_feature')
def test_duplicate_registration():
    with pytest.raises(feature_set.FeatureException):
        feature_set.register_feature(default_feature)


@patch.dict(os.environ, {}, clear=True)
@pytest.mark.usefixtures('register_feature')
@pytest.mark.parametrize('feature,expected', expected_feature_states)
def test_is_active(feature, expected):
    assert feature_set.is_active(feature) == expected


@pytest.mark.usefixtures('register_feature')
def test_all_features():
    assert feature_set.features() == dict(expected_feature_states)


@patch.dict(os.environ, {'APP_ENV': 'dev'}, clear=True)
@pytest.mark.usefixtures('register_feature')
def test_unknown_feature_dev():
    with warnings.catch_warnings(record=True) as w:
        assert not feature_set.is_active(unknown_feature)
        assert len(w) == 1
        assert issubclass(w[-1].category, RuntimeWarning)


@patch.dict(os.environ, {'APP_ENV': 'production'}, clear=True)
@pytest.mark.usefixtures('register_feature')
def test_unknown_feature_prod():
    with warnings.catch_warnings(record=True) as w:
        with pytest.raises(feature_set.FeatureException):
            assert not feature_set.is_active(unknown_feature)
        assert len(w) == 0


@patch.dict(os.environ, {'WITH_FEAT_DEFAULT_FEATURE': '1', 'WITH_FEAT_ACTIVE_FEATURE': '0'}, clear=True)
@pytest.mark.usefixtures('register_feature')
def test_is_active_from_env():
    assert feature_set.is_active(default_feature)
    assert not feature_set.is_active(active_feature)


@patch.dict(os.environ, {}, clear=True)
@pytest.mark.usefixtures('register_feature')
def test_is_active_from_toml():
    feature_set.set_config(feature_config)
    assert feature_set.is_active(default_feature)


@patch.dict(os.environ, {'APP_ENV': 'dev'}, clear=True)
def test_set_unknown_feature():
    with warnings.catch_warnings(record=True) as w:
        assert not feature_set.is_active(unknown_feature)
        feature_set.set_feature_default(unknown_feature, default_state=True)
        assert len(w) > 0
        assert feature_set.is_active(unknown_feature)


@patch.dict(os.environ, {}, clear=True)
@pytest.mark.usefixtures('register_feature')
def test_set_known_feature():
    assert not feature_set.is_active(inactive_feature)
    feature_set.set_feature_default(inactive_feature, default_state=True)
    assert feature_set.is_active(inactive_feature)


@patch.dict(os.environ, {}, clear=True)
@pytest.mark.usefixtures('register_feature')
def test_feature_source_default():
    assert feature_set._feature_state_source(default_feature) == 'default'


@patch.dict(os.environ, {'WITH_FEAT_DEFAULT_FEATURE': '1'}, clear=True)
@pytest.mark.usefixtures('register_feature')
def test_feature_source_config():
    assert feature_set._feature_state_source(default_feature) == 'config'
