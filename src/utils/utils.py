import getpass

from typing import Union, Optional
from io import TextIOWrapper, StringIO

from paramiko import RSAKey, Ed25519Key, ECDSAKey, DSSKey, PKey

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, dsa, rsa, ec


def prompt_password() -> Optional[bytes]:
    passphrase = getpass.getpass("Enter passphrase for private key (leave empty if none): ")
    passphrase = bytes(passphrase, "utf-8") if passphrase else None
    return passphrase


def read_private_key(identity_file: Union[str, TextIOWrapper]) -> PKey:
    if isinstance(identity_file, str):
        identity_file = open(identity_file, "r") 
        
    file_bytes = bytes(identity_file.read(), "utf-8")
    password = prompt_password()
    
    private_key = None
    
    try:
        key = crypto_serialization.load_ssh_private_key(
            file_bytes,
            password=password,
        )
        identity_file.seek(0)
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
        identity_file = StringIO(
            key.private_bytes(
                crypto_serialization.Encoding.PEM,
                crypto_serialization.PrivateFormat.OpenSSH,
                encryption_algorithm,
            ).decode("utf-8")
        )
        
    if isinstance(key, rsa.RSAPrivateKey):
        private_key = RSAKey.from_private_key(identity_file, password)
    elif isinstance(key, ed25519.Ed25519PrivateKey):
        private_key = Ed25519Key.from_private_key(identity_file, password)
    elif isinstance(key, ec.EllipticCurvePrivateKey):
        private_key = ECDSAKey.from_private_key(identity_file, password)
    elif isinstance(key, dsa.DSAPrivateKey):
        private_key = DSSKey.from_private_key(identity_file, password)
    else:
        raise TypeError

    identity_file.close()
    return private_key


__all__ = [
    "read_private_key"
]