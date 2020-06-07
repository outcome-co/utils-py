import pytest
from jinja2 import Template


@pytest.fixture(scope='module')
def regex_template():
    return Template("{{ name | regex_replace('o', 'oo') }}", extensions=['outcome.utils.jinja2.Extend'])


class TestRegexReplace:
    def test_basic_regex(self, regex_template: Template):
        name = 'John'
        expected = 'Joohn'
        rendered = regex_template.render(name=name)

        assert rendered == expected
