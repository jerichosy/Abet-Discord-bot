import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from cogs.AI import AI


class FakeAttachment:
    def __init__(self, filename="recording.mp3", payload=b"audio"):
        self.filename = filename
        self.size = len(payload)
        self.content_type = "audio/mpeg"
        self.payload = payload
        self.saved_path = None

    async def save(self, path):
        self.saved_path = Path(path)
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
