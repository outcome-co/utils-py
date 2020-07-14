"""Config helper."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union, cast

import toml

ValidPath = Union[str, Path]
ValidConfigType = Union[str, int, float, bool]
ConfigDict = Dict[str, ValidConfigType]


class Config:  # pragma: only-covered-in-unit-tests
    """This class helps with retrieving config values from a project environment.

    You can provide a path to a TOML file, typically the pyproject.toml, or just
    let the class try to extract the values from environment variables.

    Environment variables will always take precedence over the values found in the file.

    The keys from the TOML file will be flattened and transformed to uppercase, following
    environment variable conventions.

    For example:

    ```toml
    [app]
    port = 80
    ```

    Will be transformed into

    ```py
    {
        'APP_PORT': 80
    }
    ```
    """

    path: Optional[ValidPath]
    config: Optional[ConfigDict]
    aliases: Optional[Dict[str, str]]

    def __init__(
        self,
        path: Optional[ValidPath] = None,
        aliases: Optional[Dict[str, str]] = None,
        defaults: Optional[Dict[str, ValidConfigType]] = None,
    ) -> None:
        """Initialize the class with an optional config file and set of aliases.

        The aliases dict will rewrite config keys from key to value:

        ```
        aliases = {'ORIGINAL_KEY': 'NEW_KEY'}
        config = Config('some_file.toml', aliases)

        config.get('ORIGINAL_KEY')  # -> raises KeyError
        config.get('NEW_KEY')  # -> returns value
        ```

        The defaults dict is the final fallback.

        Arguments:
            path (ValidPath, optional): The path to the config file.
            aliases (Dict[str, str], optional): The aliasing dict.
            defaults (Dict[str, ValidConfigType], optional): A dict of hardcoded values
        """
        self.path = path
        self.config = None
        self.aliases = aliases
        self.defaults = (defaults or {}).copy()

    def get(self, key: str) -> ValidConfigType:
        if key in os.environ:
            return cast(str, os.environ.get(key))

        if self.path:
            if not self.config:
                self.config = self.get_config(self.path, self.aliases)
            if key in self.config:
                return self.config[key]  # noqa: WPS529

        return self.defaults[key]

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
