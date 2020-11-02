import pytest
from outcome.utils.transformer_dict import TransformerDict


def upper(v: str) -> str:
    return v.upper()


uc_dict = TransformerDict[str, str](transformer=upper)


@pytest.fixture(autouse=True)
def reset_dict():
    uc_dict['foo'] = 'bar'


def test_length():
    assert len(uc_dict) == 1


def test_keys():
    assert uc_dict.keys() == {'FOO'}


@pytest.mark.parametrize('key', ['foo', 'FOO'])
class TestTransformerDict:
    def test_contains(self, key):
        assert key in uc_dict

    def test_get(self, key):
        assert uc_dict[key] == 'bar'

    def test_delete(self, key):
        del uc_dict[key]
        assert key not in uc_dict
