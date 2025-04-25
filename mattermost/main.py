import asyncio

from data_source.zammad.update_tickets import process_tickets_beat_task
from mattermost.comunication import websocket_client


async def main():
    """Main function to run the bot."""
    while True:
        try:
            print("connecting to bot server ...")
            _ = asyncio.create_task(process_tickets_beat_task())
            await websocket_client()
        except Exception as e:
            print(f"Main loop error: {e}")
            print("Restarting in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
