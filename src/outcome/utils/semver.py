"""Get the compatibilty between two Semantic Versions."""

from enum import Enum

import semver


class Compatibility(Enum):
    compatible = 'compatible'
    incompatible = 'incompatible'

    # A third case, for potential future use
    # if we decide to check build or pre-release info
    unknown = 'unknown'


def compatibility(a: str, b: str) -> Compatibility:
    a_parsed = semver.VersionInfo.parse(a)
    b_parsed = semver.VersionInfo.parse(b)

    if a_parsed.major != b_parsed.major:
        return Compatibility.incompatible

    return Compatibility.compatible


def are_compatible(a: str, b: str) -> bool:
    return compatibility(a, b) == Compatibility.compatible
