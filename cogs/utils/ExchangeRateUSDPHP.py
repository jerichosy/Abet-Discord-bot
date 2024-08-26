# import asyncio
import time

UPDATE_INTERVAL = 86400  # 24 hours


class ExchangeRateUSDPHP:
    def __init__(self, session):
        self._session = session
        self._exchange_rate = None
        self._last_updated = None
        # self._loop = asyncio.get_event_loop()
        # self._loop.create_task(self._update())

    async def _update(self):
        try:
            async with self._session.get(
                "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
            ) as resp:
                resp.raise_for_status()
                self._exchange_rate = (await resp.json())["usd"]["php"]
                self._last_updated = time.time()
                print(f"Updated exchange rate: {self._exchange_rate}")
        except Exception as e:
            print(f"Failed to update exchange rate: {e}")
            raise e

    async def _check_latest(self):
        if self._exchange_rate is None:
            print("No exchange rate found, updating...")
            await self._update()
        elif time.time() - self._last_updated >= UPDATE_INTERVAL:
            print("Exchange rate is outdated, updating...")
            await self._update()

    async def latest_exchange_rate(self):
        await self._check_latest()
        print(f"Returning exchange rate: {self._exchange_rate}")
        return self._exchange_rate
