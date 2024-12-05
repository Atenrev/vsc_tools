import re
import time
import logging

from typing import Optional

from src.utils import Remote
from src.utils.data import ComputeNodeParams


class ComputeNode:
    def __init__(self, login_node: Remote, ):
        self.login_node = login_node
        self.address: Optional[str] = None

    def allocate(self, compute_node_params: ComputeNodeParams):
        logging.info("Allocating compute node...")
        salloc_cmd = [
            "salloc",
            "-n", "1",
            "-t", compute_node_params.allocation_time,
            "--ntasks", str(compute_node_params.cores),
            "--gpus-per-node=1",
            "-A", compute_node_params.group,
            "--partition", compute_node_params.partition,
            "--cluster", compute_node_params.cluster
        ]

        stdout, stderr = self.login_node.run(salloc_cmd, get_pty=True)

        output_buffer = ""
        while True:
            if stdout.channel.recv_ready():
                output = stdout.channel.recv(1024).decode('utf-8')
                output_buffer += output
                logging.info(output.strip())

                match = re.search(
                    r'salloc: Nodes (\S+) are ready for job', output_buffer)
                
                if match:
                    self.address = match.group(1)
                    break

            if stdout.channel.exit_status_ready():
                break

            time.sleep(1)

        if not self.address:
            raise Exception("Failed to allocate compute node")
        
        logging.info(f"Compute node allocated: {self.address}")

    def run(self, command, get_pty=True):
        if not self.address:
            raise Exception(
                "Compute node not allocated. Call allocate() first.")

        ssh_cmd = f"ssh {self.address} {command}"
        return self.login_node.run(ssh_cmd, get_pty=get_pty)

    def __str__(self) -> str:
        if self.address is not None:
            node_address = f"{self.login_node.username}@{self.address}"
        else:
            node_address = "Unallocated node"

        return node_address


__all__ = ["ComputeNode"]