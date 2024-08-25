# CONTRIBUTING

## Conventions:
- When receiving user input that is too long, explicitly reject it. Do not truncate it as that is only meant for output (display).
- When specifying URL variables, do not include the trailing slash (`/`) as part of the hostname. Instead, it should be the prefix of the URL path as it is clearer and is in-line with how routes are declared in web frameworks (e.g. Express, FastAPI).
- Do not create an `aiohttp.ClientSession` per request. Instead, reuse the existing session either through `ctx.session` or `bot.session` to take advantage of the connection pool and keep-alive which may speed up performance.
