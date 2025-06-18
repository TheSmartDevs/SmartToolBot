#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import UPDATE_CHANNEL_URL
from pyrogram.enums import ParseMode

# Inline Keyboard Buttons Setup By @abirxdhackz & @ISmartDevs
main_menu_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("AI Tools", callback_data="ai_tools"), InlineKeyboardButton("CC Tools", callback_data="credit_cards")],
    [InlineKeyboardButton("Crypto", callback_data="crypto"), InlineKeyboardButton("Converter", callback_data="converter")],
    [InlineKeyboardButton("Decoders", callback_data="decoders"), InlineKeyboardButton("Downloaders", callback_data="downloaders")],
    [InlineKeyboardButton("Domain Check", callback_data="domain_check"), InlineKeyboardButton("Education Utils", callback_data="education_utils")],
    [InlineKeyboardButton("Editing Utils", callback_data="rembg"), InlineKeyboardButton("Github Utils", callback_data="github")],
    [InlineKeyboardButton("Next ➡️", callback_data="next_1"), InlineKeyboardButton("Close ❌", callback_data="close")]
])

second_menu_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("Info", callback_data="info"), InlineKeyboardButton("Mail Tools", callback_data="mail_tools")],
    [InlineKeyboardButton("Network Tools", callback_data="network_tools"), InlineKeyboardButton("Random Address", callback_data="random_address")],
    [InlineKeyboardButton("String Session", callback_data="string_session"), InlineKeyboardButton("Stripe Keys", callback_data="stripe_keys")],
    [InlineKeyboardButton("Sticker", callback_data="sticker"), InlineKeyboardButton("TimeDate", callback_data="time_date")],
    [InlineKeyboardButton("Txt Spilt", callback_data="text_split"), InlineKeyboardButton("Translate", callback_data="translate")],
    [InlineKeyboardButton("Previous ⬅️", callback_data="previous_1"), InlineKeyboardButton("Next ➡️", callback_data="next_2")],
    [InlineKeyboardButton("Close ❌", callback_data="close")]
])

third_menu_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("Temp Mail", callback_data="tempmail"), InlineKeyboardButton("Text OCR", callback_data="text_ocr")],
    [InlineKeyboardButton("User Export", callback_data="bot_users_export"), InlineKeyboardButton("Web Capture", callback_data="web_capture")],
    [InlineKeyboardButton("YT Tools", callback_data="yt_tools"), InlineKeyboardButton("Previous ⬅️", callback_data="previous_2")],
    [InlineKeyboardButton("Close ❌", callback_data="close")]
])

# ALL BUTTONS CALLBACK RESPONSES WRITTEN BY @abirxdhackz & @ISmartDevs & @nkka404
responses = {
    "ai_tools": (
        "<b>🤖 AI Assistant Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Interact with AI for text-based queries and image analysis using these commands:\n\n"
        "➢ <b>/gpt [Question]</b> - Ask a question to ChatGPT 3.5.\n"
        "   - Example: <code>/gpt What is the capital of France?</code> (Returns the answer 'Paris')\n\n"
        "➢ <b>/gem [Question]</b> - Ask a question to Gemini AI.\n"
        "   - Example: <code>/gem How does photosynthesis work?</code> (Returns an explanation of photosynthesis)\n\n"
        "➢ <b>/dep [Question]</b> - Ask a question to DeepSeek AI.\n"
        "   - Example: <code>/dep How does Telegram Bot work?</code> (Returns an explanation of Telegram Bot)\n\n"
        "➢ <b>/ai [Question]</b> - Ask a question to Smart AI.\n"
        "   - Example: <code>/ai How does Man Fall In Love?</code> (Returns an explanation of Man Fall In Love)\n\n"
        "➢ <b>/imgai [Optional Prompt]</b> - Analyze an image or generate a response based on it.\n"
        "   - Basic Usage: Reply to an image with <code>/imgai</code> to get a general analysis.\n"
        "   - With Prompt: Reply to an image with <code>/imgai [Your Prompt]</code> to get a specific response.\n"
        "   - Example 1: Reply to an image with <code>/imgai</code> (Provides a general description of the image).\n"
        "   - Example 2: Reply to an image with <code>/imgai What is this?</code> (Provides a specific response based on the prompt and image).\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ These tools leverage advanced AI models for accurate and detailed outputs.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "crypto": (
        "<b>💰 Cryptocurrency Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Stay updated with real-time cryptocurrency data and market trends using these commands:\n\n"
        "➢ <b>/price [Token Name]</b> - Fetch real-time prices for a specific cryptocurrency.\n"
        "   - Example: <code>/price BTC</code> (Returns the current price of Bitcoin)\n\n"
        "➢ <b>/p2p</b> - Get the latest P2P trades for currency BDT (Bangladeshi Taka).\n"
        "   - Example: <code>/p2p</code> (Returns the latest P2P trade prices for cryptocurrencies in BDT)\n\n"
        "➢ <b>/gainers</b> - View cryptocurrencies with the highest price increases.\n"
        "   - Example: <code>/gainers</code> (Returns a list of top-performing cryptos with high price surges)\n\n"
        "➢ <b>/losers</b> - View cryptocurrencies with the largest price drops.\n"
        "   - Example: <code>/losers</code> (Returns a list of cryptos with significant price declines, indicating potential buying opportunities)\n\n"
        "➢ <b>/cx [Amount Token1 Token2]</b> - Token Conversion Tool \n"
        "   - Example: <code>/cx 10 ton usdt</code> (Shows how much 10 TON is in USDT)\n\n"
        "➢ <b>/currency [Token] [Amount] [Token]</b> - Fetch real-time converted amount in Chosen Currency \n"
        "   - Example: <code>/currency USD 1 BDT</code> (Returns the current BDT price of 1 USD)\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Data for prices, P2P trades, gainers, and losers is fetched in real-time using the Binance API.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "decoders": (
        "<b>🔤 Text and Encoding Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Perform encoding, decoding, text transformations, and word count using these commands:\n\n"
        "<b>Encoding and Decoding Commands:</b>\n"
        "➢ <b>/b64en [text]</b> - Base64 encode.\n"
        "   - Example: <code>/b64en Hello</code> (Encodes 'Hello' into Base64 format)\n"
        "➢ <b>/b64de [text]</b> - Base64 decode.\n"
        "   - Example: <code>/b64de SGVsbG8=</code> (Decodes 'SGVsbG8=' into 'Hello')\n"
        "➢ <b>/b32en [text]</b> - Base32 encode.\n"
        "   - Example: <code>/b32en Hello</code> (Encodes 'Hello' into Base32 format)\n"
        "➢ <b>/b32de [text]</b> - Base32 decode.\n"
        "   - Example: <code>/b32de JBSWY3DP</code> (Decodes 'JBSWY3DP' into 'Hello')\n"
        "➢ <b>/binen [text]</b> - Binary encode.\n"
        "   - Example: <code>/binen Hello</code> (Encodes 'Hello' into binary)\n"
        "➢ <b>/binde [text]</b> - Binary decode.\n"
        "   - Example: <code>/binde 01001000 01100101 01101100 01101100 01101111</code> (Decodes binary into 'Hello')\n"
        "➢ <b>/hexen [text]</b> - Hex encode.\n"
        "   - Example: <code>/hexen Hello</code> (Encodes 'Hello' into hexadecimal format)\n"
        "➢ <b>/hexde [text]</b> - Hex decode.\n"
        "   - Example: <code>/hexde 48656c6c6f</code> (Decodes '48656c6c6f' into 'Hello')\n"
        "➢ <b>/octen [text]</b> - Octal encode.\n"
        "   - Example: <code>/octen Hello</code> (Encodes 'Hello' into octal format)\n"
        "➢ <b>/octde [text]</b> - Octal decode.\n"
        "   - Example: <code>/octde 110 145 154 154 157</code> (Decodes '110 145 154 154 157' into 'Hello')\n\n"
        "<b>Text Transformation Commands:</b>\n"
        "➢ <b>/trev [text]</b> - Reverse text.\n"
        "   - Example: <code>/trev Hello</code> (Returns 'olleH')\n"
        "➢ <b>/tcap [text]</b> - Transform text to capital letters.\n"
        "   - Example: <code>/tcap hello</code> (Returns 'HELLO')\n"
        "➢ <b>/tsm [text]</b> - Transform text to small letters.\n"
        "   - Example: <code>/tsm HELLO</code> (Returns 'hello')\n\n"
        "<b>Word Count Command:</b>\n"
        "➢ <b>/wc [text]</b> - Count words in the given text.\n"
        "   - Example: <code>/wc Hello World!</code> (Returns 'Word Count: 2')\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Ensure text input is in a valid format for encoding and decoding commands.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "domain_check": (
        "<b>🌐 Domain Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Use the following command to check the registration status and availability of domains:\n\n"
        "➢ <b>/dmn [domain_name]</b> - Example: <code>/dmn example.com</code>\n\n"
        "<b>Multi-Domain Check:</b>\n"
        "You can check up to 20 domains at a time by separating them with spaces.\n"
        "Example: <code>/dmn example.com test.com demo.net</code>\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ The maximum limit for a single check is 20 domains.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "github": (
        "<b>🤖 Github Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n\n"
        "➢ <b>/git [url] [branch]</b> - Download Github Repository or Specific Branch.\n"
        "   - Example: <code>/git https://github.com/user/repo main</code>\n"
        "   - Example: <code>/git https://github.com/user/repo</code>\n\n"
        "<b>INSTRUCTIONS:</b>\n"
        "1. Use the <code>/git</code> command followed by a valid GitHub repository URL.\n"
        "2. Optionally, specify the branch name to download a specific branch.\n"
        "3. If no branch name is provided, the default branch of the repository will be downloaded.\n"
        "4. The repository will be downloaded as a ZIP file.\n"
        "5. The bot will send you the repository details and the file directly.\n\n"
        "<b>✨NOTE:</b>\n"
        "1. Only public repositories are supported.\n"
        "2. Ensure the URL is formatted correctly.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "protectron_utils": (
         "<b>🔒 Protectron Utils ⚙️</b>\n"
         "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
         "<b>USAGE:</b>\n"
         "Keep Your Group Fixed Using Commands Below:\n\n"
         "➢ <b>/setchannel [Channel Username]</b> - Sets Your Channel As Bindings For Your Group.\n"
         "➢ <b>/delchannel [Channel Username]</b> - Remove Your Channel As Bindings For Your Group.\n"
         "➢ <b>/setting [Full Settings Of Your Group]</b> - Show All Settings Of Your Group.\n\n"
         "<b>✨NOTE:</b>\n"
         "1️⃣ These Tools Database Is MONGODB So Your Data Will Be Available All Time Bro\n\n"
         "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
         {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "credit_cards": (
        "<b>💳 Credit Card Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Perform credit card generation, validation, filtering, and scraping using these commands:\n\n"
        "➢ <b>/gen [BIN] [Amount]</b> - Generate credit card details using a BIN.\n"
        "   - Example 1: <code>/gen 460827</code> (Generates 10 CC details by default using BIN 460827)\n"
        "   - Example 2: <code>/gen 460827 100</code> (Generates 100 CC details using BIN 460827)\n\n"
        "➢ <b>/bin [BIN]</b> - Check and validate BIN details.\n"
        "   - Example: <code>/bin 460827</code> (Returns issuer, country, and card type details for the BIN 460827)\n\n"
        "➢ <b>/mbin [Text File or Message]</b> - Check up to 20 BINs at a time from a text file or message.\n"
        "   - Example: Reply to a message or a .txt file containing BINs and use <code>/mbin</code> to validate all.\n\n"
        "➢ <b>/scr [Chat Link or Username] [Amount]</b> - Scrape credit cards from a chat.\n"
        "   - Example: <code>/scr @abcdxyz 100</code> (Scrapes 100 CC details from the specified chat)\n"
        "   - Target BIN Example: <code>/scr @abcxyz 100 460827 </code> (Scrapes 100 CC details with BIN 460827 from the chat)\n\n"
        "➢ <b>/fcc [File]</b> - Filter CC details from a file.\n"
        "   - Example: Reply to a .txt file containing CC details with <code>/fcc</code> to extract valid CC data.\n\n"
        "➢ <b>/extp [File or BIN]</b> - Extrapolate credit card data from a BIN.\n"
        "   - Example: <code>/extp 460827</code> (Generates extrapolated CC using BIN 460827)\n\n"
        "➢ <b>/mgen [BINs] [Amount]</b> - Generate CC details using multiple BINs.\n"
        "   - Example: <code>/mgen 460827,537637 10</code> (Generates 10 CC details for each BIN provided)\n\n"
        "➢ <b>/mc [Chat Link or Usernames] [Amount]</b> - Scrape CC details from multiple chats.\n"
        "   - Example: <code>/mc @Group1 @Group2 200</code> (Scrapes 200 CC details from both chats)\n\n"
        "➢ <b>/topbin [File]</b> - Find the top 20 most used BINs from a combo.\n"
        "   - Example: Reply to a .txt file with <code>/topbin</code> to extract the top 20 BINs.\n\n"
        "➢ <b>/binbank [Bank Name]</b> - Find BIN database by bank name.\n"
        "   - Example: <code>/binbank Chase</code> (Returns BIN details for cards issued by Chase Bank)\n\n"
        "➢ <b>/bindb [Country Name]</b> - Find BIN database by country name.\n"
        "   - Example: <code>/bindb USA</code> (Returns BIN details for cards issued in the USA)\n\n"
        "➢ <b>/adbin [BIN]</b> - Filter specific BIN cards from a combo.\n"
        "   - Example: <code>/adbin 460827</code> (Filters CC details with BIN 460827 from a file or message)\n\n"
        "➢ <b>/rmbin [BIN]</b> - Remove specific BIN cards from a combo.\n"
        "   - Example: <code>/rmbin 460827</code> (Removes CC details with BIN 460827 from a file or message)\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Always ensure compliance with legal and privacy regulations when using these tools.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "converter": (
        "<b>🎵 FFMPEG Converter Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Extract audio from a video using this command:\n\n"
        "➢ <b>/aud</b> - Reply to a video message with this command to convert the video into audio.\n\n"
        "➢ <b>/voice</b> - Reply to a audio message with this command to convert the audio into voice message.\n\n"
        "➢ <b>/vnote</b> - Reply to a video message to convert it into a circular Telegram video note.\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Ensure you reply directly to a video message with the <code>/aud</code> command to extract audio.\n"
        "2️⃣ Ensure you reply directly to a audio message with the <code>/voice</code> command to convert it to a voice message.\n\n"
        "3️⃣ Reply to a short video (≤ 1 minute) with /vnote to turn it into a round video note.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "downloaders": (
        "<b>🎥 ALL Platform Downloader Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Download videos and tracks from popular platforms using these commands:\n\n"
        "➢ <b>/fb [Video URL]</b> - Download a Facebook video.\n"
        "   - Example: <code>/fb https://facebook.com/video/example</code> (Downloads the specified Facebook video)\n"
        "   - Note: Private Facebook videos cannot be downloaded.\n\n"
        "➢ <b>/pnt [Video URL]</b> - Download a Pinterest video.\n"
        "   - Example: <code>/pnt https://pinterest.com/pin/example</code> (Downloads the specified Pinterest video)\n\n"
        "➢ <b>/tt [Video URL]</b> - Download a TikTok video.\n"
        "   - Example: <code>/tt https://www.tiktok.com/@user/video/1234567890</code> (Downloads the specified TikTok video)\n\n"
        "➢ <b>/in [Video URL]</b> - Download Instagram Reels& Posts.\n"
        "   - Example: <code>/in https://instagram.com/reel/example</code> (Downloads the specified Instagram reel/post)\n"
        "   - Note: 18+ Instagram Reels cannot be downloaded.\n\n"
        "➢ <b>/sp [Track URL]</b> - Download a Spotify track.\n"
        "   - Example: <code>/sp https://spotify.com/track/example</code> (Downloads the specified Spotify track)\n\n"
        "➢ <b>/yt [Video URL]</b> - Download a YouTube video.\n"
        "   - Example: <code>/yt https://youtube.com/video/example</code> (Downloads the specified YouTube video)\n\n"
        "➢ <b>/song [Video URL]</b> - Download a YouTube video as an MP3 file.\n"
        "   - Example: <code>/song https://youtube.com/video/example</code> (Converts and downloads the video as MP3)\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Provide a valid public URL for each platform to download successfully.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "education_utils": (
        "<b>📚 Language Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Enhance your language skills with these commands for fixing spelling, grammar, checking synonyms, antonyms, and pronunciations:\n\n"
        "➢ <b>/spell [Word]</b> - Correct the spelling of a word.\n"
        "   - Example: <code>/spell teh</code> (Returns the corrected spelling: 'the')\n"
        "   - Reply Example: Reply to a message with <code>/spell</code> to correct the spelling of a specific word.\n\n"
        "➢ <b>/gra [Sentence]</b> - Fix grammatical issues in a sentence.\n"
        "   - Example: <code>/gra I has a book</code> (Returns the corrected sentence: 'I have a book')\n"
        "   - Reply Example: Reply to a message with <code>/gra</code> to fix grammatical errors in the sentence.\n\n"
        "➢ <b>/syn [Word]</b> - Check synonyms and antonyms for a given word.\n"
        "   - Example: <code>/syn happy</code> (Returns synonyms like 'joyful' and antonyms like 'sad')\n\n"
        "➢ <b>/prn [Word]</b> - Check the pronunciation of a word.\n"
        "   - Example: <code>/prn epitome</code> (Returns the pronunciation in phonetic format or audio: 'eh-pit-uh-mee')\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ These tools support common English words and sentences.\n"
        "2️⃣ Ensure the word or sentence provided is clear for accurate results.\n"
        "3️⃣ Reply to a message with the command to apply it directly to the text in the message.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "info": (
        "<b>Sangmata Utils Info ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Retrieve detailed information about any user, group, or channel using this command:\n\n"
        "We are still collecting Database Like Sangmata To Give 100% Of User's Info\n\n"
        "➢ <b>/info [target]</b> - Example: <code>/info @username</code> or <code>/info -123456789</code>\n\n"
        "➢ <b>/id [target]</b> - Example: <code>/id @username</code> or <code>/id -1001234567892</code>\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ For groups/channels, use their username or numeric ID.\n"
        "2️⃣ Ensure proper input format to get accurate results.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "mail_tools": (
        "<b>📋 Email and Scrapper Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Extract and scrape emails or email-password pairs using these commands:\n\n"
        "➢ <b>/fmail</b> - Filter or extract emails by replying to a message or a text file.\n"
        "   - Example: Reply to a message containing text or a .txt file and use <code>/fmail</code> to extract all emails.\n\n"
        "➢ <b>/fpass</b> - Filter or extract email-password pairs by replying to a message or a text file.\n"
        "   - Example: Reply to a message containing credentials or a .txt file and use <code>/fpass</code> to extract all email-password pairs.\n\n"
        "➢ <b>/scrmail [Chat Username/Link] [Amount]</b> - Scrape email-password pairs from a Telegram group or channel.\n"
        "   - Example: <code>/scrmail @abir_x_official 100</code> (Scrapes the first 100 messages from the specified group or channel for email-password pairs)\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ For <code>/scrmail</code>, provide the chat username or link (e.g., <code>@ChatName</code> or <code>https://t.me/ChatName</code>) and the number of messages to scrape.\n"
        "2️⃣ Ensure that the chat username or link provided is valid and accessible.\n"
        "3️⃣ These tools are intended for data filtering and scraping; ensure compliance with privacy and legal regulations.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "random_address": (
        "<b>🏠 Fake Address Generator Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Generate random fake addresses for specific countries or regions:\n\n"
        "➢ <b>/fake [Country Code or Country Name]</b> - Generates a random address for the specified country.\n"
        "   - Example: <code>/fake BD</code> or <code>/fake Bangladesh</code>\n\n"
        "<b>Alternative Command:</b>\n"
        "➢ <b>/rnd [Country Code or Country Name]</b> - Works the same as <code>/fake</code>.\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Supported formats include either the country code (e.g., <code>US</code>, <code>BD</code>) or full country name (e.g., <code>UnitedStates</code>, <code>Bangladesh</code>).\n"
        "2️⃣ Some countries may not have address data available.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "rembg": (
         "<b>🖼 Photo Editing Utilities ⚙️</b>\n"
         "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
         "<b>✨ Features:</b>\n"
         "Effortlessly Enhance Your Image With high precision and quality.\n\n"
         "➢ <b>/enh</b> - Instantly Increase Quality of any image or photo.\n"
         "   - <b>How to use:</b> Reply to an image with the <code>/enh</code> command, and the bot will process it for you.\n\n"
         "<b>⚠️ Important Notes:</b>\n"
         "1️⃣ Enhance May Take 1 Minute To Skip Rate Limit\n"
         "2️⃣ Ensure the image is clear for the best results.\n\n"
         "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
         "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
         {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "calculator": (
        "<b>🧮 Smart Calculator Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "1. Use <code>/calc</code> to start the calculator.\n"
        "2. Use the on-screen buttons to perform calculations.\n"
        "3. Press '=' to get the result.\n"
        "4. Toggle history with the 'H' button to see or hide the last 10 calculations.\n\n"
        "<b>✨NOTE:</b>\n"
        "- The bot supports basic arithmetic: +, -, ×, ÷.\n"
        "- Prevents invalid inputs and handles errors (e.g., division by zero).\n\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "stripe_keys": (
        "<b>💳 Stripe Hunter Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Verify and retrieve information about Stripe keys using these commands:\n\n"
        "➢ <b>/sk [Stripe Key]</b> - Check whether the provided Stripe key is live or dead.\n"
        "   - Example: <code>/sk sk_live_4eC39HqLyjWDarjtT1zdp7dc</code> (Verifies the given Stripe key)\n\n"
        "➢ <b>/skinfo [Stripe Key]</b> - Retrieve detailed information about the provided Stripe key.\n"
        "   - Example: <code>/skinfo sk_live_4eC39HqLyjWDarjtT1zdp7dc</code> (Fetches details like account type, region, etc.)\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Ensure you provide a valid Stripe key for both commands.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "time_date": (
        "<b>Smart Clock 🕒 Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Get the current time and date for any country using this command:\n\n"
        "➢ <b>/time [Country Code]</b> - Fetch the current time and date of the specified country.\n"
        "   - Example: <code>/time US</code> or <code>/time BD</code>\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Use valid country codes (e.g., <code>US</code> for the United States, <code>BD</code> for Bangladesh).\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "tempmail": (
        "<b>📧 Temporary Mail Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Generate and manage temporary emails using these commands:\n\n"
        "➢ <b>/tmail</b> - Generate a random temporary email with a password.\n"
        "   - Example: <code>/tmail</code> (Creates a random email and generates a unique password)\n\n"
        "➢ <b>/tmail [username]:[password]</b> - Generate a specific temporary email with your chosen username and password.\n"
        "   - Example: <code>/tmail user123:securePass</code> (Creates <code>user123@temp.com</code> with the password <code>securePass</code>)\n\n"
        "➢ <b>/cmail [mail token]</b> - Check the most recent 10 emails received by your temporary mail.\n"
        "   - Example: <code>/cmail abc123token</code> (Displays the last 10 mails for the provided token)\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ When generating an email, a unique mail token is provided. This token is required to check received emails.\n"
        "2️⃣ Each email has a different token, so keep your tokens private to prevent unauthorized access.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "network_tools": (
        "<b>🌐 Network Utils Commands ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Utilize these commands to gather IP-related information and check HTTP/HTTPS proxies:\n\n"
        "➢ <b>/ip [IP Address]</b> - Get detailed information about a specific IP address.\n"
        "   - Example: <code>/ip 8.8.8.8</code>\n\n"
        "➢ <b>/px [Proxy/Proxies]</b> - Check the validity and status of HTTP/HTTPS proxies.\n"
        "   - Single Proxy Example: <code>/px 192.168.0.1:8080</code>\n"
        "   - With Authentication: <code>/px 192.168.0.1:8080 user password</code>\n"
        "   - Multiple Proxies Example: <code>/px 192.168.0.1:8080 10.0.0.2:3128 172.16.0.3:8080 user password</code>\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ For <code>/ip</code>, ensure the input is a valid IP address.\n"
        "2️⃣ For <code>/px</code>, proxies can be provided in either <code>[IP:Port]</code> or <code>[IP:Port User Pass]</code> formats.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "string_session": (
        "<b>🔑 String SessioN Generator Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Generate string sessions for managing Telegram accounts programmatically using these commands:\n\n"
        "➢ <b>/pyro</b> - Generate a Pyrogram Telegram string session.\n"
        "   - Example: <code>/pyro</code> (Starts the process to generate a Pyrogram string session)\n\n"
        "➢ <b>/tele</b> - Generate a Telethon Telegram string session.\n"
        "   - Example: <code>/tele</code> (Starts the process to generate a Telethon string session)\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Pyrogram and Telethon are Python libraries for interacting with Telegram APIs.\n"
        "2️⃣ Use <code>/pyro</code> for Pyrogram-based projects and <code>/tele</code> for Telethon-based projects.\n"
        "3️⃣ Follow the prompts to enter your Telegram login credentials securely. Keep the generated session string private.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "sticker": (
        "<b>🎨 Sticker Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Easily create or customize stickers with these commands:\n\n"
        "➢ <b>/q</b> - Generate a sticker from any text message.\n"
        "   - Example: Reply to any text message in the chat with <code>/q</code> to convert it into a sticker.\n\n"
        "➢ <b>/kang</b> - Add any image, sticker, or animated sticker to your personal sticker pack.\n"
        "   - Example: Reply to an image, sticker, or animated sticker with <code>/kang</code> to add it to your pack.\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ For <code>/q</code>, ensure you reply directly to a text message to generate the sticker.\n"
        "2️⃣ For <code>/kang</code>, reply directly to the media or sticker you want to add to your pack.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "translate": (
        "<b>🌐 Translation Commands</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Translate text into various languages using these commands:\n\n"
        "➢ <b>/tr[Language Code] [Text]</b> - Translate the given text into the specified language.\n"
        "   - Example: <code>/tres Hello!</code> (Translates 'Hello!' to Spanish)\n"
        "   - Reply Example: Reply to any message with <code>/tres</code> to translate it into Spanish.\n\n"
        "➢ <b>/tr [Language]</b> - Translate the text in an image to the specified language.\n"
        "   - Example: Reply to a photo with <code>/tr ja</code> to translate its text to Japanese.\n"
        "   - Supported: Use language names or codes (e.g., <code>/tr en</code>, <code>/tr bangla</code>, <code>/tr fr</code>)\n\n"
        "<b>NOTE:</b>\n"
        "1️⃣ Use the <code>/tr[Language Code]</code> format for text translation.\n"
        "2️⃣ Use <code>/tr</code> as a reply to a photo for image translation.\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "text_ocr": (
        "<b>🔍 OCR Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Extract English text from an image using this command:\n\n"
        "➢ <b>/ocr</b> - Reply to an image with this command to extract readable English text from it.\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ This command only works with clear images containing English text.\n"
        "2️⃣ Ensure the image is not blurry or distorted for accurate text extraction.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "bot_users_export": (
        "<b>🤖 Bot Users Export</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "📌 This allows you to export the users/chats list of your bot.\n\n"
        "<b>How to use:</b>\n"
        "1️⃣ Send the command: <code>/getusers <your_bot_token></code>\n"
        "2️⃣ You will receive a JSON file containing the exported data.\n\n"
        "<b>Example:</b>\n"
        "<code>/getusers 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ</code>\n\n"
        "<b>BENEFITS:</b>\n"
        "✅ Broadcast messages to all bot users\n"
        "✅ Backup user and group data for future use.\n"
        "✅ Migrate users to a new bot if needed.\n\n"
        "<b>NOTE:</b>\n"
        "🔹 Ensure that the bot token is valid.\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "web_capture": (
        "<b>🌐 Web Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Perform webpage-related tasks like taking screenshots or downloading source code using these commands:\n\n"
        "➢ <b>/ss [Website URL]</b> - Take a screenshot of the specified webpage.\n"
        "   - Example: <code>/ss https://example.com</code> (Captures a screenshot of the given website)\n\n"
        "➢ <b>/ws [Website URL]</b> - Download the HTML source code of the specified webpage.\n"
        "   - Example: <code>/ws https://example.com</code> (Downloads the source code of the given website)\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Ensure you provide a valid and accessible website URL for both commands.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "yt_tools": (
        "<b>🎥 YouTube Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Easily extract tags or download thumbnails from YouTube videos using these commands:\n\n"
        "➢ <b>/ytag [YouTube Video URL]</b> - Extract all tags from a YouTube video.\n"
        "   - Example: <code>/ytag https://youtu.be/example</code> (Fetches tags for the specified video)\n\n"
        "➢ <b>/yth [YouTube Video URL]</b> - Download the thumbnail of a YouTube video.\n"
        "   - Example: <code>/yth https://youtu.be/example</code> (Downloads the thumbnail of the specified video)\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Ensure you provide a valid YouTube video URL with the commands.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "about_me": (
        f"💥 <b>Name:</b> Smart Tool 🌟\n"
        f"✨ <b>Version:</b>  v14.0 (Beta) 🛠 \n\n"
        f"❄️ <b>Development Team:</b>\n"
        f"- 🌐 <b>Creator:</b> <a href='tg://user?id=7303810912'>Abir Arafat Chawdhury 👨‍💻</a>\n"
        f"- 💫 <b>Contributor:</b> <a href='https://t.me/nkka404'>Nyein Ko Ko Aung 👨‍💻</a>\n"
        f"👀 <b>Technical Stacks:</b>\n"
        f"- 💥 <b>Language:</b> Python 🐍\n"
        f"- 🌟 <b>Framework:</b> Fully Written In Pyrogram And Telethon 📚\n"
        f"- ✨ <b>Database:</b> MongoDB Database 🗄\n"
        f"- 🇧🇩 <b>Hosting:</b> Digital Ocean VPS 🌐\n\n"
        f"❄️ <b>About:</b> Smart Tool 💥 The ultimate Telegram toolkit! Education, AI, downloaders, temp mail, finance tools & more—simplify life! 🔥\n\n"
        f"🔔 <b>For Bot Update News</b>: <a href='{{UPDATE_CHANNEL_URL}}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "admin": (
        "<b>🚫 GroupHelpBot Utils ⚙️</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "Manage user bans and mutes in the group using these commands:\n\n"
        "➢ <b>/ban</b> with username or userid - For Ban a user from the group.\n"
        "➢ <b>/fuck</b> with username or userid - For Ban a user from the group.\n"
        "➢ <b>/unban</b> with username or userid - For unban a user from the group.\n"
        "➢ <b>/unfuck</b> with username or userid - For unban a user from the group.\n"
        "➢ <b>/ban</b> with multiple usernames or user IDs - For Multi Ban from the group.\n"
        "➢ <b>/kick</b> with usernames or user IDs - For Banning A Fucker From Group.\n"
        "➢ <b>/del</b> Reply To A Message - For Deleting Message from the group.\n"
        "➢ <b>/unban</b> with multiple usernames or user IDs - For Multi unban from the group.\n"
        "➢ <b>/mute</b> with username or userid - For mute a user in the group (they can’t send messages).\n"
        "➢ <b>/unmute</b> with username or userid - For unmute a user in the group (they can send messages again).\n"
        "➢ <b>/mute</b> with multiple usernames or user IDs - For Multi mute in the group.\n"
        "➢ <b>/unmute</b> with multiple usernames or user IDs - For Multi unmute in the group.\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ Ensure you have the necessary permissions to ban/unban/mute/unmute users in the group.\n"
        "2️⃣ Use the commands in group chats only.\n\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    ),
    "text_split": (
        "<b>📂 Text Split Utils ⚙️ </b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>USAGE:</b>\n"
        "This command allows you to split large text files into smaller parts.\n\n"
        "➢ <b>/sptxt [Number]</b>\n"
        "   - Example: Reply to a .txt file with:\n"
        "     <code>/sptxt 100</code>\n"
        "   - The bot will split the text file into parts of 100 lines each.\n\n"
        "<b>✨NOTE:</b>\n"
        "1️⃣ This command only works in private chats.\n"
        "2️⃣ Only <b>.txt</b> files are supported.\n"
        "3️⃣ The bot will return multiple split files if necessary.\n\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>🔔 For Bot Update News</b>: <a href='{UPDATE_CHANNEL_URL}'>Join Now</a>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL),
        {'parse_mode': ParseMode.HTML, 'disable_web_page_preview': True}
    )
}
