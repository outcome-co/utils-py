# utils-py
![ci-badge](https://github.com/outcome-co/utils-py/workflows/Release/badge.svg?branch=v4.13.2) ![version-badge](https://img.shields.io/badge/version-4.13.2-brightgreen)

A set of python utilities.

## Usage

```sh
poetry add outcome-utils
```

### Cache

To add cache to a module
``` python
from outcome.utils import cache

cache_settings = {
    '<your_prefix>.expiration': 300,  # Default
    '<your_prefix>.backend': 'memory',  # Default
}

region = cache.get_cache_region()
cache.configure_cache_region(region, settings=cache_settings, prefix='<your_prefix>')
```

Then add to the functions to cache:
``` python
@region.cache_on_arguments()
def func_to_cache():
    ...
```

Or for async functions:
``` python
@region.cache_on_arguments()
@cache.cache_async
async def async_func_to_cache():
    ...
```

To have the cache persist on disk, specify the path
``` python
from pathlib import Path

cache_settings = {
    ...
    '<your_prefix>.cache_path': f'{Path.home()}/.cache/example_path/cache.pkl'',
    ...
}
```

## Development

Remember to run `./pre-commit.sh` when you clone the repository.
