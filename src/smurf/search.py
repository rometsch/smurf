import json
import subprocess
import sys
import os

import smurf
import smurf.cache as cache

# timeout after which to cancel search if host does not respond
search_timeout = 10


def main():
    args = parse_command_line_args()

    rv = search(args.patterns,
                unique=args.unique,
                exclusive=args.exclusive_search,
                remote=not args.local,
                force_global=args.g,
                ensure_exist=args.validate)

    if args.json:
        print(json.dumps(rv, indent=4))
    elif args.print:
        for sim in rv:
            if args.print == "location":
                print(remote_path(sim))
            else:
                print(sim[args.print])
    else:
        print_table(rv)


def parse_command_line_args():
    import argparse
    import argcomplete
    parser = argparse.ArgumentParser()
    parser.add_argument("patterns", nargs="+", help="What to search for.")
    parser.add_argument("-v", "--verbose", default=False, action="store_true")
    parser.add_argument("-g",
                        default=False,
                        action="store_true",
                        help="Force searching all known hosts")
    parser.add_argument("--local",
                        default=False,
                        action="store_true",
                        help="Force searching only the local cache.")
    parser.add_argument("-p",
                        "--print",
                        choices=cache.sim_attributes,
                        help="Property to show.")
    parser.add_argument("--search-fields",
                        choices=cache.sim_attributes,
                        nargs="+",
                        default=cache.sim_attributes,
                        help="Properties to search.")
    parser.add_argument("-u",
                        "--unique",
                        default=False,
                        action="store_true",
                        help="Only print a unique result.")
    parser.add_argument(
        "-e",
        "--exclusive-search",
        default=False,
        action="store_true",
        help="All given pattern must match a valid search result.")
    parser.add_argument("--json",
                        default=False,
                        action="store_true",
                        help="Output as json.")
    parser.add_argument("--validate",
                        default=False,
                        action="store_true",
                        help="Check that simulation exists on host and delete from cache if not.")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    return args


def print_table(info_list):
    """ Print a formatted table of the given info dict objects.

    Parameters
    ----------
    info_list : list
        List containing info dicts.
    """
    if len(info_list) == 0:
        return
    fields = ["uuid", "name", "host", "tags"]
    maxlen = {"uuid" : 8}
    for key in fields[1:]:
        maxlen[key] = max([len(e[key]) for e in info_list] + [1]) 
    
    sorted_list = sorted(info_list, key=lambda info: info["host"])
    for info in sorted_list:
        s = ""
        for f in fields:
            s += ("{:" + str(maxlen[f]) + "s}\t").format(info[f][:maxlen[f]])
        print(s)


def remote_path(sim):
    if "host" in sim and sim["host"] != "localhost":
        return "{}:{}".format(sim["host"], sim["path"])
    else:
        return sim["path"]


def ensure_list(x):
    try:
        len(x)
        if isinstance(x, str):
            x = [x]
    except TypeError:
        x = [x]
    return x


def exists_remote(sim):
    """ Verify that the simulation exists on the remote host. """
    if sim["host"] == "localhost":
        return os.path.isdir(sim["path"])
    ans = search_net(sim, action="verify", update=True)
    return len(ans) > 0


def search_net(patterns=None, host="localhost", update=False, action="search"):
    """ Search for a pattern using the smurfnet relay server.
    
    Paramters
    ---------
    patterns: list of str
        Patterns to search.
    host: str
        Relay server.
    update: bool
        Invalidate cache and force new search.

    Returns
    -------
    dict
        Search results.
    """
    from smurfnet.client import make_request
    import urllib.parse
    query = dict(
        pattern=patterns
    )
    query = {k:v for k,v in query.items() if v is not None}
    uri = urllib.parse.urlencode(query, doseq=True)
    url = f"smurf://{host}/{action}?{uri}"
    if update:
        url += "#update"
    rv = make_request(url)
    return rv


def search(patterns,
           unique=False,
           exclusive=False,
           verbose=False,
           remote=True,
           force_global=False,
           ensure_exist=False):
    """Search local and remote caches for simulations which match given patterns.

    Parameters
    ----------
    patterns : sequence
        A list containing patterns to search for.
    unique : bool
        Throw an exception if there is more than one result.
    remote : bool
        Search remote hosts if True, else only search local.
    force_global : bool
        Force querying remote hosts and skip cached results.
    ensure_exist : bool
        Ensure that the result exists on the remote server and initiate new search if not.

    Returns
    -------
    list of dict
        Simulations that match the search patterns.
    """
    patterns = ensure_list(patterns)

    conf = smurf.Config()
    if "relay-server" in conf.data:
        rv = search_net(
            patterns=patterns, 
            host=conf.data["relay-server"])
        rv = json.loads(rv)
        return rv


    rv = search_local_cache(patterns,
                            fields=cache.sim_attributes,
                            unique=False,
                            exclusive=exclusive)
    if remote:
        rv += search_remote_cache(patterns,
                                  fields=cache.sim_attributes,
                                  unique=False,
                                  exclusive=exclusive)
    if ensure_exist:
        to_del = []
        for n, s in enumerate(rv):
            if not exists_remote(s):
                to_del.append(n)
        for k, m in enumerate(to_del):
            simid = rv[m-k]["uuid"]
            cache.RemoteSimCache().remove(simid)
            del rv[m - k]
    if (len(rv) == 0 and remote) or force_global:
        try:
            rv = search_global(patterns, verbose=verbose, exclusive=exclusive)
        except KeyError as e:
            pass
    if len(rv) > 1 and unique:
        from smurf.cache import ResultNotUniqueError
        raise ResultNotUniqueError(
            "Search result is not unique! {} results found.".format(len(rv)))
    return rv


def search_local_cache(patterns, **kwargs):
    try:
        c = cache.LocalSimCache()
        rv = c.search(patterns, **kwargs)
        for r in rv:
            r["host"] = "localhost"
    except (KeyError, cache.NoSimulationFoundError):
        return []
    return rv


def search_remote_cache(patterns, **kwargs):
    try:
        c = cache.RemoteSimCache()
        rv = c.search(patterns, **kwargs)
    except (KeyError, cache.NoSimulationFoundError):
        return []
    return rv


def search_remote(args):
    host = args[0]
    patterns = args[1]
    verbose = args[2]
    exclusive = args[3]
    res = search_net(patterns=patterns, host=host)
    simulations = json.loads(res)
    for sim in simulations:
        sim["host"] = host
    return simulations


def search_global(patterns, verbose=False, exclusive=False, remote_cache=None):
    from smurfnet.config import Config as NetConfig
    conf = NetConfig()
    hosts = [key for key in conf["hosts"]]
    args = [[h, patterns, verbose, exclusive] for h in hosts]
    try:
        from multiprocessing.pool import ThreadPool as Pool
        with Pool() as p:
            res = p.map(search_remote, args)
    except ImportError:
        res = []
        for arg in args:
            res.append(search_remote(arg))
    rv = []
    for host, r in zip(hosts, res):
        if len(res) > 0:
            rv += r
    # add results to remote cache
    c = cache.RemoteSimCache() if remote_cache is None else remote_cache
    for sim in rv:
        c.add_sim_to_cache(sim)
    if len(rv) == 0:
        rv = search_local_cache(patterns)
    return rv


if __name__ == "__main__":
    main()
