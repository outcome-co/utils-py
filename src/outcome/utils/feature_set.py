"""Feature flag management."""

import re
from typing import Optional

from outcome.utils.config import Config


class FeatureException(Exception):
    ...


_feature_pattern = r'^[a-z]+(_?[a-z]+_?[a-z])*$'
_feature_prefix = 'WITH_FEAT_'


def is_valid_feature_name(feature: str):
    return all(re.match(_feature_pattern, part) is not None for part in feature.split('.'))


def feature_to_config_key(feature: str) -> str:
    return f'{_feature_prefix}{feature.upper()}'


def str2bool(v):
    return str(v).lower() in {'yes', 'y', 'true', 't', '1'}


class FeatureSet:
    def __init__(self, config: Optional[Config] = None):
        if not config:
            config = Config()

        self.config = config
        self._features = set()
        self._feature_defaults = {}

    def register_feature(self, feature: str, default: bool = False):
        if not is_valid_feature_name(feature):
            raise FeatureException(f'Invalid feature name: {feature}')

        if feature in self._features:
            raise FeatureException(f'Duplicate feature: {feature}')

        self._features.add(feature)
        self._feature_defaults[feature] = default

    def is_active(self, feature: str) -> bool:
        if feature not in self._features:
            raise FeatureException(f'Unknown feature: {feature}')

        try:
            feature_key = feature_to_config_key(feature)
            value = self.config.get(feature_key)
            return str2bool(value) if isinstance(value, str) else value
        except KeyError:
            ...

        return self._feature_defaults[feature]
