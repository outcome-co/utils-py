from unittest.mock import Mock, patch

import pytest
from outcome.utils import loader


@pytest.fixture()
def mock_import_module():
    with patch('outcome.utils.loader.import_module', autospec=True) as mocked_import_module:
        yield mocked_import_module


def test_loader_full_path(mock_import_module: Mock):
    module = Mock()
    obj = Mock()

    mock_import_module.return_value = module
    module.my_obj = obj

    loaded_obj = loader.load_obj('my.module.name:my_obj')

    mock_import_module.assert_called_once_with('my.module.name')
    assert loaded_obj == obj


def test_loader_partial_path(mock_import_module: Mock):
    module = Mock()
    obj = Mock()

    mock_import_module.return_value = module
    module.my_obj = obj

    loaded_obj = loader.load_obj('my.module.name', default_obj='my_obj')

    mock_import_module.assert_called_once_with('my.module.name')
    assert loaded_obj == obj


def test_loader_incomplete_path():
    with pytest.raises(ValueError):
        loader.load_obj('my.module.name')


def test_loader_invalid_path():
    with pytest.raises(ValueError):
        loader.load_obj('my.module.name:invalid:invalid')
