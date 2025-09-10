from cryptography.fernet import Fernet
from bot.config import ENCRYPTION_KEY
import base64

# Ensure the key is 32 bytes
if len(ENCRYPTION_KEY) != 32:
    # Pad or truncate to 32 bytes
    key_bytes = ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
    key_bytes = (key_bytes * (32 // len(key_bytes) + 1))[:32]
    CIPHER_SUITE = Fernet(base64.urlsafe_b64encode(key_bytes))
else:
    CIPHER_SUITE = Fernet(base64.urlsafe_b64encode(ENCRYPTION_KEY))

def encrypt_data(data: str) -> str:
    "Encrypt string data"
    if not data:
        return ""
    return CIPHER_SUITE.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    "Decrypt string token"
    if not token:
        return ""
    try:
        return CIPHER_SUITE.decrypt(token.encode()).decode()
    except:
        return token  # Return as is if decryption fails