import paramiko
import logging

from src.utils import read_private_key

class Remote:
    def __init__(self, hostname: str, config_file: str):
        config = paramiko.SSHConfig.from_path(config_file)
        host = config.lookup(hostname)
        
        self.hostname = host["hostname"]
        self.port = int(host.get("port", 22))
        self.username = host["user"]
        self.private_key: paramiko.PKey = read_private_key(host["identityfile"][0])
        
        self.client = None

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.hostname,
                username=self.username,
                port=self.port,
                pkey=self.private_key,
                look_for_keys=False,
            )
            logging.info(f"Connected to {self.hostname}")
        except Exception as e:
            logging.error(f"Failed to connect to {self.hostname}: {e}")
            raise

    def run(self, command, get_pty=True):
        if self.client is None:
            raise Exception("Connection not established. Call connect() first.")
        
        stdin, stdout, stderr = self.client.exec_command(command, get_pty=get_pty)
        return stdout, stderr

    def close(self):
        if self.client:
            self.client.close()
            logging.info(f"Connection to {self.hostname} closed")
            
            
__all__ = ["Remote"]