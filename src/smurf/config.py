#!/usr/bin/env python3
# Config structure for smurf.
import os
import sys
import json

home_path = os.path.join(os.path.expanduser("~"), ".smurf")

information_types = ["rootdir", "host", "web_host"]


def main():
    args = parse_command_line_args()
    c = Config()

    if args.subparser_name in ["show"] or args.subparser_name is None:
        args.func(c)
    elif args.subparser_name in ["get"]:
        args.func(c, args.key)
    else:
        args.func(c, args.key, args.value)


def parse_command_line_args():
    import argparse, argcomplete
    import pprint
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=Config.print)

    subparsers = parser.add_subparsers(dest='subparser_name')
    parser_add = subparsers.add_parser('add', help='Add a config item.')
    parser_add.add_argument("key",
                            choices=information_types,
                            help="What to set.")
    parser_add.add_argument("value")
    parser_add.set_defaults(func=Config.add)

    parser_remove = subparsers.add_parser('remove',
                                          help='Remove a config item.')
    parser_remove.add_argument("key",
                               choices=information_types,
                               help="What to set.")
    parser_remove.add_argument("value")
    parser_remove.set_defaults(func=Config.remove)

    parser_show = subparsers.add_parser('show', help='Show the config.')
    parser_show.set_defaults(func=Config.print)
    parser_get = subparsers.add_parser(
        'get', help='Return the value of a root level config item.')
    parser_get.add_argument("key", help="What to get.")
    parser_get.set_defaults(func=Config.print_value)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    return args


def expand_path(path):
    abspath = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(abspath):
        raise FileNotFoundError("No such directory: {}".format(path))
    return abspath


def check_information_type(info_type):
    if not any((info_type == t for t in information_types)):
        raise AttributeError("Information type {} not supported".format(what))


class Config:
    def __init__(self):
        if not os.path.exists(home_path):
            os.makedirs(home_path)
        self.config_file = os.path.join(home_path, "config.json")
        self.load()

    def add(self, what, val):
        check_information_type(what)
        if what == "rootdir":
            self.add_rootdir(val)
        if what == "host":
            list_name = what + "_list"
            if not list_name in self.data:
                self.data[list_name] = []
            self.data[list_name].append(val)
        else:
            self.data[what] = val
        self.save()

    def remove(self, what, val):
        check_information_type(what)
        list_name = what + "_list"
        try:
            for n in range(len(self.data[list_name])):
                if self.data[list_name][n] == val:
                    del self.data[list_name][n]
                    break
            self.save()
        except KeyError:
            print("No config for type", what)
            pass

    def add_rootdir(self, path):
        if not "rootdir_list" in self.data:
            self.data["rootdir_list"] = []
        abspath = expand_path(path)
        # only insert if not already there
        try:
            for n, p in enumerate(self.data["rootdir_list"]):
                # check if its a parent of an already registered dir
                if abspath == os.path.commonpath([abspath, p]):
                    self.data["rootdir_list"][n] = abspath
                    raise StopIteration
        except StopIteration:
            pass
        else:
            self.data["rootdir_list"].append(abspath)
        finally:
            self.save()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, val):
        self.data[key] = val

    def save(self):
        self.data["type"] = "smurf config"
        self.data["version"] = "0.1"
        with open(self.config_file, "w") as outfile:
            outfile.write(json.dumps(self.data, indent=4))

    def load(self):
        try:
            with open(self.config_file, "r") as infile:
                self.data = json.load(infile)
        except FileNotFoundError:
            self.data = {}
            self.data["rootdir_list"] = []
            self.data["host_list"] = []
            self.data["home_path"] = home_path
            self.data["local_cache"] = "local_simcache.json"
            self.data["remote_cache"] = "remote_simcache.json"

    def print(self):
        import pprint
        pprint.pprint(self.data)

    def print_value(self, key):
        try:
            print(self[key])
        except KeyError:
            print("Error: No config value found for key '{}'".format(key))
            sys.exit(1)


if __name__ == "__main__":
    main()
