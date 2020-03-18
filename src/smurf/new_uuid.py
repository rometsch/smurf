""" Give an existing simdir a fresh uuid. """
import os
import sys

from smurf.info import Info, is_simdir


def main():
    args = parse_command_line_args()
    path = args.directory
    new_uuid(path)


def new_uuid(path):
    if not is_simdir(path):
        sys.tracebacklimit = 0
        raise ValueError("The directory is not a simdir! '{}'".format(path) +
                         "\nMaybe you want to use 'smurf init' instead?")

    info = Info(path=path, create=False)
    info.generate_uuid()
    info.save()


def parse_command_line_args():
    import argparse
    import argcomplete
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        nargs="?",
        default=os.getcwd(),
        help="Directory to give a new uuid to. [default: current directory].")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
