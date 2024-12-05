import argparse 
import logging

from src.tools import launch_vscode
from src.utils.data import ComputeNodeParams


def parse_args():
    parser = argparse.ArgumentParser(description="Open an interactive session on a remote machine and connect with vscode.")
    
    parser.add_argument("tool", default="vscode", type=str, help="The tool to use.")
    
    # Connection arguments
    parser.add_argument("--config_file", type=str, help="Path to the SSH config file.")
    parser.add_argument("--hostname", default="VSC", type=str, help="Hostname or IP address of the remote machine.")
    parser.add_argument("--username", type=str, help="Username to use for SSH connection.")
    parser.add_argument("--identity_file", type=str, help="Path to the private key file.")
    
    # Compute node arguments
    parser.add_argument("--allocation_time", default="01:00:00", type=str, help="Time limit for compute node allocation.")
    parser.add_argument("--group", type=str, help="Group to use for compute node allocation.")
    parser.add_argument("--cluster", default="genius", type=str, help="Cluster to allocate the compute node on.")
    parser.add_argument("--partition", default="gpu_v100", type=str, help="Partition to allocate the compute node on.")
    parser.add_argument("--cores", default=4, type=int, help="Number of cores to allocate.")
    
    # VSCode arguments
    parser.add_argument("--project_folder", type=str, help="Path to the project folder on the remote machine.")
    
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    
    compute_node_params = ComputeNodeParams(
        group=args.group,
        allocation_time=args.allocation_time,
        cluster=args.cluster,
        partition=args.partition,
        cores=args.cores
    )
    
    if args.tool == "vscode":
        launch_vscode(
            args.project_folder, 
            args.hostname, 
            args.config_file,
            compute_node_params
        )
    else:
        logging.error("Invalid tool specified.")
    
        
if __name__ == "__main__":
    main()