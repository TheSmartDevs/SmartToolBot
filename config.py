# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
# Note: Configure via .env (VPS/Heroku local), direct edits to this file (VPS), or Heroku config vars (app.json/dashboard).
import os
from dotenv import load_dotenv

# Load .env file if it exists (for VPS or local Heroku testing), but allow Heroku config vars to take precedence
load_dotenv()

def get_env_or_default(key, default=None, cast_func=str):
    """Helper function to load environment variables with type casting and default values."""
    value = os.getenv(key)
    if value is not None and value.strip() != "":
        try:
            return cast_func(value)
        except (ValueError, TypeError) as e:
            print(f"Error casting {key} with value '{value}' to {cast_func.__name__}: {e}")
            return default
    return default

# TELEGRAM WITH PYROGRAM MTPROTO API CONNECTION AND AUTHORIZATION SETUP
API_ID = get_env_or_default("API_ID", "Your_API_ID_Here")
API_HASH = get_env_or_default("API_HASH", "Your_API_HASH_Here")
BOT_TOKEN = get_env_or_default("BOT_TOKEN", "Your_BOT_TOKEN_Here")
SESSION_STRING = get_env_or_default("SESSION_STRING", "Your_SESSION_STRING_Here")

# ADMINS AND SUDO USERS LIST FOR BROADCAST AND OTHER SUDO WORKS
ADMIN_IDS = get_env_or_default("ADMIN_IDS", "Your_ADMIN_IDS_Here", lambda x: list(map(int, x.split(','))))
OWNER_IDS = get_env_or_default("OWNER_IDS", "Your_OWNER_IDS_Here", lambda x: list(map(int, x.split(','))))
DEVELOPER_USER_ID = get_env_or_default("DEVELOPER_USER_ID", "Your_DEVELOPER_USER_ID_Here", int)

# MONGODB URL AND DATABASE URL FOR USER DATABASE AND GROUP SETTINGS DATABASE
MONGO_URL = get_env_or_default("MONGO_URL", "Your_MONGO_URL_Here")
DATABASE_URL = get_env_or_default("DATABASE_URL", "Your_DATABASE_URL_Here")
DB_URL = get_env_or_default("DB_URL", "Your_DB_URL_Here")

# SPOTIFY CREDENTIALS (REQUIRED)
SPOTIFY_CLIENT_ID = get_env_or_default("SPOTIFY_CLIENT_ID", "Your_SPOTIFY_CLIENT_ID_Here")
SPOTIFY_CLIENT_SECRET = get_env_or_default("SPOTIFY_CLIENT_SECRET", "Your_SPOTIFY_CLIENT_SECRET_Here")

# OPENAI API KEY (REQUIRED)
OPENAI_API_KEY = get_env_or_default("OPENAI_API_KEY", "Your_OPENAI_API_KEY_Here")

# CC SCRAPPER LIMITS FOR ALL TYPE CHAT AND GENERAL AND ADMIN LIMITS
CC_SCRAPPER_LIMIT = get_env_or_default("CC_SCRAPPER_LIMIT", 5000, int)
SUDO_CCSCR_LIMIT = get_env_or_default("SUDO_CCSCR_LIMIT", 10000, int)
MULTI_CCSCR_LIMIT = get_env_or_default("MULTI_CCSCR_LIMIT", 2000, int)
MAIL_SCR_LIMIT = get_env_or_default("MAIL_SCR_LIMIT", 10000, int)
SUDO_MAILSCR_LIMIT = get_env_or_default("SUDO_MAILSCR_LIMIT", 15000, int)
CC_GEN_LIMIT = get_env_or_default("CC_GEN_LIMIT", 2000, int)
MULTI_CCGEN_LIMIT = get_env_or_default("MULTI_CCGEN_LIMIT", 5000, int)

# OTHER PREMIUM APIS FOR TOOLS SERVICES (OPTIONAL)
GOOGLE_API_KEY = get_env_or_default("GOOGLE_API_KEY", "Your_GOOGLE_API_KEY_Here")
MODEL_NAME = get_env_or_default("MODEL_NAME", "gemini-1.5-flash")
GROQ_API_KEY = get_env_or_default("GROQ_API_KEY", "Your_GROQ_API_KEY_Here")
GROQ_API_URL = get_env_or_default("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
DOMAIN_API_KEY = get_env_or_default("DOMAIN_API_KEY", "Your_DOMAIN_API_KEY_Here")
DOMAIN_API_URL = get_env_or_default("DOMAIN_API_URL", "https://www.whoisxmlapi.com/whoisserver/WhoisService")
TEXT_MODEL = get_env_or_default("TEXT_MODEL", "deepseek-r1-distill-llama-70b")
LOCATIONIQ_API_KEY = get_env_or_default("LOCATIONIQ_API_KEY", "Your_LOCATIONIQ_API_KEY_Here")
IPINFO_API_TOKEN = get_env_or_default("IPINFO_API_TOKEN", "Your_IPINFO_API_TOKEN_Here")
NEWS_API_KEY = get_env_or_default("NEWS_API_KEY", "Your_NEWS_API_KEY_Here")
BIN_KEY = get_env_or_default("BIN_KEY", "Your_BIN_KEY_Here")

# ALL COMMANDS PREFIXES FOR ALLOWING ALL COMMANDS SUPPORT
raw_prefixes = get_env_or_default("COMMAND_PREFIX", "!|.|#|,|/")
COMMAND_PREFIX = [prefix.strip() for prefix in raw_prefixes.split("|") if prefix.strip()]

# BOT DEVS CHANNEL URL AND PROFILE ERROR URL
UPDATE_CHANNEL_URL = get_env_or_default("UPDATE_CHANNEL_URL", "t.me/TheSmartDev")
PROFILE_ERROR_URL = get_env_or_default("PROFILE_ERROR_URL", "https://t.me/Bot_Bug_test/9305")

# MAX FILE SIZE LIMITS FOR OCR TOOLS AND IMGAI
IMGAI_SIZE_LIMIT = get_env_or_default("IMGAI_SIZE_LIMIT", 5242880, int)
MAX_TXT_SIZE = get_env_or_default("MAX_TXT_SIZE", 15728640, int)
MAX_VIDEO_SIZE = get_env_or_default("MAX_VIDEO_SIZE", 2147483648, int)

# CUSTOM API ENDPOINTS
OCR_WORKER_URL = get_env_or_default("OCR_WORKER_URL", "Your_OCR_WORKER_URL_Here")
TEXT_API_URL = get_env_or_default("TEXT_API_URL", "Your_TEXT_API_URL_Here")
IMAGE_API_URL = get_env_or_default("IMAGE_API_URL", "Your_IMAGE_API_URL_Here")

# YOUTUBE COOKIES PATH
YT_COOKIES_PATH = get_env_or_default("YT_COOKIES_PATH", "./cookies/ItsSmartToolBot.txt")

# VIDEO RESOLUTION FOR YOUTUBE DOWNLOADS
VIDEO_RESOLUTION = get_env_or_default("VIDEO_RESOLUTION", "1280x720", lambda x: tuple(map(int, x.split('x'))))

# DOMAIN AND PROXY CHECK LIMITS
DOMAIN_CHK_LIMIT = get_env_or_default("DOMAIN_CHK_LIMIT", 20, int)
PROXY_CHECK_LIMIT = get_env_or_default("PROXY_CHECK_LIMIT", 20, int)

# Validation for critical variables
required_vars = {
    "API_ID": API_ID,
    "API_HASH": API_HASH,
    "BOT_TOKEN": BOT_TOKEN,
    "SESSION_STRING": SESSION_STRING,
    "ADMIN_IDS": ADMIN_IDS,
    "OWNER_IDS": OWNER_IDS,
    "DEVELOPER_USER_ID": DEVELOPER_USER_ID,
    "MONGO_URL": MONGO_URL,
    "DATABASE_URL": DATABASE_URL,
    "DB_URL": DB_URL,
    "SPOTIFY_CLIENT_ID": SPOTIFY_CLIENT_ID,
    "SPOTIFY_CLIENT_SECRET": SPOTIFY_CLIENT_SECRET,
    "OPENAI_API_KEY": OPENAI_API_KEY
}

for var_name, var_value in required_vars.items():
    if var_value is None or var_value == f"Your_{var_name}_Here" or (isinstance(var_value, str) and var_value.strip() == ""):
        raise ValueError(f"Required variable {var_name} is missing or invalid. Set it in .env (VPS), config.py (VPS), or Heroku config vars.")

# Logging for debugging
print("Loaded COMMAND_PREFIX:", COMMAND_PREFIX)
gpt_api_key_source = "environment variable" if os.getenv("OPENAI_API_KEY") else "config default"
print(f"OPENAI_API_KEY loaded from {gpt_api_key_source}: {'*' * 10}{OPENAI_API_KEY[-10:]}")
spotify_id_source = "environment variable" if os.getenv("SPOTIFY_CLIENT_ID") else "config default"
print(f"SPOTIFY_CLIENT_ID loaded from {spotify_id_source}: {'*' * 10}{SPOTIFY_CLIENT_ID[-10:]}")

if not COMMAND_PREFIX:
    raise ValueError("No command prefixes found. Set COMMAND_PREFIX in .env, config.py, or Heroku config vars.")
