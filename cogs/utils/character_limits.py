from enum import Enum

# Given values are inclusive
# Some other limits:
# - 32 characters for user's display name (nickname)


class EmbedLimit(Enum):
    # https://www.pythondiscord.com/pages/guides/python-guides/discord-embed-limits/
    # https://discord.com/developers/docs/resources/channel#embed-object-embed-limits
    TITLE = 256
    DESCRIPTION = 4096
    FIELD_NAME = 256
    FIELD_VALUE = 1024


class MessageLimit(Enum):
    CONTENT = 2000


def truncate(text: str, limit: int, ellipsis: str = "...") -> str:
    # If at or below the limit, this will not do truncation (and add trailing). It will just return the same text it was given.
    return text[: limit - len(ellipsis)] + ellipsis if len(text) > limit else text
