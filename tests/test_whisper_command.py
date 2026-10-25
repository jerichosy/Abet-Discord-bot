import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord

from cogs.AI import AI, AttachmentDownloadError, save_attachment_with_retry


class FakeAttachment:
    def __init__(self, filename="recording.mp3", payload=b"audio"):
        self.filename = filename
        self.size = len(payload)
        self.content_type = "audio/mpeg"
        self.payload = payload
        self.saved_path = None
        self.failures = []
        self.save_calls = 0

    async def save(self, path):
        self.save_calls += 1
        self.saved_path = Path(path)
        if self.failures:
            self.saved_path.write_bytes(b"partial")
            raise self.failures.pop(0)
        self.saved_path.write_bytes(self.payload)


class FakeFollowup:
    def __init__(self):
        self.messages = []
        self.failure = None

    async def send(self, content=None, file=None):
        if self.failure is not None:
            raise self.failure

        message = {"content": content, "filename": None, "file_content": None}
        if file is not None:
            file.fp.seek(0)
            message["filename"] = file.filename
            message["file_content"] = file.fp.read().decode("utf-8")
        self.messages.append(message)


def make_http_error(status):
    response = SimpleNamespace(status=status, reason="attachment failure")
    return discord.HTTPException(response, "attachment failure")


def make_interaction():
    return SimpleNamespace(
        response=SimpleNamespace(defer=AsyncMock(), send_message=AsyncMock()),
        followup=FakeFollowup(),
    )


def make_cog(transcription_response=None, translation_response=None):
    cog = AI(SimpleNamespace(), SimpleNamespace())
    transcriptions = SimpleNamespace(
        create=AsyncMock(return_value=transcription_response)
    )
    translations = SimpleNamespace(create=AsyncMock(return_value=translation_response))
    cog._client_openai_direct = SimpleNamespace(
        audio=SimpleNamespace(transcriptions=transcriptions, translations=translations)
    )
    return cog, transcriptions.create, translations.create


class WhisperCommandTests(unittest.IsolatedAsyncioTestCase):
    async def invoke(
        self,
        cog,
        interaction,
        attachment,
        output="Text",
        language="auto",
        translate="No",
    ):
        await AI.whisper.callback(
            cog,
            interaction,
            attachment,
            output,
            language,
            translate,
        )

    async def test_transient_attachment_failure_is_retried_once(self):
        for status in (429, 503):
            with self.subTest(status=status):
                attachment = SimpleNamespace(
                    save=AsyncMock(side_effect=[make_http_error(status), None])
                )
                sleep = AsyncMock()

                with patch("cogs.AI.asyncio.sleep", new=sleep):
                    await save_attachment_with_retry(
                        attachment, Path("unused-recording.mp3")
                    )

                self.assertEqual(attachment.save.await_count, 2)
                sleep.assert_awaited_once_with(1)

    async def test_permanent_attachment_failure_is_not_retried(self):
        for status in (400, 403, 404):
            with self.subTest(status=status):
                attachment = SimpleNamespace(
                    save=AsyncMock(side_effect=make_http_error(status))
                )
                sleep = AsyncMock()

                with (
                    patch("cogs.AI.asyncio.sleep", new=sleep),
                    self.assertRaises(AttachmentDownloadError),
                ):
                    await save_attachment_with_retry(
                        attachment, Path("unused-recording.mp3")
                    )

                attachment.save.assert_awaited_once()
                sleep.assert_not_awaited()

    async def test_all_routes_create_expected_files_and_api_options(self):
        cases = (
            {
                "output": "Text",
                "language": "en",
                "translate": "No",
                "response": SimpleNamespace(text="plain transcript"),
                "endpoint": "transcriptions",
                "filename": "recording_transcript.txt",
                "model": "gpt-transcribe",
                "format": "json",
                "language_option": ("languages", ["en"]),
            },
            {
                "output": "SRT",
                "language": "tl",
                "translate": "No",
                "response": "1\n00:00:00,000 --> 00:00:01,000\nKumusta\n",
                "endpoint": "transcriptions",
                "filename": "recording_transcript.srt",
                "model": "whisper-1",
                "format": "srt",
                "language_option": ("language", "tl"),
            },
            {
                "output": "Text",
                "language": "auto",
                "translate": "Yes",
                "response": SimpleNamespace(text="English translation"),
                "endpoint": "translations",
                "filename": "recording_translation.txt",
                "model": "whisper-1",
                "format": "json",
                "language_option": None,
            },
            {
                "output": "SRT",
                "language": "de",
                "translate": "Yes",
                "response": "1\n00:00:00,000 --> 00:00:01,000\nHello\n",
                "endpoint": "translations",
                "filename": "recording_translation.srt",
                "model": "whisper-1",
                "format": "srt",
                "language_option": None,
            },
        )

        for case in cases:
            with self.subTest(output=case["output"], translate=case["translate"]):
                transcription_response = (
                    case["response"] if case["endpoint"] == "transcriptions" else None
                )
                translation_response = (
                    case["response"] if case["endpoint"] == "translations" else None
                )
                cog, transcribe, translate = make_cog(
                    transcription_response, translation_response
                )
                interaction = make_interaction()
                attachment = FakeAttachment()

                await self.invoke(
                    cog,
                    interaction,
                    attachment,
                    case["output"],
                    case["language"],
                    case["translate"],
                )

                selected_call = (
                    transcribe if case["endpoint"] == "transcriptions" else translate
                )
                unused_call = (
                    translate if case["endpoint"] == "transcriptions" else transcribe
                )
                selected_call.assert_awaited_once()
                unused_call.assert_not_awaited()
                options = selected_call.await_args.kwargs
                self.assertEqual(options["model"], case["model"])
                self.assertEqual(options["response_format"], case["format"])
                if case["language_option"] is None:
                    self.assertNotIn("language", options)
                    self.assertNotIn("languages", options)
                else:
                    key, value = case["language_option"]
                    self.assertEqual(options[key], value)

                self.assertEqual(
                    interaction.followup.messages[0]["filename"], case["filename"]
                )
                self.assertFalse(attachment.saved_path.exists())

    async def test_translation_language_hint_is_ignored_with_notice(self):
        cog, _, _ = make_cog(translation_response=SimpleNamespace(text="Hello"))
        interaction = make_interaction()

        await self.invoke(
            cog, interaction, FakeAttachment(), language="de", translate="Yes"
        )

        self.assertIn(
            "selected language hint was not used",
            interaction.followup.messages[0]["content"],
        )

    async def test_invalid_extension_fails_before_defer_or_save(self):
        cog, transcribe, translate = make_cog()
        interaction = make_interaction()
        attachment = FakeAttachment(filename="recording.flac")

        await self.invoke(cog, interaction, attachment)

        interaction.response.send_message.assert_awaited_once()
        interaction.response.defer.assert_not_awaited()
        transcribe.assert_not_awaited()
        translate.assert_not_awaited()
        self.assertIsNone(attachment.saved_path)

    async def test_final_compression_bitrate_is_reported(self):
        cog, _, _ = make_cog(
            transcription_response=SimpleNamespace(text="Transcript")
        )
        interaction = make_interaction()

        async def use_compressed_file(source, destination):
            return source, 32

        with patch(
            "cogs.AI.prepare_audio_for_openai",
            new=AsyncMock(side_effect=use_compressed_file),
        ):
            await self.invoke(cog, interaction, FakeAttachment())

        self.assertIn(
            "compressed to 32 kbps", interaction.followup.messages[0]["content"]
        )

    async def test_attachment_failure_is_reported_and_temp_file_is_removed(self):
        cog, transcribe, _ = make_cog()
        interaction = make_interaction()
        attachment = FakeAttachment()
        attachment.failures = [make_http_error(503), make_http_error(503)]

        with patch("cogs.AI.asyncio.sleep", new=AsyncMock()):
            await self.invoke(cog, interaction, attachment)

        self.assertEqual(attachment.save_calls, 2)
        self.assertIn(
            "couldn't download that attachment",
            interaction.followup.messages[0]["content"],
        )
        transcribe.assert_not_awaited()
        self.assertFalse(attachment.saved_path.exists())

    async def test_openai_error_is_reported_and_temp_file_is_removed(self):
        class FakeAPIError(Exception):
            pass

        cog, transcribe, _ = make_cog()
        transcribe.side_effect = FakeAPIError("API unavailable")
        interaction = make_interaction()
        attachment = FakeAttachment()

        with patch("cogs.AI.openai.APIError", FakeAPIError):
            await self.invoke(cog, interaction, attachment)

        self.assertIn(
            "OpenAI couldn't process", interaction.followup.messages[0]["content"]
        )
        self.assertFalse(attachment.saved_path.exists())

    async def test_delivery_failure_still_removes_temp_file(self):
        cog, _, _ = make_cog(transcription_response=SimpleNamespace(text="Transcript"))
        interaction = make_interaction()
        interaction.followup.failure = RuntimeError("Discord unavailable")
        attachment = FakeAttachment()

        with self.assertRaisesRegex(RuntimeError, "Discord unavailable"):
            await self.invoke(cog, interaction, attachment)

        self.assertFalse(attachment.saved_path.exists())


if __name__ == "__main__":
    unittest.main()
