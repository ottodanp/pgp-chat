from typing import Tuple

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


def verify_signed_message(message: str, signature: str, public_key: str) -> bool:
    try:
        key, _ = pgpy.PGPKey.from_blob(public_key)
        pgp_message = pgpy.PGPMessage.new(message)
        pgp_signature = pgpy.PGPSignature.from_blob(signature)

        return key.verify(pgp_message, pgp_signature)
    except Exception as e:
        return False
