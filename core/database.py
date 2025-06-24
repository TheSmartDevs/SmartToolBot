# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from motor.motor_asyncio import AsyncIOMotorClient
from config import DATABASE_URL
from utils import LOGGER

LOGGER.info("Creating Database Client From DATABASE_URL")

try:
    mongo_client = AsyncIOMotorClient(DATABASE_URL)
    db = mongo_client.get_database()
    group_settings = db["group_settings"]
    auth_admins = db["auth_admins"]
    banned_users = db["banned_users"]
    LOGGER.info("Database Client Successfully Created!")
except Exception as e:
    LOGGER.error(f"Database Client Create Error: {e}")
    raise
