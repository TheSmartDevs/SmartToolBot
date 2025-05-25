#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from misc import handle_callback_query
from utils import LOGGER
from modules import setup_modules_handlers
from sudoers import setup_sudoers_handlers
from core import setup_start_handler
from app import app  
from user import user

# CONNECT ALL MODULES WITH BOT AND USER CLIENT
setup_modules_handlers(app)
setup_sudoers_handlers(app)
setup_start_handler(app)  

@app.on_callback_query()
async def handle_callback(client, callback_query):
    await handle_callback_query(client, callback_query)

LOGGER.info("Bot Successfully Started! 💥")
user.start()
app.run()
