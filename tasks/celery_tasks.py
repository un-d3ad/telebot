import os
import asyncio
import traceback
from telegram import Bot
from telegram import InputFile
from dotenv import load_dotenv
from telegram.error import TelegramError, InvalidToken

from celery_config import celery_app

load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
MEDIA_PATH = os.environ.get("MEDIA_PATH")


######################## Send message to Private ########################
async def async_send_message_to_private(api_token, user_id, message, image_url, file_path):
    bot = Bot(token=api_token)
    try:
        if image_url:
            await bot.send_photo(chat_id=user_id, photo=image_url, caption=message, connect_timeout=20, read_timeout=20, write_timeout=20, parse_mode='HTML')
        elif file_path:
            file_path = os.path.join(MEDIA_PATH, file_path)
            with open(file_path, 'rb') as image_file:
                await bot.send_photo(chat_id=user_id, photo=InputFile(image_file), caption=message, connect_timeout=20, read_timeout=20, write_timeout=20, parse_mode='HTML')
        else:
            await bot.send_message(chat_id=user_id, text=message, connect_timeout=20, read_timeout=20, write_timeout=20, parse_mode='HTML')
        return {"status": "success", "message": f"Message sent to user: {message}"}
    except InvalidToken:
        return {"status": "error", "message": "Invalid API token"}
    except TelegramError as e:
        return {"status": "error", "message": f"Error sending message: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Unknown error: {e}"}


# Celery Task
@celery_app.task
def send_message_to_private(user_id, message, image_url, file_path):
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(async_send_message_to_private(
            BOT_TOKEN, user_id, message, image_url, file_path))
    except Exception as e:
        print(f"Failed to send message: {traceback.format_exc()}")
        result = {"status": "error", "message": f"Task failed: {e}"}

    return result


######################## Send message to Group ########################
async def async_send_message_to_group(api_token, group_id, thread_id=None, message=None, image_url=None, file_path=None):
    bot = Bot(token=api_token)

    try:
        # Handle file-based photo sending
        if file_path:
            file_path = os.path.join(MEDIA_PATH, file_path)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as image_file:
                    if thread_id:
                        await bot.send_photo(
                            chat_id=group_id,
                            message_thread_id=thread_id,
                            photo=InputFile(image_file),
                            caption=message,
                            parse_mode='HTML'
                        )
                    else:
                        await bot.send_photo(
                            chat_id=group_id,
                            photo=InputFile(image_file),
                            caption=message,
                            parse_mode='HTML'
                        )
                return {"status": "success", "message": f"Message sent to group with file: {message}\n{file_path}"}
            else:
                print(
                    f"File not found: {file_path}. Retrying without the file.")
                # Retry without the file
                file_path = None
                message = f"{message} \n\n______________________\n<i>WARN: File not found!</i>"

        # Handle URL-based photo sending
        if image_url:
            if thread_id:
                await bot.send_photo(
                    chat_id=group_id,
                    message_thread_id=thread_id,
                    photo=image_url,
                    caption=message,
                    parse_mode='HTML'
                )
            else:
                await bot.send_photo(
                    chat_id=group_id,
                    photo=image_url,
                    caption=message,
                    parse_mode='HTML'
                )
            return {"status": "success", "message": f"Message sent to group with image url: {message}"}

        # Handle text message sending
        if thread_id:
            await bot.send_message(
                chat_id=group_id,
                message_thread_id=thread_id,
                text=message,
                parse_mode='HTML'
            )
        else:
            await bot.send_message(
                chat_id=group_id,
                text=message,
                parse_mode='HTML'
            )
        return {"status": "success", "message": f"Message sent to group: {message}"}

    except InvalidToken:
        return {"status": "error", "message": "Invalid API token"}
    except TelegramError as e:
        return {"status": "error", "message": f"Telegram error: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Unknown error: {e}"}


# Celery Task
@celery_app.task
def send_message_to_group(api_token, group_id, thread_id=None, message=None, image_url=None, file_path=None):
    try:
        result = asyncio.run(async_send_message_to_group(
            api_token, group_id, thread_id, message, image_url, file_path))
        return result
    except Exception as e:
        print(f"Failed to send message: {traceback.format_exc()}")
        return {"status": "error", "message": f"Task failed: {e}"}
