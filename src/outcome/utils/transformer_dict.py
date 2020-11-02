"""A dict that transforms the keys before setting/retrieving values."""

from typing import Callable, Dict, Iterator, MutableMapping, TypeVar

KT = TypeVar('KT')
TKT = TypeVar('TKT')
VT = TypeVar('VT')

Transformer = Callable[[KT], TKT]


class TransformerDict(MutableMapping[TKT, VT]):
    def __init__(self, *args, transformer: Transformer, **kwargs) -> None:
        self.items: Dict[TKT, VT] = dict(*args, **kwargs)
        self.transformer = transformer

    def __len__(self):
        return len(self.items)

    def __getitem__(self, key: KT) -> VT:
        return self.items[self.transformer(key)]

    def __setitem__(self, key: KT, value: VT) -> None:
        self.items[self.transformer(key)] = value

    def __delitem__(self, key: KT) -> None:  # noqa: WPS603
        del self.items[self.transformer(key)]

    def __iter__(self) -> Iterator[TKT]:
        return iter(self.items)
