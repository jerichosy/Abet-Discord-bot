import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime
import time
import genshinstats as gs
from collections import Counter
import math


class Genshin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        self.characters = [
            "Fischl Xiangling",
            "Beidou Noelle",
            "Ningguang Xingqiu",
            "Razor Amber",
            "Bennett Lisa",
            "Barbara Kaeya",
        ]
        self.characterExpList = [
            0,
            1000,
            1325,
            1700,
            2150,
            2625,
            3150,
            3725,
            4350,
            5000,
            5700,
            6450,
            7225,
            8050,
            8925,
            9825,
            10750,
            11725,
            12725,
            13775,
            14875,
            16800,
            18000,
            19250,
            20550,
            21875,
            23250,
            24650,
            26100,
            27575,
            29100,
            30650,
            32250,
            33875,
            35550,
            37250,
            38975,
            40750,
            42575,
            44425,
            46300,
            50625,
            52700,
            54775,
            56900,
            59075,
            61275,
            63525,
            65800,
            68125,
            70475,
            76500,
            79050,
            81650,
            84275,
            86950,
            89650,
            92400,
            95175,
            98000,
            100875,
            108950,
            112050,
            115175,
            118325,
            121525,
            124775,
            128075,
            131400,
            134775,
            138175,
            148700,
            152375,
            156075,
            159825,
            163600,
            167425,
            171300,
            175225,
            179175,
            183175,
            216225,
            243025,
            273100,
            306800,
            344600,
            386950,
            434425,
            487625,
            547200,
        ]

    # Note to self: Don't send msg in a coding block to retain markdown support
    # TODO: Strictly speaking, the shop resets at 4 AM so this can mislead someone. Also, the bot is in NYC. I'll work on it when it seems needed.
    # TODO: Convert to embed?
    @commands.hybrid_command(aliases=["paimonbargains", "paimon'sbargains", "viewshop"])
    # @app_commands.guilds(discord.Object(id=867811644322611200))
    async def paimonsbargains(self, ctx):
        """Genshin Impact: Views current Paimon's Bargains items for the month"""
        current_month = datetime.now().month

        def display_future():
            built = "\n\n**Future:**\n"
            for x in range(1, 7):
                built += (
                    "`"
                    + self.months[((current_month + x) % 12) - 1]
                    + "` | "
                    + self.characters[((current_month + x) % 6) - 1]
                    + "\n"
                )

            return built

        def determine_weapon_series():
            return "\n  Blackcliff series" if current_month % 2 else "\n  Royal series"

        await ctx.send(
            "**Current:**\n"
            + "`"
            + self.months[current_month - 1]
            + "` | "
            + self.characters[(current_month % 6) - 1]
            + determine_weapon_series()
            + display_future()
        )

    @app_commands.command()
    async def characterexp(
        self,
        interaction: discord.Interaction,
        current_level: app_commands.Range[int, 1, 90],
        current_experience: app_commands.Range[int, 0, None],
        target_level: app_commands.Range[int, 1, 90],
    ):
        """Genshin Impact: Calculate how much Hero's Wit, etc. you need to level/ascend your characters"""

        # validation
        if current_level >= target_level:
            return await interaction.response.send_message(
                "Already achieved the target level."
            )
        if self.characterExpList[current_level] < current_experience:
            return await interaction.response.send_message(
                "Current experience exceeds the maximum experience in the current level."
            )

        totalExpNeeded = 0

        for i in range(current_level, target_level):
            if i == current_level:
                totalExpNeeded += self.characterExpList[i] - current_experience
            else:
                totalExpNeeded += self.characterExpList[i]

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

    # @app_commands.command()
    # @app_commands.guilds(discord.Object(id=867811644322611200))
    # @app_commands.describe(uid='The UID of the person you want to investigate')
    @commands.command()
    async def genshinspy(self, ctx, uid: commands.Range[int, 100000000, 999999999]):
        """Get the details of someone's Genshin account"""
        gs.set_cookie(ltuid=os.getenv("LTUID"), ltoken=os.getenv("LTOKEN"))

        async with ctx.typing():
            data = gs.get_characters(uid)
            data.sort(key=lambda x: (x["rarity"], x["level"]), reverse=True)

            def tally_artifacts(artifact):
                if not artifact:
                    return ""

                artifact_list = []
                for x in artifact:
                    artifact_list.append(x["set"]["name"])

                artifact_count = Counter(artifact_list)
                built2 = ""
                for artifact_set in artifact_count:
                    # This is okay if it reports a "3pc." or "5pc.". It's kinda funny and provokes envy as well!
                    built2 += (
                        f", {artifact_count[artifact_set]}pc. {artifact_set}"
                        if artifact_count[artifact_set] >= 2
                        else ""
                    )

                # TODO: Latter is not tested
                return (
                    f"\n    {built2[2:]}"
                    if built2[2:] is not None
                    else "(No 2pc. of any set)"
                )

            # print(json.dumps(data))

            built = ""
            for char in data:
                new = f"{char['name']} ({char['rarity']}* {char['element']}): lvl {char['level']} C{char['constellation']} | {char['weapon']['name']} ({char['weapon']['rarity']}* {char['weapon']['type']}): lvl {char['weapon']['level']} R{char['weapon']['refinement']} {tally_artifacts(char['artifacts'])}\n"
                if len(built) + len(new) <= 2000:
                    built += new
                else:
                    break
            await ctx.reply(f"```{built}```")

    @commands.hybrid_command(
        aliases=[
            "resinreplenish",
            "replenish",
            "resins",
            "resinsreplenish",
            "replenishment",
            "resinreplenishment",
            "resinsreplenishment",
            "resinfinish",
            "resinfinished",
            "resinsfinish",
            "resinsfinished",
        ]
    )
    # @app_commands.guilds(discord.Object(id=867811644322611200))
    @app_commands.describe(current_resin="The amount of resin that you have right now")
    async def resin(self, ctx, current_resin: commands.Range[int, None, 160]):
        """Genshin Impact: Calculate when your resin will replenish"""

        time_to_fully_replenished = (160 - current_resin) * (8 * 60)
        current_time = time.time()
        finished_time = current_time + time_to_fully_replenished
        await ctx.reply(
            f"Resin will be fully replenished at: <t:{int(finished_time)}:F> (<t:{int(finished_time)}:R>)"
        )


async def setup(bot):
    await bot.add_cog(Genshin(bot))
