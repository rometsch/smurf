""" Handle connections to remote hosts. """

import os
import sys
import subprocess

from smurf import auth


def get_ssh_socket_path():
    """ Get the path for the ssh multiplexing socket.

    Returns
    -------
    str:
        Path to socket.
    """
    key_dir = auth.get_key_dir()
    socket_path = os.path.join(key_dir, "%C")
    return socket_path


def multiplexed_ssh(host, cmd, multiplex_timeout="24h", **kwargs):
    """ Run command over a multiplexed ssh connection using smurf keys.

    If there is no key setup for the host, fall back to normal ssh.

    Parameters
    ----------
    host : str
        Host to connect to.
    cmd : list of str
        List of strings specifying commands to be run on remote host.
        This is the same syntax as used for subprocess.run.
    multiplex_timeout : str
        Value for the ssh multiplex ControlPersist option.
        The multiplexed connection is closed after this time if inactivity.
    **kwargs
        Passed to subprocess.run.

    Retruns
    -------
    subprocess.CompletedProcess
        Result of running the command.
    """
    priv_key_path, _ = auth.get_key_paths(host)
    if not os.path.exists(priv_key_path):
        print("No smurf ssh keys setup for host '{}'".format(host),
              file=sys.stderr)
        res = subprocess.run(["ssh", host]+cmd, **kwargs)
    else:
        socket_path = get_ssh_socket_path()
        res = subprocess.run(["ssh",
                              "-i", priv_key_path,
                              "-o", "IdentitiesOnly=yes",
                              "-o", "ControlMaster=auto",
                              "-o", "ControlPersist={}".format(
                                  multiplex_timeout),
                              "-o", "ControlPath={}".format(socket_path),
                              host] + cmd,
                             **kwargs)
    return res
