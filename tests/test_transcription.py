import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from cogs.utils import transcription


class TranscriptionRoutingTests(unittest.TestCase):
    def test_supported_extension_is_case_insensitive(self):
        self.assertEqual(
            transcription.validate_audio_extension("Recording.WEBM"), ".webm"
        )

    def test_unsupported_extension_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported audio format"):
            transcription.validate_audio_extension("Recording.flac")

    def test_source_language_resolution(self):
        self.assertIsNone(transcription.resolve_source_language("Auto"))
        self.assertEqual(transcription.resolve_source_language("EN"), "en")
        self.assertEqual(transcription.resolve_source_language("Tagalog"), "tl")

    def test_unknown_source_language_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown source language"):
            transcription.resolve_source_language("not-a-language")

    def test_language_mapping_includes_english_and_98_other_languages(self):
        self.assertEqual(len(transcription.WHISPER_LANGUAGES), 99)

    def test_language_autocomplete_searches_names_and_codes(self):
        self.assertIn(("Auto-detect", "auto"), transcription.autocomplete_languages(""))
        self.assertEqual(
            transcription.autocomplete_languages("tagalog")[0], ("Tagalog (tl)", "tl")
        )
        self.assertEqual(
            transcription.autocomplete_languages("tl")[0], ("Tagalog (tl)", "tl")
        )
        self.assertLessEqual(
            len(transcription.autocomplete_languages("", limit=10)), 10
        )

    def test_text_transcription_uses_gpt_transcribe_and_languages(self):
        route = transcription.build_transcription_route(False, "Text")
        self.assertEqual(route.endpoint, "transcriptions")
        self.assertEqual(route.model, "gpt-transcribe")
        self.assertEqual(route.output_filename_suffix, "_transcript.txt")
        self.assertEqual(
            transcription.build_openai_options(route, "en"),
            {"model": "gpt-transcribe", "response_format": "json", "languages": ["en"]},
        )

    def test_srt_transcription_uses_whisper_and_language(self):
        route = transcription.build_transcription_route(False, "SRT")
        self.assertEqual(route.endpoint, "transcriptions")
        self.assertEqual(route.model, "whisper-1")
        self.assertEqual(route.output_filename_suffix, "_transcript.srt")
        self.assertEqual(
            transcription.build_openai_options(route, "tl"),
            {"model": "whisper-1", "response_format": "srt", "language": "tl"},
        )

    def test_text_translation_uses_whisper_and_ignores_language(self):
        route = transcription.build_transcription_route(True, "Text")
        self.assertEqual(route.endpoint, "translations")
        self.assertEqual(route.output_filename_suffix, "_translation.txt")
        self.assertEqual(
            transcription.build_openai_options(route, "de"),
            {"model": "whisper-1", "response_format": "json"},
        )

    def test_srt_translation_uses_whisper(self):
        route = transcription.build_transcription_route(True, "SRT")
        self.assertEqual(route.endpoint, "translations")
        self.assertEqual(route.model, "whisper-1")
        self.assertEqual(route.response_format, "srt")
        self.assertEqual(route.output_filename_suffix, "_translation.srt")

    def test_response_extraction_supports_objects_and_raw_formats(self):
        self.assertEqual(
            transcription.extract_transcription_content("subtitle"), "subtitle"
        )
        self.assertEqual(
            transcription.extract_transcription_content(b"subtitle"), "subtitle"
        )
        self.assertEqual(
            transcription.extract_transcription_content(
                SimpleNamespace(text="transcript")
            ),
            "transcript",
        )
        with self.assertRaises(TypeError):
            transcription.extract_transcription_content(object())


class CompressionTests(unittest.IsolatedAsyncioTestCase):
    def test_bitrate_selection_uses_highest_rate_that_fits(self):
        self.assertEqual(transcription.select_opus_bitrate(4000), 48)
        self.assertEqual(transcription.select_opus_bitrate(4001), 40)
        self.assertEqual(transcription.select_opus_bitrate(4801), 32)
        self.assertEqual(transcription.select_opus_bitrate(6001), 24)
        self.assertIsNone(transcription.select_opus_bitrate(8001))

    def test_fallback_bitrate_uses_measured_container_overhead(self):
        self.assertEqual(
            transcription.select_fallback_opus_bitrate(4000, 48, 25_100_000),
            40,
        )
        self.assertIsNone(
            transcription.select_fallback_opus_bitrate(8000, 24, 25_100_000)
        )

    async def test_small_file_bypasses_media_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.mp3"
            destination = Path(directory) / "compressed.webm"
            source.write_bytes(b"audio")

            with patch.object(
                transcription, "probe_audio_duration", new=AsyncMock()
            ) as probe:
                upload, bitrate = await transcription.prepare_audio_for_openai(
                    source, destination
                )

            self.assertEqual(upload, source)
            self.assertIsNone(bitrate)
            probe.assert_not_awaited()

    async def test_large_file_is_compressed_and_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.wav"
            destination = Path(directory) / "compressed.webm"
            source.write_bytes(b"x" * 11)

            async def create_compressed_file(*args):
                destination.write_bytes(b"x" * 9)

            with (
                patch.object(transcription, "OPENAI_AUDIO_FILE_LIMIT_BYTES", 10),
                patch.object(
                    transcription,
                    "probe_audio_duration",
                    new=AsyncMock(return_value=60),
                ),
                patch.object(
                    transcription,
                    "compress_audio_for_openai",
                    new=AsyncMock(side_effect=create_compressed_file),
                ) as compress,
            ):
                upload, bitrate = await transcription.prepare_audio_for_openai(
                    source, destination
                )

            self.assertEqual(upload, destination)
            self.assertEqual(bitrate, 48)
            compress.assert_awaited_once_with(source, destination, 48)

    async def test_oversized_encode_retries_at_projected_safe_bitrate(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.wav"
            destination = Path(directory) / "compressed.webm"
            source.write_bytes(b"x" * 101)

            async def create_compressed_file(source, destination, bitrate):
                output_sizes = {48: 101, 40: 86}
                destination.write_bytes(b"x" * output_sizes[bitrate])

            with (
                patch.object(transcription, "OPENAI_AUDIO_FILE_LIMIT_BYTES", 100),
                patch.object(transcription, "COMPRESSION_TARGET_BYTES", 90),
                patch.object(
                    transcription,
                    "probe_audio_duration",
                    new=AsyncMock(return_value=0.015),
                ),
                patch.object(
                    transcription,
                    "compress_audio_for_openai",
                    new=AsyncMock(side_effect=create_compressed_file),
                ) as compress,
            ):
                upload, bitrate = await transcription.prepare_audio_for_openai(
                    source, destination
                )

            self.assertEqual(upload, destination)
            self.assertEqual(bitrate, 40)
            self.assertEqual(
                [call.args[2] for call in compress.await_args_list], [48, 40]
            )

    async def test_failed_fallback_is_rejected_without_a_third_encode(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.wav"
            destination = Path(directory) / "compressed.webm"
            source.write_bytes(b"x" * 101)

            async def create_oversized_file(*args):
                destination.write_bytes(b"x" * 101)

            with (
                patch.object(transcription, "OPENAI_AUDIO_FILE_LIMIT_BYTES", 100),
                patch.object(transcription, "COMPRESSION_TARGET_BYTES", 90),
                patch.object(
                    transcription,
                    "probe_audio_duration",
                    new=AsyncMock(return_value=0.015),
                ),
                patch.object(
                    transcription,
                    "compress_audio_for_openai",
                    new=AsyncMock(side_effect=create_oversized_file),
                ) as compress,
            ):
                with self.assertRaises(transcription.AudioTooLongError):
                    await transcription.prepare_audio_for_openai(source, destination)

            self.assertEqual(
                [call.args[2] for call in compress.await_args_list], [48, 40]
            )

    async def test_oversized_minimum_bitrate_is_not_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.wav"
            destination = Path(directory) / "compressed.webm"
            source.write_bytes(b"x" * 101)

            async def create_oversized_file(*args):
                destination.write_bytes(b"x" * 101)

            with (
                patch.object(transcription, "OPENAI_AUDIO_FILE_LIMIT_BYTES", 100),
                patch.object(transcription, "COMPRESSION_TARGET_BYTES", 90),
                patch.object(
                    transcription,
                    "probe_audio_duration",
                    new=AsyncMock(return_value=0.03),
                ),
                patch.object(
                    transcription,
                    "compress_audio_for_openai",
                    new=AsyncMock(side_effect=create_oversized_file),
                ) as compress,
            ):
                with self.assertRaises(transcription.AudioTooLongError):
                    await transcription.prepare_audio_for_openai(source, destination)

            compress.assert_awaited_once_with(source, destination, 24)

    async def test_too_long_file_is_rejected_before_compression(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.wav"
            destination = Path(directory) / "compressed.webm"
            source.write_bytes(b"x" * 11)

            with (
                patch.object(transcription, "OPENAI_AUDIO_FILE_LIMIT_BYTES", 10),
                patch.object(
                    transcription,
                    "probe_audio_duration",
                    new=AsyncMock(return_value=9000),
                ),
                patch.object(
                    transcription,
                    "compress_audio_for_openai",
                    new=AsyncMock(),
                ) as compress,
            ):
                with self.assertRaises(transcription.AudioTooLongError):
                    await transcription.prepare_audio_for_openai(source, destination)

            compress.assert_not_awaited()

    async def test_ffprobe_prefers_first_audio_stream_duration(self):
        command = AsyncMock(
            return_value='{"streams": [{"duration": "1.5"}], "format": {"duration": "10"}}'
        )
        with patch.object(transcription, "_run_media_command", new=command):
            duration = await transcription.probe_audio_duration(Path("recording.mp4"))

        self.assertEqual(duration, 1.5)
        args = command.await_args.args
        self.assertEqual(args[args.index("-select_streams") + 1], "a:0")
        self.assertEqual(
            args[args.index("-show_entries") + 1],
            "stream=duration:format=duration",
        )
        self.assertEqual(args[args.index("-of") + 1], "json")

    async def test_ffprobe_falls_back_to_container_duration(self):
        output = '{"streams": [{}], "format": {"duration": "10"}}'
        with patch.object(
            transcription, "_run_media_command", new=AsyncMock(return_value=output)
        ):
            duration = await transcription.probe_audio_duration(Path("recording.mp4"))

        self.assertEqual(duration, 10)

    async def test_ffprobe_invalid_json_is_reported(self):
        with patch.object(
            transcription, "_run_media_command", new=AsyncMock(return_value="invalid")
        ):
            with self.assertRaises(transcription.MediaProcessingError):
                await transcription.probe_audio_duration(Path("recording.wav"))

    async def test_ffprobe_unusable_durations_are_reported(self):
        output = '{"streams": [{"duration": "nan"}], "format": {"duration": "0"}}'
        with patch.object(
            transcription, "_run_media_command", new=AsyncMock(return_value=output)
        ):
            with self.assertRaises(transcription.MediaProcessingError):
                await transcription.probe_audio_duration(Path("recording.wav"))

    async def test_ffmpeg_receives_speech_optimized_settings(self):
        command = AsyncMock()
        with patch.object(transcription, "_run_media_command", new=command):
            await transcription.compress_audio_for_openai(
                Path("source.mp4"), Path("compressed.webm"), 32
            )

        args = command.await_args.args
        self.assertEqual(args[args.index("-map") + 1], "0:a:0")
        self.assertIn("-vn", args)
        self.assertIn("16000", args)
        self.assertIn("libopus", args)
        self.assertEqual(args[args.index("-vbr") + 1], "off")
        self.assertIn("32k", args)

    async def test_media_command_failure_is_reported(self):
        process = SimpleNamespace(
            returncode=1,
            communicate=AsyncMock(return_value=(b"", b"invalid media")),
        )
        with patch.object(
            transcription.asyncio,
            "create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ):
            with self.assertRaisesRegex(
                transcription.MediaProcessingError, "invalid media"
            ):
                await transcription._run_media_command("ffmpeg", "-i", "bad.wav")


if __name__ == "__main__":
    unittest.main()
