import paramiko
import logging

from src.utils import read_private_key, run_local_command, ssh_command


class Remote:
    def __init__(self, hostname: str, config_file: str):
        config = paramiko.SSHConfig.from_path(config_file)
        host = config.lookup(hostname)

        self.host = hostname
        self.hostname = host["hostname"]
        self.port = int(host.get("port", 22))
        self.username = host["user"]
        self.identity_file_path = host["identityfile"][0]
        self.private_key: paramiko.PKey = read_private_key(
            self.identity_file_path)

        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.client.connect(
                hostname=self.hostname,
                username=self.username,
                port=self.port,
                pkey=self.private_key,
                look_for_keys=False,
            )
        except Exception as e:
            # First failure might be cause because of the firewall.
            # In that case, we run an ssh command manually.
            process = ssh_command(self.host)

            if process.returncode != 0:
                logging.error(
                    f"Failed to connect to {self.hostname}: {e}. Try to ssh manually and go through the firewall and try again.")
                raise

            try:
                self.client.connect(
                    hostname=self.hostname,
                    username=self.username,
                    port=self.port,
                    pkey=self.private_key,
                    look_for_keys=False,
                )
            except Exception as e:
                logging.error(f"Failed to connect to {self.hostname}: {e}")
                raise

        logging.info(f"Connected to {self.hostname}")

    def run(self, command, get_pty=False):
        if self.client is None:
            raise Exception(
                "Connection not established. Call connect() first.")
            
        if isinstance(command, list):
            command = " ".join(command)

        stdin, stdout, stderr = self.client.exec_command(
            command, get_pty=get_pty)
        return stdout, stderr

    def close(self):
        if self.client:
            self.client.close()
            logging.info(f"Connection to {self.hostname} closed")


__all__ = ["Remote"]
