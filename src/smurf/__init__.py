import importlib

from .project import project_root
from .project import project_name
from .info import Info
from .config import Config


def Mount(search_pattern, **kwargs):
    from .mount import Mount
    from .search import search, remote_path
    sim = search(search_pattern, remote=True, unique=True)[0]
    path = remote_path(sim)
    return Mount(path)
