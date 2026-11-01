from io import BytesIO
import wave


class SpeechServiceError(RuntimeError):
    """Raised when Azure Speech cannot process audio."""


SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2


def _speech_sdk():
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError as error:
        raise SpeechServiceError(
            "El SDK de Azure Speech no está instalado. "
            "Instale las dependencias de requirements.txt."
        ) from error
    return speechsdk


def _validate_credentials(speech_key: str | None, speech_region: str | None) -> None:
    if not speech_key or not speech_region:
        raise SpeechServiceError(
            "La voz no está configurada. Defina AZURE_SPEECH_KEY y "
            "AZURE_SPEECH_REGION o continúe por texto."
        )


def transcribir_audio(
    audio_bytes: bytes,
    speech_key: str | None,
    speech_region: str | None,
) -> str:
    _validate_credentials(speech_key, speech_region)
    if not audio_bytes:
        raise SpeechServiceError("La grabación está vacía. Intente de nuevo.")

    try:
        with wave.open(BytesIO(audio_bytes), "rb") as audio_file:
            channels = audio_file.getnchannels()
            sample_width = audio_file.getsampwidth()
            sample_rate = audio_file.getframerate()
            audio_data = audio_file.readframes(audio_file.getnframes())
    except (EOFError, wave.Error) as error:
        raise SpeechServiceError(
            "El audio no tiene un formato WAV válido. Grabe de nuevo."
        ) from error

    if (
        channels != CHANNELS
        or sample_width != SAMPLE_WIDTH
        or sample_rate != SAMPLE_RATE
        or not audio_data
    ):
        raise SpeechServiceError(
            "El audio debe ser WAV mono PCM de 16 kHz. Grabe de nuevo."
        )

    try:
        speechsdk = _speech_sdk()
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region,
        )
        speech_config.speech_recognition_language = "es-MX"
        audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=sample_rate,
            bits_per_sample=sample_width * 8,
            channels=channels,
        )
        input_stream = speechsdk.audio.PushAudioInputStream(
            stream_format=audio_format,
        )
        input_stream.write(audio_data)
        input_stream.close()
        audio_config = speechsdk.audio.AudioConfig(stream=input_stream)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )
        result = recognizer.recognize_once_async().get()
    except (RuntimeError, ValueError) as error:
        raise SpeechServiceError(
            "Azure Speech no pudo transcribir el audio. "
            "Verifique el servicio e intente de nuevo o continúe por texto."
        ) from error

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        transcription = result.text.strip()
        if transcription:
            return transcription
        raise SpeechServiceError("No se reconoció voz en la grabación.")
    if result.reason == speechsdk.ResultReason.NoMatch:
        raise SpeechServiceError(
            "No se reconoció voz. Hable con claridad e intente de nuevo."
        )
    raise SpeechServiceError(
        "Azure Speech no pudo transcribir el audio. "
        "Verifique el servicio e intente de nuevo o continúe por texto."
    )


def sintetizar_voz(
    texto: str,
    speech_key: str | None,
    speech_region: str | None,
) -> bytes:
    _validate_credentials(speech_key, speech_region)
    if not texto.strip():
        raise SpeechServiceError("No hay texto para convertir a voz.")

    try:
        speechsdk = _speech_sdk()
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region,
        )
        speech_config.speech_synthesis_voice_name = "es-MX-DaliaNeural"
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
        )
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None,
        )
        result = synthesizer.speak_text_async(texto).get()
    except (RuntimeError, ValueError) as error:
        raise SpeechServiceError(
            "Azure Speech no pudo generar la respuesta de voz. "
            "Verifique el servicio e intente de nuevo."
        ) from error

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise SpeechServiceError(
            "Azure Speech no pudo generar la respuesta de voz. "
            "Verifique el servicio e intente de nuevo."
        )
    if not result.audio_data:
        raise SpeechServiceError("Azure Speech devolvió audio vacío.")
    return bytes(result.audio_data)
