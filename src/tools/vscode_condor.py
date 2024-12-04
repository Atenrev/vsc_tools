import argparse
import getpass
import paramiko
import subprocess
import re
import sys
import time
import threading
import logging


from io import StringIO
from paramiko import RSAKey, Ed25519Key, ECDSAKey, DSSKey, PKey
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, dsa, rsa, ec


def from_private_key(file_obj, password=None) -> PKey:
    private_key = None
    file_bytes = bytes(file_obj.read(), "utf-8")
    try:
        key = crypto_serialization.load_ssh_private_key(
            file_bytes,
            password=password,
        )
        file_obj.seek(0)
    except ValueError:
        key = crypto_serialization.load_pem_private_key(
            file_bytes,
            password=password,
        )
        if password:
            encryption_algorithm = crypto_serialization.BestAvailableEncryption(
                password
            )
        else:
            encryption_algorithm = crypto_serialization.NoEncryption()
        file_obj = StringIO(
            key.private_bytes(
                crypto_serialization.Encoding.PEM,
                crypto_serialization.PrivateFormat.OpenSSH,
                encryption_algorithm,
            ).decode("utf-8")
        )
    if isinstance(key, rsa.RSAPrivateKey):
        private_key = RSAKey.from_private_key(file_obj, password)
    elif isinstance(key, ed25519.Ed25519PrivateKey):
        private_key = Ed25519Key.from_private_key(file_obj, password)
    elif isinstance(key, ec.EllipticCurvePrivateKey):
        private_key = ECDSAKey.from_private_key(file_obj, password)
    elif isinstance(key, dsa.DSAPrivateKey):
        private_key = DSSKey.from_private_key(file_obj, password)
    else:
        raise TypeError
    return private_key


def parse_args():
    parser = argparse.ArgumentParser(description="Open an interactive session on a remote machine and connect with vscode.")
    parser.add_argument("--username", default="smasipca", type=str, help="Username to use for SSH connection.")
    parser.add_argument("--hostname", default="nickeline", type=str, help="Hostname or IP address of the remote machine.")
    parser.add_argument("--config_file", default="C:/Users/thema/.ssh/config", type=str, help="Path to the SSH config file.")
    parser.add_argument("--identity_file", default="C:/Claus/esat_jonen", type=str, help="Path to the private key file.")
    return parser.parse_args()


def keep_alive(client):
    # Keep the session alive by periodically sending a command
    while True:
        # Send a simple command to keep the session alive
        _, _, _ = client.exec_command('echo keep-alive')
        time.sleep(60)  # Adjust the interval as needed


def connect(hostname, config_file, pkey, gateway=None):
    if gateway:
        gateway_client = connect(gateway, config_file, pkey, None)
        sock = gateway_client.get_transport().open_channel(
            'direct-tcpip', (hostname, 22), ('', 0)
        )

    config = paramiko.SSHConfig.from_path(config_file)
    host = config.lookup(hostname)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host["hostname"],
        port=host.get("port", 22),
        username=host.get("user", "smasipca"),
        pkey=pkey,
        look_for_keys=False,
        sock=sock if gateway else None,
    )
    return client

def open_interactive_session_and_keep_alive(client):
    interactive_command = "condor_send --cpus 4 --mem 6 --gpumem 10 -t interactive"
    _, stdout, stderr = client.exec_command(interactive_command)

    if stderr.channel.recv_exit_status() != 0:
        print(f"Failed to execute command: {stderr.read().decode()}")
        sys.exit

    # Start a thread to keep the initial SSH session alive
    keep_alive_thread = threading.Thread(target=keep_alive, args=(client,))
    keep_alive_thread.daemon = True  # Daemonize thread
    keep_alive_thread.start()

    output = stdout.read().decode().strip()
    return output

def main(args):
    logging.basicConfig()
    logging.getLogger("paramiko").setLevel(logging.DEBUG)

    print("Opening an interactive session on the remote machine...")
    passphrase = getpass.getpass("Enter passphrase for private key (leave empty if none): ")
    passphrase = bytes(passphrase, "utf-8") if passphrase else None
    
    pkey = from_private_key(open(args.identity_file), passphrase)

    # Connect to the remote machine
    client = connect(args.hostname, args.config_file, pkey, "esat")

    # Execute the command via SSH
    output = open_interactive_session_and_keep_alive(client)

    # Parse the output to find the assigned machine address
    match = re.search(r"Welcome to (.+)@", output)

    if match:
        assigned_machine = match.group(1)
        print(f"Assigned machine: {assigned_machine}")

        # Open VS Code to the assigned machine
        vscode_command = f"code --remote \"ssh -i {args.identity_file} {args.username}@{assigned_machine}\""
        subprocess.run(vscode_command, shell=True)
    else:
        print("Failed to get assigned machine.")

if __name__ == "__main__":
    args = parse_args()
    main(args)
