import asyncio
import time

import aiohttp


class ExchangeRateUSDPHP:
    def __init__(self):
        self.time_since_last_update = time.time()
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.update())

    async def update(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/usd/php.json"
            ) as resp:
                if resp.status == 200:
                    self.exchange_rate = await resp.json()
        # self.date = response['date']
        # self.exchange_rate = response['php']

    async def check_latest(self):
        if time.time() - self.time_since_last_update > 86400:
            await self.update()

    async def latest_exchange_rate(self):
        await self.check_latest()
        return self.exchange_rate["php"]
