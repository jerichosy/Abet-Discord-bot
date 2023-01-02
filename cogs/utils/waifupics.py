import aiohttp


async def get_waifu(type, category):
    url_string = f"https://api.waifu.pics/{type}/{category}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url_string) as r:
            # logger.info(f"Waifu.pics: {r.status}")
            if r.status == 200:
                json_data = await r.json()
                waifu = json_data["url"]

    return waifu
