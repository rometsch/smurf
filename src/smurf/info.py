# Obtain information about the simulation of the given path
import os
import sys

meta_dir_names = ["meta", "job", ".sheep.d"]


def main():
    args = parse_command_line_args()

    try:
        sinfo = Info(args.dir)
        if args.choice is None:
            rv = str(sinfo)
        else:
            rv = getattr(sinfo, args.choice)
        if isinstance(rv, list):
            rv = ", ".join(rv)
        print(rv)
    except FileNotFoundError:
        sys.exit(1)


def parse_command_line_args():
    import argparse
    import argcomplete
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "choice",
        choices=["uuid", "name", "tags", "simcode", "path", "note"],
        nargs="?",
        help="Property to show.")
    parser.add_argument(
        "-d",
        "--dir",
        nargs="?",
        default=os.getcwd(),
        help="The path to start the search from. [default: current directory]."
    )
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    return args


class Info:
    def __init__(self, path=os.getcwd(), create=False):
        self.uuid = ""
        self.name = ""
        self.tags = []
        self.simcode = ""
        self.path = ""
        self.note = ""
        try:
            self.path = find_simdir(path)
            self.load(path)
        except FileNotFoundError:
            if create:
                self.path = path
                self.generate_uuid()
            else:
                raise

    def load(self, path):
        self.path = find_simdir(path)
        for meta_dir in meta_dir_names:
            if os.path.isdir(os.path.join(self.path, meta_dir)):
                self.meta_dir = os.path.join(self.path, meta_dir)
                break
        self.uuid = self.get_uuid()
        self.name = self.get_name()
        self.tags = self.get_tags()
        self.simcode = self.get_simcode()
        self.path = self.get_path()
        self.note = self.get_note()

    def save(self):
        self.meta_dir = os.path.join(self.path, "meta")
        os.makedirs(self.meta_dir, exist_ok=True)
        self.save_uuid()
        self.save_name()
        self.save_tags()
        self.save_simcode()
        self.save_note()
        print("uuid =", self.uuid)
        print("name =", self.name)

    def get_uuid(self):
        try:
            return get_uuid(self.path)
        except IndexError:
            return ""

    def save_uuid(self):
        uuid_dir = os.path.join(self.meta_dir, "uuid")
        os.makedirs(uuid_dir, exist_ok=True)
        for fname in os.listdir(uuid_dir):
            if all((fname[n] == "-" for n in (8, 13, 18, 23))):
                # filename is most probably a uuid
                os.remove(os.path.join(uuid_dir, fname))
        with open(os.path.join(uuid_dir, self.uuid), "w"):
            pass

    def get_name(self):
        try:
            with open(os.path.join(self.meta_dir, "name.txt")) as infile:
                rv = infile.read().strip()
            return rv
        except FileNotFoundError:
            return os.path.basename(self.get_path())

    def save_name(self):
        with open(os.path.join(self.meta_dir, "name.txt"), "w") as outfile:
            print(self.name, file=outfile)

    def get_note(self):
        try:
            with open(os.path.join(self.meta_dir, "note.txt")) as infile:
                rv = infile.read().strip()
            return rv
        except FileNotFoundError:
            return ""

    def save_note(self):
        with open(os.path.join(self.meta_dir, "note.txt"), "w") as outfile:
            print(self.note, file=outfile)

    def get_tags(self):
        try:
            tags = []
            with open(os.path.join(self.meta_dir, "tags.txt")) as infile:
                for line in infile:
                    tags.append(line.strip())
            return sorted(tags)
        except FileNotFoundError:
            return []

    def save_tags(self):
        with open(os.path.join(self.meta_dir, "tags.txt"), "w") as outfile:
            for tag in self.tags:
                print(tag, file=outfile)

    def get_simcode(self):
        try:
            with open(os.path.join(self.meta_dir, "simcode.txt")) as infile:
                rv = infile.read().strip()
            return rv
        except FileNotFoundError:
            return ""

    def save_simcode(self):
        with open(os.path.join(self.meta_dir, "simcode.txt"), "w") as outfile:
            print(self.simcode, file=outfile)

    def get_path(self):
        return self.path

    def __str__(self):
        col_len = 10
        template = "{:" + str(col_len) + "s} : {}"
        entries = []
        for attr in ["name", "uuid", "tags", "simcode", "path", "note"]:
            try:
                s = getattr(self, attr)
                if attr == "note":
                    s = ("\n" + " " * col_len + " : ").join(s.split("\n"))
                entries.append(template.format(attr, s))
            except AttributeError:
                pass
        return "\n".join(entries)

    def generate_uuid(self):
        import uuid
        self.uuid = str(uuid.uuid4())


def find_simdir(d):
    start_d = d
    d = os.path.abspath(d)
    while d != "/":
        try:
            get_uuid(d)
            return os.path.abspath(d)
        except FileNotFoundError:
            pass
        d = os.path.dirname(d)
    raise FileNotFoundError(
        "Could not find simdir starting at '{}'".format(start_d))


def get_uuid(d):
    # check for all known meta dir names
    for meta_dir in meta_dir_names:
        uuid_dir = os.path.join(d, meta_dir, "uuid")
        uuid_file = os.path.join(d, meta_dir, "uuid.txt")
        if os.path.exists(uuid_dir):
            if os.path.isfile(uuid_dir):
                return get_uuid_from_file(uuid_dir)
            else:
                try:
                    return os.listdir(uuid_dir)[0]
                except IndexError:
                    pass
        elif os.path.exists(uuid_file):
            return get_uuid_from_file(uuid_file)
    raise FileNotFoundError


def is_simdir(path):
    try:
        get_uuid(path)
        return True
    except FileNotFoundError:
        return False


def get_uuid_from_file(path):
    with open(path, "r") as infile:
        for line in infile:
            return line.strip()


if __name__ == "__main__":
    main()
