import argparse
import getpass
import paramiko
import subprocess
import re
import time
import logging

from src.utils import run_local_command, Remote, ComputeNode


CODE_COMMAND = "code"


def open_vscode_remote(compute_node: ComputeNode, project_folder: str = "~"):
    """Open VS Code remote session via PowerShell."""
    try:
        # Construct the PowerShell command
        command = [
            CODE_COMMAND,
            "--remote",
            f"ssh-remote+{compute_node.address}",
            project_folder,
        ]
        # Execute the command
        # subprocess.run(command, check=True)
        run_local_command(" ".join(command))
        logging.info(
            f"VS Code successfully launched for remote: {str(compute_node)}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to open VS Code remote session: {e}")


def launch_vscode(project_folder: str, hostname: str, config_file: str, allocation_time: str = "01:00:00"):
    logging.info("Opening an interactive session on the remote machine...")

    # Connect to the remote machine
    login_node: Remote = Remote(hostname, config_file)
    login_node.connect()

    # Execute the command via SSH
    compute_node = ComputeNode(login_node)
    compute_node.allocate(time_limit=allocation_time)

    if compute_node:
        logging.info(f"Assigned machine: {str(compute_node)}")

        # Open VS Code to the assigned machine
        open_vscode_remote(compute_node, project_folder=project_folder)

        # Loop to keep the session alive
        while True:
            time.sleep(1)
    else:
        logging.error("Failed to get assigned machine.")
