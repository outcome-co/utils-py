"""Main entrypoint for the Jinja2 extension.

Responsable for adding all of the filters to the Jinja
Environment object.
"""

from jinja2.ext import Environment, Extension
from outcome.utils.jinja2.regex_replace import regex_replace


class Extend(Extension):
    """Extends the Jinja environment with the custom filters."""

    def __init__(self, environment: Environment):
        """Initialize the plugin, but also add the filters to the environment.

        Args:
            environment: The Jinja2 environment object.
        """
        super()

        environment.filters['regex_replace'] = regex_replace
