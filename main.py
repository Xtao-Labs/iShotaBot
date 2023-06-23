import asyncio

from pyrogram import idle

from init import logs, bot, sqlite


async def main():
    logs.info("连接服务器中。。。")
    await bot.start()
    bot.loop.create_task(sqlite.create_db_and_tables())
    logs.info(f"@{bot.me.username} 运行成功！")
    await idle()
    await bot.stop()
    sqlite.stop()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
