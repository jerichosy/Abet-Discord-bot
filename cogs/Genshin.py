import math
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from cogs.utils import genshinutils


class Genshin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Note to self: Don't send msg in a coding block to retain markdown support
    # TODO: Strictly speaking, the shop resets at 4 AM so this can mislead someone. I'm not sure also with regards to host location's timezones. I'll work on it when it seems needed.
    # TODO: Convert to embed?
    @commands.hybrid_command(aliases=["paimonbargains", "paimon'sbargains", "viewshop"])
    async def paimonsbargains(self, ctx):
        """Genshin Impact: Views current Paimon's Bargains items for the month"""
        current_month = datetime.now().month

        def display_future():
            built = "\n\n**Future:**\n"
            for x in range(1, 7):
                built += (
                    "`"
                    + genshinutils.MONTHS[((current_month + x) % 12) - 1]
                    + "` | "
                    + genshinutils.CHARACTERS[((current_month + x) % 6) - 1]
                    + "\n"
                )

            return built

        def determine_weapon_series():
            return "\n  Blackcliff series" if current_month % 2 else "\n  Royal series"

        await ctx.send(
            "**Current:**\n"
            + "`"
            + genshinutils.MONTHS[current_month - 1]
            + "` | "
            + genshinutils.CHARACTERS[(current_month % 6) - 1]
            + determine_weapon_series()
            + display_future()
        )

    @app_commands.command()
    async def calc(
        self,
        interaction: discord.Interaction,
        current_level: app_commands.Range[int, 1, 90],
        current_experience: app_commands.Range[int, 0, None],
        target_level: app_commands.Range[int, 1, 90],
    ):
        """Genshin Impact: Calculate how much Hero's Wit, etc. you need to level/ascend your characters"""

        # validation
        if current_level >= target_level:
            return await interaction.response.send_message("Already achieved the target level.")
        if genshinutils.CHARACTER_EXP_LIST[current_level] < current_experience:
            return await interaction.response.send_message(
                "Current experience exceeds the maximum experience in the current level."
            )

        totalExpNeeded = 0

        for i in range(current_level, target_level):
            if i == current_level:
                totalExpNeeded += genshinutils.CHARACTER_EXP_LIST[i] - current_experience
            else:
                totalExpNeeded += genshinutils.CHARACTER_EXP_LIST[i]

        def ceilNumber(num, place):
            div = 1
            for _ in range(0, place):
                div *= 10
            return math.ceil(num / div) * div

        currentExpNeeded = ceilNumber(totalExpNeeded, 3)

        totalLargeNeeded = math.floor(currentExpNeeded / 20000)
        currentExpNeeded -= totalLargeNeeded * 20000
        totalMediumNeeded = math.floor(currentExpNeeded / 5000)
        currentExpNeeded -= totalMediumNeeded * 5000
        totalSmallNeeded = math.floor(currentExpNeeded / 1000)

        response = f"""__To ascend from level {current_level} to {target_level} with current EXP of {current_experience}, you'll need:__

    `{totalLargeNeeded:>3}` × <:HerosWit:984919059780993134> **Hero's Wit**
    `{totalMediumNeeded:>3}` × <:AdventurersExperience:984919553366708256> **Adventurer's Experience**
    `{totalSmallNeeded:>3}` × <:WanderersAdvice:984919638792085505> **Wanderer's Advice**"""

        await interaction.response.send_message(response)


async def setup(bot):
    await bot.add_cog(Genshin(bot))
