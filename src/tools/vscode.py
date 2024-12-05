import subprocess
import logging

from src.utils import run_local_command, Remote, ComputeNode, add_host_to_ssh_config


CODE_COMMAND = "code"


def open_vscode_remote(compute_node: ComputeNode, config_file: str, project_folder: str = "~"):
    """Open VS Code remote session via PowerShell."""
    logging.info("Opening VS Code remote session...")
    
    assert compute_node.address is not None, "Compute node address is not set."
    
    add_host_to_ssh_config(
        hosts_file_path=config_file,
        proxyjump="VSC",
        hostname=compute_node.address,
        user=compute_node.login_node.username,
        identityfile=compute_node.login_node.identity_file_path
    )
    
    command = [
        CODE_COMMAND,
        "--remote",
        "ssh-remote+vsc_compute_node",
        project_folder,
    ]
    
    try:
        # Execute the command
        run_local_command(command)
        logging.info(
            f"VS Code successfully launched for remote: {str(compute_node)}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to open VS Code remote session: {e}")
        

def launch_vscode(project_folder: str, hostname: str, config_file: str, allocation_time: str = "01:00:00"):
    logging.info("Opening an interactive session on the remote machine...")

    # Connect to the remote machine
    login_node: Remote = Remote(hostname, config_file)
    login_node.connect()

    # Execute the command via SSH
    compute_node = ComputeNode(login_node)
    compute_node.allocate(time_limit=allocation_time)

    if not compute_node:
        logging.error("Failed to allocate compute node.")
        return 
    
    logging.info(f"Assigned machine: {str(compute_node)}")

    # Open VS Code to the assigned machine
    try:
        open_vscode_remote(compute_node, config_file, project_folder=project_folder)
    except Exception as e:
        logging.error(f"Failed to open VS Code remote session: {e}")
        return

    # Loop to keep the session alive
    while True:
        user_input = input("Press 'r' to relaunch VS Code or 'q' to quit: ").strip().lower()
        if user_input == 'r':
            try:
                open_vscode_remote(compute_node, config_file, project_folder=project_folder)
            except Exception as e:
                logging.error(f"Failed to open VS Code remote session: {e}")
                return
        elif user_input == 'q':
            logging.info("Quitting the session.")
            break
