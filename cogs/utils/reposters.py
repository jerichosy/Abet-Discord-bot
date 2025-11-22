"""
Reposters for various social media platforms using dependency injection pattern.
Abstracts platform-specific implementation while sharing common yt-dlp processing.
"""

import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import discord
import yarl


class BaseRepostData:
    """Base data structure for repost information."""

    def __init__(self, url: str, match_id: str):
        self.url = url
        self.match_id = match_id
        self.dl_link: Optional[str] = None
        self.file_format: Optional[str] = None
        self.filename: Optional[str] = None
        self.embed_data: Dict[str, Any] = {}


class BaseReposter(ABC):
    """Abstract base class for social media reposters."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.yt_dlp_url = os.getenv("YT_DLP_MICROSERVICE")

    @property
    @abstractmethod
    def url_regex(self) -> str:
        """Regular expression pattern to match platform URLs."""
        pass

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the platform for logging/error messages."""
        pass

    @abstractmethod
    def extract_format_info(self, resp_json: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extract download link and format from yt-dlp response.

        Returns:
            Tuple of (download_link, file_format) or (None, None) if no valid format found
        """
        pass

    @abstractmethod
    def create_embed(self, repost_data: BaseRepostData, resp_json: Dict[str, Any]) -> Optional[discord.Embed]:
        """Create platform-specific Discord embed.

        Returns:
            Discord embed or None if embed should not be created
        """
        pass

    def match_url(self, content: str) -> Optional[BaseRepostData]:
        """Check if content contains a URL that matches this reposter."""
        matches = re.findall(self.url_regex, content)
        if matches:
            # Most regex patterns return tuples, take the first match
            if isinstance(matches[0], tuple):
                url, match_id = matches[0][0], matches[0][1]
            else:
                url, match_id = matches[0], None
            return BaseRepostData(url, match_id)
        return None

    async def process_repost(self, message: discord.Message, repost_data: BaseRepostData) -> bool:
        """Process a repost request.

        Returns:
            True if successfully processed, False otherwise
        """
        async with message.channel.typing():
            try:
                # Get metadata from yt-dlp microservice
                async with self.session.get(f"{self.yt_dlp_url}/extract?url={repost_data.url}") as resp:
                    print(f"{self.platform_name} yt-dlp response: {resp.status}")
                    if resp.status != 200:
                        resp_json = await resp.json()
                        print(f"yt-dlp error: {resp_json.get('detail', 'Unknown error')}")
                        return False

                    resp_json = await resp.json()

                # Extract platform-specific format information
                dl_link, file_format = self.extract_format_info(resp_json)
                if not dl_link:
                    print(f"{self.platform_name}: No valid format found")
                    return False

                repost_data.dl_link = dl_link
                repost_data.file_format = file_format
                repost_data.filename = (
                    f"{repost_data.match_id}.{file_format}" if repost_data.match_id else f"video.{file_format}"
                )

                # Download the video
                video_bytes = await self._download_video(dl_link)
                if not video_bytes:
                    print(f"{self.platform_name}: Failed to download video")
                    return False

                # Create platform-specific embed
                embed = self.create_embed(repost_data, resp_json)

                # Send the repost
                await self._send_repost(message, video_bytes, repost_data.filename, embed)
                return True

            except Exception as e:
                print(f"{self.platform_name} reposter error: {e}")
                return False

    async def _download_video(self, dl_link: str) -> Optional[BytesIO]:
        """Download video from the given URL."""
        try:
            # Handle encoded URLs like Instagram uses
            if isinstance(dl_link, str):
                dl_link = yarl.URL(dl_link, encoded=True)

            async with self.session.get(dl_link) as resp:
                print(f"{self.platform_name} video download: {resp.status}")
                if resp.status == 200:
                    return BytesIO(await resp.read())
                return None
        except Exception as e:
            print(f"{self.platform_name} download error: {e}")
            return None

    async def _send_repost(
        self,
        message: discord.Message,
        video_bytes: BytesIO,
        filename: str,
        embed: Optional[discord.Embed],
    ):
        """Send the repost to Discord."""
        try:
            await message.reply(
                embed=(message.embeds[0] if message.embeds else embed),
                mention_author=False,
                file=discord.File(video_bytes, filename),
            )
            # Suppress original embed
            await message.edit(suppress=True)
        except discord.HTTPException:
            print(f"{self.platform_name} reposter send error: Likely too big")


class InstagramReposter(BaseReposter):
    """Instagram-specific reposter implementation."""

    @property
    def url_regex(self) -> str:
        return r"(?P<url>https?:\/\/(?:www\.)?instagram\.com(?:\/[^\/]+)?\/(?:p|reel)\/(?P<id>[^\/?#&]+))"

    @property
    def platform_name(self) -> str:
        return "Instagram"

    def extract_format_info(self, resp_json: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extract Instagram video format - looks for format with no tbr and has audio."""
        valid_formats = [
            fmt
            for fmt in resp_json["formats"]
            if fmt.get("tbr") is None  # only the format we want has no tbr
            and fmt.get("acodec") != "none"  # technically not needed
        ]
        best_format = valid_formats[0] if valid_formats else None
        if best_format:
            return best_format["url"], best_format["ext"]
        return None, None

    def create_embed(self, repost_data: BaseRepostData, resp_json: Dict[str, Any]) -> Optional[discord.Embed]:
        """Create Instagram-specific embed with metadata."""
        desc = resp_json.get("description")
        timestamp = resp_json.get("timestamp")
        likes = resp_json.get("like_count")
        comments = resp_json.get("comment_count")
        author = resp_json.get("channel")
        author_display_name = resp_json.get("uploader")
        author_url = f"https://www.instagram.com/{author}/" if author else None

        embed = discord.Embed(
            description=f"[{desc if desc else '*Link*'}]({repost_data.url})",
            timestamp=datetime.fromtimestamp(timestamp) if timestamp else None,
            url=repost_data.url,
            color=0xCE0071,
        )

        if author_display_name and author:
            embed.set_author(
                name=f"{author_display_name} (@{author})",
                url=author_url,
            )

        embed.set_footer(
            text="Instagram",
            icon_url="https://cdn.discordapp.com/attachments/998571531934376006/1010817764203712572/68d99ba29cc8.png",
        )

        if likes is not None:
            embed.add_field(name="Likes", value=likes)
        if comments is not None:
            embed.add_field(name="Comments", value=comments)

        return embed


class FacebookReposter(BaseReposter):
    """Facebook-specific reposter implementation."""

    @property
    def url_regex(self) -> str:
        return r"(https?:\/\/(?:[\w-]+\.)?facebook\.com\/reel\/(?P<id>\d+))"

    @property
    def platform_name(self) -> str:
        return "Facebook"

    def extract_format_info(self, resp_json: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extract Facebook video format - uses format index 2."""
        formats = resp_json.get("formats", [])
        if len(formats) > 2:
            format_info = formats[2]
            return format_info["url"], format_info["ext"]
        return None, None

    def create_embed(self, repost_data: BaseRepostData, resp_json: Dict[str, Any]) -> Optional[discord.Embed]:
        """Facebook uses minimal embed - just description if available."""
        desc = resp_json.get("description")
        if desc:
            # Could create a simple embed here, but current implementation sends no embed
            pass
        return None


class RepostManager:
    """Manages multiple reposters using dependency injection."""

    def __init__(self, session: aiohttp.ClientSession):
        self.reposters: List[BaseReposter] = [
            InstagramReposter(session),
            FacebookReposter(session),
        ]

    async def process_message(self, message: discord.Message) -> bool:
        """Process message through all available reposters.

        Returns:
            True if any reposter processed the message, False otherwise
        """
        for reposter in self.reposters:
            repost_data = reposter.match_url(message.content)
            if repost_data:
                print(f"{reposter.platform_name} match:", repost_data.url)
                success = await reposter.process_repost(message, repost_data)
                if success:
                    return True
        return False

    def add_reposter(self, reposter: BaseReposter):
        """Add a new reposter to the manager."""
        self.reposters.append(reposter)
