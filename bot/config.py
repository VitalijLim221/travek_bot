import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'TOKEN')

# DeepSeek API Key
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'TOKEN')

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'users.db')

# Encryption key
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', b'your-32-byte-encryption-key-here!!')

# Points per visited object
POINTS_PER_OBJECT = 10

# Accuracy for location matching (in meters)

LOCATION_ACCURACY = 50
