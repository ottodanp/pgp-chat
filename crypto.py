from os import makedirs
from os.path import exists
from typing import Tuple, Optional

import pgpy


def encrypt_message(message: str, public_key: str) -> str:
    try:
        key, _ = pgpy.PGPKey.from_blob(public_key)
        pgp_message = pgpy.PGPMessage.new(message)
        encrypted_message = key.encrypt(pgp_message)

        return str(encrypted_message)
    except Exception as e:
        return f"Error during encryption: {e}"


def decrypt_message(encrypted_message: str, private_key: str) -> str:
    try:
        key, _ = pgpy.PGPKey.from_blob(private_key)
        decrypted_message = key.decrypt(encrypted_message)

        return str(decrypted_message.message)
    except Exception as e:
        return f"Error during decryption: {e}"


def generate_keypair() -> Tuple[str, str]:
    key = pgpy.PGPKey.new(pgpy.constants.PubKeyAlgorithm.RSAEncryptOrSign, 4096)

    public_key = str(key.pubkey)
    private_key = str(key)

    return public_key, private_key


def keys_exist(name: str) -> bool:
    return exists(f"data/keychain/{name}.pri") and exists(f"data/keychain/{name}.pub")


def save_keys(public_key: str, private_key: str, name: str) -> None:
    if not exists("data/keychain"):
        makedirs("data/keychain")

    with open(f"data/keychain/{name}.pub", "w") as pkey_file:
        pkey_file.write(public_key)

    with open(f"data/keychain/{name}.pri", "w") as privkey_file:
        privkey_file.write(private_key)


def load_keys(name: str) -> Optional[Tuple[str, str]]:
    if keys_exist(name):
        with open(f"data/keychain/{name}.pri", "r") as privkey_file:
            with open(f"data/keychain/{name}.pub", "r") as pubkey_file:
                return pubkey_file.read(), privkey_file.read()

