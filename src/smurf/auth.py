""" Handle tasks associated with authentication to remote hosts.

Smurf uses ssh keys to handle authentication because these can be expected
to be available in an HPC context.

Keys used by smurf are password less which is dangerous because it allows
any malicious actor to take over remote hosts should the local host
be compromised.
To mitigate this risk, smurf uses ssh jails. Using this technique, only a
single predefined command can be executed on the remote host.
"""

import os
import subprocess


def get_key_dir():
    """ Return the key directory and make sure it exists.

    Returns
    -------
    str
        Path to the key directory.
    """
    key_dir = os.path.expanduser("~/.smurf/keys")
    if not os.path.isdir(key_dir):
        os.makedirs(key_dir)
    return key_dir


def get_key_paths(host):
    """ Return the paths to private and public keys.

    Parameters
    ----------
    host : str
        Hostname of the remote host.

    Returns
    -------
    str
        Path to private key file.
    str
        Path to public key file.
    """
    key_dir = get_key_dir()
    priv_key_path = os.path.join(key_dir, "id_rsa_smurf_" + host)
    pub_key_path = priv_key_path + ".pub"
    return (priv_key_path, pub_key_path)


def generate_ssh_key(host):
    """ Generate a ssh key to allow smurf to connect to host.

    Keys are stored in the ~/.smurf directory under the keys directory.

    Parameters
    ----------
    host : str
        Hostname of the remote host to setup keys for.
    """
    priv_key_path, _ = get_key_paths(host)
    subprocess.run(["ssh-keygen", "-N", "", "-f", priv_key_path], check=True)
