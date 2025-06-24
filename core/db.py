from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import urlparse, parse_qs
from config import DB_URL
from utils import LOGGER

LOGGER.info("Creating DB Client From DB_URL")

try:
    parsed = urlparse(DB_URL)
    query_params = parse_qs(parsed.query)
    db_name = query_params.get("appName", [None])[0]

    if not db_name:
        raise ValueError("No database name found in DB_URL (missing 'appName' query param)")

    channel_db_client = AsyncIOMotorClient(DB_URL)
    channel_db = channel_db_client.get_database(db_name)
    group_channel_bindings = channel_db["group_channel_bindings"]

    LOGGER.info(f"DB Client Created Successfully! ")
except Exception as e:
    LOGGER.error(f"Failed to create DB Client for Group-Channel Bindings: {e}")
    raise
