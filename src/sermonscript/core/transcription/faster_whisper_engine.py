from faster_whisper import WhisperModel

from sermonscript.core.transcription.base import TranscriptSegment, TranscriptionEngine, TranscriptionOptions


class FasterWhisperEngine(TranscriptionEngine):
    def __init__(self, model_name: str, device: str = "auto", compute_type: str = "int8") -> None:
        self.model = WhisperModel(model_name, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str, options: TranscriptionOptions):
        segments, _info = self.model.transcribe(
            audio_path,
            language=options.language,
            beam_size=options.beam_size,
            vad_filter=options.vad_filter,
            initial_prompt=options.initial_prompt,
        )

        for seg in segments:
            yield TranscriptSegment(
                start=seg.start,
                end=seg.end,
                text=seg.text.strip(),
                avg_logprob=getattr(seg, "avg_logprob", None),
                no_speech_prob=getattr(seg, "no_speech_prob", None),
            )
