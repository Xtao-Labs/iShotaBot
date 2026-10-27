
from init import request


async def get_whois_info(domain: str) -> dict | None:
    url = f"http://whois.4.cn/api/main?domain={domain}"
    try:
        response = await request.get(url, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        if data.get("retcode") != 0:
            return None
        return data.get("data")
    except Exception:
        return None


def format_whois_result(data: dict) -> str:
    def get_field(field, default="暂无信息"):
        return data.get(field) or default

    domain_name = get_field("domain_name")
    registrars = get_field("registrars")
    expire_date = get_field("expire_date")
    create_date = get_field("create_date")
    update_date = get_field("update_date")

    status_list = data.get("status", [])
    status = (
        "\n".join([f"• {s}" for s in status_list]) if status_list else "• 暂无状态信息"
    )

    nameserver_list = data.get("nameserver", [])
    nameserver = (
        "\n".join([f"• {ns}" for ns in nameserver_list])
        if nameserver_list
        else "• 暂无DNS信息"
    )

    owner_info = [
        f"├ 姓名：{get_field('owner_name')}",
        f"├ 机构：{get_field('owner_org')}",
        f"├ 邮箱：{get_field('owner_email')}",
        f"└ 电话：{get_field('owner_phone')}",
    ]
    owner_info_text = "\n".join(owner_info)

    return f"""
🔍 Whois 查询结果 [ {domain_name} ]
──────────────────────────────
🗓 注册信息：
├ 注册机构：{registrars}
├ 创建时间：{create_date}
├ 到期时间：{expire_date}
└ 更新时间：{update_date}

📊 域名状态：
{status}

🌐 DNS 服务器：
{nameserver}

👤 持有人信息：
{owner_info_text}
""".strip()
