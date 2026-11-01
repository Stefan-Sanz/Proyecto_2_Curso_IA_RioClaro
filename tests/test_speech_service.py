import io
import sys
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from speech_service import SpeechServiceError, sintetizar_voz, transcribir_audio


def crear_audio_wav(sample_rate: int = 16000) -> tuple[bytes, bytes]:
    datos = b"\x00\x00" * 160
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(sample_rate)
        archivo.writeframes(datos)
    return buffer.getvalue(), datos


class SpeechServiceTests(unittest.TestCase):
    def test_transcribes_wav_from_memory_in_spanish(self):
        audio_wav, datos_audio = crear_audio_wav()
        input_stream = Mock()
        recognizer = Mock()
        recognizer.recognize_once_async.return_value.get.return_value = (
            SimpleNamespace(reason="recognized", text="¿Cuál es el horario?")
        )
        sdk = SimpleNamespace(
            SpeechConfig=Mock(),
            SpeechRecognizer=Mock(return_value=recognizer),
            ResultReason=SimpleNamespace(
                RecognizedSpeech="recognized",
                NoMatch="no_match",
            ),
            audio=SimpleNamespace(
                AudioStreamFormat=Mock(),
                PushAudioInputStream=Mock(return_value=input_stream),
                AudioConfig=Mock(),
            ),
        )

        with patch("speech_service._speech_sdk", return_value=sdk):
            texto = transcribir_audio(audio_wav, "key", "westus")

        self.assertEqual(texto, "¿Cuál es el horario?")
        self.assertEqual(sdk.SpeechConfig.call_args.kwargs["region"], "westus")
        self.assertEqual(input_stream.write.call_args.args[0], datos_audio)
        input_stream.close.assert_called_once()

    def test_rejects_audio_with_an_unsupported_wav_format(self):
        audio_wav, _ = crear_audio_wav(sample_rate=22050)
        with patch("speech_service._speech_sdk") as speech_sdk:
            with self.assertRaisesRegex(SpeechServiceError, "WAV mono PCM"):
                transcribir_audio(audio_wav, "key", "westus")
        speech_sdk.assert_not_called()

    def test_reports_speech_no_match_clearly(self):
        audio_wav, _ = crear_audio_wav()
        recognizer = Mock()
        recognizer.recognize_once_async.return_value.get.return_value = (
            SimpleNamespace(reason="no_match", text="")
        )
        sdk = SimpleNamespace(
            SpeechConfig=Mock(),
            SpeechRecognizer=Mock(return_value=recognizer),
            ResultReason=SimpleNamespace(
                RecognizedSpeech="recognized",
                NoMatch="no_match",
            ),
            audio=SimpleNamespace(
                AudioStreamFormat=Mock(),
                PushAudioInputStream=Mock(),
                AudioConfig=Mock(),
            ),
        )

        with patch("speech_service._speech_sdk", return_value=sdk):
            with self.assertRaisesRegex(SpeechServiceError, "No se reconoció voz"):
                transcribir_audio(audio_wav, "key", "westus")

    def test_synthesizes_speech_to_memory_without_speaker_output(self):
        synthesizer = Mock()
        synthesizer.speak_text_async.return_value.get.return_value = SimpleNamespace(
            reason="completed",
            audio_data=b"wav-audio",
        )
        sdk = SimpleNamespace(
            SpeechConfig=Mock(),
            SpeechSynthesizer=Mock(return_value=synthesizer),
            SpeechSynthesisOutputFormat=SimpleNamespace(
                Riff16Khz16BitMonoPcm="riff"
            ),
            ResultReason=SimpleNamespace(SynthesizingAudioCompleted="completed"),
            audio=SimpleNamespace(),
        )

        with patch("speech_service._speech_sdk", return_value=sdk):
            audio = sintetizar_voz("Respuesta en español", "key", "westus")

        self.assertEqual(audio, b"wav-audio")
        self.assertEqual(
            sdk.SpeechConfig.return_value.speech_synthesis_voice_name,
            "es-MX-DaliaNeural",
        )
        self.assertIsNone(sdk.SpeechSynthesizer.call_args.kwargs["audio_config"])
        synthesizer.speak_text_async.assert_called_once_with("Respuesta en español")

    def test_requires_credentials_and_does_not_call_speech(self):
        with patch("speech_service._speech_sdk") as speech_sdk:
            with self.assertRaisesRegex(SpeechServiceError, "AZURE_SPEECH_KEY"):
                sintetizar_voz("Respuesta", None, None)
        speech_sdk.assert_not_called()


if __name__ == "__main__":
    unittest.main()
