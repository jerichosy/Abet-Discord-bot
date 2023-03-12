import datetime
import itertools
import time

import discord
import pkg_resources
import psutil
import pygit2
from discord.ext import commands

from cogs.utils import timeutils


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def format_commit(self, commit: pygit2.Commit) -> str:
        short, _, _ = commit.message.partition("\n")
        short_sha2 = commit.hex[0:6]
        commit_tz = datetime.timezone(
            datetime.timedelta(minutes=commit.commit_time_offset)
        )
        commit_time = datetime.datetime.fromtimestamp(commit.commit_time).astimezone(
            commit_tz
        )

        # [`hash`](url) message (offset)
        offset = timeutils.format_relative(
            commit_time.astimezone(datetime.timezone.utc)
        )
        return f"[`{short_sha2}`](https://github.com/jerichosy/Abet-Discord-bot/commit/{commit.hex}) {short} ({offset})"

    def get_last_commits(self, count=3):
        repo = pygit2.Repository(".git")
        commits = list(
            itertools.islice(
                repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL), count
            )
        )
        return "\n".join(self.format_commit(c) for c in commits)

    @commands.hybrid_command(aliases=["info", "github", "repo", "repository"])
    async def about(self, ctx):
        """link to documentation & source code on GitHub"""

        revision = self.get_last_commits()

        embed = discord.Embed(
            title="FUCK CARL",
            color=0xEE615B,
            url="https://cdn.discordapp.com/attachments/731542246951747594/905830644607758416/abet_bot.png",
            description=f"Latest Changes:\n{revision}\n\nSource code & documentation: [GitHub repository](https://github.com/jerichosy/Abet-Discord-bot)",
        )

        embed.set_image(
            url="https://opengraph.githubassets.com/89c81820967bbd8115fc6a68d55ef62a3964c8caf19e47a321f12d969ac3b6e3/jerichosy/Abet-Discord-bot"
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        main_guild = self.bot.get_guild(self.bot.HOME_GUILD.id)
        owner = main_guild.get_member(list(self.bot.owner_ids)[1])
        embed.set_author(
            name=f"{owner.name}#{owner.discriminator}",
            icon_url=owner.display_avatar.url,
        )

        version = pkg_resources.get_distribution("discord.py").version
        embed.set_footer(
            text=f"</> with 💖 by Kyoya Intelligence Agency and Tre' Industries using Python (discord.py v{version})",
            icon_url="https://media.discordapp.net/stickers/946824812658065459.png",
        )

        process = psutil.Process()

        memory_usage = process.memory_full_info().uss / 1024**2
        cpu_usage = process.cpu_percent() / psutil.cpu_count()
        embed.add_field(
            name="Process", value=f"{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU"
        )

        # embed.add_field(name='Uptime', value=self.get_bot_uptime(brief=True))  # TODO: Follow https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/stats.py#L301

        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def ping(self, ctx):
        """Get the bot's current websocket and API latency"""
        start_time = time.time()
        to_edit = await ctx.send("Testing ping...")
        end_time = time.time()
        await to_edit.edit(
            content=f"Pong! {round(self.bot.latency * 1000)}ms | API: {round((end_time - start_time) * 1000)}ms"
        )

    @commands.hybrid_command()
    async def invite(self, ctx):
        """Add Abet bot to your server!"""
        await ctx.send(self.bot.INVITE_LINK)


async def setup(bot):
    await bot.add_cog(Info(bot))
