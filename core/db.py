# db.py
# Copyright @ISmartDevs
# Channel t.me/TheSmartDev

from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URL
from utils import LOGGER

LOGGER.info("Creating DB Client From DB_URL")

try:
    channel_db_client = AsyncIOMotorClient(DB_URL)
    channel_db = channel_db_client.get_default_database()
    group_channel_bindings = channel_db["group_channel_bindings"]
    LOGGER.info("DB Client Successfully Created!")
except Exception as e:
    LOGGER.error(f"Failed to create DB Client for Group-Channel Bindings: {e}")
    raise
