"""Filters providing regex functionality to Jinja2."""

import re
from typing import Pattern


def regex_replace(input_value: str, pattern: Pattern, replacement: str) -> str:
    """Applies a regex replace using the pattern on the input string.

    Args:
        input_value: the string in which to apply the replacement
        pattern: the regular expression pattern
        replacement: the value to use as a replacement

    Returns:
        The input string, with all occurrences of the pattern replaced
        with the replacement.
    """
    pattern = re.compile(pattern)
    return pattern.sub(replacement, input_value)
