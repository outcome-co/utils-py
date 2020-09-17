"""Load objects from a mod:obj path."""

from importlib import import_module  # pragma: no cover


def load_obj(objspec):  # pragma: no cover
    modname, objname = objspec.split(':')
    return getattr(import_module(modname), objname)
