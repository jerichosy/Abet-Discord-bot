import subprocess
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands, listening

process_pool = listening.AudioProcessPool(1)

FILE_FORMATS = {"mp3": listening.MP3AudioFile, "wav": listening.WaveAudioFile}


class VoiceListen(commands.GroupCog, name="voicelisten"):
    def __init__(self, bot):
        self.bot = bot

    async def is_in_guild(self, interaction: discord.Interaction):
        # If this interaction was invoked outside a guild
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used within a server."
            )
            return False
        return True

    async def get_vc(
        self, interaction: discord.Interaction
    ) -> Optional[listening.VoiceClient]:
        # If the bot is currently in a vc
        if interaction.guild.voice_client is not None:
            # If the bot is in a vc other than the one of the user invoking the command
            if interaction.guild.voice_client.channel != interaction.user.voice.channel:
                # Move to the vc of the user invoking the command.
                await interaction.guild.voice_client.move_to(
                    interaction.user.voice.channel
                )
            return interaction.guild.voice_client
        # If the user invoking the command is in a vc, connect to it
        if interaction.user.voice is not None:
            return await interaction.user.voice.channel.connect(
                cls=listening.VoiceClient
            )

    async def change_deafen_state(self, vc: discord.VoiceClient, deafen: bool) -> None:
        state = vc.guild.me.voice
        await vc.guild.change_voice_state(
            channel=vc.channel, self_mute=state.self_mute, self_deaf=deafen
        )

    async def send_audio_file(
        self, channel: discord.TextChannel, file: listening.AudioFile
    ):
        # Get the user id of this audio file's user if possible
        # If it's not None, then it's either a `Member` or `Object` object, both of which have an `id` attribute.
        user = file.user if file.user is None else file.user.id

        # Send the file and if the file is too big (ValueError is raised) then send a message
        # saying the audio file was too big to send.
        try:
            await channel.send(
                (
                    f"Audio file for <@{user}>"
                    if user is not None
                    else "Could not resolve this file to a user..."
                ),
                file=discord.File(file.path),
            )
        except ValueError:
            await channel.send(
                f"Audio file for <@{user}> is too big to send"
                if user is not None
                else "Audio file for unknown user is too big to send"
            )

    # The key word arguments passed in the listen function MUST have the same name.
    # You could alternatively do on_listen_finish(sink, exc, channel, ...) because exc is always passed
    # regardless of if it's None or not.
    async def on_listen_finish(
        self, sink: listening.AudioFileSink, exc=None, channel=None
    ):
        # Convert the raw recorded audio to its chosen file type
        # kwargs can be specified to convert_files, which will be specified to each AudioFile.convert call
        # here, the stdout and stderr kwargs go to asyncio.create_subprocess_exec for ffmpeg
        await sink.convert_files(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if channel is not None:
            for file in sink.output_files.values():
                await self.send_audio_file(channel, file)

        # Raise any exceptions that may have occurred
        if exc is not None:
            raise exc

    @app_commands.command(description="Join the vc you're in and begin recording.")
    @app_commands.describe(
        file_format=f"The file format to write the audio data to. Valid types: {', '.join(FILE_FORMATS.keys())}"
    )
    async def start(
        self,
        interaction: discord.Interaction,
        file_format: Literal["mp3", "wav"] = "mp3",
    ):
        if not await self.is_in_guild(interaction):
            return
        # Check that a valid file format was provided.
        file_format = file_format.lower()
        if file_format not in FILE_FORMATS:
            return await interaction.response.send_message(
                "That's not a valid file format. "
                f"Valid file formats: {', '.join(FILE_FORMATS.keys())}"
            )
        vc = await self.get_vc(interaction)
        # Make sure the person invoking the command is in a vc.
        if vc is None:
            return await interaction.response.send_message(
                "You're not currently in a vc."
            )
        # Make sure we're not already recording.
        if vc.is_listen_receiving():
            return await interaction.response.send_message("Already recording.")
        # Good practice to check this before calling listen, especially if it were being called within a loop.
        if vc.is_listen_cleaning():
            return await interaction.response.send_message(
                "Currently busy cleaning... try again in a second."
            )
        # Start listening for audio and pass it to one of the AudioFileSink objects which will
        # record the audio to file for us. We're also passing the on_listen_finish function
        # which will be called when listening has finished.
        vc.listen(
            listening.AudioFileSink(FILE_FORMATS[file_format], "audio-output"),
            process_pool,
            after=self.on_listen_finish,
            channel=interaction.channel,
        )
        await interaction.response.send_message("Started recording.")

    @app_commands.command(description="Stop the current recording.")
    async def stop(self, interaction: discord.Interaction):
        if not await self.is_in_guild(interaction):
            return
        # Make sure we're currently in vc and recording.
        if (
            interaction.guild.voice_client is None
            or not (await self.get_vc(interaction)).is_listen_receiving()
        ):
            return await interaction.response.send_message("Not currently recording.")
        vc = interaction.guild.voice_client
        # Stop listening and disconnect from vc. The after function passed to vc.listen in the start command
        # will be called after listening stops.
        vc.stop_listening()
        await interaction.response.send_message(
            "Recording stopped. Sending audio recordings after processing has finished..."
        )
        await vc.disconnect()

    @app_commands.command(description="Pause the current recording.")
    async def pause(self, interaction: discord.Interaction):
        if not await self.is_in_guild(interaction):
            return
        # Make sure we're currently in vc and recording.
        if (
            interaction.guild.voice_client is None
            or not (await self.get_vc(interaction)).is_listen_receiving()
        ):
            return await interaction.response.send_message("Not currently recording.")
        vc = interaction.guild.voice_client
        # Make sure we're not already paused
        if vc.is_listening_paused():
            return await interaction.response.send_message(
                "Recording is already paused."
            )
        # Pause the recording and then change deafen state to indicate so. Note the
        # deafen state does not actually prevent the bot from receiving audio.
        vc.pause_listening()
        await self.change_deafen_state(vc, True)
        await interaction.response.send_message("Recording paused.")

    @app_commands.command(description="Resume the current recording.")
    async def resume(self, interaction: discord.Interaction):
        if not await self.is_in_guild(interaction):
            return
        # Make sure we're currently in vc and recording.
        if (
            interaction.guild.voice_client is None
            or not (await self.get_vc(interaction)).is_listen_receiving()
        ):
            return await interaction.response.send_message("Not currently recording.")
        vc = interaction.guild.voice_client
        # Make sure we're paused
        if not vc.is_listening_paused():
            return await interaction.response.send_message(
                "Recording is already resumed."
            )
        # Resume the recording and then change the deafen state to indicate so.
        vc.resume_listening()
        await self.change_deafen_state(vc, False)
        await interaction.response.send_message("Recording resumed.")


async def setup(bot):
    try:
        await bot.add_cog(VoiceListen(bot))
    finally:
        process_pool.cleanup_processes()
