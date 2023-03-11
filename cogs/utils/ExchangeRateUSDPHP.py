import asyncio
import time

import aiohttp


class ExchangeRateUSDPHP:
    def __init__(self):
        self.last_updated = time.time()
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.update())

    async def update(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/usd/php.json"
            ) as resp:
                if resp.status == 200:
                    self.exchange_rate = (await resp.json())["php"]
        # self.date = response['date']
        # self.exchange_rate = response['php']

    async def check_latest(self):
        if time.time() - self.last_updated >= 86400:
            await self.update()

    async def latest_exchange_rate(self):
        await self.check_latest()

        # TODO: As shown here, this value is a float. The problem is that we must parse the JSON string's real number as a decimal.Decimal. But aiohttp's JSON parser does not have an option for specifying how the real number should be converted (it defaults to float instead). I already tried working around this by instead using json.loads() but unlike aiohttp's which is async, this isn't. Now given that it's a small string, it probably shouldn't matter too much. But still, maybe there's a more optimal way. Or, do we just accept that float's impreciseness is acceptible given that this value is used to just generally guage how expensive a chatgpt cmd took, and nothing more.
        print(type(self.exchange_rate))
        return self.exchange_rate
