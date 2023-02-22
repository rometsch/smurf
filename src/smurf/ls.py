# List the current directory and translate uuid directory names to the corresponding name saved inside the meta dir if existing.
import os
from pathlib import Path

from smurf.info import is_simdir, Info

maxlen = 8

def main():
    args = parse_command_line_args()
    path = args.directory

    listdir(path, full_paths=args.f, print_tags=args.tags)


def listdir(path, full_paths=False, print_tags=False):
    path = Path(path)
    names = []
    files = []
    tags = []
    for p in path.glob("*"):
        relp = p.relative_to(path)
        files.append(f"{relp}")
        if is_simdir(p):
            info = Info(p)
            name = info.name
            names.append(name)
            tags.append(", ".join(sorted(info.get_tags())))
        else:
            name = f"{relp}"
            names.append(name)
            tags.append("")

    longest = max([len(n) for n in names])
    nameptrn = "{:" + f"{longest}" + "}"
    
    longest = max([len(t) for t in tags])
    tagptrn = "{:" + f"{longest}" + "}"

    inds = [x for _, x in sorted(zip(names, list(range(len(names)))))]

    for i in inds:
        name = names[i]
        tag = tags[i]
        file = files[i]
        if file == name:
            print(nameptrn.format(name))
        else:
            dst = file
            if len(dst) > maxlen and not full_paths:
                dst = f"{dst[:maxlen]}..."
            line = nameptrn.format(name)
            if  print_tags:
                line += " | " + tagptrn.format(tag)
            line += " -> " + dst
            print(line)


def parse_command_line_args():
    import argparse
    import argcomplete
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        nargs="?",
        default=os.getcwd(),
        help="Directory to list. [default: current directory]."
    )
    parser.add_argument(
        "-f",
        action="store_true",
        help="Print full directory names."
    )
    parser.add_argument(
        "-t",
        "--tags",
        action="store_true",
        help="Print tags at end of line."
    )
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
