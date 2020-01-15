# Integration of simdata into smurf.
# simdata is a python package to handle simulation data.
# This module provides the functionality to use sim ids
# to transparently get a data object without manually
# looking up simulation dir paths.

from smurf.search import remote_path
from smurf.cache import get_cache_by_id
from .mount import Mount
import simdata.data


class RemoteData(simdata.data.Data):
    """ Data interface for simulations on remote hosts.
    Simdirs on remote hosts are mounted using sshfs. 
    Use user@host:path as the remote_path argument. The syntax of the remote path is equivalent to the arguments of scp."""
    def __init__(self, remote_path, **kwargs):
        self.remote_path = remote_path
        if is_local_path(self.remote_path):
            self.path = self.remote_path
        else:
            self.path = self.mount()
        super().__init__(self.path, **kwargs)

    def mount(self):
        self.mount_point = Mount(self.remote_path)
        local_path = self.mount_point.get_path()
        return local_path


class Data(RemoteData):
    # data loader with smurf support to locate remote simulations
    # and mount them via sshfs
    def __init__(self, simid, search_remote=True, search_args=None, **kwargs):
        self.sim = smurf_global_lookup(simid,
                                       remote=search_remote,
                                       search_args=search_args)
        if self.sim["host"] != "localhost":
            path = "{}:{}".format(self.sim["host"], self.sim["path"])
        else:
            path = self.sim["path"]
        if "simdata_code" in self.sim:
            kwargs["loader"] = self.sim["simdata_code"]
        elif "simcode" in self.sim:
            kwargs["loader"] = self.sim["simcode"]
        super().__init__(path, **kwargs)
        self.simid = simid
        self.sim["simdata_code"] = self.code
        c = get_cache_by_id(self.sim["uuid"])
        c.insert(self.sim["uuid"], self.sim)


def is_local_path(path):
    """ Evaluate whether 'path' is not of the form host:path. """
    return len(path.split(":")) < 2


def smurf_global_lookup(pattern, remote=True, search_args=None):
    try:
        from smurf.search import search
        try:
            if search_args is None:
                search_args = {}
            rv = search(pattern, remote=remote, **search_args)
            # use the first match
            if len(rv) == 0:
                raise KeyError(
                    "Could not locate simulation for pattern : '{}'".format(
                        pattern))
            return rv[0]

        except Exception as e:
            print("Smurf lookup failed with exception: {}".format(e))
            raise
    except ImportError:
        print("Smurf is not installed on this maschine!")
        return {}
