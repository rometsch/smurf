# Initialize a simdir
import os
from smurf.info import is_simdir, Info
import sys


def main():
    args = parse_command_line_args()
    path = args.directory

    if is_simdir(path):
        sys.exit(1)

    init(path)


def init(path):
    if is_simdir(path):
        raise ValueError(
            "The directory is already a simdir! '{}'".format(path))

    name = os.path.basename(path)
    info = Info(path=path, create=True)
    info.name = name
    info.save()


def parse_command_line_args():
    import argparse, argcomplete
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        nargs="?",
        default=os.getcwd(),
        help="Directory to initialize simdir in. [default: current directory]."
    )
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
