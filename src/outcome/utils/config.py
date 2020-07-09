"""TOML file config management."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union, cast

import toml

ValidPath = Union[str, Path]
ValidConfigType = Union[str, int, float, bool]
ConfigDict = Dict[str, ValidConfigType]


class Config:  # pragma: only-covered-in-unit-tests

    path: Optional[ValidPath]
    config: Optional[ConfigDict]
    aliases: Optional[Dict[str, str]]

    def __init__(self, path: Optional[ValidPath] = None, aliases: Optional[Dict[str, str]] = None):
        self.path = path
        self.config = None
        self.aliases = aliases

    def get(self, key: str) -> ValidConfigType:
        if key in os.environ:
            return cast(str, os.environ.get(key))

        if self.path and not self.config:
            self.config = self.get_config(self.path, self.aliases)
            return self.config[key]

        raise KeyError(key)

    @classmethod
    def get_config(cls, path: ValidPath, aliases: Dict[str, str] = None) -> Dict[str, ValidConfigType]:
        config = toml.load(path)
        config_flattened = cls.flatten_keys(config)

        if aliases:
            for original, alias in aliases.items():
                config_flattened[alias.upper()] = config_flattened.pop(original.upper())

        return config_flattened

    @classmethod
    def flatten_keys(cls, value: Any, key: Optional[str] = None) -> Dict[str, Any]:
        if not isinstance(value, dict):
            if not key:
                raise Exception('Value cannot be a non-dict without a key')

            return {key.upper(): value}

        flattened = {}

        for k, v in value.items():
            prefix = (f'{key}_' if key else '').upper()
            flattened.update({f'{prefix}{skey}': sval for skey, sval in cls.flatten_keys(v, k).items()})

        return flattened
