from pyrogram import idle

from init import logs, user_me, bot, sqlite


if __name__ == "__main__":
    logs.info(f"@{user_me.username} 运行成功！")
    bot.start()
    bot.loop.create_task(sqlite.create_db_and_tables())
    idle()
    bot.stop()
    sqlite.stop()
