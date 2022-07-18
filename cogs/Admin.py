import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, Context, Greedy
from discord import app_commands
from typing import Literal, Optional


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["delete", "cleanup"])
    @has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: commands.Range[int, 1, 35]):
        await ctx.channel.purge(limit=amount + 1)

    @commands.command(aliases=["close", "shutup", "logoff", "stop"])
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send("🛑 Shutting down!")
        await self.bot.close()

    # TODO: Add permissions?
    # FIXME:
    # @app_commands.command()
    # @app_commands.guilds(self.bot.HOME_GUILD)
    # # @has_permissions(manage_guild=True)
    # async def changestatus(
    #     self,
    #     interaction: discord.Interaction,
    #     activity: Literal["Playing", "Listening to", "Watching"],
    #     status_msg: str,
    # ):
    #     """Change the status/activity of the bot"""
    #     # https://discordpy.readthedocs.io/en/master/api.html#discord.ActivityType

    #     if activity == "Playing":
    #         await self.bot.change_presence(activity=discord.Game(name=status_msg))
    #     elif activity == "Listening to":
    #         await self.bot.change_presence(
    #             activity=discord.Activity(
    #                 name=status_msg, type=discord.ActivityType.listening
    #             )
    #         )
    #     elif activity == "Watching":
    #         await self.bot.change_presence(
    #             activity=discord.Activity(
    #                 name=status_msg, type=discord.ActivityType.watching
    #             )
    #         )

    #     await interaction.response.send_message(
    #         f'✅ My status is now "{activity} **{status_msg}**"'
    #     )

    @commands.command()
    async def sendmsg(self, ctx, channel_id: int, *, content):
        # print(content)
        channel = self.bot.get_channel(channel_id)
        await channel.send(content)
        await ctx.send(f"**Sent:** {content}\n**Where:** <#{channel_id}>")

    @commands.command()
    async def sendreply(self, ctx, channel_id: int, message_id: int, *, content):
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        await message.reply(content)
        await ctx.send(f"**Replied:** {content}\n**Which message:** {message.jump_url}")

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def sync(
        self,
        ctx: Context,
        guilds: Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
    ) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def setup(bot):
    await bot.add_cog(Admin(bot))
