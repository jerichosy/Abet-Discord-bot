# CONTRIBUTING

## Conventions:
- When receiving user input that is too long, explicitly reject it. Do not truncate it as that is only meant for output (display).
- When specifying URL variables, do not include the trailing slash (`/`) as part of the hostname. Instead, it should be the prefix of the URL path as it is clearer and is in-line with how routes are declared in web frameworks (e.g. Express, FastAPI).
- Do not create an `aiohttp.ClientSession` per request. Instead, reuse the existing session either through `ctx.session` or `bot.session` to take advantage of the connection pool and keep-alive which may speed up performance.
- Lazy initialize whenever possible and practical (e.g. clients, web APIs). Do not preemptively populate data like what was done for [`waifu_im_tags`](https://github.com/jerichosy/Abet-Discord-bot/blob/f06aab841dadd2c96fa81f4a6a277fa3e2dd5e96/cogs/Fun.py#L222-L228) and [`ExchangeRateUSDPHP`](https://github.com/jerichosy/Abet-Discord-bot/blob/f06aab841dadd2c96fa81f4a6a277fa3e2dd5e96/cogs/utils/ExchangeRateUSDPHP.py#L13-L14) before. Exceptions to this include the database (it's easier to catch an issue on startup) and `aiohttp.ClientSession`.
