from io import BytesIO
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context, Greedy, has_permissions


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.supress_embeds_menu = app_commands.ContextMenu(
            name="Suppress Embeds", callback=self.suppress_embeds_from_msg
        )
        self.invoke_on_msg_menu = app_commands.ContextMenu(
            name="Invoke on_message()", callback=self.invoke_on_msg
        )
        self.bot.tree.add_command(self.supress_embeds_menu)
        self.bot.tree.add_command(self.invoke_on_msg_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.supress_embeds_menu.name, type=self.supress_embeds_menu.type
        )
        self.bot.tree.remove_command(
            self.invoke_on_msg_menu.name, type=self.invoke_on_msg_menu.type
        )

    @app_commands.checks.has_permissions(manage_messages=True)
    async def suppress_embeds_from_msg(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        if not message.embeds:
            emby = discord.Embed(
                description=f"🛑 There are no embeds in that [message]({message.jump_url})"
            )
            return await interaction.response.send_message(embed=emby)

        await message.edit(suppress=True)
        emby = discord.Embed(
            description=f"Embeds from [message]({message.jump_url}) removed"
        )
        await interaction.response.send_message(embed=emby)

    @app_commands.checks.has_permissions(manage_messages=True)
    async def invoke_on_msg(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        # First respond because awaiting on_message might exceed timeout
        emby = discord.Embed(
            description=f"✅ `on_message()` called for [message]({message.jump_url})"
        )
        await interaction.response.send_message(embed=emby, ephemeral=True)
        # Then actually process the msg
        await self.bot.on_message(message)

    # ? Will this end up deleting any msg sent during cleanup?
    @commands.command(aliases=["delete", "cleanup"])
    @has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: commands.Range[int, 1, 35]):
        await ctx.channel.purge(limit=amount + 1)

    @commands.command(aliases=["close", "shutup", "logoff", "stop"])
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send("🛑 Shutting down!")
        await self.bot.close()

    # TODO: Store current status to db or file so it persists upon restart
    @app_commands.command()
    @app_commands.guilds(887980840347398144)
    async def changestatus(
        self,
        interaction: discord.Interaction,
        activity: Literal["Playing", "Listening to", "Watching"],
        status_msg: str,
    ):
        """Change the status/activity of the bot"""
        # https://discordpy.readthedocs.io/en/master/api.html#discord.ActivityType

        if activity == "Playing":
            await self.bot.change_presence(activity=discord.Game(name=status_msg))
        else:
            if activity == "Listening to":
                type = discord.ActivityType.listening
            elif activity == "Watching":
                type = discord.ActivityType.watching

            await self.bot.change_presence(
                activity=discord.Activity(name=status_msg, type=type)
            )

        await interaction.response.send_message(
            f'✅ My status is now "{activity} **{status_msg}**"'
        )

    @commands.command()
    async def sendmsg(self, ctx, channel_id: int, *, content):
        # print(content)
        channel = self.bot.get_channel(channel_id)
        sent = await channel.send(content)
        await ctx.send(f"**Sent:** {content}\n**Where:** <{sent.jump_url}>")

    @commands.command()
    async def sendreply(self, ctx, channel_id: int, message_id: int, *, content):
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        sent = await message.reply(content)
        await ctx.send(f"**Replied:** {content}\n**Where:** <{sent.jump_url}>")

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def sync(
        self,
        ctx: Context,
        guilds: Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
    ) -> None:
        # `Greedy` -> `commands.Greedy`
        # `Context` -> `commands.Context` (or your subclass)
        # `Object` -> `discord.Object`
        # `typing.Optional` and `typing.Literal`

        """Works like:*
        `&sync` -> global sync
        `&sync ~` -> sync current guild
        `&sync *` -> copies all global app commands to current guild and syncs
        `&sync ^` -> clears all commands from the current guild target and syncs (removes guild commands)
        `&sync id_1 id_2` -> syncs guilds with id 1 and 2
        """

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

            appcmds = "\n".join(sorted([f"- {appcmd.name}" for appcmd in synced]))
            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}\n{appcmds}"
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

    @commands.command()
    @commands.is_owner()
    async def reset_bot_nicknames(self, ctx):
        success = []
        fail = []

        async with ctx.typing():
            for member in ctx.guild.members:
                if member.bot:
                    print(member.name)
                    try:
                        await member.edit(nick=None)
                        success.append(member.mention)
                    except discord.Forbidden:
                        fail.append(member.mention)

            NEWLINE = "\n"  # Workaround for limitation that f-string expressions part cannot contain backslashes
            await ctx.send(
                f"Successfully reset the nicknames of the following bots:\n{NEWLINE.join(success)}\n\nI don't have permission to reset the nicknames of the following bots:\n{NEWLINE.join(fail)}"
            )

    @commands.command(aliases=["count_role", "role_count"])
    @commands.is_owner()
    async def count_roles(self, ctx, *roles: discord.Role):
        if not roles:
            # If no roles are provided, count all roles in the guild
            roles = ctx.guild.roles

        role_list = "\n".join([f"{role.name}: {len(role.members)}" for role in roles])

        # Send the role list
        await ctx.send(
            f"**__Here are the member counts for each role:__**\n{role_list}"
        )

    @commands.command(aliases=["error", "send_error"])
    @commands.is_owner()
    async def test_error(self, ctx):
        raise Exception("This is a test\nThis is another line")

    @commands.command(aliases=["string", "send_string", "test_string"])
    @commands.is_owner()
    async def test_string_as_file(self, ctx):
        # Replace this with your own string
        content = "your-string" * 5000

        # Create a discord.File instance using the string
        file = discord.File(BytesIO(content.encode()), "string.txt")

        # Send the file as a message
        await ctx.send(file=file)


async def setup(bot):
    await bot.add_cog(Admin(bot))
