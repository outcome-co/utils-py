"""Load objects from a mod:obj path."""

from importlib import import_module, util  # pragma: no cover
from typing import Optional


def load_obj(objspec: str, default_obj: Optional[str] = None):
    parts = objspec.split(':')
    modname = None
    objname = None

    if len(parts) == 1:
        modname = parts[0]
        objname = default_obj

    elif len(parts) == 2:
        modname, objname = parts

    if not (modname and objname):
        raise ValueError(f'Invalid objspec: {objspec}')

    return getattr(import_module(modname), objname)


def load_module(name: str, path: str):  # pragma: no cover
    spec = util.spec_from_file_location(name, path)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
