"""Utils CLI."""

import click
from outcome.utils.loader import load_obj


@click.group()
def main():
    ...


@main.command(help='List available feature flags')
@click.option('--feature-set', default='outcome.utils:feature_set')
def features(feature_set):
    fs = load_obj(feature_set)
    fs.display_features()
