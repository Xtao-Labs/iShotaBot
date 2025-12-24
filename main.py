import asyncio
from pyrogram import idle

from defs import browser
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
    scheduler.shutdown()
    await browser.shutdown_browser()


if __name__ == "__main__":
    bot.run(main())
