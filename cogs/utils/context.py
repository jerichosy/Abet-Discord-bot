from typing import TYPE_CHECKING

from aiohttp import ClientSession
from discord.ext import commands

if TYPE_CHECKING:
    from main import AbetBot


class Context(commands.Context):
    bot: "AbetBot"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def session(self) -> ClientSession:
        return self.bot.session
