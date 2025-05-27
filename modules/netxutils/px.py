# Copyright @ISmartDevs
# Channel t.me/TheSmartDev

import asyncio
import socket
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIX, PROXY_CHECK_LIMIT
from utils import LOGGER, notify_admin   # Use LOGGER and notify_admin
from core import banned_users           # Use banned_users

PROXY_TIMEOUT = 10
GEOLOCATION_TIMEOUT = 3

class HTTPProxyChecker:
    def __init__(self):
        self.geo_service = {
            'name': 'ipinfo.io',
            'url': "https://ipinfo.io/{ip}/json",
            'parser': lambda data: f"{data.get('region', 'Unknown')} ({data.get('country', 'Unknown')})",
            'headers': {'User-Agent': 'Mozilla/5.0'}
        }

    async def get_location(self, session, ip):
        try:
            url = self.geo_service['url'].format(ip=ip)
            async with session.get(
                url,
                headers=self.geo_service.get('headers', {}),
                timeout=GEOLOCATION_TIMEOUT
            ) as response:
                data = await response.json()
                LOGGER.info(f"Location API Response: {data}")
                if response.status == 200:
                    return self.geo_service['parser'](data)
                return f"❌ HTTP {response.status}"
        except asyncio.TimeoutError:
            return "⏳ Timeout"
        except Exception as e:
            LOGGER.error(f"Error fetching location: {e}")
            return f"❌ Error ({str(e)[:30]})"

    async def check_anonymity(self, session, proxy_url):
        try:
            async with session.get(
                "http://httpbin.org/headers",
                proxy=proxy_url,
                timeout=PROXY_TIMEOUT,
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as response:
                if response.status == 200:
                    headers_data = await response.json()
                    client_headers = headers_data.get('headers', {})
                    if 'X-Forwarded-For' in client_headers:
                        return 'Transparent'
                    elif 'Via' in client_headers:
                        return 'Anonymous'
                    else:
                        return 'Elite'
                return 'Unknown'
        except:
            return 'Unknown'

    async def check_proxy(self, proxy, proxy_type='http', auth=None):
        result = {
            'proxy': f"{proxy}",
            'status': 'Dead 🔴',
            'location': '• Not determined',
            'anonymity': 'Unknown'
        }

        ip = proxy.split(':')[0]

        try:
            proxy_url = f"{proxy_type}://{auth['username']}:{auth['password']}@{proxy}" if auth else f"{proxy_type}://{proxy}"
            connector = aiohttp.TCPConnector()

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    "http://httpbin.org/ip",
                    proxy=proxy_url,
                    timeout=PROXY_TIMEOUT,
                    headers={'User-Agent': 'Mozilla/5.0'}
                ) as response:
                    data = await response.json()
                    LOGGER.info(f"Proxy Check API Response: {data}")
                    if response.status == 200:
                        result.update({
                            'status': 'Live ✅',
                            'ip': ip
                        })
                        result['anonymity'] = await self.check_anonymity(session, proxy_url)

                result['location'] = await self.get_location(session, ip)

        except Exception as e:
            LOGGER.error(f"Error checking proxy: {e}")
            async with aiohttp.ClientSession() as session:
                result['location'] = await self.get_location(session, ip)

        return result

checker = HTTPProxyChecker()

def setup_px_handler(app):
    @app.on_message(filters.command(["px", "proxy"], prefixes=COMMAND_PREFIX) & (filters.group | filters.private))
    async def px_command_handler(client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        args = message.text.split()[1:]
        if len(args) > 0:
            if len(args) >= 3 and ':' not in args[-1] and ':' not in args[-2]:
                auth = {'username': args[-2], 'password': args[-1]}
                proxy_args = args[:-2]
            else:
                auth = None
                proxy_args = args
        else:
            if message.reply_to_message and message.reply_to_message.text:
                proxy_text = message.reply_to_message.text
                potential_proxies = proxy_text.split()
                proxy_args = [p for p in potential_proxies if ':' in p]
                auth = None
            else:
                return await client.send_message(
                    message.chat.id,
                    "<b>❌ Provide at least one proxy for check</b>"
                )

        if len(proxy_args) > PROXY_CHECK_LIMIT:
            return await client.send_message(
                message.chat.id,
                "<b> ❌ Sorry Bro Maximum Proxy Check Limit Is 20 </b>"
            )

        proxies_to_check = []
        for proxy in proxy_args:
            if '://' in proxy:
                parts = proxy.split('://')
                if len(parts) == 2 and parts[0].lower() in ['http', 'https']:
                    proxy_type = parts[0].lower()
                    proxy_addr = parts[1]
                    if ':' in proxy_addr:
                        proxies_to_check.append((proxy_type, proxy_addr))
            else:
                if ':' in proxy:
                    proxies_to_check.append(('http', proxy))

        if not proxies_to_check:
            return await client.send_message(
                message.chat.id,
                "<b>❌ The Proxies Are Not Valid At All</b>"
            )

        processing_msg = await client.send_message(
            chat_id=message.chat.id,
            text=f"<b> Smart Proxy Checker Checking Proxies 💥</b>"
        )

        try:
            tasks = [checker.check_proxy(proxy, proxy_type, auth) for proxy_type, proxy in proxies_to_check]
            results = await asyncio.gather(*tasks)
            await send_results(client, message, processing_msg, results)
        except Exception as e:
            LOGGER.error(f"Error during proxy check: {e}")
            await processing_msg.edit_text("<b>Sorry Bro Proxy Checker API Dead</b>")
            await notify_admin(client, "/px", e, message)

async def send_results(client, original_msg, processing_msg, results):
    response = []

    for res in results:
        response.append(f"<b>Proxy:</b> <code>{res['proxy']}</code>\n")
        response.append(f"<b>Status:</b> {res['status']}\n")
        if res['status'] == 'Live ✅':
            response.append(f"<b>Anonymity:</b> {res['anonymity']}\n")
        response.append(f"<b>Region:</b> {res['location']}\n")
        response.append("\n")

    full_response = ''.join(response)
    await processing_msg.edit_text(full_response)