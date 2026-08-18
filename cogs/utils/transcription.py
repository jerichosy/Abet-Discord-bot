import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

OPENAI_AUDIO_FILE_LIMIT_BYTES = 25_000_000
COMPRESSION_TARGET_BYTES = 24_000_000
SUPPORTED_AUDIO_EXTENSIONS = frozenset(
    {".m4a", ".mp3", ".mp4", ".mpeg", ".mpga", ".wav", ".webm"}
)
OPUS_BITRATES_KBPS = (48, 40, 32, 24)

# Language names and codes supported by the hosted Whisper model. The newer
# gpt-transcribe model accepts these codes through its `languages` parameter.
WHISPER_LANGUAGES = {
    "af": "Afrikaans",
    "am": "Amharic",
    "ar": "Arabic",
    "as": "Assamese",
    "az": "Azerbaijani",
    "ba": "Bashkir",
    "be": "Belarusian",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "bo": "Tibetan",
    "br": "Breton",
    "bs": "Bosnian",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "eu": "Basque",
    "fa": "Persian",
    "fi": "Finnish",
    "fo": "Faroese",
    "fr": "French",
    "gl": "Galician",
    "gu": "Gujarati",
    "ha": "Hausa",
    "haw": "Hawaiian",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "ht": "Haitian Creole",
    "hu": "Hungarian",
    "hy": "Armenian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "jw": "Javanese",
    "ka": "Georgian",
    "kk": "Kazakh",
    "km": "Khmer",
    "kn": "Kannada",
    "ko": "Korean",
    "la": "Latin",
    "lb": "Luxembourgish",
    "ln": "Lingala",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mg": "Malagasy",
    "mi": "Maori",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mr": "Marathi",
    "ms": "Malay",
    "mt": "Maltese",
    "my": "Myanmar",
    "ne": "Nepali",
    "nl": "Dutch",
    "nn": "Nynorsk",
    "no": "Norwegian",
    "oc": "Occitan",
    "pa": "Punjabi",
    "pl": "Polish",
    "ps": "Pashto",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sa": "Sanskrit",
    "sd": "Sindhi",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sn": "Shona",
    "so": "Somali",
    "sq": "Albanian",
    "sr": "Serbian",
    "su": "Sundanese",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "tg": "Tajik",
    "th": "Thai",
    "tk": "Turkmen",
    "tl": "Tagalog",
    "tr": "Turkish",
    "tt": "Tatar",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "zh": "Chinese",
}

_AUTOCOMPLETE_PRIORITY = (
    "en",
    "tl",
    "zh",
    "ja",
    "ko",
    "es",
    "fr",
    "de",
    "pt",
    "ru",
    "ar",
    "hi",
)


class MediaProcessingError(RuntimeError):
    pass


class AudioTooLongError(MediaProcessingError):
    pass


@dataclass(frozen=True)
class TranscriptionRoute:
    endpoint: Literal["transcriptions", "translations"]
    model: str
    response_format: Literal["json", "srt"]
    output_filename_suffix: str


def validate_audio_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_AUDIO_EXTENSIONS:
        supported = ", ".join(
            sorted(
                extension.removeprefix(".").upper()
                for extension in SUPPORTED_AUDIO_EXTENSIONS
            )
        )
        raise ValueError(f"Unsupported audio format. Supported formats: {supported}.")
    return extension


def resolve_source_language(value: str) -> str | None:
    normalized = value.strip().casefold()
    if not normalized or normalized in {"auto", "auto-detect", "autodetect"}:
        return None

    if normalized in WHISPER_LANGUAGES:
        return normalized

    for code, name in WHISPER_LANGUAGES.items():
        if normalized == name.casefold():
            return code

    raise ValueError(
        "Unknown source language. Select Auto or a language from autocomplete."
    )


def autocomplete_languages(query: str, limit: int = 25) -> list[tuple[str, str]]:
    normalized = query.strip().casefold()
    choices: list[tuple[str, str]] = []

    if not normalized or "auto-detect".startswith(normalized):
        choices.append(("Auto-detect", "auto"))

    languages = list(WHISPER_LANGUAGES.items())
    if not normalized:
        priority = {code: index for index, code in enumerate(_AUTOCOMPLETE_PRIORITY)}
        languages.sort(key=lambda item: (priority.get(item[0], len(priority)), item[1]))
    else:
        languages = [
            item
            for item in languages
            if normalized in item[0].casefold() or normalized in item[1].casefold()
        ]
        languages.sort(
            key=lambda item: (not item[1].casefold().startswith(normalized), item[1])
        )

    choices.extend((f"{name} ({code})", code) for code, name in languages)
    return choices[:limit]


def build_transcription_route(translate: bool, output: str) -> TranscriptionRoute:
    normalized_output = output.strip().casefold()
    if normalized_output not in {"text", "srt"}:
        raise ValueError("Output must be Text or SRT.")

    response_format: Literal["json", "srt"] = (
        "srt" if normalized_output == "srt" else "json"
    )
    extension = ".srt" if normalized_output == "srt" else ".txt"

    if translate:
        return TranscriptionRoute(
            "translations", "whisper-1", response_format, f"_translation{extension}"
        )
    if normalized_output == "srt":
        return TranscriptionRoute(
            "transcriptions", "whisper-1", response_format, f"_transcript{extension}"
        )
    return TranscriptionRoute(
        "transcriptions", "gpt-transcribe", response_format, f"_transcript{extension}"
    )


def build_openai_options(
    route: TranscriptionRoute, source_language: str | None
) -> dict[str, object]:
    options: dict[str, object] = {
        "model": route.model,
        "response_format": route.response_format,
    }
    if route.endpoint == "translations" or source_language is None:
        return options
    if route.model == "gpt-transcribe":
        options["languages"] = [source_language]
    else:
        options["language"] = source_language
    return options


def extract_transcription_content(response: object) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, bytes):
        return response.decode("utf-8")

    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text
    raise TypeError("OpenAI returned an unsupported transcription response.")


def select_opus_bitrate(duration_seconds: float) -> int | None:
    if duration_seconds <= 0:
        raise ValueError("Audio duration must be greater than zero.")

    for bitrate_kbps in OPUS_BITRATES_KBPS:
        estimated_bytes = duration_seconds * bitrate_kbps * 1000 / 8
        if estimated_bytes <= COMPRESSION_TARGET_BYTES:
            return bitrate_kbps
    return None


async def _run_media_command(*args: str) -> str:
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as error:
        raise MediaProcessingError(f"Unable to start {args[0]}.") from error

    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        details = stderr.decode("utf-8", errors="replace").strip()
        raise MediaProcessingError(f"{args[0]} failed: {details[-1000:]}")
    return stdout.decode("utf-8", errors="replace").strip()


async def probe_audio_duration(path: Path) -> float:
    output = await _run_media_command(
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    )
    try:
        duration = float(output)
    except ValueError as error:
        raise MediaProcessingError(
            "FFprobe returned an invalid audio duration."
        ) from error
    if duration <= 0:
        raise MediaProcessingError("The recording has no measurable duration.")
    return duration


async def compress_audio_for_openai(
    source: Path, destination: Path, bitrate_kbps: int
) -> None:
    await _run_media_command(
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "libopus",
        "-b:a",
        f"{bitrate_kbps}k",
        str(destination),
    )


async def prepare_audio_for_openai(
    source: Path, destination: Path
) -> tuple[Path, int | None]:
    if source.stat().st_size <= OPENAI_AUDIO_FILE_LIMIT_BYTES:
        return source, None

    duration = await probe_audio_duration(source)
    bitrate_kbps = select_opus_bitrate(duration)
    if bitrate_kbps is None:
        raise AudioTooLongError(
            "This recording is too long to compress below OpenAI's 25 MB limit at the minimum speech bitrate. "
            "Automatic chunking is not enabled."
        )

    await compress_audio_for_openai(source, destination, bitrate_kbps)
    if (
        not destination.exists()
        or destination.stat().st_size > OPENAI_AUDIO_FILE_LIMIT_BYTES
    ):
        raise AudioTooLongError(
            "The compressed recording is still over OpenAI's 25 MB limit. Automatic chunking is not enabled."
        )
    return destination, bitrate_kbps
