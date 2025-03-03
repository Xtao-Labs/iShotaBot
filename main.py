import asyncio

from pyrogram import idle

from init import logs, bot, sqlite
from models.services.bsky import bsky_client
from scheduler import scheduler


async def main():
    logs.info("连接服务器中。。。")
    await bot.start()
    if not scheduler.running:
        scheduler.start()
    bot.loop.create_task(sqlite.create_db_and_tables())
    bot.loop.create_task(bsky_client.initialize())
    logs.info(f"@{bot.me.username} 运行成功！")
    await idle()
    await bot.stop()
    sqlite.stop()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
