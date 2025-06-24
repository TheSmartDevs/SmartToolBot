# mongo.py
# Copyright @ISmartDevs
# Channel t.me/TheSmartDev

from motor.motor_asyncio import AsyncIOMotorClient
from utils import LOGGER
from config import MONGO_URL

LOGGER.info("Creating MONGO_CLIENT From MONGO_URL")

try:
    MONGO_CLIENT = AsyncIOMotorClient(MONGO_URL)
    db = MONGO_CLIENT.get_default_database()
    user_activity_collection = db["user_activity"]
    LOGGER.info("MONGO_CLIENT Successfully Created!")
except Exception as e:
    LOGGER.error(f"Failed to create MONGO_CLIENT: {e}")
    raise
