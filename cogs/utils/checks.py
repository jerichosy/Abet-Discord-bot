from discord import Interaction


async def owner_only(interaction: Interaction):
    return await interaction.client.is_owner(interaction.user)
