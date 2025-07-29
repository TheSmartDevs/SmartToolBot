# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import asyncio
import socket
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, PROXY_CHECK_LIMIT, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

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
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return

        args = message.text.split()[1:]
        proxies_to_check = []

        if len(args) > 0:
            # Handle single proxy with auth (format: ip:port:user:pass)
            if len(args) == 1 and args[0].count(':') == 3:
                ip_port, username, password = args[0].rsplit(':', 2)
                proxies_to_check.append(('http', ip_port))
                auth = {'username': username, 'password': password}
            # Handle proxy with separate auth
            elif len(args) >= 3 and ':' not in args[-1] and ':' not in args[-2]:
                auth = {'username': args[-2], 'password': args[-1]}
                proxy_args = args[:-2]
                for proxy in proxy_args:
                    if '://' in proxy:
                        parts = proxy.split('://')
                        if len(parts) == 2 and parts[0].lower() in ['http', 'https']:
                            proxies_to_check.append((parts[0].lower(), parts[1]))
                    elif ':' in proxy:
                        proxies_to_check.append(('http', proxy))
            else:
                auth = None
                for proxy in args:
                    if '://' in proxy:
                        parts = proxy.split('://')
                        if len(parts) == 2 and parts[0].lower() in ['http', 'https']:
                            proxies_to_check.append((parts[0].lower(), parts[1]))
                    elif ':' in proxy:
                        proxies_to_check.append(('http', proxy))
        else:
            if message.reply_to_message and message.reply_to_message.text:
                proxy_text = message.reply_to_message.text
                potential_proxies = proxy_text.split()
                auth = None
                for proxy in potential_proxies:
                    if ':' in proxy:
                        if proxy.count(':') == 3:  # Format ip:port:user:pass
                            ip_port, username, password = proxy.rsplit(':', 2)
                            proxies_to_check.append(('http', ip_port))
                            auth = {'username': username, 'password': password}
                        else:
                            proxies_to_check.append(('http', proxy))
            else:
                return await client.send_message(
                    message.chat.id,
                    "<b>❌ Provide at least one proxy for check</b>",
                    parse_mode=ParseMode.HTML
                )

        if not proxies_to_check:
            return await client.send_message(
                message.chat.id,
                "<b>❌ The Proxies Are Not Valid At All</b>",
                parse_mode=ParseMode.HTML
            )

        if len(proxies_to_check) > PROXY_CHECK_LIMIT:
            return await client.send_message(
                message.chat.id,
                "<b> ❌ Sorry Bro Maximum Proxy Check Limit Is 20 </b>",
                parse_mode=ParseMode.HTML
            )

        processing_msg = await client.send_message(
            chat_id=message.chat.id,
            text=f"<b> Smart Proxy Checker Checking Proxies 💥</b>",
            parse_mode=ParseMode.HTML
        )

        try:
            tasks = [checker.check_proxy(proxy, proxy_type, auth) for proxy_type, proxy in proxies_to_check]
            results = await asyncio.gather(*tasks)
            await send_results(client, message, processing_msg, results)
        except Exception as e:
            LOGGER.error(f"Error during proxy check: {e}")
            await processing_msg.edit_text("<b>Sorry Bro Proxy Checker API Dead</b>", parse_mode=ParseMode.HTML)
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
    await processing_msg.edit_text(full_response, parse_mode=ParseMode.HTML)
