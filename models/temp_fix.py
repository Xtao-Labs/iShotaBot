import pyrogram


async def temp_fix(
    client: "pyrogram.Client",
    message: pyrogram.raw.base.Message,
    users: dict,
    chats: dict,
    topics: dict = None,
    is_scheduled: bool = False,
    replies: int = 1,
    business_connection_id: str = None,
    reply_to_message: "raw.base.Message" = None,
):
    parsed = await pyrogram.types.Message.old_parse(
        client,
        message,
        users,
        chats,
        topics,
        is_scheduled,
        replies,
        business_connection_id,
        reply_to_message,
    )  # noqa
    if (
        isinstance(message, pyrogram.raw.types.Message)
        and message.reply_to
        and hasattr(message.reply_to, "forum_topic")
        and message.reply_to.forum_topic
        and not message.reply_to.reply_to_top_id
    ):
        parsed.reply_to_top_message_id = parsed.reply_to_message_id
        parsed.reply_to_message_id = None
        parsed.reply_to_message = None
    return parsed
