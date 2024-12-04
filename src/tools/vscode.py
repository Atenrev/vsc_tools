import argparse
import getpass
import paramiko
import subprocess
import re
import time
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
        username=host.get("user"),
        pkey=pkey,
        look_for_keys=False,
        sock=sock if gateway else None,
    )
    return client


def allocate_compute_node(ssh, time_limit="01:00:00"):
    """Allocate a compute node using SLURM's salloc command."""
    salloc_cmd = f"salloc -n 1 -t {time_limit} --ntasks=4 --gpus-per-node=1 -A lcomputervision --partition=gpu --cluster=wice"
    
    stdin, stdout, stderr = ssh.exec_command(salloc_cmd, get_pty=True)

    node_address = None
    output_buffer = ""
    while True:
        # Read available output without blocking
        if stdout.channel.recv_ready():
            output = stdout.channel.recv(1024).decode('utf-8')
            output_buffer += output
            logging.info(output.strip())  # logging.info output for debugging/logging

            # Check for the compute node allocation message
            match = re.search(r'salloc: Nodes (\S+) are ready for job', output_buffer)
            if match:
                node_address = match.group(1)
                break

        # Exit if the command completes
        if stdout.channel.exit_status_ready():
            break

        # Avoid busy-waiting
        time.sleep(1)

    return node_address


def open_vscode_remote(identity_file, username, compute_node, project_folder="~"):
    """Open VS Code remote session via PowerShell."""
    try:
        # Construct the PowerShell command
        command = [
            "powershell",
            "-Command",
            f"code --remote ssh-remote+{compute_node} {project_folder}"
        ]
        # Execute the command
        subprocess.run(command, check=True)
        logging.info(f"VS Code successfully launched for remote: {username}@{compute_node}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to open VS Code remote session: {e}")


def launch_vscode(args):
    logging.basicConfig()

    logging.info("Opening an interactive session on the remote machine...")
    passphrase = getpass.getpass("Enter passphrase for private key (leave empty if none): ")
    passphrase = bytes(passphrase, "utf-8") if passphrase else None
    
    pkey = from_private_key(open(args.identity_file), passphrase)

    # Connect to the remote machine
    ssh = connect(args.hostname, args.config_file, pkey, None)

    # Execute the command via SSH
    compute_node = allocate_compute_node(ssh)

    if compute_node:
        logging.info(f"Assigned machine: {compute_node}")

        # Open VS Code to the assigned machine
        open_vscode_remote(args.identity_file, args.username, compute_node)

        # Loop to keep the session alive
        while True:
            time.sleep(1)
    else:
        logging.error("Failed to get assigned machine.")
