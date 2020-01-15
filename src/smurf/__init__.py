import importlib

from .provide import Provider
from .project import project_root
from .project import project_name
from .info import Info
from .config import Config


def Data(*args, **kwargs):
    from . import simdata_integration
    return simdata_integration.Data(*args, **kwargs)
