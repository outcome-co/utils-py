import pytest
from outcome.utils.meta import _flatten_list_of_types, get_init_args


def test_flatten_with_correct_list_of_types():
    # This list of types is correct, the result should be as expected.
    types_non_flattened = [dict, [list], (str, str)]
    result = _flatten_list_of_types(types_non_flattened)
    expected = {dict, list, str}
    assert result == expected


def test_flatten_with_incorrect_list_of_types():
    # This list of types is incorrect: it should contain only types and Iterables.
    # The function should return a type error.
    non_type_non_iterable = [1, 2, 3]
    with pytest.raises(TypeError):
        _flatten_list_of_types(non_type_non_iterable)


class Parent:
    def __init__(self, a: str):
        ...


class Child(Parent):
    def __init__(self, b: str):
        ...


def test_get_init_args():
    assert get_init_args(Child) == {'a', 'b'}
