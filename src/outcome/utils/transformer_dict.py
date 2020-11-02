"""A dict that transforms the keys before setting/retrieving values."""

import typing

KT = typing.TypeVar('KT')
TKT = typing.TypeVar('TKT')
VT = typing.TypeVar('VT')


class TransformerDict(typing.Generic[KT, VT, TKT], typing.MutableMapping[KT, VT]):  # noqa: WPS214
    def __init__(self, *args, transformer: typing.Callable[[KT], TKT], **kwargs) -> None:
        self._inner_dict: typing.Dict[TKT, VT] = dict(*args, **kwargs)
        self.transformer = transformer

    def __len__(self):
        return len(self._inner_dict)

    def __getitem__(self, key: KT) -> VT:
        return self._inner_dict[self.transformer(key)]

    def __setitem__(self, key: KT, value: VT) -> None:
        self._inner_dict[self.transformer(key)] = value

    def __delitem__(self, key: KT) -> None:  # noqa: WPS603
        del self._inner_dict[self.transformer(key)]

    def __iter__(self) -> typing.Iterator[TKT]:  # pragma: no cover
        return iter(self._inner_dict)

    # The following methods are overriden for type annotations
    def keys(self) -> typing.KeysView[TKT]:  # pragma: no cover
        return self._inner_dict.keys()

    def items(self) -> typing.AbstractSet[typing.Tuple[TKT, VT]]:  # pragma: no cover
        return self._inner_dict.items()
