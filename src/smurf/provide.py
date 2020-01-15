#!/usr/bin/env python3
# Provide a source copy of a setup along with
# a copy of the simulation source code
# in a single folder.
# If no output path is specified, create a temporary one.
import importlib
import argparse
import os
from subprocess import run, PIPE
import tempfile
import uuid
import json
import smurf

meta_info_dir = "meta"


def main():

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "config",
        help='Config file containing the paths of files to be copied"')
    arg_parser.add_argument(
        "--name", help="Name of the simulation used to construct a tar file.")
    arg_parser.add_argument(
        "--dst",
        default=os.getcwd(),
        help="Destination (with scp syntax) where to copy the tar file to.")
    arg_parser.add_argument("--keep",
                            default=False,
                            action="store_true",
                            help="Don't remove the temporary dir")
    args = arg_parser.parse_args()

    provider = Provider(args.config, keep=args.keep)

    provider.make_tar(name=args.name)
    if args.dst:
        provider.copy_tar_to(args.dst, name=args.name)

    print(provider.outDir)


class Provider:
    def __init__(self, configFile, name=None, keep=False, note=""):
        self.configFile = os.path.expanduser(configFile)
        self.outDir = None
        self.uuid = str(uuid.uuid4())
        self.short_uuid = self.uuid.split("-")[0]
        if name is None:
            self.name = self.uuid
        else:
            self.name = name
        self.param = None
        self.info = None
        self.note = note
        self.dst = None
        self.keep = keep
        self.provide()

    def __del__(self):
        if not self.keep:
            run(["rm", "-rf", self.outDir])

    def __str__(self):
        # describe the simulation
        rv = "uuid : {}".format(self.uuid)
        if self.name is not None:
            rv += "\nname : " + self.name
        if self.dst is not None:
            rv += "\npath : " + self.dst
        if self.note != "":
            rv += "\nnote : " + self.note
        return rv

    def provide(self):
        #provide a temp dir to work in
        self.outDir = tempfile.mkdtemp()

        self.config = parse_config(self.configFile)

        copy_sources(self.outDir, self.config["sources"])
        os.makedirs(os.path.join(self.outDir, 'output'), exist_ok=True)
        add_runscript_in_root(self.outDir)
        ensure_meta_dir(self.outDir)
        add_name(self.outDir, self.name)
        add_uuid(self.outDir, self.uuid)
        add_note(self.outDir, self.note)
        if "tags" in self.config:
            add_tags(self.outDir, self.config["tags"])
        if "simcode" in self.config:
            add_simcode_info(self.outDir, self.config["simcode"])
        self.info = smurf.Info(self.outDir)
        return self.outDir

    def add_tag(self, tag):
        add_tags(self.outDir, [tag])

    def make_tar(self, name=None):
        tar_file = self.create_tarname(name)
        run(["tar", "-C", self.outDir, "-czvf", tar_file] +
            os.listdir(self.outDir),
            stdout=PIPE)
        return tar_file

    def copy_tar_to(self, dst, name=None):
        self.dst = dst
        tar_file = self.make_tar(name=name)
        run(["scp", tar_file, dst])

    def create_tarname(self, name=None):
        filename = self.short_uuid + "-"
        name = self.name if name is None else name
        filename += name.replace(" ", "_")
        # make a tar file of the out dir
        tar_file = os.path.join(self.outDir, filename + ".tgz")
        return tar_file


def copy_sources(outDir, sources):
    for src in sources:
        make_clean_source(outDir, src)
        make_dirs(outDir, src)
        copy_list(outDir, src["root"], src["copy"])


def make_clean_source(outDir, src):
    if "makeclean" in src:
        if isinstance(src["makeclean"], str):
            l = [src["makeclean"]]
        else:
            l = src["makeclean"]
        for clean_dir in l:
            run(["make", "clean", "-C",
                 os.path.join(src["root"], clean_dir)],
                stdout=PIPE,
                stderr=PIPE)


def make_dirs(outDir, src):
    if "mkdir" in src:
        for md in src["mkdir"]:
            os.makedirs(os.path.join(outDir, md))


def ensure_meta_dir(outDir):
    if not os.path.isdir(os.path.join(outDir, meta_info_dir)):
        os.makedirs(os.path.join(outDir, meta_info_dir))


def add_uuid(outDir, uuidstr):
    os.makedirs(os.path.join(outDir, meta_info_dir, "uuid"))
    open(os.path.join(outDir, meta_info_dir, "uuid", uuidstr), "a").close()


def add_tags(outDir, tags):
    with open(os.path.join(outDir, meta_info_dir, "tags.txt"), "a") as tagfile:
        for tag in tags:
            print(tag, file=tagfile)


def add_simcode_info(outDir, simcode):
    with open(os.path.join(outDir, meta_info_dir, "simcode.txt"),
              "a") as outfile:
        print(simcode, file=outfile)
    with open(os.path.join(outDir, meta_info_dir, "tags.txt"), "a") as tagfile:
        print(simcode, file=tagfile)


def add_note(outDir, note):
    with open(os.path.join(outDir, meta_info_dir, "note.txt"), "a") as outfile:
        print(note, file=outfile)


def add_name(outDir, note):
    with open(os.path.join(outDir, meta_info_dir, "name.txt"), "a") as outfile:
        print(note, file=outfile)


def add_runscript_in_root(outDir):
    ### link the run script
    if os.path.exists(os.path.join(outDir, meta_info_dir, "run.sh")):
        os.symlink('meta/run.sh', os.path.join(outDir, 'run.sh'))


def copy(src, dst):
    # a wrapper around cp
    if isinstance(src, str):
        src = [src]
    run(['cp', '-r'] + src + [dst])


def path_abs(root, path):
    # return the an absolute path
    # either with joined with root
    # or unaltered if its already absolute
    path = os.path.expanduser(path)
    root = os.path.expanduser(root)
    if os.path.abspath(path) == path:
        return path
    else:
        return os.path.join(root, path)


def copy_list(outDir, srcroot, copylist):
    for d in copylist:
        src = path_abs(srcroot, d["src"])
        if "dst" in d:
            dst = os.path.join(outDir, d["dst"])
        else:
            dst = outDir
        copy(src, dst)


def parse_config(configFile):
    ### parse config files with version 0.1
    if os.path.splitext(configFile)[1] != ".json":
        raise ValueError(
            "Only json config files are supported but extention is '{}'!".
            format(os.path.splitext(configFile)[1]))

    ### load json file
    with open(configFile) as infile:
        rv = json.loads(infile.read())

    ### check version
    if rv["version"] != "0.1":
        raise ValueError("Unsupported version of config file '{}'".format(
            rv["version"]))

    ### check code to use config with
    if rv["usewith"] != "smurf provide":
        raise ValueError(
            "Config file is intended for another code ('{}'), should be 'simprepare provide'"
            .format(rv["code"]))

    ### substitude '.' with the dir containing the config file
    for src in rv["sources"]:
        if src["root"] == ".":
            src["root"] = os.path.dirname(os.path.abspath(configFile))

    return rv


if __name__ == "__main__":
    main()
