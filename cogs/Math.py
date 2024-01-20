import math

import discord
from discord import app_commands
from discord.ext import commands


class Math(commands.GroupCog, name="math"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(
        display_size="The diagonal measurement of your display in inches"
    )
    @app_commands.describe(
        resolution_width="Number of pixels across the width of your display (native)"
    )
    @app_commands.describe(
        resolution_height="Number of pixels across the height of your display (native)"
    )
    async def screen_dimensions(
        self,
        interaction: discord.Interaction,
        display_size: app_commands.Range[float, 0.0001, None],
        resolution_width: app_commands.Range[int, 1, None],
        resolution_height: app_commands.Range[int, 1, None],
    ) -> None:
        """Calculates the dimensions of your screen given the diagonal display size and resolution."""

        def calculate_screen_dimensions(
            diagonal_size_inches, resolution_width_px, resolution_height_px
        ):
            # Calculate the physical width and height of the screen
            diagonal_size_px = math.sqrt(
                resolution_width_px**2 + resolution_height_px**2
            )
            pixel_size_inches = diagonal_size_inches / diagonal_size_px

            # Calculate the physical width and height based on pixel size
            width_inches = pixel_size_inches * resolution_width_px
            height_inches = pixel_size_inches * resolution_height_px

            # Convert inches to centimeters
            width_cm = width_inches * 2.54
            height_cm = height_inches * 2.54

            return width_inches, height_inches, width_cm, height_cm

        diagonal_size = display_size  # Screen diagonal size in inches
        resolution = (
            resolution_width,
            resolution_height,
        )  # Screen resolution (width px x height px)

        width_inches, height_inches, width_cm, height_cm = calculate_screen_dimensions(
            diagonal_size, *resolution
        )

        await interaction.response.send_message(
            f"Screen width: {width_inches:.2f} inches ({width_cm:.2f} cm)\nScreen height: {height_inches:.2f} inches ({height_cm:.2f} cm)"
        )


async def setup(bot):
    await bot.add_cog(Math(bot))
