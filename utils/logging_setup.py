#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
#We Used A Just Logger Stream Handler Module To Capture Logs From Console Method By @abirxdhackz And @ISmartDevs
import logging
from logging.handlers import RotatingFileHandler

# LOGGER SETUP TO CAPTURE LOGS SMOOTHLY THORUGH BOT USING /LOGS
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s", 
    datefmt='%Y-%m-%d %H:%M:%S',  
    handlers=[
        RotatingFileHandler(
            "botlog.txt",
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)

# Set Logging Levels For Specific Core Libraries  Pyrogram AIOHTTP APSCHEDULER TELETHON
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("telethon").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)  
logging.getLogger("apscheduler").setLevel(logging.ERROR)

LOGGER = logging.getLogger(__name__)