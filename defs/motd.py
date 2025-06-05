import traceback
from typing import Optional
from mcstatus import JavaServer

from defs.glover import mc_server_url, mc_group_id
from init import bot

SERVER_PLAYER_LIST = []


async def get_server_players() -> Optional[list[str]]:
    """
    Fetch the server's message of the day (MOTD).
    Returns:
        str: The MOTD text.
    """
    if not mc_server_url:
        return None
    try:
        server = JavaServer.lookup(mc_server_url)
        status = server.status()
        return [i.name for i in status.players.sample if i.name != "Anonymous Player"]
    except Exception as e:
        traceback.print_exc()
        return None


async def send_mc_notice():
    if not mc_group_id:
        return
    new_player_list = await get_server_players()
    if new_player_list is None:
        return
    if new_player_list != SERVER_PLAYER_LIST:
        left_players = set(SERVER_PLAYER_LIST) - set(new_player_list)
        if left_players:
            await bot.send_message(
                mc_group_id,
                f"{', '.join(left_players)} 退出了服务器。",
            )
        joined_players = set(new_player_list) - set(SERVER_PLAYER_LIST)
        if joined_players:
            await bot.send_message(
                mc_group_id,
                f"{', '.join(joined_players)} 加入了服务器。",
            )
    SERVER_PLAYER_LIST.clear()
    SERVER_PLAYER_LIST.extend(new_player_list)
