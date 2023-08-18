from enum import Enum


# Given values are inclusive
class EmbedLimit(Enum):
    # https://www.pythondiscord.com/pages/guides/python-guides/discord-embed-limits/
    TITLE = 256
    DESCRIPTION = 4096


def truncate(text: str, limit: Enum, ellipsis: str = "...") -> str:
    # If at or below the limit, this will not do truncation (and add trailing). It will just return the same text it was given.
    return (
        text[: limit.value - len(ellipsis)] + ellipsis
        if len(text) > limit.value
        else text
    )
