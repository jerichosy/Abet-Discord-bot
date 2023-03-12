import asyncio
import time

import aiohttp


class ExchangeRateUSDPHP:
    def __init__(self):
        self._last_updated = time.time()
        self._loop = asyncio.get_event_loop()
        self._loop.create_task(self._update())

    async def _update(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/usd/php.json"
            ) as resp:
                if resp.status == 200:
                    self._exchange_rate = (await resp.json())["php"]

    async def _check_latest(self):
        if time.time() - self._last_updated >= 86400:
            await self._update()

    async def latest_exchange_rate(self):
        await self._check_latest()
        return self._exchange_rate
