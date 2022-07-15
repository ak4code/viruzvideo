import logging
import os
from dotenv import load_dotenv
from utils import ViruzVideo

from aiogram import Bot, Dispatcher, executor, types

load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
vv = ViruzVideo()


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await message.reply("Привет! Этот бот ищет и отправляет видео из TikToka!")


@dp.message_handler()
async def echo(message: types.Message):
    result = await vv.get_video(message.text, message)
    await message.answer(result)
    # await message.answer_video(open('output/out.mp4', 'rb'))


@dp.message_handler()
async def video(message: types.Message):
    pass


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
