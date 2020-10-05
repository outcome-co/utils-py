"""Load objects from a mod:obj path."""

from importlib import import_module, util  # pragma: no cover


def load_obj(objspec: str):  # pragma: no cover
    modname, objname = objspec.split(':')
    return getattr(import_module(modname), objname)


def load_module(name: str, path: str):  # pragma: no cover
    spec = util.spec_from_file_location(name, path)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
