import subprocess
import platform

from typing import List, Tuple, Union


def run_local_command(command: Union[str, Union[Tuple[str], List[str]]]) -> subprocess.CompletedProcess:
    system = platform.system()
    if system == "Windows":
        command = ["powershell", "-Command", *command]
    elif system == "Linux" or system == "Darwin":  # Darwin is macOS
        command = ["/bin/bash", "-c", *command]
    else:
        raise NotImplementedError(f"Unsupported operating system: {system}")

    result = subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=True,
    )

    return result


def ssh_command(hostname: str) -> subprocess.Popen:
    system = platform.system()
    command = [
        'ssh',
        hostname
    ]
    
    # if system == "Windows":
    #     command = ["powershell", "-Command", *command]
    # elif system == "Linux" or system == "Darwin":  # Darwin is macOS
    #     command = ["/bin/bash", "-c", *command]
    # else:
    #     raise NotImplementedError(f"Unsupported operating system: {system}")
    
    process = subprocess.run(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    
    return process


__all__ = ["run_local_command", "ssh_command"]
