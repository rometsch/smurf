""" Enable the shell plugin of smurf. """
import os
import shutil

package_name = "smurf"


def main():
    # define paths to dirs and files
    package_dir = os.path.dirname(__file__)
    plugin_file = os.path.join(package_dir, "shell_plugin")
    completion_file = os.path.join(package_dir, "shell_completion")
    dot_dir = os.path.expanduser("~/." + package_name)

    # write a file for the shell completion to hint at the package dir
    if not os.path.exists(dot_dir):
        os.makedirs(dot_dir)
    with open(os.path.join(dot_dir, "script_dir.txt"), "w") as of:
        of.write(package_dir)

    # copy files
    shutil.copy2(plugin_file, dot_dir)
    shutil.copy2(completion_file, dot_dir)

    print_hints()


def print_hints():
    """ Print instructions on how to activate the plugin. """
    print("To activate the shell plugin for this session, run:")
    print("source ~/.smurf/shell_plugin")
    if not plugin_in_rc_file():
        print("Add the following lines to your rc file:")
        print("# smurf: enable shell plugin")
        print("[[ -f ~/.smurf/shell_plugin ]] && source ~/.smurf/shell_plugin")


def plugin_in_rc_file():
    """ Check whether the shell plugin is sources in the rc file """
    rc_file = get_shell_rc_file()
    if rc_file is None:
        return False
    pattern = "[[ -f ~/.smurf/shell_plugin ]] && source ~/.smurf/shell_plugin"
    with open(rc_file, "r") as infile:
        if pattern in infile.read():
            return True
    return False


def get_shell_rc_file():
    """ Guess the path to the shell's rc file. """
    shell_path = os.getenv("SHELL")
    if "zsh" in shell_path:
        return os.path.expanduser("~/.zshrc")
    elif "bash" in shell_path:
        return os.path.expanduser("~/.bashrc")
    else:
        print("Shell is neither bash nor zsh. You're on your own!")
        None


if __name__ == "__main__":
    main()
