import ssl
import json
import websockets
import asyncio
import urllib3
import aiohttp

from core.log_config import mattermost_bot_logger as logger

from ai.query import query_controller

from core.config import (
    MATTERMOST_URL,
    MATTERMOST_WEBSOCKET_URL,
    MATTERMOST_BOT_TOKEN,
    MATTERMOST_BOT_USERNAME
)

HEADERS = {
    "Authorization": f"Bearer {MATTERMOST_BOT_TOKEN}",
    "Content-Type": "application/json"
}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

processed_messages = set()


async def send_message(channel_id: str, message: str, root_id: str = None):
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{MATTERMOST_URL}/api/v4/posts"
            payload = {
                "channel_id": channel_id,
                "message": message,
                "root_id": root_id
            }

            async with session.post(url, json=payload, headers=HEADERS, ssl=False) as response:
                if response.status == 201:
                    logger.info(f"Message sent successfully in channel {channel_id}: {message}")
                else:
                    error_msg = await response.text()
                    logger.error(f"Failed to send message. Status: {response.status}, Error: {error_msg}")
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise


async def handle_message(message_data: dict):
    try:
        if message_data.get('event') != 'posted':
            return

        post = json.loads(message_data['data']['post'])
        message_id = post['id']
        channel_id = post['channel_id']
        message = post['message']

        if message_id in processed_messages or post.get('props', {}).get('from_bot', False):
            return

        is_direct_message = False
        async with aiohttp.ClientSession() as session:
            url = f"{MATTERMOST_URL}/api/v4/channels/{channel_id}"
            async with session.get(url, headers=HEADERS, ssl=False) as response:
                if response.status == 200:
                    channel_info = await response.json()
                    is_direct_message = channel_info.get("type") == "D"

        bot_mentioned = f"@{MATTERMOST_BOT_USERNAME}" in message

        if not is_direct_message and not bot_mentioned:
            return

        processed_messages.add(message_id)

        logger.info(f"\033[94mReceived message in channel {channel_id}: {message}\033[0m")

        responses = await query_controller(message)
        logger.info(f"Generated response: {responses}")
        root_id = post.get("root_id") or message_id  # Reply in the thread
        [await send_message(channel_id, response, root_id) for response in responses]

        logger.info(f"Response sent to channel {channel_id}: {responses}")

    except Exception as e:
        logger.error(f"Error handling message: {str(e)}", exc_info=True)


async def websocket_client():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    seq_num = 1

    while True:
        try:
            async with websockets.connect(MATTERMOST_WEBSOCKET_URL, ssl=ssl_context) as websocket:
                logger.info("Connected to WebSocket")

                auth_message = {
                    "seq": seq_num,
                    "action": "authentication_challenge",
                    "data": {"token": MATTERMOST_BOT_TOKEN}
                }
                await websocket.send(json.dumps(auth_message))
                logger.info("Authentication message sent")

                auth_response = await websocket.recv()
                logger.info(f"Auth response: {auth_response}")

                while True:
                    try:
                        message = await websocket.recv()
                        message_data = json.loads(message)
                        await handle_message(message_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message: {e}", exc_info=True)
                    except websockets.ConnectionClosed:
                        logger.warning("WebSocket connection closed")
                        break
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}", exc_info=True)
            logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)


async def main():
    while True:
        try:
            await websocket_client()
        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
            logger.info("Restarting in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
