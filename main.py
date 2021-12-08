from init import logs, user_me, bot


if __name__ == "__main__":
    logs.info(f"@{user_me.username} 运行成功！")
    bot.run()
