import asyncio
import time

import aiohttp

UPDATE_INTERVAL = 86400  # 24 hours


class ExchangeRateUSDPHP:
    def __init__(self):
        self._exchange_rate = None
        self._last_updated = time.time()
        self._loop = asyncio.get_event_loop()
        self._loop.create_task(self._update())

    async def _update(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
                ) as resp:
                    resp.raise_for_status()
                    self._exchange_rate = (await resp.json())["usd"]["php"]
                    self._last_updated = time.time()
        except Exception as e:
            print(f"Failed to update exchange rate: {e}")
            raise e

    async def _check_latest(self):
        if time.time() - self._last_updated >= UPDATE_INTERVAL:
            await self._update()

    async def latest_exchange_rate(self):
        await self._check_latest()
        return self._exchange_rate
