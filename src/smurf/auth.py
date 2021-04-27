""" Handle tasks associated with authentication to remote hosts.

Smurf uses ssh keys to handle authentication because these can be expected
to be available in an HPC context.

Keys used by smurf are password less which is dangerous because it allows
any malicious actor to take over remote hosts should the local host
be compromised.
To mitigate this risk, smurf uses ssh command restriction. 
Using this technique, only a single predefined command can be executed 
on the remote host.
"""

import os
import subprocess

from smurf import config

def main():
    c = config.Config()
    for host in c["host_list"]:
        priv_key_path, _ = get_key_paths(host)
        if not os.path.exists(priv_key_path):
            print(f"No smurf ssh key found for host '{host}' : setting up new key...")
            setup_smurf_ssh_key(host)
        else:
            print(f"Smurf ssh key found for host '{host}' : '{priv_key_path}'")
    

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
    comment = "'limited smurf access from {}@{}'".format(
        os.environ["USER"], os.uname()[1])
    subprocess.run(["ssh-keygen", "-C", comment, "-N",
                    "", "-f", priv_key_path], check=True)


def get_pub_key(host):
    """ Get the public key data for a host. 

    Parameters
    ----------
    host : str
        Hostname of the remote host.

    Returns
    -------
    str
        Public key and comment.
    """
    _, pub_key_path = get_key_paths(host)
    with open(pub_key_path, "r") as infile:
        content = infile.read().strip()
    return content


def copy_ssh_key(host):
    """ Copy the smurf key to the remote host and setup command restriction.

    This is done by preparing a temporary file and copying
    its content using ssh-copy-id.

    Parameters
    ----------
    host : str
        Remote host to register key on.
    """
    preprend = 'command="~/.local/bin/smurf --use-ssh-original-command",no-agent-forwarding,no-port-forwarding,no-pty,no-user-rc,no-X11-forwarding'
    content = preprend + " " + get_pub_key(host)
    _, pub_key_path = get_key_paths(host)
    os.rename(pub_key_path, pub_key_path + ".bak")
    with open(pub_key_path, "w") as outfile:
        outfile.write(content)
    subprocess.run(["ssh-copy-id", "-i", pub_key_path, host], check=True)
    os.rename(pub_key_path + ".bak", pub_key_path)


def setup_smurf_ssh_key(host):
    """ Generates a key for smurf and copy it to the remote host.

    Parameters
    ----------
    host : str
        Hostname of the remote host.
    """
    generate_ssh_key(host)
    copy_ssh_key(host)


if __name__ == "__main__":
    main()
