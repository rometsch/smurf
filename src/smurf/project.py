#!/usr/bin/env python3
# find the root folder of the project indicated by a .project file containing the projects name
import os
import sys


def main():
    import argparse
    aprs = argparse.ArgumentParser()
    aprs.add_argument("information",
                      help="Type of information to get.",
                      choices={"name", "root"})
    aprs.add_argument(
        "simulation",
        nargs="?",
        default=os.getcwd(),
        help=
        "The simulation (ids or dir) to process. [default: current directory]."
    )
    args = aprs.parse_args()

    if args.information == "name":
        try:
            print(project_name(args.simulation))
        except FileNotFoundError:
            sys.exit(1)
    elif args.information == "root":
        try:
            print(project_root(args.simulation))
        except FileNotFoundError:
            sys.exit(1)


def project_root(d):
    d = os.path.abspath(d)
    while d != "/":
        project_file = os.path.join(d, ".project")
        if os.path.exists(project_file):
            return os.path.abspath(d)
        d = os.path.dirname(d)
    raise FileNotFoundError


def project_name(d):
    root = project_root(d)
    with open(os.path.join(root, ".project")) as infile:
        rv = infile.read().strip()
    return rv


if __name__ == "__main__":
    main()
