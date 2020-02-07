# Caller for scripts in the smurf package
import os, sys
from subprocess import run

this_files_dir = os.path.dirname(os.path.abspath(__file__))


def main():
    args = parse_command_line_args()
    name = args.script
    if script_file_name(name)[-3:] == ".py":
        import importlib
        script_module = importlib.import_module("." + name, package="smurf")
        sys.argv = [os.path.join(this_files_dir, name + ".py")] + sys.argv[2:]
        script_module.main()
    else:
        run([script_path(name)] + args.args)


def parse_command_line_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("script",
                        choices=available_scripts(),
                        help="name of the script to run")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    return args


def available_scripts(filenames=False):
    files = os.listdir(this_files_dir)
    python_scripts = [f for f in files if f[-3:] == ".py" and not f[0] == "_"]
    bash_scripts = [f for f in files if f[-3:] == ".sh"]
    scripts = [f[:-3] for f in python_scripts]
    script_filenames = [f for f in python_scripts]
    for f in bash_scripts:
        name = f[:-3]
        if name not in scripts:
            scripts.append(name)
            script_filenames.append(f)
    scripts.sort()
    script_filenames.sort()
    scripts = filter_backend_scripts(scripts)
    script_filenames = filter_backend_scripts(script_filenames)
    if filenames:
        return script_filenames
    else:
        return scripts


def filter_backend_scripts(unfiltered):
    to_filter = ["simdata_integration", "doublefork", "mount"]
    rv = []
    for s in unfiltered:
        if all([x not in s for x in to_filter]):
            rv.append(s)
    return rv


def script_file_name(name):
    files = os.listdir(this_files_dir)
    for f in files:
        if f.startswith(name):
            bash_name = f[:-3] + ".sh"
            python_name = f[:-3] + ".py"
            if python_name in files:
                return python_name
            else:
                return bash_name
    raise FileNotFoundError(
        "Could not find script file for script '{}'".format(name))


def script_path(name):
    return os.path.join(this_files_dir, script_file_name(name))


if __name__ == "__main__":
    main()
