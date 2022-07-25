import contextlib


def ip_info(url, ipinfo_json):
    ipinfo_list = [f"查询目标： `{url}`"]
    if ipinfo_json['query'] != url:
        ipinfo_list.extend(["解析地址： `" + ipinfo_json['query'] + "`"])
    ipinfo_list.extend(["地区： `" + ipinfo_json['country'] + ' - ' + ipinfo_json['regionName'] + ' - ' +
                        ipinfo_json['city'] + "`"])
    ipinfo_list.extend(["经纬度： `" + str(ipinfo_json['lat']) + ',' + str(ipinfo_json['lon']) + "`"])
    ipinfo_list.extend(["ISP： `" + ipinfo_json['isp'] + "`"])
    if ipinfo_json['org'] != '':
        ipinfo_list.extend(["组织： `" + ipinfo_json['org'] + "`"])
    with contextlib.suppress(Exception):
        ipinfo_list.extend(
            ['[' + ipinfo_json['as'] + '](https://bgp.he.net/' + ipinfo_json['as'].split()[0] + ')'])
    if ipinfo_json['mobile']:
        ipinfo_list.extend(['此 IP 可能为**蜂窝移动数据 IP**'])
    if ipinfo_json['proxy']:
        ipinfo_list.extend(['此 IP 可能为**代理 IP**'])
    if ipinfo_json['hosting']:
        ipinfo_list.extend(['此 IP 可能为**数据中心 IP**'])
    return '\n'.join(ipinfo_list)
