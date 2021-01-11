# Generate a database with simdirs and uuids in the project root
import os
import sys
import json
import re
import smurf
import smurf.info as siminfo
import uuid


class NoSimulationFoundError(Exception):
    pass


class ResultNotUniqueError(Exception):
    pass


def main():
    args = parse_command_line_args()

    c = LocalSimCache()

    if args.notify:
        for p in args.patterns:
            c.add_sim_to_cache(expand_path(p))
        sys.exit(0)

    if args.scrub:
        c.scrub()
        sys.exit(0)

    if args.remove:
        try:
            c.remove(args.remove)
        except KeyError:
            pass
        try:
            RemoteSimCache().remove(args.remove)
        except KeyError:
            pass
        return

    if args.generate:
        c.rebuild()

    if args.list:
        crem = RemoteSimCache()
        data = [x for x in c.data.values()] + [x for x in crem.data.values()]
        if args.json:
            print(json.dumps(data, indent=4))
        else:
            from smurf.search import print_table
            print_table(data)


sim_attributes = ["uuid", "name", "tags", "simcode", "path", "host"]


def parse_command_line_args():
    import argparse
    import argcomplete
    parser = argparse.ArgumentParser()
    parser.add_argument("patterns",
                        default=[os.getcwd()],
                        nargs="*",
                        help="What to search for.")
    parser.add_argument("--json",
                        default=False,
                        action="store_true",
                        help="Output as json.")
    parser.add_argument("-g",
                        "--generate",
                        default=False,
                        action="store_true",
                        help="Force (re)generation of the cache.")
    parser.add_argument("-s",
                        "--scrub",
                        default=False,
                        action="store_true",
                        help="Remove non existing simulations from the cache.")
    parser.add_argument("-n",
                        "--notify",
                        default=False,
                        action="store_true",
                        help="Notify the cache about a simulation.")
    parser.add_argument("-l",
                        "--list",
                        default=False,
                        action="store_true",
                        help="List all cached items.")
    parser.add_argument("-r",
                        "--remove",
                        help="Remove simulation with given id from cache.")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    return args


def expand_path(path):
    """ Support paths including ~ for home.
    
    Parameters
    ----------
    path: str
        Input path.

    Returns
    -------
    str
        Path with ~ replace by user's home.
     """
    abspath = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(abspath):
        raise FileNotFoundError("No such directory: {}".format(path))
    return abspath


class CacheMiss(Exception):
    pass


class Cache:
    """ Implementation of a simple cache. """

    def __init__(self):
        self.data = {}

    def request(self, req):
        """ Request an element from the cache for key 'req' """
        try:
            return self.data[req]
        except KeyError:
            raise CacheMiss("Nothing found for", req)

    def regex_request(self, req):
        """ Like request, but check for 'req' regex match any key """
        pattern = re.compile(req)
        for key in self.data:
            if re.search(pattern, key):
                return self.data[key]
        raise CacheMiss("Nothing found for", req)

    def insert(self, key, value):
        """ Insert an element into the cache """
        self.data[key] = value

    def remove(self, key):
        """ Remove the element from the cache """
        try:
            del self.data[key]
        except KeyError:
            pass

    def contains(self, key):
        """ Return True if the cache contains key, false otherwise. """
        rv = key in self.data
        return rv


class DoubleUuidCache(Cache):
    """ Extension of Cache which uses two sets of keys, uuids and the first part of uuids. """

    def __init__(self):
        self.key_map = {}

    def map_key(self, key):
        """ Get full uuid from key map if its a shortened id. """
        try:
            rv = self.key_map[key]
        except KeyError:
            rv = key
        return rv

    def create_map(self):
        """ Create the map with shortened uuids. """
        for key in self.data:
            self.key_map[key.split("-")[0]] = key

    def request(self, req):
        """ Wrap around parent's request. """
        req = self.map_key(req)
        return super().request(req)

    def insert(self, key, value):
        """ Insert value with full uuid and register shortened uuid """
        if not self.is_uuid(key):
            raise ValueError("'{}' is not a valid uuid".format(key))
        short = key.split("-")[0]
        self.key_map[short] = key
        super().insert(key, value)

    def remove(self, key):
        """ Remove the value belonging to key from the dict """
        key = self.map_key(key)
        short = key.split("-")[0]
        super().remove(key)
        del self.key_map[short]

    def is_uuid(self, key):
        """ Check whether a key is a valid uuid. """
        try:
            uuid.UUID(key)
        except ValueError:
            return False
        return True

    def contains(self, key):
        """ Return True if the cache contains key, false otherwise. """
        rv = key in self.data or key in self.key_map
        return rv


class JsonCache(DoubleUuidCache):
    """ Implementation of a simple cache with the ability to store data in a json file """

    def __init__(self, cache_file):
        super().__init__()
        self.cache_file = cache_file
        self.load()
        super().create_map()

    def save(self):
        """ Save the cache to file. """
        with open(self.cache_file, "w") as outfile:
            outfile.write(json.dumps(self.data))

    def load(self):
        """ Load the cache from file or create an empty one. """
        try:
            with open(self.cache_file, "r") as infile:
                self.data = json.load(infile)
        except FileNotFoundError:
            self.data = {}

    def insert(self, key, value):
        """ Insert an element and save the cache to file. """
        super().insert(key, value)
        self.save()

    def remove(self, key):
        """ Remove the element from the cache and save the cache to file. """
        super().remove(key)
        self.save()


class SimCache(JsonCache):
    """ A cache for simulations """

    def __init__(self, cache_file):
        super().__init__(cache_file)

    def search(self,
               patterns,
               fields=sim_attributes,
               unique=False,
               exclusive=False):
        """ Search through all information (key and all values) in the cache. """
        # make sure patterns is an iterable
        patterns = ensure_is_list(patterns)
        matches = []
        for sim in self.data.values():
            for field in fields:
                res = [re.search(p, sim[field]) is not None for p in patterns]
                success = all(res) if exclusive else any(res)
                if success:
                    matches.append(sim)
                    break
        if len(matches) == 0:
            raise NoSimulationFoundError(
                "No result found for '{}'".format(patterns))
        if unique:
            if len(matches) > 1:
                raise ResultNotUniqueError(
                    "Search result is not unique! {} results found.".format(
                        len(matches)))
            return matches[0]
        else:
            return matches


class LocalSimCache(SimCache):
    """ A cache for simulations on the local host. """

    def __init__(self):
        self.conf = smurf.Config()
        cache_file = os.path.join(self.conf["home_path"],
                                  self.conf["local_cache"])
        self.rootdir_list = self.conf["rootdir_list"]
        super().__init__(cache_file)

    def rebuild(self, base=None):
        self.scrub()
        self.generate(base=base)

    def scrub(self):
        """ Verify each cache entry and delete nonexisting entries. """
        for key, sim in list(self.data.items()):
            if not os.path.exists(sim["path"]):
                self.remove(key)

    def generate(self, base=None):
        # only generate cache inside basedir if given
        if base is not None:
            bases = [base]
        else:
            bases = self.rootdir_list
        for base in bases:
            for root, _, _ in os.walk(base):
                if siminfo.is_simdir(root):
                    self.add_sim_to_cache(root)

    def add_sim_to_cache(self, simdir):
        info = siminfo.Info(simdir)
        self.insert(
            info.uuid, {
                "uuid": info.uuid,
                "name": info.name,
                "path": info.path,
                "host": "localhost",
                "tags": ", ".join(info.tags),
                "simcode": info.simcode
            })
        return info.uuid


class RemoteSimCache(SimCache):
    """ A cache for simulations on remote hosts. """

    def __init__(self):
        self.conf = smurf.Config()
        cache_file = os.path.join(self.conf["home_path"],
                                  self.conf["remote_cache"])
        super().__init__(cache_file)

    def add_sim_to_cache(self, sim):
        self.insert(sim["uuid"], sim)


def ensure_is_list(x):
    """ Ensure that the argument is an iterable item with a length. 

    Parameters
    ----------
    x
        Any iterable or object.

    Returns
    -------
        x if x is an iterable, otherwise [x]
    """
    try:
        len(x)
        if isinstance(x, str):
            x = [x]
    except ValueError:
        x = [x]
    return x


def get_cache_by_id(simid):
    """ Get the cache which contains the key.

    Parameters
    ----------
    simid : str
        Id of the simulations.

    Returns
    -------
    smurf.cache.SimCache
    """
    c = LocalSimCache()
    if c.contains(simid):
        rv = c
    else:
        c = RemoteSimCache()
        if c.contains(simid):
            rv = c
        else:
            rv = None
    return rv


if __name__ == "__main__":
    main()
