#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram import Client
from utils import LOGGER
from config import SESSION_STRING

# Initialize User Client
LOGGER.info("Creating User Client From SESSION_STRING")

user = Client(
    "user_session",
    session_string=SESSION_STRING,
    workers=1000
)

LOGGER.info("User Client Successfully Created!")
