import asyncio

from core.log_config import ai_logger as logger
from mattermost.comunication import websocket_client
from data_source.forum.update_topics import process_topics_beat_task
from data_source.zammad.update_tickets import process_tickets_beat_task


async def main():
    """Main function to run the bot."""
    while True:
        try:
            logger.info("Connecting to BOT server")
            _ = asyncio.create_task(process_tickets_beat_task())
            _ = asyncio.create_task(process_topics_beat_task())
            await websocket_client()
        except Exception as err:
            logger.error(f"main loop error {err}")
            logger.info("Restarting in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
