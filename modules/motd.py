from defs.motd import send_mc_notice
from scheduler import scheduler


@scheduler.scheduled_job("interval", minutes=1, id="mc_server_notice")
async def mc_server_notice():
    await send_mc_notice()
