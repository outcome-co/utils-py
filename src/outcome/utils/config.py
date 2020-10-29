"""Config helper."""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

import toml

ValidPath = Union[str, Path]
ValidConfigType = Union[str, int, float, bool]
ConfigDict = Dict[str, ValidConfigType]


class Sentinel:
    ...


NO_DEFAULT = Sentinel()


class ConfigBackend(ABC):
    @abstractmethod
    def get(self, key: str) -> ValidConfigType:  # pragma: no cover
        ...

    @abstractmethod
    def __contains__(self, key: str) -> bool:  # pragma: no cover
        ...


class EnvBackend(ConfigBackend):
    def get(self, key: str) -> ValidConfigType:
        return cast(str, os.environ[key])

    def __contains__(self, key: str) -> bool:
        return key in os.environ


class DefaultBackend(ConfigBackend):

    defaults: Dict[str, str]

    def __init__(self, defaults: Dict[str, str]):
        self.defaults = defaults

    def get(self, key: str) -> ValidConfigType:
        return self.defaults[key]

    def __contains__(self, key: str) -> bool:
        return key in self.defaults


class TomlBackend(ConfigBackend):

    path: Optional[ValidPath]
    config: Optional[ConfigDict]
    aliases: Optional[Dict[str, str]]

    def __init__(self, path: Optional[ValidPath] = None, aliases: Optional[Dict[str, str]] = None):
        self.path = path
        self.aliases = aliases
        self.config = None

    def get(self, key: str) -> ValidConfigType:
        if not self.config:
            self.load_config()
        return self.config[key]

    def __contains__(self, key: str) -> bool:
        if not self.config:
            self.load_config()
        return key in self.config

    def load_config(self):
        self.config = self.get_config(self.path, self.aliases)

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

    If needed you can modify Config backends to change the order of priority, or to add your own backends.
    You can use add_backend method to add your own backend at the desired priority.
    If you wish to add your own backend, it needs to inherit from ConfigBackend abstract class.
    """

    backends: List[ConfigBackend]
    default_backend: DefaultBackend

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
        self.backends = [EnvBackend()]
        if path:
            self.backends.append(TomlBackend(path=path, aliases=aliases))

        self.default_backend = DefaultBackend(defaults or {})

    def get(self, key: str, default: Optional[Union[ValidConfigType, Sentinel]] = NO_DEFAULT) -> ValidConfigType:

        for backend in self.backends:
            if key in backend:
                return backend.get(key)

        try:
            return self.default_backend.get(key)
        except KeyError as exc:
            if default != NO_DEFAULT:
                return default
            raise exc

    def add_backend(self, backend: ConfigBackend, priority: int):
        self.backends.insert(priority, backend)
