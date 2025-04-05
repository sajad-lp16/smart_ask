import json
import websockets
import asyncio
import ssl
import urllib3
import aiohttp
import logging

from decouple import config

# from ai. import query_documents

MATTERMOST_URL = config("MATTERMOST_URL")
MM_BOT_TOKEN = config("MM_BOT_TOKEN")
WEBSOCKET_URL = config("WEBSOCKET_URL")
BOT_USERNAME = config("BOT_USERNAME")

HEADERS = {
    "Authorization": f'Bearer {MM_BOT_TOKEN}',
    "Content-Type": "application/json"
}

# Configure logging
MESSAGES_LOG_FILE = "messages.log"
EVENTS_LOG_FILE = "events.log"

# Logging for received messages
messages_logger = logging.getLogger('messages')
messages_logger.setLevel(logging.INFO)
messages_handler = logging.FileHandler(MESSAGES_LOG_FILE)
messages_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
messages_logger.addHandler(messages_handler)

# Logging for other events
events_logger = logging.getLogger('events')
events_logger.setLevel(logging.INFO)
events_handler = logging.FileHandler(EVENTS_LOG_FILE)
events_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
events_logger.addHandler(events_handler)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Keep track of processed messages
processed_messages = set()


async def send_message(channel_id: str, message: str, root_id: str = None):
    """Send a message and log it."""
    async with aiohttp.ClientSession() as session:
        url = f"{MATTERMOST_URL}/api/v4/posts"
        payload = {
            "channel_id": channel_id,
            "message": message,
            "root_id": root_id
        }

        async with session.post(url, json=payload, headers=HEADERS, ssl=False) as response:
            if response.status == 201:
                events_logger.info(f"Message sent successfully in channel {channel_id}: {message}")
            else:
                error_msg = await response.text()
                events_logger.error(f"Failed to send message. Status: {response.status}, Error: {error_msg}")


async def handle_message(message_data: dict):
    """Handle messages, log all received messages, and respond when necessary."""
    try:
        if message_data.get('event') != 'posted':
            return

        post = json.loads(message_data['data']['post'])
        message_id = post['id']
        channel_id = post['channel_id']
        message = post['message']

        # Prevent bot from responding to itself
        if message_id in processed_messages or post.get('props', {}).get('from_bot', False):
            return

        # Check if it's a direct message
        is_direct_message = False
        async with aiohttp.ClientSession() as session:
            url = f"{MATTERMOST_URL}/api/v4/channels/{channel_id}"
            async with session.get(url, headers=HEADERS, ssl=False) as response:
                if response.status == 200:
                    channel_info = await response.json()
                    is_direct_message = channel_info.get("type") == "D"

        # Check if bot is mentioned in a public/private channel
        bot_mentioned = f"@{BOT_USERNAME}" in message

        # Ignore message if not in DM and not mentioned
        if not is_direct_message and not bot_mentioned:
            return

        processed_messages.add(message_id)  # Mark message as processed

        # Log received message
        messages_logger.info(f"Received message in channel {channel_id}: {message}")

        response = await query_documents(message)
        events_logger.info(f"Generated response: {response}")
        root_id = post.get("root_id") or message_id  # Reply in the thread
        await send_message(channel_id, response, root_id)

        # Log sent response
        messages_logger.info(f"Response sent to channel {channel_id}: {response}")

    except Exception as e:
        events_logger.error(f"Error handling message: {e}", exc_info=True)


async def websocket_client():
    """Maintain WebSocket connection and handle messages."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    seq_num = 1

    while True:
        try:
            async with websockets.connect(WEBSOCKET_URL, ssl=ssl_context) as websocket:
                events_logger.info("Connected to WebSocket")

                # Authentication
                auth_message = {
                    "seq": seq_num,
                    "action": "authentication_challenge",
                    "data": {"token": MM_BOT_TOKEN}
                }
                await websocket.send(json.dumps(auth_message))
                events_logger.info("Authentication message sent")

                # Wait for auth response
                auth_response = await websocket.recv()
                events_logger.info(f"Auth response: {auth_response}")

                while True:
                    try:
                        message = await websocket.recv()
                        message_data = json.loads(message)
                        await handle_message(message_data)
                    except json.JSONDecodeError as e:
                        events_logger.error(f"Failed to parse message: {e}", exc_info=True)
                    except websockets.ConnectionClosed:
                        events_logger.warning("WebSocket connection closed")
                        break
                    except Exception as e:
                        events_logger.error(f"Error processing message: {e}", exc_info=True)

        except Exception as e:
            events_logger.error(f"WebSocket connection error: {e}", exc_info=True)
            events_logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)


async def main():
    """Main function to run the bot."""
    while True:
        try:
            await websocket_client()
        except Exception as e:
            events_logger.error(f"Main loop error: {e}", exc_info=True)
            events_logger.info("Restarting in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
