"""Feature flag management."""

import re
import warnings
from typing import Dict

from outcome.utils import env
from outcome.utils.config import Config
from rich.console import Console
from rich.table import Table


class FeatureException(Exception):
    ...


_feature_pattern = r'^[a-z]+(_?[a-z]+_?[a-z])*$'
_feature_prefix = 'WITH_FEAT_'

_features: Dict[str, bool]
_config: Config


def reset():
    global _config, _features
    _config = Config()  # noqa: WPS122,WPS442
    _features = {}  # noqa: WPS122,WPS442


reset()


def _is_valid_feature_name(feature: str):
    return all(re.match(_feature_pattern, part) is not None for part in feature.split('.'))


def _feature_to_env_key(feature: str) -> str:
    replaced = feature.replace('.', '_').upper()
    return f'{_feature_prefix}{replaced}'


def _coerce_boolean(v):
    return str(v).lower() in {'yes', 'y', 'true', 't', '1'}


def set_config(config: Config):
    global _config
    _config = config  # noqa: WPS122,WPS442


def register_feature(feature: str, default: bool = False) -> None:
    if not _is_valid_feature_name(feature):
        raise FeatureException(f'Invalid feature name: {feature}')

    if feature in _features:
        raise FeatureException(f'Duplicate feature: {feature}')

    _features[feature] = default


def features() -> Dict[str, bool]:
    return {k: is_active(k) for k in _features.keys()}


def display_features():  # pragma: no cover
    console = Console()

    table = Table(show_header=True, header_style='bold')
    table.add_column('Feature Flag')
    table.add_column('State', justify='right')
    table.add_column('Default State', justify='right')

    def state_repr(state):
        return '[bold green]active[/bold green]' if state else '[bold red]inactive[/bold red]'

    for feat, state in features().items():
        table.add_row(feat, state_repr(state), state_repr(_features[feat]))

    console.print(table)


def is_active(feature: str) -> bool:
    if not _feature_check(feature):
        return False

    try:
        feature_key = _feature_to_env_key(feature)
        value = _config.get(feature_key)
        return _coerce_boolean(value) if isinstance(value, str) else value
    except KeyError:
        ...

    return _features[feature]


def _feature_check(feature):
    if feature not in _features:
        if env.is_dev():
            warnings.warn(
                f'Checking unknown feature "{feature}", maybe you forgot to register it? This will raise an exception in production',  # noqa: E501
                RuntimeWarning,
            )
            return False
        raise FeatureException(f'Unknown feature: {feature}')
    return True


def set_feature_default(feature: str, default_state: bool) -> None:
    _feature_check(feature)
    _features[feature] = default_state
