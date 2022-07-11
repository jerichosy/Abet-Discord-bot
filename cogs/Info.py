import discord
from discord.ext import commands
import psutil
import pkg_resources
import time


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()

    @commands.command(aliases=["info", "github", "repo", "repository"])
    async def about(self, ctx):
        """link to documentation & source code on GitHub"""
        # await ctx.send("Source code & documentation: https://github.com/jerichosy/Abet-Discord-bot")

        embed = discord.Embed(
            title="FUCK CARL",
            colour=discord.Colour(0xEE615B),
            url="https://cdn.discordapp.com/attachments/731542246951747594/905830644607758416/abet_bot.png",
            description="Source code & documentation: [GitHub repository](https://github.com/jerichosy/Abet-Discord-bot)",
        )

        embed.set_image(
            url="https://opengraph.githubassets.com/89c81820967bbd8115fc6a68d55ef62a3964c8caf19e47a321f12d969ac3b6e3/jerichosy/Abet-Discord-bot"
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        main_guild = self.bot.get_guild(self.bot.HOME_GUILD.id)
        owner = main_guild.get_member(self.bot.owner_id)
        embed.set_author(name=str(owner), icon_url=owner.display_avatar.url)

        version = pkg_resources.get_distribution("discord.py").version
        embed.set_footer(
            text=f"</> with 💖 by Kyoya Intelligence Agency and Tre' Industries using Python (discord.py v{version})",
            icon_url="https://media.discordapp.net/stickers/946824812658065459.png",
        )

        memory_usage = self.process.memory_full_info().uss / 1024**2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        embed.add_field(
            name="Process", value=f"{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU"
        )

        # embed.add_field(name='Uptime', value=self.get_bot_uptime(brief=True))  # TODO: 2.0 thing

        await ctx.send(embed=embed)

    @commands.command(aliases=["code", "showcode", "sc"])
    async def sourcecode(self, ctx):
        """Have the bot upload it's own sourcecode here in Discord"""
        await ctx.send(file=discord.File("main.py"))

    @commands.hybrid_command()
    # @app_commands.guilds(discord.Object(id=867811644322611200))
    async def ping(self, ctx):
        """Get the bot's current websocket and API latency"""
        start_time = time.time()
        to_edit = await ctx.send("Testing ping...")
        end_time = time.time()
        await to_edit.edit(
            content=f"Pong! {round(self.bot.latency * 1000)}ms | API: {round((end_time - start_time) * 1000)}ms"
        )


async def setup(bot):
    await bot.add_cog(Info(bot))
