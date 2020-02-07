#!/usr/bin/env python3
import smurf.cache as cache
import smurf
import subprocess
import json

# timeout after which to cancel search if host does not respond
search_timeout = 10


def main():
    args = parse_command_line_args()

    rv = search(args.patterns,
                unique=args.unique,
                exclusive=args.exclusive_search,
                force_global=args.g)

    if args.json:
        import json
        print(json.dumps(rv, indent=4))
    elif args.print:
        for sim in rv:
            if args.print == "path":
                print(remote_path(sim))
            else:
                print(sim[args.print])
    else:
        print_table(rv)


def parse_command_line_args():
    import argparse, argcomplete
    parser = argparse.ArgumentParser()
    parser.add_argument("patterns", nargs="+", help="What to search for.")
    parser.add_argument("-v", "--verbose", default=False, action="store_true")
    parser.add_argument("-g",
                        default=False,
                        action="store_true",
                        help="Force searching all known hosts")
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
    fields = [("uuid", 8), ("host", 15), ("name", 40)]
    for info in info_list:
        s = ""
        for f, l in fields:
            s += ("{:" + str(l) + "s}\t").format(info[f][:l])
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
    res = run([
        "ssh", sim["host"], "'[[ -e \"{}\" ]] && exit 0 || exit 1'".format(
            sim["path"])
    ],
              stdout=subprocess.PIPE,
              stderr=subprocess.PIPE)
    return res.returncode == 0


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
    rv = search_local_cache(patterns,
                            fields=cache.sim_attributes,
                            unique=False,
                            exclusive=exclusive)
    try:
        c = cache.RemoteSimCache()
        if len(rv) == 0 and remote and not force_global:
            rv = search_remote_cache(patterns,
                                     fields=cache.sim_attributes,
                                     unique=False,
                                     exclusive=exclusive)
        if ensure_exist:
            to_del = []
            for n, s in enumerate(rv):
                if not exists_remote(sim):
                    to_del.append(n)
            for k, n in enumerate(to_del):
                del rv[n - k]
        if len(rv) == 0 or force_global:
            rv = search_global(patterns,
                               verbose=verbose,
                               exclusive=exclusive,
                               remote_cache=c)
    except KeyError:
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
    try:
        command = ["ssh", host, "$HOME/.local/bin/smurf", "cache", "--json"
                   ] + patterns
        if exclusive:
            command += ["-e"]
        res = subprocess.run(command,
                             check=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             timeout=search_timeout)
        stdout = res.stdout.decode("utf-8")
        if verbose:
            print("Response from '{}' for search patter '{}':\n{}".format(
                host, pattern, stdout))
        simulations = json.loads(stdout)
        for sim in simulations:
            sim["host"] = host
        return simulations
    except subprocess.CalledProcessError as e:
        if verbose:
            print("Exception occured during search on '{}': {}".format(
                host, e))
        return []


def search_global(patterns, verbose=False, exclusive=False, remote_cache=None):
    conf = smurf.Config()
    hosts = conf["host_list"]
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
        c = cache.LocalSimCache()
        rv = c.search(patterns)
    return rv


if __name__ == "__main__":
    main()
