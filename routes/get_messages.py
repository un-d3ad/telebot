import pytz
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Request
from telethon.sync import TelegramClient

from config.logger import logger
from utils.helper import ResponseHelper

router = APIRouter()
response = ResponseHelper()

# Use your own Telegram API credentials
API_ID = 12345678
API_HASH = 'your_api_hash'

# Initialize Telegram Client
client = TelegramClient('session_name', API_ID, API_HASH)


# Start the client with the bot token
async def start_client():
    await client.start()


# Ensure the client is started before handling requests
@router.on_event("startup")
async def startup_event():
    await start_client()


class MessageCountBody(BaseModel):
    group_id: int = Field(...,)
    start_time: str = Field(...,)
    end_time: str = Field(...,)
    thread_id: int = Field(None,)


@router.post("/get-message-count")
async def get_message_count(
    request: Request,
    data: MessageCountBody
):
    """Fetch the number of messages in a Telegram group between start_time and end_time."""

    # Convert string timestamps to datetime objects
    tz = pytz.UTC  # Ensure UTC timezone
    start_dt = tz.localize(datetime.strptime(
        data.start_time, "%Y-%m-%d %H:%M:%S"))
    end_dt = tz.localize(datetime.strptime(data.end_time, "%Y-%m-%d %H:%M:%S"))

    try:
        count = 0
        async for message in client.iter_messages(data.group_id, offset_date=end_dt):
            logger.info(f"Message: {message}")
            if message.date < start_dt:
                break  # Stop fetching if the message is older than the start time

            # If thread_id is provided, filter messages in the specific thread
            if data.thread_id and message.reply_to_msg_id != int(data.thread_id):
                continue

            count += 1

        return {"group_id": data.group_id, "thread_id": data.thread_id, "message_count": count}

    except Exception as e:
        return {"error": str(e)}
